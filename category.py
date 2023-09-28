import psycopg2
import requests

# PostgreSQL database connection parameters
db_url = "postgres://sdshmdjm:9DENXUHGf17Abm7-MbyH-Pg87GkttKyg@castor.db.elephantsql.com/sdshmdjm"

# API endpoints for fetching categories
opentdb_api_url = "https://opentdb.com/api_category.php"
the_trivia_api_url = "https://the-trivia-api.com/v2/categories"

# Define table name for the merged categories
topics_table_name = "topics"

# Function to create the "topics" table in the PostgreSQL database
def create_topics_table():
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Create the "topics" table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            category_id VARCHAR(255) PRIMARY KEY,
            category_name VARCHAR(255) NOT NULL,
            source VARCHAR(255) NOT NULL
        )
        """)

        conn.commit()
        print("Table 'topics' created successfully.")
    except psycopg2.Error as e:
        print(f"Error creating 'topics' table: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to fetch and format categories from the OpenTDB API
def fetch_opentdb_categories(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        categories = []

        for category in data.get("trivia_categories", []):
            categories.append({"category_id": str(category["id"]), "category_name": category["name"], "source": "opentdb"})

        return categories
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch categories from {api_url}: {e}")
        return []

# Function to fetch and format categories from the trivia API
def fetch_the_trivia_categories(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        categories = []

        for category_name, subcategories in data.items():
            # Insert the main category with one of its subcategories into the table
            if subcategories:
                category_id = subcategories[0]  # Choose the first subcategory
                categories.append({"category_id": category_id, "category_name": category_name, "source": "trivia"})

        return categories
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch categories from {api_url}: {e}")
        return []

# Function to insert categories into the "topics" table
def insert_categories_into_topics(categories):
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        for category in categories:
            cursor.execute(f"INSERT INTO {topics_table_name} (category_id, category_name, source) VALUES (%s, %s, %s)",
                           (category["category_id"], category["category_name"], category["source"]))

        conn.commit()
        print(f"Inserted {len(categories)} categories into the '{topics_table_name}' table.")
    except psycopg2.Error as e:
        print(f"Error inserting data into '{topics_table_name}' table: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Create the "topics" table in the PostgreSQL database
    create_topics_table()

    # Fetch and format categories from both APIs
    opentdb_categories = fetch_opentdb_categories(opentdb_api_url)
    the_trivia_categories = fetch_the_trivia_categories(the_trivia_api_url)

    # Merge and insert categories into the "topics" table
    merged_categories = opentdb_categories + the_trivia_categories
    insert_categories_into_topics(merged_categories)
