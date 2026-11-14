import bcrypt

# Passlib 1.7.4 compatibility fix for bcrypt 4.0.0+
if not hasattr(bcrypt, '__about__'):
    class _About:
        __version__ = getattr(bcrypt, '__version__', '4.2.1')
    bcrypt.__about__ = _About()

from passlib.context import CryptContext
from jose import jwt,JWTError
from app.core.config import settings
from datetime import datetime, timedelta
from fastapi import HTTPException,status
from fastapi.security import OAuth2PasswordBearer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
CREDENTIALS_EXCEPTION = HTTPException(
    status_code = status.HTTP_401_UNAUTHORIZED,
    detail = "유효하지 않은 토큰",
    headers ={"WWW-Authenticate" : "Bearer"}
)

def decode_access_token(token: str) -> tuple[str, int]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        version = payload.get("ver", 1)
        if not user_id:
            raise CREDENTIALS_EXCEPTION
        return user_id, int(version if version is not None else 1)
    except JWTError:
        raise CREDENTIALS_EXCEPTION



#비밀번호 검증
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password,hashed_password)

#회원가입 시 사용될 hash 생성 후 반환 함수
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

#로그인, 회원가입 성공 후 토근 발급 함수
def create_access_token(data : dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp" : expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)