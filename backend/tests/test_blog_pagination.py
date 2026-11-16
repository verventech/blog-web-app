import unittest

from fastapi import HTTPException
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from models import Blog, User, UserFollow
from routes.blogs import getAllBlogs, getFeed


class BlogPaginationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

        self.viewer = User(
            name="Viewer",
            username="viewer",
            email="viewer@example.com",
            hashed_password="unused",
        )
        self.followed = User(
            name="Followed",
            username="followed",
            email="followed@example.com",
            hashed_password="unused",
        )
        self.other = User(
            name="Other",
            username="other",
            email="other@example.com",
            hashed_password="unused",
        )
        self.session.add_all([self.viewer, self.followed, self.other])
        self.session.commit()
        self.session.refresh(self.viewer)
        self.session.refresh(self.followed)
        self.session.refresh(self.other)

        self.session.add(UserFollow(follower_id=self.viewer.id, followed_id=self.followed.id))
        authors = [self.followed, self.other, self.followed, self.viewer, self.followed]
        self.blogs = [
            Blog(title=f"Story {index}", content="Content", author_id=author.id)
            for index, author in enumerate(authors, start=1)
        ]
        self.session.add_all(self.blogs)
        self.session.commit()
        for blog in self.blogs:
            self.session.refresh(blog)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_blogs_use_stable_cursor_pages_and_author_filter(self):
        first_page = getAllBlogs(session=self.session, limit=2, author_id=None)
        second_page = getAllBlogs(
            session=self.session,
            limit=2,
            cursor=first_page.next_cursor,
            author_id=None,
        )
        third_page = getAllBlogs(
            session=self.session,
            limit=2,
            cursor=second_page.next_cursor,
            author_id=None,
        )

        self.assertEqual(
            [item.id for item in first_page.items + second_page.items + third_page.items],
            [blog.id for blog in reversed(self.blogs)],
        )
        self.assertTrue(first_page.has_more)
        self.assertTrue(second_page.has_more)
        self.assertFalse(third_page.has_more)
        self.assertIsNone(third_page.next_cursor)

        author_page = getAllBlogs(
            session=self.session,
            limit=10,
            author_id=self.followed.id,
        )
        self.assertEqual(
            {item.author_id for item in author_page.items},
            {self.followed.id},
        )

    def test_feed_paginates_only_followed_authors(self):
        page = getFeed(
            session=self.session,
            current_user=self.viewer,
            limit=1,
        )
        items = list(page.items)
        while page.has_more:
            page = getFeed(
                session=self.session,
                current_user=self.viewer,
                limit=1,
                cursor=page.next_cursor,
            )
            items.extend(page.items)

        self.assertEqual(
            [item.id for item in items],
            [blog.id for blog in reversed(self.blogs) if blog.author_id == self.followed.id],
        )

    def test_invalid_cursor_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            getAllBlogs(
                session=self.session,
                cursor="invalid",
                limit=20,
                author_id=None,
            )

        self.assertEqual(context.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
