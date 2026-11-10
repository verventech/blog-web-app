import os
import random
import bcrypt
import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "blog_app"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "blogpsqlpass_123"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}

TARGET_USERS = int(os.getenv("TARGET_USERS", "500"))
TARGET_TOTAL_BLOGS = int(os.getenv("TARGET_BLOGS", "350"))

salt = bcrypt.gensalt()
DEFAULT_HASH = bcrypt.hashpw(b"password123", salt).decode("utf-8")

FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "Riley",
    "Jesse", "Casey", "Avery", "Cameron", "Dakota", "Reese", "Rowan", "Hayden"
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson"
]
TITLES = [
    "Mastering FastAPI and PostgreSQL Architecture",
    "System Design: Contrasting Fan-Out on Read vs Fan-Out on Write",
    "How to Optimize N+1 Query Aggregations in SQL",
    "Building Microservices with Docker and Reverse Proxies",
    "Benchmarking Database Latency Under High Concurrency",
    "A Guide to Indexing Strategies for Feed Generation",
    "Scaling Read-Heavy Applications with In-Memory Caches",
    "Understanding Connection Pooling and Concurrency Limits",
    "Event-Driven Architectures with Kafka and Redis Streams",
    "Designing High-Throughput Relational Schemas",
    "Mitigating Lock Contention in PostgreSQL Write Queues",
    "Cache Invalidation Trade-offs: Write-Through vs Write-Back",
]
COMMENTS = [
    "Really insightful post, thanks for sharing!",
    "Great breakdown of the architecture bottlenecks.",
    "Encountered this exact issue in production last month.",
    "Looking forward to reading the next part!",
    "Bookmarking this for system design review.",
    "Clear, concise, and straight to the point.",
    "How does this scale when read-to-write ratio hits 100:1?",
    "Solid analysis of the query execution plan.",
]


def sync_sequences(cur):
    """Resynchronizes PostgreSQL sequences to prevent duplicate key collisions."""
    tables = [('"user"', "id"), ("blog", "id"), ("comment", "id")]
    for tbl, col in tables:
        cur.execute(f"""
            DO $$
            DECLARE
                seq_name TEXT;
                max_val BIGINT;
            BEGIN
                SELECT pg_get_serial_sequence('{tbl}', '{col}') INTO seq_name;
                IF seq_name IS NOT NULL THEN
                    EXECUTE 'SELECT COALESCE(MAX({col}), 0) FROM {tbl}' INTO max_val;
                    IF max_val > 0 THEN
                        PERFORM setval(seq_name, max_val, true);
                    ELSE
                        PERFORM setval(seq_name, 1, false);
                    END IF;
                END IF;
            END $$;
        """)


