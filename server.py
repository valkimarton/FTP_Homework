from netsim.netinterface import network_interface
from messages.HandshakeMessage import HandshakeMessage
from messages.FileTransferMessage import FileTransferMessage
from utils.GeneralUtils import *
from utils.enums import *
from utils.constants import *
from utils.CryptoUtils import *
from server_root.database import database


class Server:
    def __init__(self, network_path, own_address):
        self.network_path = network_path
        self.own_address = own_address
        self.networkInterface = network_interface(network_path, own_address)

        self.secret_encryption_key = 'secret_encryption_key'

        #########
        # STATE #
        #########
        self.connected_to_client = False
        self.active_client = ''
        self.session_key = b''
        self.shared_secret = b''
        self.sequence_number = -1

    def main_loop(self):
        print('Server main loop started...')

        # The main loop
        while True:

            # HANDSHAKE LOOP - until successfully completed handshake with a client
            while not self.connected_to_client:
                self.handle_handshake_request()

            # COMMAND LOOP - Until Client closes connection with FIN-handshake
            while True:
                print('Waiting for commands')

                status, msg = self.networkInterface.receive_msg(blocking=True)

                # Ha HANDSHAKE típúsú üzenet jön
                if self.get_message_id(msg) == HANDSHAKE_MESSAGE_ID:
                    session_ended = self.handle_handshake_messages_during_session(
                        msg)  # Ha valid FIN üzenet jön -> kapcsolat bontása
                    if session_ended:
                        break
                # Ha COMMAND típúsú üzenet jön
                elif self.get_message_id(msg) == COMMAND_MESSAGE_ID:

                    self.networkInterface.send_msg(self.active_client, b'COMMAND ARRIVED, handling not implemented')

                    ###############################
                    # COMMAND MESSAGE HANDLING HERE
                    ###############################
                elif self.get_message_id(msg) == FILE_TRANSFER_MESSAGE_ID:
                    upload = False
                    download = False
                    if self.get_message_type(msg) == FileTransferMessageTypes.NEW_DNL:
                        download = True
                        filename = self.get_message_payload(msg)
                        print(filename)
                    elif self.get_message_type(msg) == FileTransferMessageTypes.NEW_UPL:
                        upload = True
                        filename = self.get_message_payload(msg)
                        print(filename)
                    else:
                        print('Wrong message type!')

                    if (download):
                        self.init_download(filename)
                        self.send_file(filename)

                    elif (upload):
                        self.init_upload(filename)
                        self.save_file(filename)

                else:
                    print('Invalid message type')

        print('Server main loop ended... (Should not happen)')

    ##################
    # NÓRI
    ##################

    ##################
    # PETI
    ##################
    def get_message_type(self, message: bytes) -> str:
        return message[4:7].decode('utf-8')

    def get_message_payload(self, message: bytes) -> str:
        return message[33:-16].decode('utf-8')

    def init_download(self, filename: str):
        timestamp = get_current_timestamp()
        payload = filename.encode('utf-8')
        message = FileTransferMessage(self.own_address, FileTransferMessageTypes.DNL_NEW_ACK, timestamp,
                                      payload, 0)
        self.networkInterface.send_msg(self.active_client, message.to_bytes())
        message = FileTransferMessage(self.own_address, FileTransferMessageTypes.SEND, timestamp,
                                      payload, 0)
        self.networkInterface.send_msg(self.active_client, message.to_bytes())

    def init_upload(self, filename: str):
        timestamp = get_current_timestamp()
        payload = filename.encode('utf-8')
        message = FileTransferMessage(self.own_address, FileTransferMessageTypes.UPL_NEW_ACK, timestamp,
                                      payload, 0)
        self.networkInterface.send_msg(self.active_client, message.to_bytes())
        status, msg = self.networkInterface.receive_msg(blocking=True)
        message = FileTransferMessage()
        message.from_bytes(msg)
        if message.type == FileTransferMessageTypes.SEND:
            print('SND received')

    def send_file(self, filename: str):
        last = False
        seq_num = 1
        while (last == False):
            timestamp = get_current_timestamp()
            f = open(filename, 'r')
            payload = f.read(512).encode('utf-8')
            if len(payload) <= 512:
                last = True
                f.close()
                payload.ljust(512, '0'.encode('utf-8'))  # padding
            message = FileTransferMessage(self.own_address, FileTransferMessageTypes.DAT, timestamp,
                                          payload, seq_num, last)
            self.networkInterface.send_msg(self.active_client, message.to_bytes())
            seq_num += 1
            # Miután elküldött mindent, vár egy FIN-üzenetre, hogy a kliens megkapta-e az utolsó darabot is
            # Ha megkapja, akkor nyugtázza
            if last:
                status, msg = self.networkInterface.receive_msg(blocking=True)
                message = FileTransferMessage()
                message.from_bytes(msg)
                if message.type == FileTransferMessageTypes.FIN:
                    print('FIN received, closing download...')
                    self.close_download(filename)
                    print('Done.')
                    break

    def save_file(self, filename: str):
        last = False
        while not last:
            status, msg = self.networkInterface.receive_msg(blocking=True)
            message = FileTransferMessage()
            message.from_bytes(msg)
            if message.type == FileTransferMessageTypes.DAT:
                print('DAT received, saving file...')
                payload = message.payload
                f = open(filename, 'a')
                f.write(payload)
                f.close()
                if message.last:
                    last = True
            else:
                print('Invalid message type!')
                break
            if last:
                print('Done.')
                self.close_upload(filename)

    def close_download(self, filename: str):
        timestamp = get_current_timestamp()
        payload = filename.encode('utf-8')
        message = FileTransferMessage(self.own_address, FileTransferMessageTypes.ACK_FIN, timestamp,
                                      payload, 0)
        self.networkInterface.send_msg(self.active_client, message.to_bytes())

    def close_upload(self, filename: str):
        timestamp = get_current_timestamp()
        payload = filename.encode('utf-8')
        message = FileTransferMessage(self.own_address, FileTransferMessageTypes.FIN, timestamp,
                                      payload, 0)
        self.networkInterface.send_msg(self.active_client, message.to_bytes())
        status, msg = self.networkInterface.receive_msg(blocking=True)
        message = FileTransferMessage()
        message.from_bytes(msg)
        if message.type == FileTransferMessageTypes.ACK_FIN:
            print('FIN_ACK received, closing upload...')

    ##################
    # MARCI
    ##################

    # A HANDSHAKE loop-ban várja és kezeli az érkező üzeneteket
    def handle_handshake_request(self):
        print('Handling a handshake request...')

        status, msg = self.networkInterface.receive_msg(blocking=True)
        message = decrypt_message(msg, get_shared_secret_by_client(msg[1:2].decode('utf-8'), self.secret_encryption_key)) # még nincs beállítva a self.shared_secret
        message.print()

        # felhasználónév + jelszó ellenőrzés
        if not self.is_password_valid(message):
            self.reject_handshake(message)

        # ha nincs aktív kliens vagy az aktív kliens küldte újra a handshake-et (nem kapta meg a választ mondjuk)
        elif self.active_client == '' or self.active_client == message.client:
            self.create_session(message)
            self.accept_handshake()
        else:  # Ha már foglalt a szerver
            self.reject_handshake(message)

    # Új session állapot generálása, beállítása
    def create_session(self, message: HandshakeMessage):
        print('Creating new session with client: ' + message.client)

        self.shared_secret = get_shared_secret_by_client(message.client, self.secret_encryption_key)
        self.active_client = message.client
        self.sequence_number = 0
        self.session_key = get_random_session_key()
        self.connected_to_client = True

    # érvényes Hanshake NEW üzenet elfogadása
    def accept_handshake(self):
        response = HandshakeMessage.HandshakeMessage(self.active_client, HandshakeMessageTypes.NEW_ACK, get_current_timestamp(),
                                    self.session_key)
        self.networkInterface.send_msg(self.active_client, encrypt_message(response, self.shared_secret))
        print('Handshake accepted...')

    # HANDSHAKE típusú üzenetek kezelése a COMMAND loop alatt. !!! RETURN TYPE: BOOL --> Így lehet kilépni a COMMAND loop-ból FIN üzenet esetén !!!
    def handle_handshake_messages_during_session(self, msg: bytes) -> bool:
        message = decrypt_message(msg, self.shared_secret)
        if message.type == HandshakeMessageTypes.FIN and message.client == self.active_client:
            self.close_session()
            return True
        elif message.type == HandshakeMessageTypes.NEW and message.client == self.active_client:
            self.accept_handshake()
            return False
        elif message.type == HandshakeMessageTypes.NEW and message.client != self.active_client:
            self.reject_handshake(message)
            return False
        else:
            return False  # Ignore

    # Kapcsolat bontása FIN esetén
    def close_session(self):
        fin_ack = HandshakeMessage.HandshakeMessage(self.active_client, HandshakeMessageTypes.FIN_ACK, get_current_timestamp())
        self.networkInterface.send_msg(self.active_client, encrypt_message(fin_ack, self.shared_secret))

        # !!! Implement wait for FIN_ACK

        print('Session closed with client: ' + self.active_client)
        self.reset_state()

    def reject_handshake(self, message: HandshakeMessage):
        response = HandshakeMessage.HandshakeMessage(message.client, HandshakeMessageTypes.REJ, get_current_timestamp())
        self.networkInterface.send_msg(message.client, encrypt_message(response, get_shared_secret_by_client(message.client, self.secret_encryption_key)))  # még nincs beállítva a self.shared_secret
        print('Handshake rejected...')

    # check credentials
    def is_password_valid(self, message: HandshakeMessage) -> bool:
        password = message.payload.decode('utf-8')
        password_hash = get_password_hash(password)

        if password_hash == database[message.client]['password_hash']:
            print(password_hash)
            print(database[message.client]['password_hash'])
            return True
        else:
            return False

    def get_message_id(self, message: bytes) -> str:
        return message[0:1].decode('utf-8')

    def reset_state(self):
        self.shared_secret = b''
        self.connected_to_client = False
        self.active_client = ''
        self.session_key = ''
        self.sequence_number = -1
        self.upload = False
        self.download = False

    def print(self):
        print('Address: ' + self.own_address + '\n' + 'Network path: ' + self.network_path)

    def initSession(self, client):
        self.importSharedSecret()

    def importSharedSecret(self, client):
        pass
