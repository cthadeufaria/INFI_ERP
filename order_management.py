import xml.etree.ElementTree as ET


class Order:

    def __init__(self, file):
        # tree = ET.parse(file)
        tree = ET.ElementTree(ET.fromstring(file))
        root = tree.getroot()

        client = root[0].attrib

        orders = [order.attrib for order in root[1:]]

        for order in orders:
            order['Number'] = int(order['Number'])
            order['Quantity'] = int(order['Quantity'])
            order['DueDate'] = int(order['DueDate'])
            order['LatePen'] = int(order['LatePen'])
            order['EarlyPen'] = int(order['EarlyPen'])

        self.file = [
            client,
            orders
        ]
