import socket


class UDPsocket:

    def __init__(self, ip, port) -> None:
        self.UDP_IP = ip
        self.UDP_PORT = port
        self.data = None

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))
        
        print("UDP socket created on %s:%s" % (self.UDP_IP, self.UDP_PORT))


    def listen(self):
        print("Listening for UDP packets on %s:%s" % (self.UDP_IP, self.UDP_PORT))
        
        while True:
            data, addr = self.sock.recvfrom(1024)
            print("Received packet from %s: %s" % (addr, data.decode('utf-8')))
            self.data = data.decode('utf-8')

    def reset_data(self):
        self.data = None