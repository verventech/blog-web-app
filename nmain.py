import sqlite3
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select

# 1. Database Setup: Reads directly from your init.sql file
DB_FILENAME = "blog_app.db"

def init_db():
    conn = sqlite3.connect(DB_FILENAME) // connect to a db file. if missing, it creates a new file
    cursor = conn.cursor() // cursor allows python to run SQL commands in db
    with open("init.sql", "r") as file:
        cursor.executescript(file.read())
    conn.commit() // write all changes to db permanently
    conn.close() // connection is closed

init_db()

# 2. Engine & Session
engine = create_engine(f"sqlite:///{DB_FILENAME}", connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session

# 3. Models
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    username: str = Field(unique=True, nullable=False)
    password: str = Field(nullable=False)
    email: str = Field(unique=True, nullable=False)
    
class Blog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    content: str = Field(nullable=False)
    author_id: int = Field(foreign_key="user.id", nullable=False)

# 4. FastAPI Routes
app = FastAPI()

@app.post("/user")
def createUser(user: User, session: Session = Depends(get_session)):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.get("/user")
def getUser(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/user")
def editUser(user_id: int, updated_user: User, session: Session = Depends(get_session)):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.name = updated_user.name
    db_user.username = updated_user.username
    db_user.email = updated_user.email
    db_user.password = updated_user.password

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.post("/blog")
def createBlog(blog: Blog, session: Session = Depends(get_session)):
    session.add(blog)
    session.commit()
    session.refresh(blog)
    return blog

@app.get("/blog")
def getBlog(blog_id: Optional[int] = None, session: Session = Depends(get_session)):
    if blog_id:
        blog = session.get(Blog, blog_id)
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        return blog
    return session.exec(select(Blog)).all()

@app.delete("/blog")
def deleteBlog(blog_id: int, session: Session = Depends(get_session)):
    blog = session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    session.delete(blog)
    session.commit()
    return {"message": "Blog deleted successfully"}