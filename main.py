import threading
import time

from order_management import Order
from receive_udp import UDPsocket
from time_management import Clock
from mps import MPS



def main():
    udp_orders = UDPsocket("127.0.0.1", 24680)
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
            order.update_clients_orders()
            udp_orders.reset_data()

        if clock.trigger:
            # mps.create_mps(clock.today)
            print('Create MPS')
            clock.reset_trigger()

if __name__ == "__main__":
    main()
