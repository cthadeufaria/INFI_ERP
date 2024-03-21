import psycopg2
import os


class Database:

    def __init__(self):

        try:
            self.conn = psycopg2.connect(
                host="db.fe.up.pt",
                port="5432",
                user=os.getenv('db_user'),
                password=os.getenv('db_password'),
                database=os.getenv('db_name')
            )

        except psycopg2.Error as e:
            print("Error connecting to the database:")
            print(e)
        else:
            print("Connection established successfully")