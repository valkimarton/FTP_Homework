from netsim.netinterface import *

# Üzenet ID-k
HANDSHAKE_MESSAGE_ID = 'H'
COMMAND_MESSAGE_ID = 'C'
FILE_TRANSFER_MESSAGE_ID = 'F'  # H: handshake, C: command, F: file transfer     állítsátok át ha gondoljátok.

# Lehetséges üzenet ID-k
ID_SPACE = [HANDSHAKE_MESSAGE_ID, COMMAND_MESSAGE_ID, FILE_TRANSFER_MESSAGE_ID]

# Lehetséges kliens azonosítók
CLIENT_SPACE = network_interface.addr_space

# Milyen ID-khoz milyen típúsok tartoznak (Validációhoz)
TYPE_SPACE = {
    'H': ['NEW', 'NAC', 'REJ', 'FIN', 'FAC'],  # A HandshakeMessage lehetséges TYPE mezői
    'C': ['MKD', 'RMD', 'GWD', 'CWD', 'LST', 'RMF'], # A CommandMessage lehetseges TYPE mezoi
    'F': ['UNW', 'DNW', 'UNA', 'DNA', 'SND', 'DAT', 'FIN', 'FNA']  # Fájlátvitel (FileTransferMessage) lehetséges TYPE mezői
}
