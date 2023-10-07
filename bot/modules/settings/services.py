from bot.database.models import UserPreferences
from sqlalchemy.orm import sessionmaker
from bot.helpers.yaml import load_config
from typing import Final, Dict
from sqlalchemy import create_engine

# YAML Loader
db_config = load_config("config.yml")["database"]

# Constants
DB_SCHEMA: Final[str] = db_config.get("schema")

db_engine = create_engine(DB_SCHEMA)
Session = sessionmaker(bind=db_engine)

async def get_user_global_config(user_id: int):
    session = Session()
    try:
        user_preferences = session.query(UserPreferences).filter_by(user_id=user_id).first()
        if user_preferences:
            return user_preferences.settings
        else:
            return None
    except Exception as e:
        print(f'Error fetching user global preferences: {e}')
        return None
    finally:
        session.close()

async def set_user_global_config(user_id: int, settings: Dict[str, str]):
    session = Session()
    try:
        existing_preferences = session.query(UserPreferences).filter_by(user_id=user_id).first()
        if existing_preferences:
            existing_preferences.settings = settings
        else:
            user_preferences = UserPreferences(user_id=user_id, settings=settings)
            session.add(user_preferences)
        session.commit()
    except Exception as e:
        print(f'Error saving user preferences: {e}')
        session.rollback()
    finally:
        session.close()