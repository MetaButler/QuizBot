import httpx
from bot.main import db_engine
from bot.database.models import Topic
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from typing import List, Dict

Session = sessionmaker(bind=db_engine)

def fetch_opentdb_categories(API_URL_OPENTDB: str) -> List[Dict[str, str]]:
    try:
        with httpx.Client() as client:
            response = client.get(API_URL_OPENTDB)
            response.raise_for_status()
            data = response.json()
            categories = []

            for category in data.get("trivia_categories", []):
                categories.append({"category_id": str(category["id"]), "category_name": category["name"], "source": "opentdb"})

            return categories
    except httpx.HTTPError as e:
        print(f"Failed to fetch categories from {API_URL_OPENTDB}: {e}")
        return []

def fetch_the_trivia_categories(API_URL_TRIVIA: str) -> List[Dict[str, str]]:
    try:
        with httpx.Client() as client:
            response = client.get(API_URL_TRIVIA)
            response.raise_for_status()
            data = response.json()
            categories = []

            for category_name, subcategories in data.items():
                if subcategories:
                    category_id = subcategories[0]
                    categories.append({"category_id": category_id, "category_name": category_name, "source": "trivia"})

            return categories
    except httpx.HTTPError as e:
        print(f"Failed to fetch categories from {API_URL_TRIVIA}: {e}")
        return []

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