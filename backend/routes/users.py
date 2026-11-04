from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, func, select

from db import get_session
from models import User, UserCreate, UserFollow, UserGet, UserPut
from security import get_current_user, hash_password

router = APIRouter(tags=["Users"])


@router.post("/user", response_model=UserGet, status_code=status.HTTP_201_CREATED)
def createUser(user: UserCreate, session: Session = Depends(get_session)):
    clean_username = user.username.strip().lower()
    clean_email = user.email.strip().lower()

    if session.exec(
        select(User).where(func.lower(User.username) == clean_username)
    ).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken..",
        )

    if session.exec(
        select(User).where(func.lower(User.email) == clean_email)
    ).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered..",
        )

    db_user = User(
        name=user.name.strip(),
        username=clean_username,
        email=clean_email,
        bio=user.bio,
        hashed_password=hash_password(user.password),
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get("/user/me", response_model=UserGet)
def getMyProfile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/user/me", response_model=UserGet)
def editCurrentUser(
    updated_user: UserPut,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    clean_username = updated_user.username.strip().lower()
    clean_email = updated_user.email.strip().lower()

    if clean_username != current_user.username:
        if session.exec(
            select(User).where(func.lower(User.username) == clean_username)
        ).first():
            raise HTTPException(status_code=409, detail="Username already in use")

    if clean_email != current_user.email:
        if session.exec(
            select(User).where(func.lower(User.email) == clean_email)
        ).first():
            raise HTTPException(status_code=409, detail="Email already in use")

    current_user.name = updated_user.name.strip()
    current_user.username = clean_username
    current_user.email = clean_email
    current_user.bio = updated_user.bio

    if updated_user.password:
        current_user.hashed_password = hash_password(updated_user.password)

    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.get("/user/{user_id}", response_model=UserGet)
def getUser(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/user/{target_user_id}/follow")
def followUser(
    target_user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Users cannot follow themselves")
    if not session.get(User, target_user_id):
        raise HTTPException(status_code=404, detail="Target user not found")

    existing_follow = session.get(UserFollow, (current_user.id, target_user_id))
    if existing_follow:
        session.delete(existing_follow)
        session.commit()
        return {"message": f"Unfollowed user {target_user_id}", "following": False}
    else:
        new_follow = UserFollow(
            follower_id=current_user.id, followed_id=target_user_id
        )
        session.add(new_follow)
        session.commit()
        return {"message": f"Now following user {target_user_id}", "following": True}