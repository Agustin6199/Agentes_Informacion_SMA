import time
import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template

class ReglasDifusasAgent(Agent):
	class RecvBehav(CyclicBehaviour):
	
		async def on_start(self):
			print('onstart')
		async def run(self):
			print("RecvBehav running")

			msg = await self.receive(timeout=10) # wait for a message for 10 seconds
			if msg:
				print("Message received with content: {}".format(msg.body))
				self.kill(exit_code=10)
			else:
				print("Did not received any message after 10 seconds")
				

			# stop agent from behaviour
			await asyncio.sleep(1)

		async def on_end(self):
			print('on_end')

	async def setup(self):
		print("ReceiverAgent started")
		b = self.RecvBehav()
		template = Template()
		template.set_metadata("performative", "inform")
		self.add_behaviour(b, template)



if __name__ == "__main__":
	receiveragent = ReglasDifusasAgent("reglas_difusas_agente_sma@xmpp.jp", "sma_mola_mazo")
	future = receiveragent.start()
	future.result() # wait for receiver agent to be prepared.

	while True:
		try:
			time.sleep(1)
		except KeyboardInterrupt:
			receiveragent.stop()
			break
	print("Agents finished")
