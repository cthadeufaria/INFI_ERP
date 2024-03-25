import xml.etree.ElementTree as ET


class Order:

    def __init__(self, file, path='./xml_orders_examples/'):
    
        tree = ET.parse(path + file)

        root = tree.getroot()

        orders_list = [order.attrib for order in root[1:]]

        for order_dict in orders_list:
            order_dict['Number'] = int(order_dict['Number'])
            order_dict['Quantity'] = int(order_dict['Quantity'])
            order_dict['DueDate'] = int(order_dict['DueDate'])
            order_dict['LatePen'] = float(order_dict['LatePen'])
            order_dict['EarlyPen'] = float(order_dict['EarlyPen'])

        self.xml = [
            root[0].attrib,
            orders_list
        ]
