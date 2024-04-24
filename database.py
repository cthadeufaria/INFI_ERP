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


    def update_clients_orders(self, xml):
        client_tuple, orders_tuples = self.create_tuples(xml)

        ans = self.send_query(
            """SELECT * from erp_mes.client;""", 
            fetch=True
        )

        in_any = False

        for tuple in ans:
            if client_tuple[0] in tuple:
                in_any = True

        if not in_any:
            self.send_query(
                """INSERT INTO erp_mes.client (name) VALUES (%s);""", 
                parameters=client_tuple
            )

        ans = self.send_query(
            """SELECT * from erp_mes.client as c WHERE c.name = (%s);""", 
            parameters=client_tuple,
            fetch=True
        )

        for t in orders_tuples:
            self.send_query(
                """INSERT INTO erp_mes.client_order (number, piece, quantity, duedate, latepen, earlypen, client_id) VALUES (%s, %s, %s, %s, %s, %s, %s);""", 
                parameters=t + (ans[0][0],)
            )


    def send_query(self, query, parameters=None, fetch=False):
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

        return ans


    def create_tuples(self, xml):
        return tuple(xml[0].values()), [tuple(x.values()) for x in xml[1]]