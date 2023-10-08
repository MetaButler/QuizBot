import time
from typing import Final

START_UNIX_TIME: Final[int] = int(time.time())

def get_start_time() -> int:
    return START_UNIX_TIME