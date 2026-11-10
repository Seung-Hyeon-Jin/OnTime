from fastapi import Depends , Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import oauth2_scheme, decode_access_token, CREDENTIALS_EXCEPTION
from app.models.user import User
from app.services.arrival_service import ArrivalService
from app.services.route_service import RouteService
from app.services.routine_execution_service import RoutineExecutionService

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id, version = decode_access_token(token)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise CREDENTIALS_EXCEPTION
    user_ver = user.token_version if user.token_version is not None else 1
    if user_ver != version:
        raise CREDENTIALS_EXCEPTION
    return user


def get_arrival_service(request: Request) -> ArrivalService:
    return request.app.state.arrival_service


def get_route_service(request: Request) -> RouteService:
    return request.app.state.route_service


def get_routine_execution_service(request: Request) -> RoutineExecutionService:
    return request.app.state.routine_execution_service