import random
from datetime import datetime
from pydantic import BaseModel, Field


class Guild(BaseModel):
    id: int = Field(..., alias="_id")
    name: str = Field(...)
    owner: int = Field(...)
    icon: str = Field(
        default=f"https://cdn.discordapp.com/embed/avatars/{random.randint(0, 4)}.png",
    )
    created_at: datetime = Field(...)
    timezone: str = Field(default="UTC")
