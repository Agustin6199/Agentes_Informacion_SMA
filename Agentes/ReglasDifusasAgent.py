import time
import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template
import numpy as np
import random, json
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt
from threading import Thread
import sys

class ReglasDifusasAgent(Agent):

	# Setup del agente ReglasDifusasAgent
	async def setup(self):
		print("Instanciado agente ReglasDifusasAgent")
		# Instanciamos el comportamiento RecvBehav
		b = self.RecvBehav()

		# Declaramos la plantilla que utilizaremos para filtrar los mensajes que recibiremos en el comportamiento RecvBehav
		template = Template()
		template.set_metadata("performative", "inform")

		# Añadimos el comportamiento junto con la plantilla definida
		self.add_behaviour(b, template)
		
	
	# Comportamiento encargado de recibir la información recopilada en los RecolectorAgent
	class RecvBehav(CyclicBehaviour):
	
		async def on_start(self):
			print('[RecvBehav] Iniciando comportamiento encargado de recibir la información recopilada en los RecolectorAgent...')
			self.local = False
			self.visitante = False
			self.equipo_local = {}
			self.equipo_visitante = {}

		async def run(self):
			print("[RecvBehav] Esperando mensajes...")

			if self.local:
				if self.visitante:
					print("\n[RecvBehav] Información del Equipo Local recibida: \n{}".format(str(self.equipo_local)))
					print("\n[RecvBehav] Información del Equipo Visitante recibida: \n{}\n".format(str(self.equipo_visitante)))
					self.kill(exit_code=10)
				else:
					msg = await self.receive(timeout=10) # wait for a message for 10 seconds
					if msg:
						print("[RecvBehav] Mensaje recibido con el siguiente contenido: {}".format(msg.body))
						self.equipo_visitante = json.loads(msg.body.replace("'", "\""))
						self.visitante = True
			else:
				msg = await self.receive(timeout=10) # wait for a message for 10 seconds
				if msg:
					print("[RecvBehav] Mensaje recibido con el siguiente contenido: {}".format(msg.body))
					self.equipo_local = json.loads(msg.body.replace("'", "\"")) 
					self.local = True

			await asyncio.sleep(1)

		async def on_end(self):
			print('[RecvBehav] Finalizando comportamiento encargado de recibir la información recopilada en los RecolectorAgent...')
			self.agent.add_behaviour(self.agent.ReglasBehav(self.equipo_local, self.equipo_visitante))


	# Comportamiento encargado de aplicar las Reglas Difusas y calcular los grados de pertenencia a cada etiqueta
	class ReglasBehav(OneShotBehaviour):

		def __init__(self, equipo_local={}, equipo_visitante={}):
			self.equipo_local = equipo_local
			self.equipo_visitante = equipo_visitante

		async def on_start(self):
			print('[ReglasBehav] Iniciando comportamiento encargado de aplicar las reglas difusas y generar el signo de la quiniela...')

		async def run(self):
			print('[ReglasBehav] Comportamiento encargado de aplicar las reglas difusas y generar el signo de la quiniela en proceso...')
			self.define_clasificacion_rangos()
			self.define_etiquetas()
			self.define_reglas_difusas()
			self.resultado()
			#self.team = []

			if self.team:
				self.kill(exit_code=10)

		async def on_end(self):
			print('[ReglasBehav] Finalizando comportamiento encargado de aplicar las reglas difusas y generar el signo de la quiniela...')


		##############################################################################################################
		##########################################DEFINICIÓN DE RANGOS################################################
		def define_clasificacion_rangos(self):
			Rango_Equipos  = np.arange(1, 20, 1)


			ZonaAlta = fuzz.trapmf(Rango_Equipos, [1, 1, 4, 6])
			ZonaMediaAlta = fuzz.trapmf(Rango_Equipos, [4, 6, 6, 8])
			ZonaMedia = fuzz.trapmf(Rango_Equipos, [6, 8, 12, 14])
			ZonaMediaBaja = fuzz.trapmf(Rango_Equipos, [12, 14, 14, 16])
			ZonaDescenso = fuzz.trapmf(Rango_Equipos, [14, 16, 20, 20])


			"""## Rachas Ultimos Partidos"""

			RangoRacha  = np.arange(0, 3.5, 0.5)


			BuenaRacha = fuzz.trapmf(RangoRacha, [1, 2, 3, 3])
			MalaRacha = fuzz.trapmf(RangoRacha, [0,0, 1, 2])


			"""## Media de posesión del balón por partidos"""

			self.Rango_Media_Posesion  = np.arange(25, 75, 0.01)

			Alta = fuzz.trapmf(self.Rango_Media_Posesion, [53, 62.5, 75, 75])
			Media = fuzz.trapmf(self.Rango_Media_Posesion, [37.5, 47, 53, 62.5])
			Baja = fuzz.trapmf(self.Rango_Media_Posesion, [25, 25, 37.5, 47])


			"""## Media de tiros a puerta por partido"""

			self.Rango_Media_Tiros_A_Puerta  = np.arange(0, 25, 0.01)

			Baja = fuzz.trapmf(self.Rango_Media_Tiros_A_Puerta, [0, 0, 7, 11])
			Media = fuzz.trapmf(self.Rango_Media_Tiros_A_Puerta, [7, 11, 13, 17])
			Alta = fuzz.trapmf(self.Rango_Media_Tiros_A_Puerta, [13, 17, 25, 25])


			"""## Media de goles por partido"""

			self.Rango_Media_Goles_Partido  = np.arange(0, 5, 0.01)

			Baja = fuzz.trapmf(self.Rango_Media_Goles_Partido, [0, 0, 1.5, 3.5])
			Alta = fuzz.trapmf(self.Rango_Media_Goles_Partido, [1.5, 3.5, 5, 5])


		
			"""## Número de habitantes			"""

			self.Rango_Num_Habitantes  = np.arange(0, 4000000, 1)

			Muy_Bajo = fuzz.trapmf(self.Rango_Num_Habitantes, [0, 0, 0, 500000])
			Bajo = fuzz.trapmf(self.Rango_Num_Habitantes, [0, 500000, 500000, 1000000])
			Medio = fuzz.trapmf(self.Rango_Num_Habitantes, [500000, 1000000, 1000000, 1500000])
			Alto = fuzz.trapmf(self.Rango_Num_Habitantes, [1000000, 1500000, 1500000, 2000000])
			Muy_Alto = fuzz.trapmf(self.Rango_Num_Habitantes, [1500000, 2000000, 4000000, 4000000])



		##############################################################################################################
		#######################################DEFINICIÓN DE ETIQUIETAS###############################################
		def define_etiquetas(self):
			self.Clasificacion_Local = ctrl.Antecedent(np.arange(1, 20, 1), 'Clasificación Local')
			self.Clasificacion_Visitante = ctrl.Antecedent(np.arange(1, 20, 1), 'Clasificación Visitante')

			self.Media_Posesion_Local = ctrl.Antecedent(self.Rango_Media_Posesion, 'Media de posesión del balón del local')
			self.Media_Posesion_Visitante = ctrl.Antecedent(self.Rango_Media_Posesion, 'Media de posesión del balón del visitante')

			self.Media_Tiros_Puerta_Local = ctrl.Antecedent(self.Rango_Media_Tiros_A_Puerta, 'Media de tiros a puerta del local')
			self.Media_Tiros_Puerta_Visitante = ctrl.Antecedent(self.Rango_Media_Tiros_A_Puerta, 'Media de tiros a puerta del visitante')

			self.Media_Goles_Partido_Local = ctrl.Antecedent(self.Rango_Media_Goles_Partido, 'Media de goles por partido del local')
			self.Media_Goles_Partido_Visitante = ctrl.Antecedent(self.Rango_Media_Goles_Partido, 'Media de goles por partido del visitante')

			self.Numero_Habitantes_Local = ctrl.Antecedent(self.Rango_Num_Habitantes, 'Número de habitantes de la ciudad del local')
			self.Numero_Habitantes_Visitante = ctrl.Antecedent(self.Rango_Num_Habitantes, 'Número de habitantes de la ciudad del visitante')

			self.Racha_Local = ctrl.Antecedent(np.arange(1, 3, 0.5), 'Racha Local')
			self.Racha_Visitante = ctrl.Antecedent(np.arange(1, 3, 0.5), 'Racha Visitante')

			self.Result= ctrl.Consequent(np.arange(1,9,1), 'Result')

			Clasificacion_labels = ['Zona Alta', 'Zona Media Alta', 'Zona Media', 'Zona Media Baja', 'Zona Descenso']
			racha_labels = ['Buena Racha', 'Racha Normal', 'Mala Racha']
			posesion_labels = ['Alta', 'Media', 'Baja']
			tiros_puerta_labels = ['Alta', 'Media', 'Baja']
			goles_partido_labels = ['Alta', 'Baja']
			num_habitantes_labels = ['Muy alta', 'Alta', 'Media', 'Baja', 'Muy baja']

			self.Racha_Local.automf(names=racha_labels)
			self.Racha_Visitante.automf(names=racha_labels)

			posesion_labels = ['Alta', 'Media', 'Baja']
			tiros_puerta_labels = ['Alta', 'Media', 'Baja']
			goles_partido_labels = ['Alta', 'Baja']
			num_habitantes_labels = ['Muy alta', 'Alta', 'Media', 'Baja', 'Muy baja']

			self.Media_Posesion_Local.automf(names=posesion_labels)
			self.Media_Posesion_Visitante.automf(names=posesion_labels)

			self.Media_Tiros_Puerta_Local.automf(names=tiros_puerta_labels)
			self.Media_Tiros_Puerta_Visitante.automf(names=tiros_puerta_labels)

			self.Media_Goles_Partido_Local.automf(names=goles_partido_labels)
			self.Media_Goles_Partido_Visitante.automf(names=goles_partido_labels)

			self.Numero_Habitantes_Local.automf(names=num_habitantes_labels)
			self.Numero_Habitantes_Visitante.automf(names=num_habitantes_labels)

			self.Clasificacion_Local.automf(names=Clasificacion_labels)
			self.Clasificacion_Visitante.automf(names=Clasificacion_labels)

			result_labels= ['1','X','2'] 

			self.Result.automf(names=result_labels)


		##############################################################################################################
		####################################DEFINICIÓN DE LAS REGLAS DIFUSAS##########################################
		def define_reglas_difusas(self):
			rule1 = ctrl.Rule(self.Media_Posesion_Local['Alta'] | self.Media_Posesion_Visitante['Baja'], self.Result['1'])
			rule2 = ctrl.Rule((self.Media_Posesion_Local['Media'] & self.Media_Posesion_Visitante['Media']) & self.Media_Tiros_Puerta_Visitante['Alta'], self.Result['2'])
			rule3 = ctrl.Rule(self.Media_Goles_Partido_Local['Baja'] | self.Media_Goles_Partido_Visitante['Baja'], self.Result['X'])
			rule4 = ctrl.Rule((self.Numero_Habitantes_Local['Muy baja'] | self.Numero_Habitantes_Local['Baja']) & (self.Numero_Habitantes_Visitante['Muy alta'] | self.Numero_Habitantes_Visitante['Alta']), self.Result['2'])
			rule5 = ctrl.Rule(self.Media_Goles_Partido_Local['Alta'] & self.Media_Goles_Partido_Visitante['Baja'], self.Result['1'])
			rule6 = ctrl.Rule((self.Media_Tiros_Puerta_Local['Alta'] & self.Media_Tiros_Puerta_Local['Alta']) | (self.Media_Tiros_Puerta_Local['Baja'] & self.Media_Tiros_Puerta_Local['Baja']), self.Result['X'])

			rule7 = ctrl.Rule(((self.Clasificacion_Visitante['Zona Media Baja'] & self.Clasificacion_Local['Zona Media Baja']) |
			                  (self.Clasificacion_Visitante['Zona Media Alta'] & self.Clasificacion_Local['Zona Media Alta']) |
			                  (self.Clasificacion_Visitante['Zona Media'] & self.Clasificacion_Local['Zona Media']) |
			                  (self.Clasificacion_Visitante['Zona Descenso'] & self.Clasificacion_Local['Zona Descenso']) |
			                  (self.Clasificacion_Visitante['Zona Alta'] & self.Clasificacion_Local['Zona Alta'])) &
			                  (self.Racha_Local['Buena Racha'] & self.Racha_Visitante['Mala Racha']),
			                  self.Result['1'])

			rule8 = ctrl.Rule(((self.Clasificacion_Visitante['Zona Media Baja'] & self.Clasificacion_Local['Zona Media Baja']) |
			                  (self.Clasificacion_Visitante['Zona Media Alta'] & self.Clasificacion_Local['Zona Media Alta']) |
			                  (self.Clasificacion_Visitante['Zona Media'] & self.Clasificacion_Local['Zona Media']) |
			                  (self.Clasificacion_Visitante['Zona Descenso'] & self.Clasificacion_Local['Zona Descenso']) |
			                  (self.Clasificacion_Visitante['Zona Alta'] & self.Clasificacion_Local['Zona Alta'])) &
			                  (self.Racha_Visitante['Buena Racha'] & self.Racha_Local['Mala Racha']),
			                  self.Result['2'])

			rule9 = ctrl.Rule(((self.Clasificacion_Visitante['Zona Media Baja'] & self.Clasificacion_Local['Zona Media Baja']) |
			                  (self.Clasificacion_Visitante['Zona Media'] & self.Clasificacion_Local['Zona Media']) |
			                  (self.Clasificacion_Visitante['Zona Descenso'] & self.Clasificacion_Local['Zona Descenso'])) &
			                  ((self.Racha_Visitante['Buena Racha'] & self.Racha_Local['Buena Racha'])|
			                   (self.Racha_Visitante['Mala Racha'] & self.Racha_Local['Mala Racha'])|
			                   (self.Racha_Visitante['Racha Normal'] & self.Racha_Local['Racha Normal'])),
			                  self.Result['X'])

			rule10 = ctrl.Rule(((self.Clasificacion_Visitante['Zona Media Alta'] & self.Clasificacion_Local['Zona Media Alta']) |
			                  (self.Clasificacion_Visitante['Zona Alta'] & self.Clasificacion_Local['Zona Alta'])) &
			                  ((self.Racha_Visitante['Mala Racha'] & self.Racha_Local['Mala Racha'])|
			                   (self.Racha_Visitante['Racha Normal'] & self.Racha_Local['Racha Normal'])), 
			                  self.Result['X'])

			rule11 = ctrl.Rule(((self.Clasificacion_Visitante['Zona Media Alta'] & self.Clasificacion_Local['Zona Media Alta']) |
			                  (self.Clasificacion_Visitante['Zona Alta'] & self.Clasificacion_Local['Zona Alta'])) &
			                  (self.Racha_Visitante['Buena Racha'] & self.Racha_Local['Buena Racha']), 
			                  self.Result['1'])

			rule12 = ctrl.Rule((self.Clasificacion_Visitante['Zona Media Baja'] | self.Clasificacion_Visitante['Zona Descenso']) &
			                  (self.Clasificacion_Local['Zona Media Alta'] | self.Clasificacion_Local['Zona Alta'] | self.Clasificacion_Local['Zona Media']),
			                  self.Result['1'])

			rule13 = ctrl.Rule((self.Clasificacion_Local['Zona Media Baja'] | self.Clasificacion_Local['Zona Descenso']) &
			                  (self.Clasificacion_Visitante['Zona Media Alta'] | self.Clasificacion_Visitante['Zona Alta'] | self.Clasificacion_Visitante['Zona Media']),
			                  self.Result['2'])

			rule14 = ctrl.Rule(self.Clasificacion_Local['Zona Media'] | self.Clasificacion_Visitante['Zona Media'], self.Result['X'])
			quiniela_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8 , rule9, rule10, rule11, rule12, rule13, rule14])
			self.quiniela = ctrl.ControlSystemSimulation(quiniela_ctrl)


		##############################################################################################################
		################################################RESULTADOS####################################################
		def resultado(self):
			self.quiniela.input['Clasificación Local'] = self.equipo_local.get('Ranking')
			self.quiniela.input['Clasificación Visitante'] = self.equipo_visitante.get('Ranking')


			self.quiniela.input['Racha Local'] = self.equipo_local.get('Racha de Partidos Ganados') + 0.5 * self.equipo_local.get('Racha de Partidos Empatados')
			self.quiniela.input['Racha Visitante'] = self.equipo_visitante.get('Racha de Partidos Ganados') + 0.5 * self.equipo_visitante.get('Racha de Partidos Empatados')


			self.quiniela.input['Media de posesión del balón del local'] = self.equipo_local.get('Posesion')
			self.quiniela.input['Media de posesión del balón del visitante'] = self.equipo_visitante.get('Posesion')


			self.quiniela.input['Media de tiros a puerta del local'] = self.equipo_local.get('Tiros a puerta')
			self.quiniela.input['Media de tiros a puerta del visitante'] = self.equipo_visitante.get('Tiros a puerta')


			self.quiniela.input['Media de goles por partido del local'] = self.equipo_local.get('Goles')
			self.quiniela.input['Media de goles por partido del visitante'] = self.equipo_visitante.get('Goles')


			self.quiniela.input['Número de habitantes de la ciudad del local'] = self.equipo_local.get('Poblacion')
			self.quiniela.input['Número de habitantes de la ciudad del visitante'] = self.equipo_visitante.get('Poblacion')

			# Crunch the numbers
			self.quiniela.compute()

			print(self.quiniela.output['Result'])
			#self.Result.view(sim=self.quiniela)

			val = self.quiniela.output['Result']
			range = np.arange(1, 9, 1)
			variable = self.Result['1']
			dict_result = {}
			dict_result['1'] = fuzz.interp_membership(range, variable.mf, val)
			
			variable = self.Result['X']
			dict_result['X'] = fuzz.interp_membership(range, variable.mf, val)

			variable = self.Result['2']
			dict_result['2'] = fuzz.interp_membership(range, variable.mf, val)
			print(dict_result)

			print('La etiqueta ligüistica ', max(dict_result.keys()), 'es la de mayor pertenencia')


if len(sys.argv) == 1:

	receiveragent = ReglasDifusasAgent("reglas_difusas_agente_sma@xmpp.jp", "sma_mola_mazo")
	future = receiveragent.start()
	future.result() # wait for receiver agent to be prepared.

	while True:
		try:
			time.sleep(1)
		except KeyboardInterrupt:
			receiveragent.stop()
			break
	print("Agente finalizado")

else:
	print("Error, argumentos incorrectos. La sintaxis correcta para lanzar el agente es la siguiente: python3 ReglasDifusasAgent.py")