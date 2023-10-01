from bot.database.models import GroupPreference, UserScore
from sqlalchemy.orm import sessionmaker
from bot.helpers.yaml import load_config
from typing import Final, Tuple, Optional
from sqlalchemy import create_engine

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