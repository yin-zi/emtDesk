import socket


class EMTClient:
    def __init__(self):
        self.client = None

    def connect_socket(self, host, port):
        client = None
        for af, socktype, proto, canonname, sa in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            try:
                client = socket.socket(af, socktype, proto)
                client.connect(sa)
            except OSError:
                if client is not None:
                    client.close()
                client = None
                continue
        self.client = client


if __name__ == '__main__':
    pass
