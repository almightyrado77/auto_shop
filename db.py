import os

import oracledb
from dotenv import load_dotenv

load_dotenv()

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dsn=os.getenv("DB_DSN"),
            min=1,
            max=5,
            increment=1,
        )
    return _pool


def get_connection():
    return get_pool().acquire()