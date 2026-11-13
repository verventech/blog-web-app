import os
import time
import bcrypt
import psycopg2

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "blog_app"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "blogpsqlpass_123"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5433")),
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
    cur.execute("SET work_mem = '256MB';")
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

    cur.execute('SELECT MIN(id), MAX(id), COUNT(*) FROM "user";')
    min_uid, max_uid, total_users = cur.fetchone()

    # 2. Insert blogs directly via generate_series
    cur.execute("SELECT COALESCE(MAX(id), 0), COUNT(*) FROM blog;")
    max_bid, current_blogs = cur.fetchone()
    needed_blogs = max(0, TARGET_BLOGS - current_blogs)

    if needed_blogs > 0:
        t1 = time.perf_counter()
        cur.execute(
            """
            INSERT INTO blog (title, content, author_id)
            SELECT
                'Benchmark Architecture Post #' || g,
                'Evaluating index scans and pagination at million-row scale for post #' || g,
                %s + ((g * 7919) %% %s)
            FROM generate_series(%s, %s) AS g;
            """,
            (min_uid, total_users, max_bid + 1, max_bid + needed_blogs),
        )
        conn.commit()
        print(f"[2/5] Inserted {needed_blogs:,} blogs in {time.perf_counter() - t1:.2f}s")

    cur.execute("SELECT MIN(id), MAX(id), COUNT(*) FROM blog;")
    min_bid, max_bid, total_blogs = cur.fetchone()

    # 3. Insert follow relationships (coprime stride guarantees zero duplicates without sorting)
    t1 = time.perf_counter()
    cur.execute(
        """
        INSERT INTO userfollow (follower_id, followed_id)
        SELECT
            u,
            %s + (((u - %s) + s * 7919) %% %s)
        FROM generate_series(%s, %s) AS u
        CROSS JOIN generate_series(1, %s) AS s
        ON CONFLICT (follower_id, followed_id) DO NOTHING;
        """,
        (min_uid, min_uid, total_users, min_uid, max_uid, FOLLOWS_PER_USER),
    )
    conn.commit()
    print(f"[3/5] Inserted follows in {time.perf_counter() - t1:.2f}s")

    # 4. Insert likes directly via generate_series
    t1 = time.perf_counter()
    cur.execute(
        """
        INSERT INTO liketracker (liker_id, blog_id)
        SELECT
            %s + (((b * 31) + s * 104729) %% %s),
            b
        FROM generate_series(%s, %s) AS b
        CROSS JOIN generate_series(1, %s) AS s
        ON CONFLICT (liker_id, blog_id) DO NOTHING;
        """,
        (min_uid, total_users, min_bid, max_bid, LIKES_PER_BLOG),
    )
    conn.commit()
    print(f"[4/5] Inserted likes in {time.perf_counter() - t1:.2f}s")

    # 5. Insert comments directly via generate_series
    t1 = time.perf_counter()
    cur.execute(
        """
        INSERT INTO comment (text, commenter_id, blog_id)
        SELECT
            'Great breakdown on post #' || b,
            %s + ((b + s * 4999) %% %s),
            b
        FROM generate_series(%s, %s) AS b
        CROSS JOIN generate_series(1, %s) AS s;
        """,
        (min_uid, total_users, min_bid, max_bid, COMMENTS_PER_BLOG),
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