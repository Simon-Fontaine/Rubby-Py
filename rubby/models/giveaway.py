from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Giveaway(BaseModel):
    message_id: int = Field(..., alias="_id")
    result_message_id: Optional[int] = None

    channel_id: int = Field(...)
    guild_id: int = Field(...)

    created_by: int = Field(...)
    participants: list[int] = Field(default=[])

    # Settings
    title: str = Field(...)
    description: str = Field(...)
    prize: str = Field(...)

    winner_count: int = Field(..., ge=1)
    ended: bool = Field(default=False)
    end_date: datetime = Field(..., gt=datetime.utcnow())
    created_at: datetime = Field(default=datetime.utcnow())
