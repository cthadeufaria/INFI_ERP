import asyncio



class EchoUDPProtocol(asyncio.DatagramProtocol):

    def connection_made(self, transport):
    
        self.transport = transport
        self.message = None

    
    def datagram_received(self, data, addr):
    
        self.message = data.decode()
        print(f"Received {self.message} from {addr}")

    def get_message(self):

        return self.message


class UDPsocket:

    def __init__(self) -> None:
        
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 24680
    

    async def create_socket(self):

        print("Starting UDP server")

        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: EchoUDPProtocol(),
            local_addr=(self.UDP_IP, self.UDP_PORT)
        )


    def listen(self):

        data = None

        print("Listening for UDP packets on %s: %s" % (self.UDP_IP, self.UDP_PORT))
        
        while data == None:
            data, addr = self.sock.recvfrom(1024)
            print("Received packet from %s: %s" % (addr, data.decode('utf-8')))

        return data.decode('utf-8')

