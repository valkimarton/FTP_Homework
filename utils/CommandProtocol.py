from messages.CommandMessage import *
from utils.GeneralUtils import *

class CommandProtocol:

    def makeMessage(fullCommand: str, own_addr: str, seq_num: int) -> CommandMessage:
        commmand = command[0:3]
        payload = command[4:]
        if self.payload_is_valid(payload) == true:
            sequence_num = seq_num + 1
            message = CommandMessage(own_addr, commmand, get_current_timestamp(), payload, sequence_num)
            return message
        else: 
            return None

    def payload_is_valid(payload: str) -> bool:
        if payload.split() > 1:
            return false
        else:
            return true

