import pendulum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class Giveaway(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    message_id: int = Field(..., alias="_id")
    result_message_id: Optional[int] = None

    channel_id: int = Field(...)
    guild_id: int = Field(...)

    created_by: int = Field(...)
    participants: Optional[list[int]] = Field(default=[])
    finished_configuring: Optional[bool] = Field(default=False)

    # Settings
    title: str = Field(...)
    description: str = Field(...)
    prize: str = Field(...)

    winner_count: int = Field(..., ge=1)
    allowed_roles: Optional[list[int]] = Field(default=[])

    ended: Optional[bool] = Field(default=False)
    end_date: pendulum.DateTime
    created_at: pendulum.DateTime
