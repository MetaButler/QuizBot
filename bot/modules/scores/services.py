from bot.database.models import UserScore, WeeklyScore
from sqlalchemy.orm import sessionmaker
from bot.helpers.yaml import load_config
from typing import Final
from sqlalchemy import create_engine, desc

# YAML Loader
db_config = load_config("config.yml")["database"]

# Constants
DB_SCHEMA: Final[str] = db_config.get("schema")

db_engine = create_engine(DB_SCHEMA)
Session = sessionmaker(bind=db_engine)

async def get_top_scores(chat_id, limit=5):
    try:
        session = Session()
        top_scores = (
            session.query(UserScore.user_id, UserScore.score)
            .filter_by(chat_id=chat_id)
            .order_by(desc(UserScore.score))
            .limit(limit)
            .all()
        )
        session.close()
        return top_scores
    except Exception as e:
        print(f"Error fetching top scores: {e}")
        return []
    
async def get_top_weekly_scores(chat_id, limit=5):
    try:
        session = Session()
        top_weekly_scores = (
            session.query(WeeklyScore.user_id, WeeklyScore.score)
            .filter_by(chat_id=chat_id)
            .order_by(desc(WeeklyScore.score))
            .limit(limit)
            .all()
        )
        session.close()
        return top_weekly_scores
    except Exception as e:
        print(f"Error fetching top weekly scores: {e}")
        return []
    
def reset_weekly_scores() -> None:
    try:
        session = Session()
        session.query(WeeklyScore).update({
            WeeklyScore.score: 0,
            WeeklyScore.correct_answers: 0,
            WeeklyScore.wrong_answers: 0
        })
        session.commit()
        session.close()
    except Exception as e:
        print(f"Error resetting weekly scores: {e}")