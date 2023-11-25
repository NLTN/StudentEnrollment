import sqlite3
import contextlib
# import logging
from pydantic_settings import BaseSettings
from itertools import cycle

class Settings(BaseSettings, env_file=".env", extra="ignore"):
    USER_SERVICE_PRIMARY_DB_PATH: str
    USER_SERVICE_SECONDARY_DB_PATH: str
    USER_SERVICE_TERTIARY_DB_PATH: str
    #logging_config: str #= "./etc/logging.ini"

# logging.basicConfig(filename=f'{__name__}.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

settings = Settings()

db_names = [
    settings.USER_SERVICE_SECONDARY_DB_PATH,
    settings.USER_SERVICE_TERTIARY_DB_PATH
]
databases = cycle(db_names)

def get_db():
    with contextlib.closing(sqlite3.connect(settings.USER_SERVICE_PRIMARY_DB_PATH)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        #db.set_trace_callback(logging.debug)
        yield db

def get_db_replicas():
    curr_db = next(databases)
    try:
        connection = sqlite3.connect(curr_db, check_same_thread=False)
    except:
        curr_db = next(databases)
        connection = sqlite3.connect(curr_db, check_same_thread=False)
    finally:
        with contextlib.closing(connection) as db:
            db.row_factory = sqlite3.Row
            yield db
