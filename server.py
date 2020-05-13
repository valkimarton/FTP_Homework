from netsim.netinterface import network_interface


class Server:
    def __init__(self, network_path, own_address):
        self.network_path = network_path
        self.own_address = own_address
        self.networkIF = network_interface(network_path, own_address)

    def mainLoop(self):
        print('Server main loop started...')

        while True:
            status, msg = self.networkIF.receive_msg(blocking=True)  # when returns, status is True and msg contains a message
            message = msg.decode('utf-8')

            print(message)

            response = 'ACK'
            self.networkIF.send_msg('C', response.encode('utf-8'))

        print('Client main loop ended...')

    def print(self):
        print('Address: ' + self.own_address + '\n' + 'Network path: ' + self.network_path)
