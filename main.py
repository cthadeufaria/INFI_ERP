from database import Database as db
from order_management import Order


if __name__ == "__main__":
    
    conn = db()

    order = Order('command4.xml')