def seed():
    print(f"[1/6] Connecting to {DB_CONFIG['dbname']} at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Step 0: Ensure sequences are aligned before touching data
    sync_sequences(cur)
    conn.commit()

    # 1. Discover existing users
    cur.execute('SELECT id, username FROM "user";')
    existing_user_rows = cur.fetchall()
    existing_user_ids = [r[0] for r in existing_user_rows]
    current_user_count = len(existing_user_ids)
    print(f"[2/6] Discovered {current_user_count} pre-existing users in DB.")

    # Expand users up to TARGET_USERS if needed
    if current_user_count < TARGET_USERS:
        needed = TARGET_USERS - current_user_count
        new_users = []
        for i in range(1, needed + 1):
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            rand_suffix = random.randint(1000, 999999)
            username = f"user_{current_user_count + i}_{rand_suffix}"
            email = f"{username}@testbench.local"
            bio = f"Platform engineer #{i} testing distributed queries."
            new_users.append((name, username, DEFAULT_HASH, email, bio))

        execute_values(
            cur,
            """
            INSERT INTO "user" (name, username, hashed_password, email, bio)
            VALUES %s
            ON CONFLICT (username) DO NOTHING;
            """,
            new_users,
            page_size=2000,
        )
        conn.commit()
        sync_sequences(cur)
        print(f"  Created {needed} synthetic users.")

    # Re-fetch all live user IDs (existing + newly created)
    cur.execute('SELECT id FROM "user";')
    all_user_ids = [r[0] for r in cur.fetchall()]
    if not all_user_ids:
        print("ERROR: No users present in database. Aborting.")
        cur.close()
        conn.close()
        return

    # 2. Add fresh blogs to EVERY pre-existing user AND backfill to TARGET_TOTAL_BLOGS
    print("[3/6] Generating blogs (including articles for discovered pre-existing users)...")
    blogs_to_insert = []

    # Guarantee that every existing user has at least 2 to 4 fresh blogs published under their ID
    for uid in existing_user_ids:
        blogs_count = random.randint(2, 4)
        for _ in range(blogs_count):
            title = f"{random.choice(TITLES)} (Author {uid})"
            content = (
                f"# {title}\n\n"
                "System architecture decisions dictate how your database performs under stress. "
                "Here we review indexing, query plans, and connection pool behavior.\n\n"
                "```sql\n"
                "EXPLAIN ANALYZE SELECT * FROM blog ORDER BY id DESC LIMIT 20;\n"
                "```\n\n"
                "Evaluating query plans and connection latency under high load."
            )
            blogs_to_insert.append((title, content, uid))

    # Check overall blog count and backfill remaining quota across all users
    cur.execute("SELECT count(*) FROM blog;")
    total_existing_blogs = cur.fetchone()[0]
    remaining_quota = max(0, TARGET_TOTAL_BLOGS - (total_existing_blogs + len(blogs_to_insert)))

    for i in range(remaining_quota):
        author = random.choice(all_user_ids)
        title = f"{random.choice(TITLES)} (Vol. {random.randint(10, 999)})"
        content = (
            f"# {title}\n\n"
            "Benchmarking fan-out latency and database query plans.\n\n"
            "Live system testing under concurrent follower loads."
        )
        blogs_to_insert.append((title, content, author))

    if blogs_to_insert:
        execute_values(
            cur,
            "INSERT INTO blog (title, content, author_id) VALUES %s;",
            blogs_to_insert,
            page_size=2000,
        )
        conn.commit()
        sync_sequences(cur)
        print(f"  Inserted {len(blogs_to_insert)} total blogs (including posts for existing users).")

    # Fetch complete collection of live blog IDs
    cur.execute("SELECT id FROM blog;")
    all_blog_ids = [r[0] for r in cur.fetchall()]

    # 3. Interconnect Follow Graph (guarantee existing users have followers & following)
    print("[4/6] Interconnecting follow networks for all users...")
    cur.execute("SELECT follower_id, followed_id FROM userfollow;")
    existing_follows = set(cur.fetchall())
    new_follows = set()

    # For each pre-existing user: ensure they have 15-40 followers and follow 10-25 creators
    for uid in existing_user_ids:
        other_users = [u for u in all_user_ids if u != uid]
        if not other_users:
            continue

        # Give them incoming followers
        num_followers = min(random.randint(15, 40), len(other_users))
        chosen_followers = random.sample(other_users, k=num_followers)
        for f in chosen_followers:
            pair = (f, uid)
            if pair not in existing_follows:
                new_follows.add(pair)

        # Make them follow other creators so their /feed has content
        num_following = min(random.randint(10, 25), len(other_users))
        chosen_following = random.sample(other_users, k=num_following)
        for c in chosen_following:
            pair = (uid, c)
            if pair not in existing_follows:
                new_follows.add(pair)

    # General social distribution across the rest of the users
    for uid in all_user_ids:
        candidates = [u for u in all_user_ids if u != uid]
        if not candidates:
            continue
        num_targets = min(random.randint(3, 12), len(candidates))
        for target in random.sample(candidates, k=num_targets):
            pair = (uid, target)
            if pair not in existing_follows:
                new_follows.add(pair)

    if new_follows:
        execute_values(
            cur,
            """
            INSERT INTO userfollow (follower_id, followed_id)
            VALUES %s
            ON CONFLICT (follower_id, followed_id) DO NOTHING;
            """,
            list(new_follows),
            page_size=2500,
        )
        conn.commit()
        print(f"  Added {len(new_follows)} new follow relationships.")

    # 4. Populate Likes on existing & new blogs
    print("[5/6] Distributing likes across blogs...")
    cur.execute("SELECT liker_id, blog_id FROM liketracker;")
    existing_likes = set(cur.fetchall())
    new_likes = set()

    for b_id in all_blog_ids:
        num_likes = min(random.randint(5, 25), len(all_user_ids))
        sampled_likers = random.sample(all_user_ids, k=num_likes)
        for liker in sampled_likers:
            pair = (liker, b_id)
            if pair not in existing_likes:
                new_likes.add(pair)

    if new_likes:
        execute_values(
            cur,
            """
            INSERT INTO liketracker (liker_id, blog_id)
            VALUES %s
            ON CONFLICT (liker_id, blog_id) DO NOTHING;
            """,
            list(new_likes),
            page_size=2500,
        )
        conn.commit()
        print(f"  Added {len(new_likes)} new likes.")

    # 5. Distribute Comments on existing & new blogs
    print("[6/6] Distributing comments across blogs...")
    new_comments = []
    for b_id in all_blog_ids:
        num_comments = min(random.randint(2, 6), len(all_user_ids))
        sampled_commenters = random.sample(all_user_ids, k=num_comments)
        for commenter in sampled_commenters:
            text = random.choice(COMMENTS)
            new_comments.append((text, commenter, b_id))

    if new_comments:
        execute_values(
            cur,
            "INSERT INTO comment (text, commenter_id, blog_id) VALUES %s;",
            new_comments,
            page_size=2500,
        )
        conn.commit()
        sync_sequences(cur)
        print(f"  Added {len(new_comments)} new comments.")

    conn.commit()
    cur.close()
    conn.close()

    print("-----------------------------------------------------------------")
    print("Database Dynamic Seeding Complete!")
    print(f"- Discovered Initial Users: {len(existing_user_ids)}")
    print(f"- Total Users Now:          {len(all_user_ids)}")
    print(f"- Total Blogs Now:          {len(all_blog_ids)}")
    print(f"- Total New Follows:        {len(new_follows)}")
    print(f"- Total New Likes:          {len(new_likes)}")
    print(f"- Total New Comments:       {len(new_comments)}")
    print("-----------------------------------------------------------------")


if __name__ == "__main__":
    seed()