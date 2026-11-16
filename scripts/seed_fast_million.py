import os
import time
import bcrypt
import psycopg2

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "blog_app"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "blogpsqlpass_123"),
    "host": os.getenv("POSTGRES_HOST", "db"),
    "port": int(os.getenv("POSTGRES_INTERNAL_PORT", "5432")),
}

TARGET_USERS = int(os.getenv("TARGET_USERS", "1000000"))
TARGET_BLOGS = int(os.getenv("TARGET_BLOGS", "6000000"))
FOLLOWS_PER_USER = int(os.getenv("FOLLOWS_PER_USER", "5"))
LIKES_PER_BLOG = int(os.getenv("LIKES_PER_BLOG", "2"))
COMMENTS_PER_BLOG = int(os.getenv("COMMENTS_PER_BLOG", "1"))

DEFAULT_HASH = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")


def seed_fast():
    t0 = time.perf_counter()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("SET synchronous_commit = OFF;")
    cur.execute("SET work_mem = '512MB';")
    cur.execute("SET maintenance_work_mem = '512MB';")

    # 1. Discover existing users so accounts like 'faizan' stay intact
    cur.execute('SELECT COALESCE(MAX(id), 0), COUNT(*) FROM "user";')
    max_uid, current_users = cur.fetchone()
    needed_users = max(0, TARGET_USERS - current_users)

    if needed_users > 0:
        t1 = time.perf_counter()
        cur.execute(
            """
            INSERT INTO "user" (name, username, hashed_password, email, bio)
            SELECT
                'User ' || g,
                'user_' || g,
                %s,
                'user_' || g || '@testbench.local',
                'Scale benchmark engineer #' || g
            FROM generate_series(%s, %s) AS g
            ON CONFLICT (username) DO NOTHING;
            """,
            (DEFAULT_HASH, max_uid + 1, max_uid + needed_users),
        )
        conn.commit()
        print(f"[1/5] Inserted {needed_users:,} users in {time.perf_counter() - t1:.2f}s")
    else:
        print(f"[1/5] Skipping users — already at {current_users:,}")

    cur.execute('SELECT COUNT(*) FROM "user";')
    total_users = cur.fetchone()[0]

    # 2. Insert blogs using actual user IDs (safe against deleted user IDs)
    cur.execute("SELECT COALESCE(MAX(id), 0), COUNT(*) FROM blog;")
    max_bid, current_blogs = cur.fetchone()
    needed_blogs = max(0, TARGET_BLOGS - current_blogs)

    if needed_blogs > 0:
        t1 = time.perf_counter()
        cur.execute(
            """
            WITH users AS (
                SELECT ARRAY(SELECT id FROM "user" ORDER BY id) AS ids
            )
            INSERT INTO blog (title, content, author_id)
            SELECT
                'Benchmark Architecture Post #' || g,
                'Evaluating index scans and pagination at million-row scale for post #' || g,
                users.ids[1 + ((g::bigint * 7919) %% array_length(users.ids, 1))]
            FROM generate_series(%s, %s) AS g
            CROSS JOIN users;
            """,
            (max_bid + 1, max_bid + needed_blogs),
        )
        conn.commit()
        print(f"[2/5] Inserted {needed_blogs:,} blogs in {time.perf_counter() - t1:.2f}s")
    else:
        print(f"[2/5] Skipping blogs — already at {current_blogs:,}")

    cur.execute("SELECT COUNT(*) FROM blog;")
    total_blogs = cur.fetchone()[0]

    # 3. Insert follow relationships using actual user IDs
    cur.execute("SELECT COUNT(*) FROM userfollow;")
    current_follows = cur.fetchone()[0]
    if current_follows < total_users * (FOLLOWS_PER_USER - 1):
        t1 = time.perf_counter()
        cur.execute(
            """
            WITH users AS (
                SELECT ARRAY(SELECT id FROM "user" ORDER BY id) AS ids
            ),
            indexed_users AS (
                SELECT u.id AS follower_id, u.ord AS idx
                FROM "user"
                CROSS JOIN LATERAL (SELECT id) AS x
                JOIN unnest((SELECT ids FROM users)) WITH ORDINALITY AS u(id, ord) ON true
            )
            INSERT INTO userfollow (follower_id, followed_id)
            SELECT
                iu.follower_id,
                users.ids[1 + (((iu.idx - 1) + s::bigint * 7919) %% array_length(users.ids, 1))]
            FROM indexed_users iu
            CROSS JOIN generate_series(1, %s) AS s
            CROSS JOIN users
            WHERE iu.follower_id <> users.ids[1 + (((iu.idx - 1) + s::bigint * 7919) %% array_length(users.ids, 1))]
            ON CONFLICT (follower_id, followed_id) DO NOTHING;
            """,
            (FOLLOWS_PER_USER,),
        )
        conn.commit()
        print(f"[3/5] Inserted follows in {time.perf_counter() - t1:.2f}s")
    else:
        print(f"[3/5] Skipping follows — already at {current_follows:,}")

    # 4. Insert likes directly from existing blog IDs and real user IDs
    t1 = time.perf_counter()
    cur.execute(
        """
        WITH users AS (
            SELECT ARRAY(SELECT id FROM "user" ORDER BY id) AS ids
        )
        INSERT INTO liketracker (liker_id, blog_id)
        SELECT
            users.ids[1 + (((b.id::bigint * 31) + s::bigint * 104729) %% array_length(users.ids, 1))],
            b.id
        FROM blog b
        CROSS JOIN generate_series(1, %s) AS s
        CROSS JOIN users
        ON CONFLICT (liker_id, blog_id) DO NOTHING;
        """,
        (LIKES_PER_BLOG,),
    )
    conn.commit()
    print(f"[4/5] Inserted likes in {time.perf_counter() - t1:.2f}s")

    # 5. Insert comments directly from existing blog IDs and real user IDs
    t1 = time.perf_counter()
    cur.execute(
        """
        WITH users AS (
            SELECT ARRAY(SELECT id FROM "user" ORDER BY id) AS ids
        )
        INSERT INTO comment (text, commenter_id, blog_id)
        SELECT
            'Great breakdown on post #' || b.id,
            users.ids[1 + ((b.id::bigint + s::bigint * 4999) %% array_length(users.ids, 1))],
            b.id
        FROM blog b
        CROSS JOIN generate_series(1, %s) AS s
        CROSS JOIN users;
        """,
        (COMMENTS_PER_BLOG,),
    )
    conn.commit()
    print(f"[5/5] Inserted comments in {time.perf_counter() - t1:.2f}s")

    # Sync sequences & update planner statistics
    for tbl in ('"user"', "blog", "comment"):
        cur.execute(
            f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), COALESCE(MAX(id), 1)) FROM {tbl};"
        )
    conn.commit()

    cur.close()
    conn.autocommit = True
    with conn.cursor() as acur:
        acur.execute("ANALYZE;")
    conn.close()

    print(f"\nDone in {time.perf_counter() - t0:.2f}s — {total_users:,} users, {total_blogs:,} blogs.")


if __name__ == "__main__":
    seed_fast()