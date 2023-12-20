import os
from abc import ABC
from typing import Final

from dotenv import load_dotenv

load_dotenv()


class Env(ABC):
    TOKEN: Final[str] = os.environ.get("TOKEN")
    MONGO_URI: Final[str] = os.environ.get("MONGO_URI")
    MONGO_DBNAME: Final[str] = os.environ.get("MONGO_DBNAME")
