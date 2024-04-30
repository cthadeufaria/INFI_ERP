import xml.etree.ElementTree as ET
from database import Database


class Order(Database):

    def __init__(self, file):
        super().__init__()

        tree = ET.ElementTree(ET.fromstring(file))
        root = tree.getroot()

        client = root[0].attrib

        orders = [order.attrib for order in root[1:]]

        for order in orders:
            order['Number'] = int(order['Number'])
            order['Quantity'] = int(order['Quantity'])
            order['WorkPiece'] = str(order['WorkPiece'])
            order['DueDate'] = int(order['DueDate'])
            order['LatePen'] = int(order['LatePen'])
            order['EarlyPen'] = int(order['EarlyPen'])

        self.file = [
            client,
            orders
        ]


    def update_clients_orders(self):
        client_tuple, orders_tuples = self.create_tuples(self.file)

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


    def create_tuples(self, xml):
        return tuple(xml[0].values()), [tuple(x.values()) for x in xml[1]]