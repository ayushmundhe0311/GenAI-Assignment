import psycopg2
import pandas as pd

def get_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="genai_db",
        user="postgres",
        password="root"
    )
    return conn

def run_query(query):
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

if __name__ == "__main__":
    query  ="SELECT * FROM aggregations LIMIT 10;"
    result = run_query(query)
    print(result)