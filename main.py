from database import Database as db
from order_management import Order


if __name__ == "__main__":

    order = Order('command0.xml')

    db = db()

    db.update(order.xml)

    print('stop')