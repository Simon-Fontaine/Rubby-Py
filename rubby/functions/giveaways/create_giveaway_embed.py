import disnake
import pendulum

from rubby.functions.time_object import TimeObject
from rubby.functions.truncate_components import truncate_embed
from rubby.functions.user_details import UserDetails


def create_giveaway_embed(
    created_by: UserDetails,
    title: str,
    description: str,
    winner_count: int,
    end_date: TimeObject,
    allowed_roles: list[int] = None,
):
    color = (
        disnake.Color.blurple()
        if end_date.date_time > pendulum.now()
        else disnake.Color.red()
    )

    embed = disnake.Embed(
        title=title,
        description=description,
        color=color,
    )

    embed.set_footer(
        text=f"Max Winners: {winner_count} • Hosted by {created_by.name}",
    )
    embed.timestamp = end_date.date_time

    if allowed_roles:
        embed.add_field(
            name="Allowed Roles",
            value=", ".join([f"<@&{role_id}>" for role_id in allowed_roles]),
        )

    return truncate_embed(embed)
