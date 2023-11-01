import psycopg2

# init env variables and keys
import os
from dotenv import load_dotenv
load_dotenv()

POSTGRES_DABATASE_URL = os.getenv("POSTGRES_DATABASE_URL")

# create a database connection Class to use in other files
class Database:
    def __init__(self):
        self.connection = psycopg2.connect(POSTGRES_DABATASE_URL)
        self.cursor = self.connection.cursor()

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params)
        self.connection.commit()
        return self.cursor

    def fetchone(self, sql, params=None):
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()

    def fetchall(self, sql, params=None):
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.connection.close()