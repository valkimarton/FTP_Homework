class HandshakeMessageTypes:
    NEW = 'NEW'
    NEW_ACK = 'NAC'
    REJ = 'REJ'
    FIN = 'FIN'
    FIN_ACK = 'FAC'


class CommandMessageTypes:
    MKD = 'MKD'


class FileTransferMessageTypes:
    NEW_UPL = 'UNW'
    NEW_DNL = 'DNW'
    UPL_NEW_ACK = 'UNA'
    DNL_NEW_ACK = 'DNA'
    SEND = 'SND'
    DAT = 'DAT'
    FIN = 'FIN'
    ACK_FIN = 'FNA'
