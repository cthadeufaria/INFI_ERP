import psycopg2
import os


class Database:

    def __init__(self):
        self.host = "db.fe.up.pt"
        self.port = "5432"
        self.user = os.getenv('db_user')
        self.password = os.getenv('db_password')
        self.database = os.getenv('db_name')


    def connect(self):
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )

        except psycopg2.Error as e:
            print("Error connecting to the database:")
            print(e)

        else:
            print("Connection to database established successfully")
        
        return conn


    def send_query(self, query, parameters=None, fetch=False):
        while True:
            try:    
                conn = self.connect()
                cur = conn.cursor()

                if parameters == None:
                    cur.execute(query)
                else:
                    cur.execute(query, (parameters))

                if fetch == True:
                    ans = cur.fetchall()
                else:
                    ans = None
                conn.commit()
                cur.close()
                conn.close()
                print("Connection to database closed")
                break
            
            except:
                print("Database error. Trying again.")

        return ans