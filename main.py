from database import Database
from order_management import Order
from receive_udp import UDPsocket


def main():
    
    udp = UDPsocket()
    udp.create_socket()
    udp.listen()

    order = Order('command0.xml')

    db = Database()
    db.update(order.xml)

    print('stop')


if __name__ == "__main__":
    main()