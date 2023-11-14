import sqlite3
import contextlib
# import logging
from pydantic_settings import BaseSettings

class Settings(BaseSettings, env_file=".env", extra="ignore"):
    USER_SERVICE_PRIMARY_DB_PATH: str
    #logging_config: str #= "./etc/logging.ini"

# logging.basicConfig(filename=f'{__name__}.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

settings = Settings()

def get_db():
    with contextlib.closing(sqlite3.connect(settings.USER_SERVICE_PRIMARY_DB_PATH)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        #db.set_trace_callback(logging.debug)
        yield db