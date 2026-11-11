#To introduce /feed and aggregated joins
from typing import Optional
from sqlmodel import Field, SQLModel


# ==============================================================================
# BASE MODELS (Shared Core Attributes)
# ==============================================================================


class UserBase(SQLModel):
    name: str = Field(nullable=False)
    username: str = Field(unique=True, index=True, nullable=False)
    email: str = Field(unique=True, index=True, nullable=False)
    bio: Optional[str] = Field(default=None)


class BlogBase(SQLModel):
    title: str = Field(nullable=False)
    content: str = Field(nullable=False)


class CommentBase(SQLModel):
    text: str = Field(nullable=False)


# ==============================================================================
# DATABASE TABLES (Entities)
# ==============================================================================


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(nullable=False)


class Blog(BlogBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id", nullable=False)


class Comment(CommentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    commenter_id: int = Field(foreign_key="user.id", nullable=False)
    blog_id: int = Field(foreign_key="blog.id", nullable=False)


class LikeTracker(SQLModel, table=True):
    liker_id: int = Field(foreign_key="user.id", primary_key=True)
    blog_id: int = Field(foreign_key="blog.id", primary_key=True)


class UserFollow(SQLModel, table=True):
    follower_id: int = Field(foreign_key="user.id", primary_key=True)
    followed_id: int = Field(foreign_key="user.id", primary_key=True)


# ==============================================================================
# SCHEMAS (Request & Response)
# ==============================================================================


# User Schemas
class UserCreate(UserBase):
    password: str


class UserGet(UserBase):
    id: int
    followers_count: int = 0


class UserPut(UserBase):
    password: Optional[str] = None


class Token(SQLModel):
    access_token: str
    token_type: str


# Blog Schemas
class BlogCreate(BlogBase):
    pass


class BlogDetailResponse(BlogBase):
    id: int
    author_id: int
    author_name: str
    author_username: str
    likes_count: int = 0
    comments_count: int = 0


# Comment Schemas
class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: int
    text: str
    blog_id: int
    commenter_id: int
    commenter_name: str
    commenter_username: str