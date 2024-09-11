from typing import Final, Optional, Tuple

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from bot.database.models import ActiveGroupStat, ActiveUserStat, GroupPreference, UserScore
from bot.helpers.yaml import load_config

# YAML Loader
db_config = load_config("config.yml")["database"]

# Constants
DB_SCHEMA: Final[str] = db_config.get("schema")

db_engine = create_engine(DB_SCHEMA)
Session = sessionmaker(bind=db_engine)


def get_bot_stats() -> Tuple[Optional[int], Optional[int]]:
    total_chats = None
    total_users = None
    session = Session()
    try:
        total_chats = session.query(GroupPreference).count()
        total_users = session.query(UserScore.user_id).distinct().count()
    except Exception as ex:
        print(f'Exception in collecting stats: {ex}')
        total_chats = None
        total_users = None
    finally:
        session.close()
        return (total_chats, total_users)


def get_recent_stats() -> Tuple[int, int]:
    session = Session()
    user_row_count = session.query(func.count(ActiveUserStat.user_id)).scalar()
    chat_row_count = session.query(func.count(
        ActiveGroupStat.chat_id)).scalar()
    return user_row_count, chat_row_count
