from bot.database.models import Topic
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from bot.helpers.yaml import load_config
from typing import Final, List, Dict
from sqlalchemy import create_engine

# YAML Loader
db_config = load_config("config.yml")["database"]

# Constants
DB_SCHEMA: Final[str] = db_config.get("schema")

db_engine = create_engine(DB_SCHEMA)
Session = sessionmaker(bind=db_engine)

def insert_categories_into_topics(categories: List[Dict[str, str]]) -> None:
    inserted_count = 0
    try:
        session = Session()
        for category in categories:
            category_id = category["category_id"]
            source = category["source"]
            existing_topic = session.query(Topic).filter_by(category_id=category_id, source=source).first()
            if not existing_topic:
                inserted_count += 1
                new_topic = Topic(
                    category_id=category_id,
                    category_name=category["category_name"],
                    source=source
                )
                session.add(new_topic)
        session.commit()
        if inserted_count:
            print(f"Inserted {inserted_count} categories into the 'topics' table.")
    except IntegrityError as e:
        session.rollback()
        print(f"IntegrityError: {e}")
    except Exception as e:
        print(f"Error inserting data into 'topics' table: {e}")
    finally:
        session.close()