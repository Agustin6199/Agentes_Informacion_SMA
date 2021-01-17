import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template

class RecolectorAgent(Agent):
	class InformBehav(OneShotBehaviour):
	
		async def run(self):
			print("InformBehav running")
			msg = Message(to="reglas_difusas_agente_sma@xmpp.jp")     # Instantiate the message
			msg.set_metadata("performative", "inform")  # Set the "inform" FIPA performative
			msg.set_metadata("ontology", "myOntology")  # Set the ontology of the message content
			msg.set_metadata("language", "OWL-S")       # Set the language of the message content
			msg.body = "Hello World"			        # Set the message content

			await self.send(msg)
			print("Message sent!", msg)

			# stop agent from behaviour
			await self.agent.stop()

	async def setup(self):
		print("SenderAgent started")
		b = self.InformBehav()
		self.add_behaviour(b)


if __name__ == "__main__":
	senderagent = RecolectorAgent("recolector_agente_sma@xmpp.jp", "sma_mola_mazo")
	senderagent.start()

	while True:
		try:
			time.sleep(1)
		except KeyboardInterrupt:
			senderagent.stop()
			break
	print("Agents finished")
