from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.base import Base, engine, SessionLocal # <-- 1. IMPORT SessionLocal
from .api.routers import auth, projects, issues, members, admin, phases

# --- 2. NEW IMPORTS for default user creation ---
from .crud import crud_user
from .schemas.user import UserCreate
from .db.models import User
# --- END NEW IMPORTS ---

app = FastAPI()

@app.on_event("startup")
def on_startup():
    print("Application startup...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

    # --- 3. NEW: Create default admin user ---
    db = SessionLocal()
    try:
        # Check if user exists
        user = crud_user.get_user_by_email(db, email="admin@ceat.com")
        if not user:
            # Create user data
            user_in = UserCreate(
                email="admin@ceat.com",
                full_name="Admin User",
                password="admin@123" # Set default password to 'admin'
            )
            # Create the user
            user = crud_user.create_user(db, user_in=user_in)
            
            # --- IMPORTANT: Elevate user to superuser ---
            user.is_superuser = True
            db.add(user)
            db.commit()
            print("Default admin user (admin@ceat.com) created.")
        else:
            print("Admin user already exists.")
    finally:
        db.close()
    # --- END OF NEW LOGIC ---

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
app.include_router(phases.router, prefix="/api", tags=["Phases"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the ProjectFlow API!"}