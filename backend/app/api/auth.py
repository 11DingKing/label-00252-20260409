"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import get_db
from app.models.user import User, OperationLog
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo, PasswordChangeRequest
from app.schemas.common import ResponseModel
from app.core.security import verify_password, get_password_hash, create_access_token, get_current_user
from app.core.config import settings
from app.core.logging import get_logger
from app.api.deps import get_client_ip

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
logger = get_logger(__name__)


@router.post("/login", response_model=ResponseModel[LoginResponse])
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login endpoint."""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Log operation
    log = OperationLog(
        user_id=user.id,
        action="login",
        module="auth",
        detail=f"User {user.username} logged in",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"User {user.username} logged in successfully")
    
    return ResponseModel(
        data=LoginResponse(
            access_token=access_token,
            user=UserInfo.model_validate(user)
        )
    )


@router.post("/logout", response_model=ResponseModel)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User logout endpoint."""
    log = OperationLog(
        user_id=current_user.id,
        action="logout",
        module="auth",
        detail=f"User {current_user.username} logged out",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"User {current_user.username} logged out")
    
    return ResponseModel(message="Logged out successfully")


@router.get("/profile", response_model=ResponseModel[UserInfo])
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return ResponseModel(data=UserInfo.model_validate(current_user))


@router.put("/password", response_model=ResponseModel)
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    current_user.password_hash = get_password_hash(password_data.new_password)
    
    log = OperationLog(
        user_id=current_user.id,
        action="change_password",
        module="auth",
        detail=f"User {current_user.username} changed password",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"User {current_user.username} changed password")
    
    return ResponseModel(message="Password changed successfully")
