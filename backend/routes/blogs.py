from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, func, select

from db import get_session
from models import (
    Blog,
    BlogCreate,
    BlogDetailResponse,
    Comment,
    CommentCreate,
    CommentResponse,
    LikeTracker,
    User,
    UserFollow,
)
from security import get_current_user

router = APIRouter(tags=["Blogs & Comments"])


@router.get("/feed", response_model=List[BlogDetailResponse])
def getFeed(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Posts from accounts the current user follows."""
    likes_count = (
        select(func.count(LikeTracker.liker_id))
        .where(LikeTracker.blog_id == Blog.id)
        .correlate(Blog)
        .scalar_subquery()
    )
    comments_count = (
        select(func.count(Comment.id))
        .where(Comment.blog_id == Blog.id)
        .correlate(Blog)
        .scalar_subquery()
    )
    statement = (
        select(
            Blog.id,
            Blog.title,
            Blog.content,
            Blog.author_id,
            User.name.label("author_name"),
            User.username.label("author_username"),
            likes_count.label("likes_count"),
            comments_count.label("comments_count"),
        )
        .join(UserFollow, UserFollow.followed_id == Blog.author_id)
        .join(User, User.id == Blog.author_id)
        .where(UserFollow.follower_id == current_user.id)
        .order_by(Blog.id.desc())
    )
    rows = session.exec(statement).all()

    return [
        BlogDetailResponse(
            id=r[0],
            title=r[1],
            content=r[2],
            author_id=r[3],
            author_name=r[4],
            author_username=r[5],
            likes_count=r[6],
            comments_count=r[7],
        )
        for r in rows
    ]


@router.post("/blog", response_model=BlogDetailResponse, status_code=status.HTTP_201_CREATED)
def createBlog(
    blog: BlogCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    new_blog = Blog(
        title=blog.title,
        content=blog.content,
        author_id=current_user.id,
    )
    session.add(new_blog)
    session.commit()
    session.refresh(new_blog)

    return BlogDetailResponse(
        id=new_blog.id,
        title=new_blog.title,
        content=new_blog.content,
        author_id=new_blog.author_id,
        author_name=current_user.name,
        author_username=current_user.username,
        likes_count=0,
        comments_count=0,
    )


@router.get("/blog/{blog_id}", response_model=BlogDetailResponse)
def getBlog(blog_id: int, session: Session = Depends(get_session)):
    likes_count = (
        select(func.count(LikeTracker.liker_id))
        .where(LikeTracker.blog_id == Blog.id)
        .correlate(Blog)
        .scalar_subquery()
    )
    comments_count = (
        select(func.count(Comment.id))
        .where(Comment.blog_id == Blog.id)
        .correlate(Blog)
        .scalar_subquery()
    )
    statement = (
        select(
            Blog.id,
            Blog.title,
            Blog.content,
            Blog.author_id,
            User.name.label("author_name"),
            User.username.label("author_username"),
            likes_count.label("likes_count"),
            comments_count.label("comments_count"),
        )
        .join(User, User.id == Blog.author_id)
        .where(Blog.id == blog_id)
    )
    row = session.exec(statement).first()
    if not row:
        raise HTTPException(status_code=404, detail="Blog not found")

    return BlogDetailResponse(
        id=row[0],
        title=row[1],
        content=row[2],
        author_id=row[3],
        author_name=row[4],
        author_username=row[5],
        likes_count=row[6],
        comments_count=row[7],
    )


@router.get("/blogs", response_model=List[BlogDetailResponse])
def getAllBlogs(session: Session = Depends(get_session)):
    likes_count = (
        select(func.count(LikeTracker.liker_id))
        .where(LikeTracker.blog_id == Blog.id)
        .correlate(Blog)
        .scalar_subquery()
    )
    comments_count = (
        select(func.count(Comment.id))
        .where(Comment.blog_id == Blog.id)
        .correlate(Blog)
        .scalar_subquery()
    )
    statement = (
        select(
            Blog.id,
            Blog.title,
            Blog.content,
            Blog.author_id,
            User.name.label("author_name"),
            User.username.label("author_username"),
            likes_count.label("likes_count"),
            comments_count.label("comments_count"),
        )
        .join(User, User.id == Blog.author_id)
        .order_by(Blog.id.desc())
    )
    rows = session.exec(statement).all()

    return [
        BlogDetailResponse(
            id=r[0],
            title=r[1],
            content=r[2],
            author_id=r[3],
            author_name=r[4],
            author_username=r[5],
            likes_count=r[6],
            comments_count=r[7],
        )
        for r in rows
    ]


@router.delete("/blog/{blog_id}")
def deleteBlog(
    blog_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    blog = session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    if blog.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this blog post",
        )

    session.delete(blog)
    session.commit()
    return {"message": "Blog and all associated comments/likes deleted successfully"}


@router.post(
    "/blog/{blog_id}/comment",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def addComment(
    blog_id: int,
    comment_data: CommentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not session.get(Blog, blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")

    new_comment = Comment(
        text=comment_data.text,
        commenter_id=current_user.id,
        blog_id=blog_id,
    )
    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)

    return CommentResponse(
        id=new_comment.id,
        text=new_comment.text,
        blog_id=new_comment.blog_id,
        commenter_id=new_comment.commenter_id,
        commenter_name=current_user.name,
        commenter_username=current_user.username,
    )


@router.get("/blog/{blog_id}/comments", response_model=List[CommentResponse])
def getBlogComments(blog_id: int, session: Session = Depends(get_session)):
    if not session.get(Blog, blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")

    statement = (
        select(
            Comment.id,
            Comment.text,
            Comment.blog_id,
            Comment.commenter_id,
            User.name.label("commenter_name"),
            User.username.label("commenter_username"),
        )
        .join(User, User.id == Comment.commenter_id)
        .where(Comment.blog_id == blog_id)
        .order_by(Comment.id.asc())
    )
    rows = session.exec(statement).all()

    return [
        CommentResponse(
            id=r[0],
            text=r[1],
            blog_id=r[2],
            commenter_id=r[3],
            commenter_name=r[4],
            commenter_username=r[5],
        )
        for r in rows
    ]


@router.post("/blog/{blog_id}/like")
def toggleLike(
    blog_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not session.get(Blog, blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")

    existing_like = session.get(LikeTracker, (current_user.id, blog_id))
    if existing_like:
        session.delete(existing_like)
        session.commit()
        return {"message": "Post unliked", "liked": False}
    else:
        new_like = LikeTracker(liker_id=current_user.id, blog_id=blog_id)
        session.add(new_like)
        session.commit()
        return {"message": "Post liked", "liked": True}