import threading
import time

from order_management import Order
from receive_udp import UDPsocket
from time_management import Clock
from mps import MPS
# from mes import MES



def main():
    udp_orders = UDPsocket("0.0.0.0", 24680)
    clock = Clock(debug=False)
    mps = MPS(debug=False)
    # mes = MES(debug=True)

    udp_thread = threading.Thread(target=udp_orders.listen)
    udp_thread.start()

    clock_thread = threading.Thread(target=clock.listen)
    clock_thread.start()

    print("Server is running")
    
    while True:
        time.sleep(1)

        if udp_orders.data != None:
            order = Order(udp_orders.data)
            order.update_clients_orders()
            udp_orders.reset_data()

        if clock.trigger: # and mes.is_online(clock.today):
            mps.create_mps(clock.today)
            print('MPS created for day ', clock.today)
            clock.reset_trigger()


if __name__ == "__main__":
    main()
