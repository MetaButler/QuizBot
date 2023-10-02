from bot.database.models import UserScore, WeeklyScore, PollAnswer
from sqlalchemy.orm import sessionmaker
from bot.helpers.yaml import load_config
from typing import Final
from sqlalchemy import create_engine, desc, func

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

async def get_user_score(chat_id: int, user_id: int):
    session = Session()
    try:
        user_score_record = (
            session.query(UserScore.score, UserScore.correct_answers, UserScore.wrong_answers)
            .filter_by(chat_id=chat_id, user_id=user_id)
            .first()
        )
        session.close()
        if user_score_record:
            user_score, correct_answers, wrong_answers = user_score_record
            accuracy = (correct_answers / (correct_answers + wrong_answers)) * 100 if correct_answers + wrong_answers > 0 else 0
            return (user_score, correct_answers, wrong_answers, accuracy)
        else:
            return (0, 0, 0, 0)
    except Exception as ex:
        print(f'Error fetching user scores: {ex}')
        return (None, None, None, None)
    
async def get_user_total_score(user_id: int):
    session = Session()
    try:
        total_score, total_correct_answers, total_wrong_answers = (
            session.query(
                func.sum(UserScore.score),
                func.sum(UserScore.correct_answers),
                func.sum(UserScore.wrong_answers)
            )
            .filter_by(user_id=user_id)
            .first()
        )
        session.close()
        return (total_score, total_correct_answers, total_wrong_answers)
    except Exception as ex:
        print(f'Error fetching user\'s total scores: {ex}')
        return (None, None, None)
    
async def get_poll_answer_record(poll_id: str):
    session = Session()
    try:
        poll_answer_record = session.query(PollAnswer.chat_id, PollAnswer.correct_option_id).filter_by(poll_id=poll_id).first()
        session.close()
        return poll_answer_record
    except Exception as e:
        print(f"Error in get_poll_answer_record function: {e}")
        return None
    
async def update_user_scores(user_id: int, poll_id: str, option_id: int):
    session = Session()
    poll_answer_record = await get_poll_answer_record(poll_id=poll_id)
    if poll_answer_record:
        chat_id, correct_option_id = poll_answer_record
    try:
        if correct_option_id == option_id:
            user_score = session.query(UserScore).filter_by(user_id=user_id, chat_id=chat_id).first()
            weekly_score = session.query(WeeklyScore).filter_by(user_id=user_id, chat_id=chat_id).first()
            if user_score:
                user_score.score += 1
                user_score.correct_answers += 1
            else:
                user_score = UserScore(user_id=user_id, chat_id=chat_id, score=1, correct_answers=1)
                session.add(user_score)
            if weekly_score:
                weekly_score.score += 1
                weekly_score.correct_answers += 1
            else:
                weekly_score = WeeklyScore(user_id=user_id, chat_id=chat_id, score=1, correct_answers=1)
                session.add(weekly_score)
        else:
            user_score = session.query(UserScore).filter_by(user_id=user_id, chat_id=chat_id).first()
            weekly_score = session.query(WeeklyScore).filter_by(user_id=user_id, chat_id=chat_id).first()
            if user_score:
                user_score.score -= 0.5
                user_score.wrong_answers += 1
            else:
                user_score = UserScore(user_id=user_id, chat_id=chat_id, score=-0.5, wrong_answers=1)
                session.add(user_score)
            if weekly_score:
                weekly_score.score -= 0.5
                weekly_score.wrong_answers += 1
            else:
                weekly_score = WeeklyScore(user_id=user_id, chat_id=chat_id, score=-0.5, wrong_answers=1)
                session.add(weekly_score)
        session.commit()
        session.close()
    except Exception as e:
        print(f"Error in update_user_scores function: {e}")