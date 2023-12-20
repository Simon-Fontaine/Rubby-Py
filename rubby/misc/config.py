import pathlib

from abc import ABC
from typing import Final, Iterable


class Config(ABC):
    DESCRIPTION: Final[str] = "Your Friendly Neighborhood Bot."
    OWNER_IDS: Iterable[int] = [517770661733859329]
    GUILD_IDS: Final[list[int]] = [1023948114593321071, 1139893699787104256]
    COGS_DIR: Final[pathlib.Path] = pathlib.Path(__file__).parent.parent / "cogs"
