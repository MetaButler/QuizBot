from bot.database.models import GroupPreference
from sqlalchemy.orm import sessionmaker
from bot.helpers.yaml import load_config
from typing import Final
from sqlalchemy import create_engine

# YAML Loader
db_config = load_config("config.yml")["database"]

# Constants
DB_SCHEMA: Final[str] = db_config.get("schema")

db_engine = create_engine(DB_SCHEMA)
Session = sessionmaker(bind=db_engine)

def is_quiz_enabled(chat_id: int) -> bool:
    try:
        session = Session()
        group_preference = session.query(GroupPreference).filter_by(chat_id=chat_id).first()
        if group_preference:
            return group_preference.send_questions
        else:
            return False
    except Exception as e:
        print(f"Error checking quiz enable status: {e}")
        return False
    finally:
        session.close()