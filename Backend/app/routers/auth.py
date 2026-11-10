from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse,UserLogin, TokenResponse
from app.core.database import get_db
from app.schemas.user import DeviceTokenUpdate, UserUpdate
from app.schemas.user import MessageResponse
from app.services.notification_service import NotificationDeliveryError


router = APIRouter(prefix="/api/v1/auth",tags=["auth"])

@router.post("/register",response_model=TokenResponse,status_code=status.HTTP_201_CREATED)
def register(user_in : UserCreate, db : Session = Depends(get_db)) -> TokenResponse:
    existing_email = db.query(User).filter(User.email == user_in.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 가입된 이메일입니다."
        )
    existing_name = db.query(User).filter(User.name == user_in.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 존재하는 이름입니다."
        )
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email = user_in.email,
        name = user_in.name,
        hashed_password= hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token_ver = new_user.token_version if new_user.token_version is not None else 1
    access_token = create_access_token(data={"sub": new_user.user_id, "ver": token_ver})
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(user_in: UserLogin,db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(
        (User.name == user_in.name) | (User.email == user_in.name)
    ).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= "아이디(이름 또는 이메일) 또는 비밀번호가 잘못되었습니다."
        )
    token_ver = user.token_version if user.token_version is not None else 1
    access_token = create_access_token(data={"sub": user.user_id, "ver": token_ver})
    return TokenResponse(access_token=access_token)

@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me/device-token", response_model = UserResponse)
def update_device_token(
    body: DeviceTokenUpdate,
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db)
) -> User:
    # 단일 기기 시연 구조이므로 사용자 레코드에 token을 직접 저장합니다.
    current_user.device_token = body.device_token
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/test-notification", response_model=MessageResponse)
async def send_test_notification(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    if not current_user.device_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="등록된 기기 토큰이 없습니다. 앱을 다시 실행해 주세요.",
        )
    if not current_user.notifications_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="알림 설정이 꺼져 있습니다.",
        )

    notification_service = request.app.state.routine_execution_service.notification_service
    try:
        await notification_service.provider.send(
            token=current_user.device_token,
            title="OnTime 테스트 알림",
            message="알림 설정과 FCM 연결이 정상적으로 동작합니다.",
        )
    except NotificationDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return MessageResponse(message="테스트 알림을 발송했습니다.")



'''
    내 정보 수정시 사용자 이름 중복 체크 및 비밀번호 해싱 후 업데이트
'''
@router.patch("/me", response_model = UserResponse)
def update_me(
    user_in : UserUpdate,
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db)
) -> User:
    data = user_in.model_dump(exclude_none=True)

    if "name" in data:
        existing = (
            db.query(User)
            .filter(User.name == data["name"]).first()
        )
        if existing :
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 존재하는 이름입니다."
            )
        current_user.name = data["name"]
    if "password" in data:
        current_user.hashed_password = get_password_hash(data["password"])
    if "notifications_enabled" in data:
        current_user.notifications_enabled = data["notifications_enabled"]
    db.commit()
    db.refresh(current_user)
    return current_user


    