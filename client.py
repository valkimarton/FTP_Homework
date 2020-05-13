from netsim.netinterface import network_interface

class Client:
	def __init__(self, network_path, own_address):
		self.network_path = network_path
		self.own_address = own_address
		self.networkIF = network_interface(network_path, own_address)

	def mainLoop(self):
		print('Client main loop started...')
		while True:
			msg = input('Type a message: ')
			dst = input('Type a destination address: ')

			self.networkIF.send_msg(dst, msg.encode('utf-8'))

			status, rsp = self.networkIF.receive_msg(blocking=True)
			response = rsp.decode('utf-8')
			print('response: ' + response)

			if input('Continue? (y/n): ') == 'n': break

		print('Client main loop ended...')

	def print(self):
		print('Address: ' + self.own_address + '\n' + 'Network path: ' +  self.network_path)
