from netsim.netinterface import network_interface
from messages.HandshakeMessage import HandshakeMessage

class Client:

	def __init__(self, network_path, own_address):
		self.network_path = network_path
		self.own_address = own_address
		self.networkIF = network_interface(network_path, own_address)

		self.session_key = ''
		self.sequence_number = -1

	def main_loop(self):
		print('Client main loop started...')
		while True:
			data = input('Type a message: ')
			dst = input('Type a destination address: ')

			message = HandshakeMessage(self.own_address, 'NEW', 123456789, data)
			message_bytes = message.to_bytes()

			self.networkIF.send_msg(dst, message_bytes)

			status, rsp = self.networkIF.receive_msg(blocking=True)
			response = rsp.decode('utf-8')
			print('response: ' + response)

			if input('Continue? (y/n): ') == 'n': break

		print('Client main loop ended...')

	def print(self):
		print('Address: ' + self.own_address + '\n' + 'Network path: ' +  self.network_path)
