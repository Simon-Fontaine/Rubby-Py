import pendulum
import random

import disnake
from disnake.ext import commands


class UserDetails:
    def __init__(
        self,
        user_id: int,
        name: str,
        created_at: pendulum.DateTime,
        avatar: str = f"https://cdn.discordapp.com/embed/avatars/{random.randint(0, 4)}.png",
    ):
        self.id = user_id
        self.name = name
        self.avatar = avatar
        self.created_at = created_at


async def get_user_details(user: disnake.User | int, bot: commands.Bot) -> UserDetails:
    if isinstance(user, int) and not isinstance(user, disnake.User):
        user = await bot.fetch_user(user)

    if not user:
        raise ValueError(f"I couldn't find a user with `{user}` as their ID.")

    return UserDetails(
        user.id,
        f"@{user.name}"
        if user.discriminator == "0"
        else f"{user.name}#{user.discriminator}",
        user.created_at,
        user.avatar.url,
    )
