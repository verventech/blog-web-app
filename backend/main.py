from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import TimeoutError as PoolTimeout

from db import init_db
from routes import auth, blogs, users

# Run the SQL migration script on app startup
init_db()

app = FastAPI(
    title="Modular Blog Backend with JWT & Bcrypt",
    swagger_ui_parameters={"persistAuthorization": True},
)

@app.exception_handler(PoolTimeout)
async def pool_exhausted(_request: Request, _exc: PoolTimeout):
    return JSONResponse(
        status_code=503,
        content={"detail": "Server is busy. Try again."},
    )


# Mount individual routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(blogs.router)