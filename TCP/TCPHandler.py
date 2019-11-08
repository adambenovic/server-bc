import socket
import time

BUFFER_SIZE = 1024

class TCPListener(object):

    def __init__(self, ip="127.0.0.1", port=5001):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((ip, port))
        self._sock.listen(1)
        return

    def run(self, handler=None):
        while True:
            conn, addr = self._sock.accept()
            while True:
                try:        
                    data = conn.recv(BUFFER_SIZE)
                    if(not data):
                        break
                    if(handler):
                        handler(data)
                    conn.send("OK\n")
                except socket.error as error:
                    print error
                    break
            conn.close()

class TCPSender(object):

    def __init__(self, ip="127.0.0.1", port=5000):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((ip, port))
        return

    def send(self, message):
        self._sock.send(message)
        respond = self._sock.recv(BUFFER_SIZE)
        return respond

    #TODO how to use with
    def close(self):
        self._sock.close()

def handler(data):
    print data

if __name__=="__main__":
    """
    sender = TCPSender()
    print sender.send("1\n")
    print sender.send("1\n")
    print sender.send("1\n")
    print sender.send("1\n")
    sender.close()
    """
    listener = TCPListener()
    listener.run()
