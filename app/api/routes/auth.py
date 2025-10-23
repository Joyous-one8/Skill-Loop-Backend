from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import User
from app.schemas.schemas import UserCreate, UserResponse
from config import get_settings
import httpx
import logging
from urllib.parse import urlencode, quote_plus
import secrets

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/login")
async def login(request: Request):
    """
    Redirect to Auth0 login page
    """
    state = secrets.token_urlsafe(32)
    redirect_uri = str(request.url_for("auth_callback"))
    
    # Build Auth0 authorization URL
    params = {
        "response_type": "code",
        "client_id": settings.auth0_client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email",
        "state": state,
    }
    
    auth_url = f"https://{settings.auth0_domain}/authorize?{urlencode(params)}"
    logger.info(f"Redirecting to: {auth_url}")
    
    return RedirectResponse(auth_url)


@router.get("/callback")
async def auth_callback(
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Auth0 callback and exchange code for tokens
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No authorization code provided"
        )
    
    redirect_uri = str(request.url_for("auth_callback"))
    
    # Exchange authorization code for tokens
    async with httpx.AsyncClient() as client:
        try:
            token_response = await client.post(
                f"https://{settings.auth0_domain}/oauth/token",
                json={
                    "grant_type": "authorization_code",
                    "client_id": settings.auth0_client_id,
                    "client_secret": settings.auth0_client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"content-type": "application/json"}
            )
            
            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token exchange failed: {token_response.text}"
                )
            
            tokens = token_response.json()
            logger.info("Tokens received successfully")
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during token exchange: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to exchange code for token: {str(e)}"
            )
    
    # Get user info
    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")
    
    async with httpx.AsyncClient() as client:
        try:
            userinfo_response = await client.get(
                f"https://{settings.auth0_domain}/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if userinfo_response.status_code != 200:
                logger.error(f"Failed to get user info: {userinfo_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to get user information"
                )
            
            user_info = userinfo_response.json()
            logger.info(f"User info retrieved: {user_info.get('email')}")
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting user info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user info: {str(e)}"
            )
    
    # Extract user data
    auth0_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name", email)
    avatar = user_info.get("picture")
    
    if not auth0_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user information received"
        )
    
    # Create or update user in database
    existing_user = db.query(User).filter(User.auth0_id == auth0_id).first()
    
    if not existing_user:
        logger.info(f"Creating new user: {email}")
        new_user = User(
            auth0_id=auth0_id,
            email=email,
            name=name,
            avatar=avatar
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
    else:
        logger.info(f"Existing user found: {email}")
        user = existing_user
    
    return JSONResponse({
        "access_token": access_token,
        "id_token": id_token,
        "token_type": "Bearer",
        "expires_in": tokens.get("expires_in"),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "avatar": user.avatar,
            "credits": user.credits,
            "rating": user.rating
        }
    })


@router.post("/register")
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user manually
    """
    existing_user = db.query(User).filter(User.auth0_id == user_data.auth0_id).first()
    
    if existing_user:
        return {
            "message": "User already exists",
            "user": existing_user
        }
    
    new_user = User(**user_data.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "User created successfully",
        "user": new_user
    }


@router.get("/logout")
async def logout(request: Request):
    """
    Get Auth0 logout URL
    """
    return_to = str(request.base_url)
    
    logout_url = (
        f"https://{settings.auth0_domain}/v2/logout?"
        + urlencode(
            {
                "returnTo": return_to,
                "client_id": settings.auth0_client_id,
            },
            quote_via=quote_plus,
        )
    )
    
    return JSONResponse({
        "logout_url": logout_url,
        "message": "Redirect to this URL to complete logout"
    })


@router.post("/logout")
async def logout_post(request: Request):
    """
    Alternative POST logout endpoint
    """
    return_to = str(request.base_url)
    
    logout_url = (
        f"https://{settings.auth0_domain}/v2/logout?"
        + urlencode(
            {
                "returnTo": return_to,
                "client_id": settings.auth0_client_id,
            },
            quote_via=quote_plus,
        )
    )
    
    return JSONResponse({
        "logout_url": logout_url,
        "message": "Redirect to this URL to complete logout"
    })


@router.post("/token")
async def get_token_machine_to_machine():
    """
    Get access token for machine-to-machine authentication
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"https://{settings.auth0_domain}/oauth/token",
                json={
                    "client_id": settings.auth0_client_id,
                    "client_secret": settings.auth0_client_secret,
                    "audience": settings.auth0_api_audience,
                    "grant_type": "client_credentials"
                },
                headers={"content-type": "application/json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to get access token: {response.text}"
                )
            
            return response.json()
        except httpx.ConnectTimeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Connection to Auth0 timed out"
            )
