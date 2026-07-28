from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def list_users(self, db: Session, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
        query = db.query(User)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_user(self, db: Session, user_id) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def create_user(self, db: Session, data: UserCreate) -> User:
        if self.get_by_email(db, data.email):
            raise ValueError("Email already registered")
        if self.get_by_username(db, data.username):
            raise ValueError("Username already taken")

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update_user(self, db: Session, user: User, data: UserUpdate) -> User:
        if data.email is not None and data.email != user.email:
            if self.get_by_email(db, data.email):
                raise ValueError("Email already registered")
            user.email = data.email

        if data.username is not None and data.username != user.username:
            if self.get_by_username(db, data.username):
                raise ValueError("Username already taken")
            user.username = data.username

        if data.password is not None:
            user.hashed_password = hash_password(data.password)

        if data.is_active is not None:
            user.is_active = data.is_active

        db.commit()
        db.refresh(user)
        return user

    def delete_user(self, db: Session, user: User) -> None:
        db.delete(user)
        db.commit()
