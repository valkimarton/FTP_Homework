from netsim.netinterface import network_interface
from messages.HandshakeMessage import HandshakeMessage
from messages.FileTransferMessage import FileTransferMessage
from messages.CommandMessage import CommandMessage
from utils.GeneralUtils import *
from utils.enums import *
from utils.constants import *
from utils.CryptoUtils import *
from server_root.database import database
import os, shutil


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
        self.currentDir = ''

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
                decryptedMsg = decrypt_message(msg, self.session_key)

                # Ha HANDSHAKE típúsú üzenet jön
                if decryptedMsg.id == HANDSHAKE_MESSAGE_ID:
                    session_ended = self.handle_handshake_messages_during_session(
                        msg)  # Ha valid FIN üzenet jön -> kapcsolat bontása
                    if session_ended:
                        break


                # Ha COMMAND típúsú üzenet jön
                elif decryptedMsg.id == COMMAND_MESSAGE_ID:
                    print('got a command message')
                    msgType = decryptedMsg.type
                    basePath = self.currentDir + '/'

                    if msgType == CommandMessageTypes.RMD:
                        print('RMD')
                        path = basePath + decryptedMsg.payload
                        resMsg = ''
                        if not os.path.exists(path) & (self.currentDir != path):
                            resMsg = 'Error. No such directory in folder: ' + self.currentDir
                        else:
                            shutil.rmtree(path)
                            resMsg = 'Delete a folder: ' + decryptedMsg.payload

                        resMessage = CommandMessage.CommandMessage(self.own_address, CommandMessageTypes.RMD,
                                                                   get_current_timestamp(), resMsg.encode('utf-8'), 0)
                        self.networkInterface.send_msg(self.active_client, resMessage.to_bytes())

                    elif msgType == CommandMessageTypes.RMF:
                        print('RMF')
                        pathWithFile = basePath + decryptedMsg.payload
                        resMsg = ''
                        if os.path.isfile(pathWithFile):
                            os.remove(pathWithFile)
                            resMsg = 'Removed a file from ' + self.currentDir + '/ ' + decryptedMsg.payload
                        else:
                            resMsg = "Error, file dosen't exist in directory: " + self.currentDir

                        resMessage = CommandMessage.CommandMessage(self.own_address, CommandMessageTypes.RMF,
                                                                   get_current_timestamp(), resMsg.encode('utf-8'), 0)
                        self.networkInterface.send_msg(self.active_client, resMessage.to_bytes())

                    elif msgType == CommandMessageTypes.GWD:
                        print('GWD')
                        resMsg = 'Current directory: ' + self.currentDir
                        resMessage = CommandMessage.CommandMessage(self.own_address, CommandMessageTypes.GWD,
                                                                   get_current_timestamp(), resMsg.encode('utf-8'), 0)
                        self.networkInterface.send_msg(self.active_client, resMessage.to_bytes())


                    elif msgType == CommandMessageTypes.CWD:
                        print('CWD')
                        changeto = decryptedMsg.payload
                        goIn = self.currentDir + '/' + changeto
                        rootDirOfClient = 'server_root/' + self.active_client + '_root'
                        resMsg = ''
                        if (changeto == '../') & (self.currentDir != rootDirOfClient):
                            self.currentDir = self.currentDir[0:self.currentDir.rindex('/')]
                            resMsg = "changed to: " + self.currentDir
                        elif os.path.isdir(goIn) & (changeto != '../'):
                            self.currentDir = goIn
                            resMsg = "changed to: " + self.currentDir
                        else:
                            resMsg = "Folder doesn't exists or can't navigate there"

                        resMessage = CommandMessage.CommandMessage(self.own_address, CommandMessageTypes.GWD,
                                                                   get_current_timestamp(), resMsg.encode('utf-8'), 0)
                        self.networkInterface.send_msg(self.active_client, resMessage.to_bytes())

                    elif msgType == CommandMessageTypes.LST:
                        print('LST')
                        resMsg = os.listdir(self.currentDir)
                        resMessage = CommandMessage.CommandMessage(self.own_address, CommandMessageTypes.GWD,
                                                                   get_current_timestamp(),
                                                                   ', '.join(resMsg).encode('utf-8'), 0)
                        self.networkInterface.send_msg(self.active_client, resMessage.to_bytes())

                    elif msgType == CommandMessageTypes.MKD:
                        print('MKD')
                        path = basePath + decryptedMsg.payload
                        os.mkdir(path)
                        responseMessage = 'Made a new dir, name: ' + decryptedMsg.payload
                        resMessage = CommandMessage.CommandMessage(self.own_address, CommandMessageTypes.MKD,
                                                                   get_current_timestamp(),
                                                                   responseMessage.encode('utf-8'), 0)
                        self.networkInterface.send_msg(self.active_client, resMessage.to_bytes())

                elif decryptedMsg.id == FILE_TRANSFER_MESSAGE_ID:
                    download = False
                    if decryptedMsg.type == FileTransferMessageTypes.NEW_DNL:
                        download = True
                        filename = decryptedMsg.payload.decode('utf-8')
                    elif decryptedMsg.type == FileTransferMessageTypes.NEW_UPL:
                        download = False
                        filename = decryptedMsg.payload.decode('utf-8')
                    else:
                        print('Wrong message type!')

                    if download:
                        self.init_download(filename)
                        self.send_file(filename)

                    elif not download:
                        self.init_upload(filename)
                        self.save_file(filename)
                else:
                    print('Invalid message type')

        print('Server main loop ended... (Should not happen)')

    ##################
    # NÓRI
    ##################

    def get_messages_type(self, message: bytes) -> str:
        return message[4:7].decode('utf-8')

    def executeCommand(self):
        return 0

    ##################
    # PETI
    ##################
    def init_download(self, filename: str):
        timestamp = get_current_timestamp()
        payload = filename.encode('utf-8')
        message = FileTransferMessage.FileTransferMessage(self.own_address, FileTransferMessageTypes.DNL_NEW_ACK,
                                                          timestamp,
                                                          payload, 0)
        self.networkInterface.send_msg(self.active_client, encrypt_message(message, self.session_key))
        message = FileTransferMessage.FileTransferMessage(self.own_address, FileTransferMessageTypes.SEND, timestamp,
                                                          payload, 0)
        self.networkInterface.send_msg(self.active_client, encrypt_message(message, self.session_key))

    def init_upload(self, filename: str):
        timestamp = get_current_timestamp()
        payload = filename.encode('utf-8')
        message = FileTransferMessage.FileTransferMessage(self.own_address, FileTransferMessageTypes.UPL_NEW_ACK,
                                                          timestamp,
                                                          payload, 0)
        self.networkInterface.send_msg(self.active_client, encrypt_message(message, self.session_key))
        status, rsp = self.networkInterface.receive_msg(blocking=True)
        response = decrypt_message(rsp, self.session_key)
        if response.type == FileTransferMessageTypes.SEND:
            print('Response (SND):')
            response.print()

    def send_file(self, filename: str):
        last = False
        seq_num = 1
        f = open(self.currentDir + '/' + filename, 'rb')
        while not last:
            timestamp = get_current_timestamp()
            payload = f.read(2048)
            if len(payload) < 2048:
                last = True
                f.close()
                # payload.ljust(512, '0'.encode('utf-8'))  # padding
            message = FileTransferMessage.FileTransferMessage(self.own_address, FileTransferMessageTypes.DAT, timestamp,
                                                              payload, seq_num, last)
            self.networkInterface.send_msg(self.active_client, encrypt_message(message, self.session_key))
            seq_num += 1
            # Miután elküldött mindent, vár egy FIN-üzenetre, hogy a kliens megkapta-e az utolsó darabot is
            # Ha megkapja, akkor nyugtázza
            if last:
                status, rsp = self.networkInterface.receive_msg(blocking=True)
                response = decrypt_message(rsp, self.session_key)
                if response.type == FileTransferMessageTypes.FIN:
                    print('FIN received, closing download...')
                    response.print()
                    self.close_download(filename)
                    print('Done.')
                    break

    def save_file(self, filename: str):
        last = False
        f = open(self.currentDir + '/' + filename, 'ab')
        while not last:
            status, rsp = self.networkInterface.receive_msg(blocking=True)
            response = decrypt_message(rsp, self.session_key)
            if response.type == FileTransferMessageTypes.DAT:
                print('DAT received, saving file...')
                payload = response.payload
                f.write(payload)
                if response.last:
                    last = True
                    f.close()
            else:
                print('Invalid message type!')
                break
            if last:
                print('Done.')
                self.close_upload(filename)

    def close_download(self, filename: str):
        timestamp = get_current_timestamp()
        payload = filename.encode('utf-8')
        message = FileTransferMessage.FileTransferMessage(self.own_address, FileTransferMessageTypes.ACK_FIN, timestamp,
                                                          payload, 0)
        self.networkInterface.send_msg(self.active_client, encrypt_message(message, self.session_key))

    def close_upload(self, filename: str):
        timestamp = get_current_timestamp()
        payload = filename.encode('utf-8')
        message = FileTransferMessage.FileTransferMessage(self.own_address, FileTransferMessageTypes.FIN, timestamp,
                                                          payload, 0)
        self.networkInterface.send_msg(self.active_client, encrypt_message(message, self.session_key))
        status, rsp = self.networkInterface.receive_msg(blocking=True)
        response = decrypt_message(rsp, self.session_key)
        if status:
            if response.type == FileTransferMessageTypes.ACK_FIN:
                print('FIN_ACK received, closing upload...')
                print('Response (ACK_FIN):')
                response.print()
            else:
                print('Wrong message type!')
        else:
            print('No answer arrived!')

    ##################
    # MARCI
    ##################

    # A HANDSHAKE loop-ban várja és kezeli az érkező üzeneteket
    def handle_handshake_request(self):
        print('Handling a handshake request...')

        status, msg = self.networkInterface.receive_msg(blocking=True)
        message = decrypt_message(msg, get_shared_secret_by_client(msg[1:2].decode('utf-8'),
                                                                   self.secret_encryption_key))  # még nincs beállítva a self.shared_secret
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
        self.currentDir = 'server_root/' + message.client + '_root'

    # érvényes Hanshake NEW üzenet elfogadása
    def accept_handshake(self):
        response = HandshakeMessage.HandshakeMessage(self.active_client, HandshakeMessageTypes.NEW_ACK,
                                                     get_current_timestamp(),
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
        fin_ack = HandshakeMessage.HandshakeMessage(self.active_client, HandshakeMessageTypes.FIN_ACK,
                                                    get_current_timestamp())
        self.networkInterface.send_msg(self.active_client, encrypt_message(fin_ack, self.shared_secret))

        # !!! Implement wait for FIN_ACK

        print('Session closed with client: ' + self.active_client)
        self.reset_state()

    def reject_handshake(self, message: HandshakeMessage):
        response = HandshakeMessage.HandshakeMessage(message.client, HandshakeMessageTypes.REJ, get_current_timestamp())
        self.networkInterface.send_msg(message.client, encrypt_message(response,
                                                                       get_shared_secret_by_client(message.client,
                                                                                                   self.secret_encryption_key)))  # még nincs beállítva a self.shared_secret
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
        self.currentDir = ''

    def print(self):
        print('Address: ' + self.own_address + '\n' + 'Network path: ' + self.network_path)

    def initSession(self, client):
        self.importSharedSecret()

    def importSharedSecret(self, client):
        pass
