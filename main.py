from database import Database
from order_management import Order
from receive_udp import UDPsocket
import threading
import time


def main():
    udp = UDPsocket()
    db = Database()

    receive_thread = threading.Thread(target=udp.listen)
    receive_thread.start()

    while True:
        time.sleep(3)
        print('loop')

        if udp.data != None:
            order = Order(udp.data)
            db.update(order.file)
            udp.reset_data()


if __name__ == "__main__":
    main()
