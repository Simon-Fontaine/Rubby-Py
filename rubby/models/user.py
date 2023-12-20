import random
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    id: int = Field(..., alias="_id")
    name: str = Field(...)
    avatar: str = Field(
        default=f"https://cdn.discordapp.com/embed/avatars/{random.randint(0, 4)}.png",
    )
    email: Optional[EmailStr] = None
    created_at: datetime = Field(...)
