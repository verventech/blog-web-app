from fastapi import FastAPI

from db import init_db
from routes import auth, blogs, users

# Run the SQL migration script on app startup
init_db()

app = FastAPI(
    title="Modular Blog Backend with JWT & Bcrypt",
    swagger_ui_parameters={"persistAuthorization": True},
)

# Mount individual routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(blogs.router)