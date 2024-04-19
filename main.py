from database import Database
from order_management import Order
from receive_udp import UDPsocket
import threading
import time


def main():
    udp = UDPsocket("127.0.0.1", 24680)
    db = Database()

    receive_thread = threading.Thread(target=udp.listen)
    receive_thread.start()

    while True:
        time.sleep(1)
        print('loop')

        if udp.data != None:
            order = Order(udp.data)
            db.update(order.file)
            udp.reset_data()


if __name__ == "__main__":
    main()
