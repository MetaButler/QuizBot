from sqlalchemy import (JSON, BigInteger, Boolean, Column, DateTime, Float,
                        ForeignKey, Integer, String, Text, UniqueConstraint)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class GroupPreference(Base):
    __tablename__ = 'group_preferences'

    chat_id = Column(BigInteger, primary_key=True)
    send_questions = Column(Boolean, default=True)
    trivia_topics = Column(Text)
    opentdb_topics = Column(Text)
    message_thread_id = Column(BigInteger)
    settings = Column(JSON, nullable=True)


class PollAnswer(Base):
    __tablename__ = 'poll_answers'

    poll_id = Column(String, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('group_preferences.chat_id'))
    correct_option_id = Column(Integer)


class UserScore(Base):
    __tablename__ = 'user_scores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    chat_id = Column(BigInteger)
    score = Column(Float, default=0.0)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    __table_args__ = (UniqueConstraint('user_id', 'chat_id'), )


class SentQuestion(Base):
    __tablename__ = 'sent_questions'

    chat_id = Column(BigInteger, primary_key=True)
    question_id = Column(String, primary_key=True)
    __table_args__ = (UniqueConstraint('chat_id', 'question_id'), )


class WeeklyScore(Base):
    __tablename__ = 'weekly_scores'

    user_id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, primary_key=True)
    score = Column(Float, default=0.0)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    __table_args__ = (UniqueConstraint('user_id', 'chat_id'), )


class Topic(Base):
    __tablename__ = 'topics'

    category_id = Column(String, primary_key=True)
    category_name = Column(String, nullable=False)
    source = Column(String, primary_key=True)


class UserPreferences(Base):
    __tablename__ = 'user_preferences'

    user_id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    settings = Column(JSON, nullable=True)


class ActiveUserStat(Base):
    __tablename__ = 'active_user_stat'

    user_id = Column(BigInteger, primary_key=True, unique=True, nullable=True)
    last_quiz_active_time = Column(DateTime, nullable=False)


class ActiveGroupStat(Base):
    __tablename__ = 'active_group_stat'
    chat_id = Column(BigInteger, primary_key=True, unique=True, nullable=True)
    last_quiz_group_active_time = Column(DateTime, nullable=False)
