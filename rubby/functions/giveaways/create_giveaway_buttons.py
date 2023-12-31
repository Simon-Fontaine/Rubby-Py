import disnake
import pendulum

from rubby.functions.time_object import TimeObject
from rubby.functions.truncate_components import truncate_buttons


async def create_giveaway_buttons(
    count: int, end_date: TimeObject, disabled: bool = False
) -> list[disnake.ui.Button]:
    disabled = end_date.date_time <= pendulum.now() or disabled

    time_string = (
        f"Ends on {end_date.normal_date_format}"
        if not disabled
        else f"Ended on {end_date.normal_date_format}"
    )

    return truncate_buttons(
        [
            disnake.ui.Button(
                style=disnake.ButtonStyle.primary,
                label=f"Participate ({count})",
                disabled=disabled,
                custom_id="giveaway:enter",
                emoji="🎉",
            ),
            disnake.ui.Button(
                style=disnake.ButtonStyle.secondary,
                label=time_string,
                disabled=True,
                custom_id="giveaway:ends",
            ),
        ]
    )
