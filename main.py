from database import Database as db
from order_management import Order
from receive_udp import UDPsocket
import asyncio


def main():
    
    udp = UDPsocket()
    udp.create_socket()
    udp.listen()

    order = Order('command0.xml')

    db = db()

    db.update(order.xml)

    print('stop')


if __name__ == "__main__":
    main()