from database import Database
from order_management import Order
from receive_udp import UDPsocket
import threading



def main():
    udp = UDPsocket()

    receive_thread = threading.Thread(target=udp.listen)
    receive_thread.start()

    order = Order('command0.xml')
    # order = Order(xml) Qual o formato do arquivo recebido? Como adaptar a funcao para recebe-lo?

    # db = Database()
    # db.update(order.file)

    while True:
        pass

    print('stop')


if __name__ == "__main__":

    while True:
        main()