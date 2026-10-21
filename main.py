import sqlite3
from fastapi import FastAPI

class User(SQLModel, table=True):
    """Database Entity Model for Users."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    username: str = Field(unique=True, nullable=False)
    password: str = Field(nullable=False)
    email: str = Field(unique=True, nullable=False)
    
class Blog(SQLModel, table=True):
    """Database Entity Model for Blogs."""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    content: str = Field(nullable=False)
    author_id: int = Field(foreign_key="user.id", nullable=False)

app = FastAPI()

@app.post("/blog")
def createBlog():

@app.get("/blog")
def getBlog():

@app.delete("/blog")
def deleteBlog():

@app.post("/user")
def createUser():


@app.get("/user")
def getUser():

@app.PUT("/user")
def editUser():