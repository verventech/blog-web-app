import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Annotated, List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import SQLModel, Field, Session, create_engine, select, func

# ==============================================================================
# 1. DATABASE SETUP
# ==============================================================================

DB_FILENAME = "blog_app.db"

def init_db():
    conn = sqlite3.connect(DB_FILENAME)
    with open("init.sql", "r") as file:
        conn.executescript(file.read())
    conn.commit()
    conn.close()

init_db()

engine = create_engine(f"sqlite:///{DB_FILENAME}", connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session


# ==============================================================================
# 2. SECURITY CONFIGURATION (BCRYPT & JWT)
# ==============================================================================

SECRET_KEY = "your-custom-production-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ==============================================================================
# 3. DATABASE MODELS (Entities)
# ==============================================================================

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    username: str = Field(unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    email: str = Field(unique=True, nullable=False)
    bio: Optional[str] = Field(default=None)


class Blog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    content: str = Field(nullable=False)
    author_id: int = Field(foreign_key="user.id", nullable=False)


class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str = Field(nullable=False)
    commenter_id: int = Field(foreign_key="user.id", nullable=False)
    blog_id: int = Field(foreign_key="blog.id", nullable=False)


class LikeTracker(SQLModel, table=True):
    liker_id: int = Field(foreign_key="user.id", primary_key=True)
    blog_id: int = Field(foreign_key="blog.id", primary_key=True)


class UserFollow(SQLModel, table=True):
    follower_id: int = Field(foreign_key="user.id", primary_key=True)
    followed_id: int = Field(foreign_key="user.id", primary_key=True)


# ==============================================================================
# 4. REQUEST / RESPONSE SCHEMAS
# ==============================================================================

class UserCreate(SQLModel):
    name: str
    username: str
    password: str
    email: str
    bio: Optional[str] = None


class UserGet(SQLModel):
    id: int
    name: str
    username: str
    email: str
    bio: Optional[str] = None


class UserPut(SQLModel):
    name: str
    username: str
    password: Optional[str] = None
    email: str
    bio: Optional[str] = None


class Token(SQLModel):
    access_token: str
    token_type: str


class BlogCreate(SQLModel):
    title: str
    content: str


class BlogDetailResponse(SQLModel):
    id: int
    title: str
    content: str
    author_id: int
    likes_count: int
    comments_count: int


class CommentCreate(SQLModel):
    text: str


class CommentResponse(SQLModel):
    id: int
    text: str
    commenter_id: int
    blog_id: int


# ==============================================================================
# 5. AUTH DEPENDENCY
# ==============================================================================

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    return user


# ==============================================================================
# 6. FASTAPI APP & ROUTES
# ==============================================================================

app = FastAPI(title="Blog Backend - Iteration 2")


# ----------------------- AUTH & REGISTRATION (PUBLIC) -----------------------

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    clean_username = form_data.username.strip().lower()
    user = session.exec(select(User).where(func.lower(User.username) == clean_username)).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/user", response_model=UserGet, status_code=status.HTTP_201_CREATED)
def createUser(user: UserCreate, session: Session = Depends(get_session)):
    clean_username = user.username.strip().lower()
    clean_email = user.email.strip().lower()

    if session.exec(select(User).where(func.lower(User.username) == clean_username)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken.."
        )

    if session.exec(select(User).where(func.lower(User.email) == clean_email)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.."
        )

    db_user = User(
        name=user.name.strip(),
        username=clean_username,
        email=clean_email,
        bio=user.bio,
        hashed_password=hash_password(user.password)
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


# -------------------------- USER ROUTES (MIXED) ------------------------------

@app.get("/user/me", response_model=UserGet)
def getMyProfile(current_user: User = Depends(get_current_user)):
    """🔒 Locked: Profile of the currently logged-in user."""
    return current_user


@app.put("/user/me", response_model=UserGet)
def editCurrentUser(
    updated_user: UserPut, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """🔒 Locked: Updates only the logged-in user's own profile."""
    clean_username = updated_user.username.strip().lower()
    clean_email = updated_user.email.strip().lower()

    if clean_username != current_user.username:
        if session.exec(select(User).where(func.lower(User.username) == clean_username)).first():
            raise HTTPException(status_code=409, detail="Username already in use")

    if clean_email != current_user.email:
        if session.exec(select(User).where(func.lower(User.email) == clean_email)).first():
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


@app.get("/user/{user_id}", response_model=UserGet)
def getUser(user_id: int, session: Session = Depends(get_session)):
    """🔓 Public: Read any author's public profile."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# -------------------------- BLOG ROUTES (MIXED) ------------------------------

@app.post("/blog", response_model=Blog, status_code=status.HTTP_201_CREATED)
def createBlog(
    blog: BlogCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """🔒 Locked: Author ID is automatically bound to the logged-in user."""
    new_blog = Blog(
        title=blog.title,
        content=blog.content,
        author_id=current_user.id
    )
    session.add(new_blog)
    session.commit()
    session.refresh(new_blog)
    return new_blog


@app.get("/blog/{blog_id}", response_model=BlogDetailResponse)
def getBlog(blog_id: int, session: Session = Depends(get_session)):
    """🔓 Public: Read any blog and its counts."""
    blog = session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    likes = session.exec(select(func.count(LikeTracker.liker_id)).where(LikeTracker.blog_id == blog_id)).one()
    comments = session.exec(select(func.count(Comment.id)).where(Comment.blog_id == blog_id)).one()

    return BlogDetailResponse(
        id=blog.id,
        title=blog.title,
        content=blog.content,
        author_id=blog.author_id,
        likes_count=likes,
        comments_count=comments
    )


@app.get("/blogs", response_model=List[BlogDetailResponse])
def getAllBlogs(session: Session = Depends(get_session)):
    """🔓 Public: Read feed of all blogs."""
    blogs = session.exec(select(Blog)).all()
    result = []
    for b in blogs:
        likes = session.exec(select(func.count(LikeTracker.liker_id)).where(LikeTracker.blog_id == b.id)).one()
        comments = session.exec(select(func.count(Comment.id)).where(Comment.blog_id == b.id)).one()
        result.append(BlogDetailResponse(
            id=b.id,
            title=b.title,
            content=b.content,
            author_id=b.author_id,
            likes_count=likes,
            comments_count=comments
        ))
    return result


@app.delete("/blog/{blog_id}")
def deleteBlog(
    blog_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """🔒 Locked: Enforces ownership check (only author can delete)."""
    blog = session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    if blog.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to delete this blog post"
        )

    session.delete(blog)
    session.commit()
    return {"message": "Blog and all associated comments/likes deleted successfully"}


# ------------------------ COMMENT ROUTES (MIXED) -----------------------------

@app.post("/blog/{blog_id}/comment", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def addComment(
    blog_id: int, 
    comment_data: CommentCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """🔒 Locked: Commenter ID is extracted from current_user."""
    if not session.get(Blog, blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")

    new_comment = Comment(
        text=comment_data.text,
        commenter_id=current_user.id,
        blog_id=blog_id
    )
    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)
    return new_comment


@app.get("/blog/{blog_id}/comments", response_model=List[CommentResponse])
def getBlogComments(blog_id: int, session: Session = Depends(get_session)):
    """🔓 Public: Anyone can read comments."""
    if not session.get(Blog, blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")
    return session.exec(select(Comment).where(Comment.blog_id == blog_id)).all()


# ----------------------- LIKE & FOLLOW ROUTES (LOCKED) -----------------------

@app.post("/blog/{blog_id}/like")
def toggleLike(
    blog_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """🔒 Locked: Uses current_user.id as liker_id."""
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


@app.post("/user/{target_user_id}/follow")
def followUser(
    target_user_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """🔒 Locked: Uses current_user.id as follower_id."""
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
        new_follow = UserFollow(follower_id=current_user.id, followed_id=target_user_id)
        session.add(new_follow)
        session.commit()
        return {"message": f"Now following user {target_user_id}", "following": True}