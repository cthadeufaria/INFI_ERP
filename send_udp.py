import socket



UDP_IP = "127.0.0.1"  
UDP_PORT = 24680   
path = './xml_orders_examples/'
files = ['command2a.xml', 'command4.xml']

for file in files:
    xml = open(path + file)
    message = xml.read(1024)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.sendto(message.encode(), (UDP_IP, UDP_PORT))
        print(f"Sent UDP packet to {UDP_IP}:{UDP_PORT}: {message}")
    finally:
        sock.close()