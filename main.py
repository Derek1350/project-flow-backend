from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.base import Base, engine
from api.routers import auth, projects, issues

app = FastAPI()

@app.on_event("startup")
def on_startup():
    # Code to run on startup
    print("Application startup...")
    # Create all database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

# CORS Middleware Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # must NOT be "*" if you use credentials
    allow_credentials=True,         # set True if you send cookies/Authorization headers
    allow_methods=["*"],            # or ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allow_headers=["*"],            # include "Authorization", "Content-Type", etc.
)

# Include API routers with specific prefixes
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(issues.router, prefix="/api/issues", tags=["Issues"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the Jira-Lite API!"}

