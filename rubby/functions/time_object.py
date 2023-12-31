import pendulum

from rubby.database import get_database
from rubby.models import Guild

DEFAULT_TIMEZONE = "UTC"
SMALL_DATE_FORMAT = "DD[/]MM[/]YYYY HH:mm"
NORMAL_DATE_FORMAT = "ddd DD MMM YYYY [at] HH:mm [(]z[)]"
FULL_DATE_FORMAT = "dddd, MMMM DD YYYY, HH:mm:ss [(]z[)]"


class TimeObject:
    def __init__(
        self,
        date_time: pendulum.DateTime,
        small_date_format: str,
        normal_date_format: str,
        full_date_format: str,
    ):
        self.date_time = date_time
        self.small_date_format = small_date_format
        self.normal_date_format = normal_date_format
        self.full_date_format = full_date_format

    def __str__(self):
        return "\n".join(
            [
                f"Date: {self.date_time}",
                f"Small Date Format: {self.small_date_format}",
                f"Normal Date Format: {self.normal_date_format}",
                f"Full Date Format: {self.full_date_format}",
            ]
        )


async def create_time_object(
    guild_id: int, time: str | pendulum.DateTime = None
) -> TimeObject:
    database = await get_database()
    guild: Guild = await database.guilds.find_one({"_id": guild_id})
    timezone = guild["timezone"] if guild else DEFAULT_TIMEZONE

    if not time:
        time = pendulum.now(tz=timezone)
    elif not isinstance(time, pendulum.DateTime):
        try:
            time = pendulum.from_format(string=time, fmt=SMALL_DATE_FORMAT, tz=timezone)
        except ValueError as error:
            raise ValueError(
                f"Time must be in the format of `{SMALL_DATE_FORMAT.replace('[/]', '/')}`."
            ) from error
    else:
        time = time.in_tz(timezone)

    return TimeObject(
        time,
        time.format(SMALL_DATE_FORMAT),
        time.format(NORMAL_DATE_FORMAT),
        time.format(FULL_DATE_FORMAT),
    )
