import os
import contextlib
from typing import Generator
from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv


@contextlib.contextmanager
def get_mongo_database() -> Generator[Database]:
    load_dotenv("./.env")
    client = MongoClient(host=os.getenv("MONGODB_ATLAS_URI"))
    try:
        yield Database(client, name=os.getenv("MONGODB_DATABASE"))
    finally:
        client.close()