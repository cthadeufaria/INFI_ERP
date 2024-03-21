import xml.etree.ElementTree as ET


class Order:

    def __init__(self, file, path='./xml_orders_examples/'):
    
        tree = ET.parse(path + file)

        root = tree.getroot()

        print(root)

        self.order = {
            root[0].attrib,
            [order.attrib for order in root[1:]]
        }
