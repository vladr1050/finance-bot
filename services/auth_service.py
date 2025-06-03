# app/services/auth_service.py
import bcrypt
from uuid import uuid4
from sqlalchemy import select
from app.db.database import async_session
from app.db.models import User


async def register_user(email: str, password: str, telegram_id: int = None) -> User:
    """
    Registers a new user with email and password.
    If a Telegram ID is provided, it's saved as well.
    Raises ValueError if the email is already in use.
    """
    async with async_session() as session:
        existing_user = await session.scalar(select(User).where(User.email == email))
        if existing_user:
            raise ValueError("Email is already registered.")

        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        new_user = User(
            user_uuid=uuid4(),
            email=email,
            password_hash=hashed_pw,
            telegram_id=telegram_id,
            email_confirmed=True,  # Placeholder: email confirmation to be implemented
            created_from="telegram" if telegram_id else "web"
        )

        session.add(new_user)
        await session.commit()
        return new_user


async def authenticate_user(email: str, password: str) -> User | None:
    """
    Authenticates a user by email and password.
    Returns the user if successful, otherwise None.
    """
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.email == email))
        if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return user
        return None


async def link_telegram_id(user_uuid: str, telegram_id: int) -> None:
    """
    Links a Telegram ID to an existing user by UUID.
    """
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_uuid == user_uuid))
        if user:
            user.telegram_id = telegram_id
            await session.commit()
