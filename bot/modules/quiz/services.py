from bot.database.models import GroupPreference, PollAnswer, SentQuestion
from sqlalchemy.orm import sessionmaker
from bot.helpers.yaml import load_config
from typing import Final
from sqlalchemy import create_engine
import random

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

async def insert_question_into_db(chat_id, question_id, correct_option_id):
    session = Session()
    try:
        sent_question = SentQuestion(chat_id=chat_id, question_id=question_id)
        session.add(sent_question)
        poll_answer = PollAnswer(poll_id=question_id, chat_id=chat_id, correct_option_id=correct_option_id)
        session.merge(poll_answer)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error inserting data into the database: {e}")

def get_random_trivia_category(chat_id: int):
    session = Session()
    preferences = session.query(GroupPreference).filter_by(chat_id=chat_id).first()
    if preferences and preferences.trivia_topics:
        categories = preferences.trivia_topics.split(',')
        return random.choice(categories)
    return None

def get_random_opentdb_category(chat_id: int):
    session = Session()
    preferences = session.query(GroupPreference).filter_by(chat_id=chat_id).first()
    if preferences and preferences.opentdb_topics:
        categories = preferences.opentdb_topics.split(',')
        return random.choice(categories)
    return None

def is_question_sent(chat_id: int, question_id):
    session = Session()
    return session.query(SentQuestion).filter_by(chat_id=chat_id, question_id=question_id).first() is not None