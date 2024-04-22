from database import Database
from order_management import Order
from receive_udp import UDPsocket
from time_management import Clock
from mps import MPS
import threading
import time


def main():
    udp_orders = UDPsocket("127.0.0.1", 24680)
    db = Database()
    clock = Clock()
    mps = MPS()

    udp_thread = threading.Thread(target=udp_orders.listen)
    udp_thread.start()

    clock_thread = threading.Thread(target=clock.listen)
    clock_thread.start()

    while True:
        time.sleep(1)
        print('loop')

        if udp_orders.data != None:
            order = Order(udp_orders.data)
            db.update_clients_orders(order.file)
            udp_orders.reset_data()

        if clock.trigger:
            mps.create_mps(clock.today)


if __name__ == "__main__":
    main()
