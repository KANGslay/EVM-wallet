from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends, WebSocket
from fastapi.security import OAuth2PasswordBearer

from app.models.user import User
from app.schemas.auth import UserCreate, TokenData
from passlib.context import CryptContext
import bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_id(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()

def get_password_hash(password: str) -> str:
    # 使用bcrypt库直接生成salt和hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 使用bcrypt库直接验证密码
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
from app.config import settings
from app.models import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_user(db: Session, user: UserCreate) -> User:
    """创建新用户"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, str(user.hashed_password)):
        return None
    return user

def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_minutes is not None:
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def create_long_lived_token(username: str, expires_days: int = 365) -> str:
    """创建长期有效的令牌，默认一年有效期"""
    data = {"sub": username}
    expire = datetime.utcnow() + timedelta(days=expires_days)
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(
        data, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    获取当前认证用户
    
    Args:
        token: JWT token
        db: 数据库会话
        
    Returns:
        User: 用户对象
        
    Raises:
        HTTPException: 认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username = str(payload.get("sub", ""))  # 确保返回字符串类型，避免None值
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_ws(websocket: WebSocket, db: Session) -> Optional[User]:
    """
    从WebSocket连接中获取当前用户
    
    Args:
        websocket: WebSocket连接
        db: 数据库会话
        
    Returns:
        Optional[User]: 当前用户，如果认证失败则返回None
    """
    try:
        # 从查询参数或Cookie中获取令牌
        token = websocket.query_params.get("token")
        if not token:
            cookies = websocket.cookies
            token = cookies.get("token")
        
        if not token:
            return None
        
        # 验证令牌
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username = str(payload.get("sub", ""))
        if username is None or username == "":
            return None
        
        # 获取用户
        user = db.query(User).filter(User.username == username).first()
        return user
    except JWTError:
        return None
    except Exception:
        return None