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
)
from security import get_current_user

router = APIRouter(tags=["Blogs & Comments"])


@router.post("/blog", response_model=Blog, status_code=status.HTTP_201_CREATED)
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
    return new_blog


@router.get("/blog/{blog_id}", response_model=BlogDetailResponse)
def getBlog(blog_id: int, session: Session = Depends(get_session)):
    blog = session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    likes = session.exec(
        select(func.count(LikeTracker.liker_id)).where(LikeTracker.blog_id == blog_id)
    ).one()
    comments = session.exec(
        select(func.count(Comment.id)).where(Comment.blog_id == blog_id)
    ).one()

    return BlogDetailResponse(
        id=blog.id,
        title=blog.title,
        content=blog.content,
        author_id=blog.author_id,
        likes_count=likes,
        comments_count=comments,
    )


@router.get("/blogs", response_model=List[BlogDetailResponse])
def getAllBlogs(session: Session = Depends(get_session)):
    blogs = session.exec(select(Blog)).all()
    result = []
    for b in blogs:
        likes = session.exec(
            select(func.count(LikeTracker.liker_id)).where(LikeTracker.blog_id == b.id)
        ).one()
        comments = session.exec(
            select(func.count(Comment.id)).where(Comment.blog_id == b.id)
        ).one()
        result.append(
            BlogDetailResponse(
                id=b.id,
                title=b.title,
                content=b.content,
                author_id=b.author_id,
                likes_count=likes,
                comments_count=comments,
            )
        )
    return result


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
    return new_comment


@router.get("/blog/{blog_id}/comments", response_model=List[CommentResponse])
def getBlogComments(blog_id: int, session: Session = Depends(get_session)):
    if not session.get(Blog, blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")
    return session.exec(select(Comment).where(Comment.blog_id == blog_id)).all()


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