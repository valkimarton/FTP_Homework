import time

from netsim.netinterface import network_interface
from messages.HandshakeMessage import HandshakeMessage
from messages.FileTransferMessage import FileTransferMessage
from messages.CommandMessage import CommandMessage
from utils.GeneralUtils import *
from utils.enums import *
from utils.CryptoUtils import *
from utils.constants import *


class Client:

    def __init__(self, network_path, own_address):
        self.network_path = network_path
        self.own_address = own_address
        self.networkInterface = network_interface(network_path, own_address)

        self.shared_secret = b'shared_secret_' + own_address.encode(
            'utf-8') + b'_0123456789012345'  # TODO: fájblól beolvasni mint a szervernél...

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
                elif command[0:3] in TYPE_SPACE['C']:
                    print('Use command protocol')
                    commandMessage = self.makeMessage(command, self.own_address, self.sequence_number)
                    if commandMessage != None:
                        self.sequence_number += 1
                        self.networkInterface.send_msg(self.server_address,
                                                       encrypt_message(commandMessage, self.session_key))
                        status, rsp = self.networkInterface.receive_msg(blocking=True)
                        if status:
                            response = CommandMessage.CommandMessage()
                            response.from_bytes(rsp)
                            print(response.payload)
                ########
                # Other commands here
                ########

                elif command[0:3] == 'UPL':
                    filename = command[4:]
                    self.upload(filename)
                elif command[0:3] == 'DNL':
                    filename = command[4:]
                    self.download(filename)
                else:
                    print('Invalid command!')

            if input('Continue? (y/n): ') == 'n': break

        print('Client main loop ended...')

    ##################
    # NÓRI
    ##################

    def makeMessage(self, fullCommand: str, own_addr: str, seq_num: int) -> CommandMessage:
        commmand = fullCommand[0:3]
        payload = fullCommand[4:]
        if self.payload_is_valid(payload) == True:
            sequence_num = seq_num + 1
            message = CommandMessage.CommandMessage(own_addr, commmand, get_current_timestamp(),
                                                    payload.encode('utf-8'), sequence_num)
            return message
        else:
            return None

    def payload_is_valid(self, payload: str) -> bool:  # bad file or foldername format exception?
        if len(payload.split()) > 1:
            raise Exception('Bad file or folder format, use just one word')
        else:
            return True

    ##################
    # PETI
    ##################
    def upload(self, filename: str):
        payload = filename.encode('utf-8')
        timestamp = get_current_timestamp()
        # Initiate connection
        message = FileTransferMessage.FileTransferMessage(self.own_address, FileTransferMessageTypes.NEW_UPL, timestamp,
                                                          payload, 0)
        self.networkInterface.send_msg(self.server_address, encrypt_message(message, self.session_key))
        print('NEW_UPL message sent. Waiting for answer...')
        status, rsp = self.networkInterface.receive_msg(blocking=True)
        if status:
            response = decrypt_message(rsp, self.session_key)
            # Ha kapott ACK-t, akkor küld egy SEND-et, majd az adatokat
            if response.type == FileTransferMessageTypes.UPL_NEW_ACK:
                print('Response (UPL_NEW_ACK): ')
                response.print()
                print('Sending SEND')
                timestamp = get_current_timestamp()
                message = FileTransferMessage.FileTransferMessage(self.own_address, FileTransferMessageTypes.SEND,
                                                                  timestamp, payload, 0)
                self.networkInterface.send_msg(self.server_address, encrypt_message(message, self.session_key))
                print('Uploading file...')
                self.send_file(filename)
            else:
                print('Wrong message type!')
        else:
            print('No answer arrived in 2 seconds')

    def send_file(self, filename: str):
        last = False
        seq_num = 1
        while not last:
            timestamp = get_current_timestamp()
            f = open(filename, 'r')
            payload = f.read(512).encode('utf-8')
            if len(payload) <= 512:
                last = True
                f.close()
                # payload.ljust(512, '0'.encode('utf-8'))  # padding
            message = FileTransferMessage.FileTransferMessage(self.own_address, FileTransferMessageTypes.DAT, timestamp,
                                                              payload, seq_num, last)
            self.networkInterface.send_msg(self.server_address, encrypt_message(message, self.session_key))
            seq_num += 1
            # Miután elküldött mindent, vár egy FIN-üzenetre, hogy a szerver megkapta-e az utolsó darabot is
            # Ha megkapja, akkor nyugtázza
            if last:
                status, rsp = self.networkInterface.receive_msg(blocking=True)
                response = decrypt_message(rsp, self.session_key)
                if response.type == FileTransferMessageTypes.FIN:
                    print('FIN received, uploading finished.')
                    print('Response (FIN): ')
                    response.print()
                    self.close_upload(filename)
                    print('Upload successful.')
                    break

    def download(self, filename: str):
        payload = filename.encode('utf-8')
        timestamp = get_current_timestamp()
        # Initiate connection
        message = FileTransferMessage.FileTransferMessage(self.own_address, FileTransferMessageTypes.NEW_DNL, timestamp,
                                                          payload, 0)
        self.networkInterface.send_msg(self.server_address, encrypt_message(message, self.session_key))
        # Waiting for response
        status, rsp = self.networkInterface.receive_msg(blocking=True)
        if status:
            response = decrypt_message(rsp, self.session_key)
            if response.type == FileTransferMessageTypes.DNL_NEW_ACK:
                print('Response (DNL_NEW_ACK): ')
                response.print()
                status, rsp = self.networkInterface.receive_msg(blocking=True)
                if status:
                    response = decrypt_message(rsp, self.session_key)
                    print('Response (SND): ')
                    response.print()
                    if response.type == FileTransferMessageTypes.SEND:
                        self.save_file(filename)
            else:
                print('Wrong message type!')
        else:
            print('No answer arrived!')

    def close_upload(self, filename: str):
        timestamp = get_current_timestamp()
        payload = filename.encode('utf-8')
        message = FileTransferMessage.FileTransferMessage(self.own_address, FileTransferMessageTypes.ACK_FIN, timestamp,
                                                          payload, 0)
        self.networkInterface.send_msg(self.server_address, encrypt_message(message, self.session_key))
        print('Download successful.')

    def save_file(self, filename: str):
        last = False
        while not last:
            status, rsp = self.networkInterface.receive_msg(blocking=True)
            response = decrypt_message(rsp, self.session_key)
            if response.type == FileTransferMessageTypes.DAT:
                print('DAT received, saving file...')
                chunk = response.payload
                f = open(filename, 'a')
                f.write(chunk)
                f.close()
                if response.last:
                    last = True
            else:
                print('Invalid message type!')
                break
            if last:
                print('Done.')
                self.close_upload(filename)

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
            response = decrypt_message(rsp, self.shared_secret)  # decrypting response
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

        message = HandshakeMessage.HandshakeMessage(self.own_address, HandshakeMessageTypes.FIN,
                                                    get_current_timestamp())
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
