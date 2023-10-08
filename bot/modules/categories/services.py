from bot.database.models import GroupPreference, Topic
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

def fetch_category_names():
    session = Session()
    try:
        categories = (
            session.query(Topic.category_name, Topic.category_id)
            .distinct()
            .all()
        )
        category_opts = dict()
        for name, id in categories:
            category_opts[str(id)] = name
        return category_opts
    except Exception as e:
        print(f"Error fetching category names: {e}")
        return None
    finally:
        session.close()

def get_chat_ids_in_group_preferences():
    session = Session()
    try:
        chat_ids = (
            session.query(GroupPreference.chat_id)
            .all()
        )
        return [int(chat_id[0]) for chat_id in chat_ids]
    except Exception as e:
        print(f"Error fetching chat_ids in group preferences: {e}")
        return []
    
def determine_source(category_id):
    session = Session()
    try:
        source = (
            session.query(Topic.source)
            .filter(Topic.category_id == category_id)
            .first()
        )
        return source[0] if source else None
    except Exception as e:
        print(f"Error determining source: {e}")
        return None
    finally:
        session.close()
    
def update_database(chat_id, trivia_topics, opentdb_topics):
    session = Session()
    try:
        group_pref = (
            session.query(GroupPreference)
            .filter_by(chat_id=chat_id)
            .first()
        )
        if trivia_topics:
            group_pref.trivia_topics = trivia_topics
        if opentdb_topics:
            group_pref.opentdb_topics = opentdb_topics
        session.commit()
    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        session.close()

def reset_topics_to_none(chat_id: int):
    session = Session()
    try:
        session.query(GroupPreference).filter_by(chat_id=chat_id).update({GroupPreference.trivia_topics: None, GroupPreference.opentdb_topics: None})
        session.commit()
    except Exception as e:
        print(f"Error resetting topics to None: {e}")
    finally:
        session.close()

def fetch_categories(chat_id: int):
    session = Session()
    try:
        existing_topics = session.query(GroupPreference.trivia_topics, GroupPreference.opentdb_topics).filter(GroupPreference.chat_id == chat_id).first()
        return existing_topics
    except Exception as e:
        print(f'Error in fetching group categories: {e}')
        return None
    finally:
        session.close()