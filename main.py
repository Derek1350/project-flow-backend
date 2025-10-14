from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.base import Base, engine
from api.routers import auth, projects, issues, members, admin

app = FastAPI()

@app.on_event("startup")
def on_startup():
    print("Application startup...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173", # Corrected typo here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers with specific prefixes
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(issues.router, prefix="/api/issues", tags=["Issues"])
app.include_router(members.router, prefix="/api", tags=["Members"])
app.include_router(admin.router, prefix="/api", tags=["Admin"]) 

@app.get("/")
def read_root():
    return {"message": "Welcome to the ProjectFlow API!"}

