import time

from netsim.netinterface import network_interface
from messages.HandshakeMessage import HandshakeMessage
from messages.FileTransferMessage import FileTransferMessage
from utils.GeneralUtils import *
from utils.enums import *
from utils.CryptoUtils import *


class Client:

    def __init__(self, network_path, own_address):
        self.network_path = network_path
        self.own_address = own_address
        self.networkInterface = network_interface(network_path, own_address)

        self.shared_secret = b'shared_secret_' + own_address.encode('utf-8') + b'_0123456789012345'    # TODO: fájblól beolvasni mint a szervernél...

        #########
        # STATE #
        #########
        self.connected_to_server = False
        self.server_address = ''
        self.session_key = ''
        self.sequence_number = -1

    def main_loop(self):
        print('Client main loop started...')

        # main loop
        while True:

            # Handshake loop until successful handshake
            while not self.connected_to_server:
                self.connect_to_server()

            # Command loop until a FINISH command
            while True:
                command = input('Type a command: ')
                if command == 'FIN':
                    self.disconnect_from_server()
                    break
                elif command == 'MKD':
                    print('Not implemented...')
                ########
                # Other commands here
                ########
                elif command == 'UPL':
                    self.init_upload()
                elif command == 'DNL':
                    self.init_download()
                else:
                    print('Invalid command!')

            if input('Continue? (y/n): ') == 'n': break

        print('Client main loop ended...')

    ##################
    # NÓRI
    ##################

    ##################
    # PETI
    ##################
    def init_upload(self):
        filename = input('Choose a file to upload: ')
        payload = filename.encode('utf-8')
        timestamp = get_current_timestamp()
        # Initiate connection
        message = FileTransferMessage(self.own_address, FileTransferMessageTypes.NEW_UPL, timestamp, payload)
        self.networkInterface.send_msg(self.server_address, message.to_bytes())
        time.sleep(2)  # REMOVE
        status, rsp = self.networkInterface.receive_msg(blocking=False)
        if status:
            response = FileTransferMessage()
            response.from_bytes(rsp)
            if response.type == FileTransferMessageTypes.UPL_NEW_ACK:
                print('ack arrived')
            else:
                pass
            print('Response (UPL_NEW_ACK): ')
            response.print()
        else:
            print('No answer arrived in 2 seconds')


    def init_download(self):
        print('Not implemented...')
        filename = input('Choose a file to download: ')
        payload = filename.encode('utf-8')
        timestamp = get_current_timestamp()
        # Initiate connection
        message = FileTransferMessage(self.own_address, FileTransferMessageTypes.NEW_DNL, timestamp, payload, 0)
        self.networkInterface.send_msg(self.server_address, message.to_bytes())
        time.sleep(2)  # REMOVE
        # Waiting for response
        status, rsp = self.networkInterface.receive_msg(blocking=False)
        if status:
            response = FileTransferMessage()
            response.from_bytes(rsp)
            if response.type == FileTransferMessageTypes.DNL_NEW_ACK:
                print('DNL_NEW_ACK arrived')
            else:
                pass
            print('Response (DNL_NEW_ACK): ')
            response.print()
        else:
            print('No answer arrived in 2 seconds')
        # # time.sleep(2)  # REMOVE
        # status, rsp = self.networkInterface.receive_msg(blocking=False)
        # if status:
        #     response = FileTransferMessage()
        #     response.from_bytes(rsp)
        #     if response.type == FileTransferMessageTypes.SEND:
        #         print('SEND arrived')
        #     else:
        #         pass
        #     print('Response (SEND): ')
        #     response.print()
        # else:
        #     print('No answer arrived in 2 seconds')

    ##################
    # MARCI
    ##################

    # Csatlakozás kezdeményezése, válasz kezelése, session_state beállítása
    def connect_to_server(self):
        self.server_address = input('Initiating connection. Type server address: ')

        password = input('Type your password: ')
        payload = password.encode('utf-8')
        timestamp = get_current_timestamp()

        # NEW
        message = HandshakeMessage.HandshakeMessage(self.own_address, HandshakeMessageTypes.NEW, timestamp, payload)
        self.networkInterface.send_msg(self.server_address, encrypt_message(message, self.shared_secret))

        # Handle response
        time.sleep(2)  # REMOVE
        status, rsp = self.networkInterface.receive_msg(blocking=False)
        if status:
            response = decrypt_message(rsp, self.shared_secret) #decrypting response
            if response.type == HandshakeMessageTypes.NEW_ACK:
                self.create_session(response)
            else:
                pass

            print('Response (' + response.type + '):')
            response.print()
        else:
            print('No answer arrived in 2 seconds')

    # Session state beállítása
    def create_session(self, response: HandshakeMessage):
        self.session_key = response.payload
        self.sequence_number = 0
        self.connected_to_server = True
        print('Session created with server: ' + self.server_address + ', shared secret: ', self.session_key)

    # Kapcsolat bontásának kezdeményezése, válasz kezelése, session lebontása sikeres esetben
    def disconnect_from_server(self):

        message = HandshakeMessage.HandshakeMessage(self.own_address, HandshakeMessageTypes.FIN, get_current_timestamp())
        self.networkInterface.send_msg(self.server_address, encrypt_message(message, self.shared_secret))

        # wait for FIN ACK
        time.sleep(2)
        status, rsp = self.networkInterface.receive_msg(blocking=False)
        if status:
            response = decrypt_message(rsp, self.shared_secret)
            if response.type == HandshakeMessageTypes.FIN_ACK:
                self.reset_state()
                print('Session closed (Partially implemented...)')
            else:
                print('Anticipated FIN_ACK, but got something else...')
        else:
            print('No response arrived to FIN')

        '''
        Handshake process incomplete
        '''

        print('Closing Handshake Partially implemented...')

    def reset_state(self):
        self.server_address = ''
        self.connected_to_server = False
        self.session_key = ''
        self.sequence_number = -1

    # Nem blokkoló mechanizmus parancs elküldésére és válaszra várásra
    # A válasz elveszése, kései érkezése probléma lehet.
    # A válasz elveszése esetében a blokkoló várakozásból nem lehet kilépni
    # Erre lehet csinálni egy ilyen retry-os nem blokkoló várakozásos megoldást, ha nagyon sok időnk van.
    #
    # call_to_make: Az elküldendő üzenet
    # wait_length: várakozási idő két újrapróbálkozás között
    # num_of_retries: maximum próbálkozások száma
    def call_wait_retry(self, call_to_make, wait_length, num_of_reties):
        print('Not implemented')

    def print(self):
        print('Address: ' + self.own_address + '\n' + 'Network path: ' + self.network_path)