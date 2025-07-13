# models.py
from typing import Optional
from sqlmodel import Field, SQLModel
from passlib.hash import bcrypt

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str

    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.hashed_password)

class UserCreate(SQLModel):
    email: str
    password: str

class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    owner_id: int = Field(foreign_key="user.id")
