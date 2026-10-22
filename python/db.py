import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost", port=5433,
        dbname="docs", user="postgres", password="postgres"
    )