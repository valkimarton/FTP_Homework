from netsim.netinterface import network_interface
from messages import HandshakeMessage

class Server:
    def __init__(self, network_path, own_address):
        self.network_path = network_path
        self.own_address = own_address
        self.networkIF = network_interface(network_path, own_address)

        self.active_client = ''
        self.session_key = ''
        self.sequence_number = -1


    def main_loop(self):
        print('Server main loop started...')

        while True:
            status, bytes_message = self.networkIF.receive_msg(blocking=True)  # when returns, status is True and msg contains a message
            message = HandshakeMessage.HandshakeMessage()
            message.from_bytes(bytes_message)

            message.print()

            response = 'ACK'
            self.networkIF.send_msg('C', response.encode('utf-8'))

        print('Client main loop ended...')

    def print(self):
        print('Address: ' + self.own_address + '\n' + 'Network path: ' + self.network_path)

    def initSession(self, client):
        self.importSharedSecret()

    def importSharedSecret(self, client):
        pass

