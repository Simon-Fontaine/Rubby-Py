import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from rubby.misc import Env


class DatabaseManager:
    _instance = None

    def __init__(self):
        raise RuntimeError(
            "DatabaseManager instantiation not allowed. Use DatabaseManager.initialize() instead."
        )

    @classmethod
    async def initialize(cls):
        if cls._instance is None:
            if Env.MONGO_URI is None:
                raise ValueError(
                    "MongoDB URI not provided. Please provide a valid MongoDB URI to initialize the DatabaseManager."
                )
            cls._instance = cls.__new__(cls)
            cls._instance.client = AsyncIOMotorClient(Env.MONGO_URI)
            cls._instance.initialized = True
            logging.info(
                "DatabaseManager initialized successfully. Using new instance."
            )
        else:
            logging.info(
                "DatabaseManager already initialized. Using existing instance."
            )

    @classmethod
    def instance(cls):
        if cls._instance is None:
            raise RuntimeError(
                "DatabaseManager has not been initialized yet. Please call DatabaseManager.initialize() before using this method."
            )
        return cls._instance


async def get_database(database_name: Optional[str] = "rubby"):
    if not DatabaseManager.instance().initialized:
        logging.info("Initializing DatabaseManager for database access.")
        await DatabaseManager.initialize()
    else:
        logging.info("Using existing DatabaseManager instance for database access.")
    return DatabaseManager.instance().client[database_name]
