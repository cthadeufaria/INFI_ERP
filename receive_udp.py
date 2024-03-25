
import socket
import asyncio

class UDPsocket:

    def __init__(self) -> None:
        
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 24680
    

    def create_socket(self):

        # self.sock = await asyncio.loop.create_datagram_endpoint(
        #     lambda: asyncio.DatagramProtocol(), local_addr=(self.UDP_IP, self.UDP_PORT))
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))
        
        print("UDP socket created on %s: %s" % (self.UDP_IP, self.UDP_PORT))


    def listen(self):

        self.data = None

        print("Listening for UDP packets on %s: %s" % (self.UDP_IP, self.UDP_PORT))
        
        while self.data == None:
            self.data, self.addr = self.sock.recvfrom(1024)
            print("Received packet from %s: %s" % (self.addr, self.data.decode('utf-8')))
