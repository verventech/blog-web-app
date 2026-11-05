-- 1. Users table
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio TEXT
);

-- 2. Blogs table
CREATE TABLE IF NOT EXISTS blog (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    author_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE
);

-- 3. Comments table
CREATE TABLE IF NOT EXISTS comment (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    commenter_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    blog_id INTEGER NOT NULL REFERENCES blog(id) ON DELETE CASCADE
);

-- 4. Like Tracker
CREATE TABLE IF NOT EXISTS liketracker (
    liker_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    blog_id INTEGER NOT NULL REFERENCES blog(id) ON DELETE CASCADE,
    PRIMARY KEY (liker_id, blog_id)
);

-- 5. User Follows
CREATE TABLE IF NOT EXISTS userfollow (
    follower_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    followed_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    PRIMARY KEY (follower_id, followed_id)
);

-- 6. Indexes for query optimization
CREATE INDEX IF NOT EXISTS ix_blog_author_id ON blog(author_id);
CREATE INDEX IF NOT EXISTS ix_comment_blog_id ON comment(blog_id);
CREATE INDEX IF NOT EXISTS ix_liketracker_blog_id ON liketracker(blog_id);
CREATE INDEX IF NOT EXISTS ix_userfollow_followed ON userfollow(followed_id);