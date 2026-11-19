from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from models import Blog, User
from routes.blogs import getAllBlogs


def test_pagination_splits_blogs_into_pages():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(
            name="Ali",
            username="ali",
            email="ali@test.com",
            hashed_password="123",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        session.add_all(
            [
                Blog(title=f"Post {number}", content="Body", author_id=user.id)
                for number in range(1, 4)
            ]
        )
        session.commit()

        page = getAllBlogs(session=session, limit=2, author_id=None)

        assert len(page.items) == 2
        assert page.has_more is True
