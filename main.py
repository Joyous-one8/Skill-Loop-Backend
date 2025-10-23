from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.api.routes import users, skills, matches, sessions, auth, credits

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="SkillSwap API - A platform for skill exchange and learning",
    version="1.0.0"
)

# Session middleware (optional now, but kept for future use)
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.secret_key,
    session_cookie="session",
    max_age=3600,
    same_site="lax",
    https_only=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4040"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(credits.router, prefix="/api/credits", tags=["credits"])


@app.get("/api/public")
def public():
    return {
        "status": "success",
        "message": "Hello from a public endpoint! You don't need to be authenticated to see this."
    }


@app.get("/")
def root(request: Request):
    base_url = str(request.base_url).rstrip("/")
    
    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            if route.path not in ["/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"]:
                for method in route.methods:
                    if method != "HEAD":
                        routes.append({
                            "path": route.path,
                            "method": method,
                            "name": route.name,
                            "url": f"{base_url}{route.path}"
                        })
    
    grouped_routes = {
        "Authentication": [],
        "Users": [],
        "Skills": [],
        "Matches": [],
        "Sessions": [],
        "Credits": [],
        "Other": []
    }
    
    for route in routes:
        if route["path"].startswith("/api/auth"):
            grouped_routes["Authentication"].append(route)
        elif route["path"].startswith("/api/users"):
            grouped_routes["Users"].append(route)
        elif route["path"].startswith("/api/skills"):
            grouped_routes["Skills"].append(route)
        elif route["path"].startswith("/api/matches"):
            grouped_routes["Matches"].append(route)
        elif route["path"].startswith("/api/sessions"):
            grouped_routes["Sessions"].append(route)
        elif route["path"].startswith("/api/credits"):
            grouped_routes["Credits"].append(route)
        else:
            grouped_routes["Other"].append(route)
    
    grouped_routes = {k: v for k, v in grouped_routes.items() if v}
    
    return {
        "message": "SkillSwap API",
        "version": "1.0.0",
        "docs": f"{base_url}/docs",
        "redoc": f"{base_url}/redoc",
        "endpoints": grouped_routes,
        "total_endpoints": len(routes)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
