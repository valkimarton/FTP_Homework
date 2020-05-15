import time
import Crypto.Random

def get_random_session_key():
    return Crypto.Random.get_random_bytes(16)


def get_current_timestamp():
    return int(time.time())
