from netsim.netinterface import *

HANDSHAKE_MESSAGE_ID = 'H'
COMMAND_MESSAGE_ID = 'C'
FILE_TRANSFER_MESSAGE_ID = 'F'          # H: handshake, C: commad, F: file transfer     állítsátok át ha gondoljátok.

ID_SPACE = [HANDSHAKE_MESSAGE_ID, COMMAND_MESSAGE_ID, FILE_TRANSFER_MESSAGE_ID]

CLIENT_SPACE = network_interface.addr_space

TYPE_SPACE = {
    'H': ['NEW', 'NAC', 'REJ', 'FIN', 'FAC'],   # A HandshakeMessage lehetséges TYPE mezői
    'C': [],
    'F': []
}
