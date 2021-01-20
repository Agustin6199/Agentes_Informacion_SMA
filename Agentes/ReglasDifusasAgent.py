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

class ReglasDifusasAgent(Agent):

	async def setup(self):
		print("ReglasDifusasAgent started")
		b = self.RecvBehav()
		template = Template()
		template.set_metadata("performative", "inform")
		self.add_behaviour(b, template)
		
		
	class RecvBehav(CyclicBehaviour):
	
		async def on_start(self):
			print('RecvBehav starting')
			self.local = False
			self.visitante = False
			self.equipo_local = {}
			self.equipo_visitante = {}

		async def run(self):
			print("RecvBehav running....")

			if self.local:
				if self.visitante:
					print("Equipo Local: {}\nEquipo Visitante: {}".format(str(self.equipo_local), str(self.equipo_visitante)))
					self.kill(exit_code=10)
				else:
					msg = await self.receive(timeout=10) # wait for a message for 10 seconds
					if msg:
						print("Message received with content: {}".format(msg.body))
						self.equipo_visitante = json.loads(msg.body.replace("'", "\""))
						self.visitante = True
			else:
				msg = await self.receive(timeout=10) # wait for a message for 10 seconds
				if msg:
					print("Message received with content: {}".format(msg.body))
					self.equipo_local = json.loads(msg.body.replace("'", "\"")) 
					self.local = True
					



				

			# stop agent from behaviour
			await asyncio.sleep(1)

		async def on_end(self):
			print('RecvBehav ending')
			self.agent.add_behaviour(self.agent.ReglasBehav(self.equipo_local, self.equipo_visitante))

	class ReglasBehav(OneShotBehaviour):


		def __init__(self, equipo_local={}, equipo_visitante={}):
			self.equipo_local = equipo_local
			self.equipo_visitante = equipo_visitante

		async def on_start(self):
			print('ReglasBehav starting')
			self.define_clasificacion_rangos()
			#self.define_etiquetas()
			#self.resultado()
			self.team = []



		async def run(self):
			print('ReglasBehav running')
		
			if self.team:
				self.kill(exit_code=10)

		async def on_end(self):
			print('ReglasBehav ending')

#############################################DEFINICION DE RANGOS#####################################
		def define_clasificacion_rangos(self):
			Rango_Equipos  = np.arange(1, 20, 1)


			ZonaAlta = fuzz.trapmf(Rango_Equipos, [1, 1, 4, 6])
			ZonaMediaAlta = fuzz.trapmf(Rango_Equipos, [4, 6, 6, 8])
			ZonaMedia = fuzz.trapmf(Rango_Equipos, [6, 8, 12, 14])
			ZonaMediaBaja = fuzz.trapmf(Rango_Equipos, [12, 14, 14, 16])
			ZonaDescenso = fuzz.trapmf(Rango_Equipos, [14, 16, 20, 20])

			#@title Clasificación {run: "auto"}
			value = 15 #@param { type: "slider", min: 1, max: 20, step: 1}

			print("Zona Descenso, ",fuzz.interp_membership(np.arange(1,20,1),ZonaDescenso,value))

			print("Zona Media Baja, ",fuzz.interp_membership(np.arange(1,20,1),ZonaMediaBaja,value))

			print("Zona Media, ",fuzz.interp_membership(np.arange(1,20,1),ZonaMedia,value))

			print("Zona Media Alta, ",fuzz.interp_membership(np.arange(1,20,1),ZonaMediaAlta,value))

			print("Zona Alta, ",fuzz.interp_membership(np.arange(1,20,1),ZonaAlta,value))

			"""## Rachas Ultimos Partidos"""

			RangoRacha  = np.arange(0, 3.5, 0.5)


			BuenaRacha = fuzz.trapmf(RangoRacha, [1, 2, 3, 3])
			MalaRacha = fuzz.trapmf(RangoRacha, [0,0, 1, 2])

			#@title Racha Ultimos 3 partidos {run: "auto"}
			value = 1.5 #@param { type: "slider", min: 0, max: 3, step: 0.5}

			print("Buena Racha, ",fuzz.interp_membership(np.arange(0, 3.5, 0.5),BuenaRacha,value))

			print("Mala Racha, ",fuzz.interp_membership(np.arange(0,3.5,0.5),MalaRacha,value))

			"""## Media de posesión del balón por partidos"""

			Rango_Media_Posesion  = np.arange(25, 75, 0.01)

			Alta = fuzz.trapmf(Rango_Media_Posesion, [53, 62.5, 75, 75])
			Media = fuzz.trapmf(Rango_Media_Posesion, [37.5, 47, 53, 62.5])
			Baja = fuzz.trapmf(Rango_Media_Posesion, [25, 25, 37.5, 47])

			#@title Media de posesión del balón por partidos {run: "auto"}
			value = 87.5 #@param { type: "slider", min: 0, max: 100, step: 0.5}

			#Tenemos varios ejemplos de fuzzificación. Valores enteros en el rango 1,20 que toman pertenencia o no a una etiqueta
			#Se especifica el rango, la etiqueta de la que se quiere calcular su pertenencia y el entero a fuzzificar

			print("Alta ",fuzz.interp_membership(Rango_Media_Posesion,Alta,value))

			print("Media ",fuzz.interp_membership(Rango_Media_Posesion,Media,value))

			print("Baja ",fuzz.interp_membership(Rango_Media_Posesion,Baja,value))

			"""## Media de tiros a puerta por partido"""

			Rango_Media_Tiros_A_Puerta  = np.arange(0, 25, 0.01)

			Baja = fuzz.trapmf(Rango_Media_Tiros_A_Puerta, [0, 0, 7, 11])
			Media = fuzz.trapmf(Rango_Media_Tiros_A_Puerta, [7, 11, 13, 17])
			Alta = fuzz.trapmf(Rango_Media_Tiros_A_Puerta, [13, 17, 25, 25])

			#@title Media de tiros a puerta por partido {run: "auto"}
			value = 4 #@param { type: "slider", min: 0, max: 25, step: 0.5}

			#Tenemos varios ejemplos de fuzzificación. Valores enteros en el rango 1,20 que toman pertenencia o no a una etiqueta
			#Se especifica el rango, la etiqueta de la que se quiere calcular su pertenencia y el entero a fuzzificar

			print("Alta ",fuzz.interp_membership(Rango_Media_Tiros_A_Puerta, Alta, value))

			print("Media ",fuzz.interp_membership(Rango_Media_Tiros_A_Puerta, Media, value))

			print("Baja ",fuzz.interp_membership(Rango_Media_Tiros_A_Puerta, Baja, value))

			"""## Media de goles por partido"""

			Rango_Media_Goles_Partido  = np.arange(0, 5, 0.01)

			Baja = fuzz.trapmf(Rango_Media_Goles_Partido, [0, 0, 1.5, 3.5])
			Alta = fuzz.trapmf(Rango_Media_Goles_Partido, [1.5, 3.5, 5, 5])

			#@title Media de goles por partido {run: "auto"}
			value = 4 #@param { type: "slider", min: 0, max: 5, step: 0.5}

			#Tenemos varios ejemplos de fuzzificación. Valores enteros en el rango 1,20 que toman pertenencia o no a una etiqueta
			#Se especifica el rango, la etiqueta de la que se quiere calcular su pertenencia y el entero a fuzzificar

			print("Alta ",fuzz.interp_membership(Rango_Media_Goles_Partido, Alta, value))

			print("Baja ",fuzz.interp_membership(Rango_Media_Goles_Partido, Baja, value))

			"""## Número de habitantes

			"""

			Rango_Num_Habitantes  = np.arange(0, 4000000, 1)

			Muy_Bajo = fuzz.trapmf(Rango_Num_Habitantes, [0, 0, 0, 500000])
			Bajo = fuzz.trapmf(Rango_Num_Habitantes, [0, 500000, 500000, 1000000])
			Medio = fuzz.trapmf(Rango_Num_Habitantes, [500000, 1000000, 1000000, 1500000])
			Alto = fuzz.trapmf(Rango_Num_Habitantes, [1000000, 1500000, 1500000, 2000000])
			Muy_Alto = fuzz.trapmf(Rango_Num_Habitantes, [1500000, 2000000, 4000000, 4000000])

			#@title Media de goles por partido {run: "auto"}
			value = 1219936 #@param { type: "slider", min: 0, max: 4000000, step: 1}

			#Tenemos varios ejemplos de fuzzificación. Valores enteros en el rango 1,20 que toman pertenencia o no a una etiqueta
			#Se especifica el rango, la etiqueta de la que se quiere calcular su pertenencia y el entero a fuzzificar

			print("Muy baja, ",fuzz.interp_membership(Rango_Num_Habitantes,Muy_Bajo,value))

			print("Baja, ",fuzz.interp_membership(Rango_Num_Habitantes,Bajo,value))

			print("Media, ",fuzz.interp_membership(Rango_Num_Habitantes,Medio,value))

			print("Alta, ",fuzz.interp_membership(Rango_Num_Habitantes,Alto,value))

			print("Muy alta, ",fuzz.interp_membership(Rango_Num_Habitantes,Muy_Alto,value))


#######################################DEFINICION DE ETIQUETAS#####################################################
		#def define_etiquetas(self):
			Clasificacion_Local = ctrl.Antecedent(np.arange(1, 20, 1), 'Clasificación Local')
			Clasificacion_Visitante = ctrl.Antecedent(np.arange(1, 20, 1), 'Clasificación Visitante')

			Media_Posesion_Local = ctrl.Antecedent(Rango_Media_Posesion, 'Media de posesión del balón del local')
			Media_Posesion_Visitante = ctrl.Antecedent(Rango_Media_Posesion, 'Media de posesión del balón del visitante')

			Media_Tiros_Puerta_Local = ctrl.Antecedent(Rango_Media_Tiros_A_Puerta, 'Media de tiros a puerta del local')
			Media_Tiros_Puerta_Visitante = ctrl.Antecedent(Rango_Media_Tiros_A_Puerta, 'Media de tiros a puerta del visitante')

			Media_Goles_Partido_Local = ctrl.Antecedent(Rango_Media_Goles_Partido, 'Media de goles por partido del local')
			Media_Goles_Partido_Visitante = ctrl.Antecedent(Rango_Media_Goles_Partido, 'Media de goles por partido del visitante')

			Numero_Habitantes_Local = ctrl.Antecedent(Rango_Num_Habitantes, 'Número de habitantes de la ciudad del local')
			Numero_Habitantes_Visitante = ctrl.Antecedent(Rango_Num_Habitantes, 'Número de habitantes de la ciudad del visitante')

			Racha_Local = ctrl.Antecedent(np.arange(1, 3, 0.5), 'Racha Local')
			Racha_Visitante = ctrl.Antecedent(np.arange(1, 3, 0.5), 'Racha Visitante')

			Result= ctrl.Consequent(np.arange(1,9,1), 'Result')

			Clasificacion_labels = ['Zona Alta', 'Zona Media Alta', 'Zona Media', 'Zona Media Baja', 'Zona Descenso']
			racha_labels = ['Buena Racha', 'Racha Normal', 'Mala Racha']
			posesion_labels = ['Alta', 'Media', 'Baja']
			tiros_puerta_labels = ['Alta', 'Media', 'Baja']
			goles_partido_labels = ['Alta', 'Baja']
			num_habitantes_labels = ['Muy alta', 'Alta', 'Media', 'Baja', 'Muy baja']

			Racha_Local.automf(names=racha_labels)
			Racha_Visitante.automf(names=racha_labels)

			posesion_labels = ['Alta', 'Media', 'Baja']
			tiros_puerta_labels = ['Alta', 'Media', 'Baja']
			goles_partido_labels = ['Alta', 'Baja']
			num_habitantes_labels = ['Muy alta', 'Alta', 'Media', 'Baja', 'Muy baja']

			Media_Posesion_Local.automf(names=posesion_labels)
			Media_Posesion_Visitante.automf(names=posesion_labels)

			Media_Tiros_Puerta_Local.automf(names=tiros_puerta_labels)
			Media_Tiros_Puerta_Visitante.automf(names=tiros_puerta_labels)

			Media_Goles_Partido_Local.automf(names=goles_partido_labels)
			Media_Goles_Partido_Visitante.automf(names=goles_partido_labels)

			Numero_Habitantes_Local.automf(names=num_habitantes_labels)
			Numero_Habitantes_Visitante.automf(names=num_habitantes_labels)

			Clasificacion_Local.automf(names=Clasificacion_labels)
			Clasificacion_Visitante.automf(names=Clasificacion_labels)

			result_labels= ['1','X','2'] 

			Result.automf(names=result_labels)



###################################################REGLAS DIFUSAS#######################################
		#def define_reglas_difusas(self):
			rule1 = ctrl.Rule(Media_Posesion_Local['Alta'] | Media_Posesion_Visitante['Baja'], Result['1'])
			rule2 = ctrl.Rule((Media_Posesion_Local['Media'] & Media_Posesion_Visitante['Media']) & Media_Tiros_Puerta_Visitante['Alta'], Result['2'])
			rule3 = ctrl.Rule(Media_Goles_Partido_Local['Baja'] | Media_Goles_Partido_Visitante['Baja'], Result['X'])
			rule4 = ctrl.Rule((Numero_Habitantes_Local['Muy baja'] | Numero_Habitantes_Local['Baja']) & (Numero_Habitantes_Visitante['Muy alta'] | Numero_Habitantes_Visitante['Alta']), Result['2'])
			rule5 = ctrl.Rule(Media_Goles_Partido_Local['Alta'] & Media_Goles_Partido_Visitante['Baja'], Result['1'])
			rule6 = ctrl.Rule((Media_Tiros_Puerta_Local['Alta'] & Media_Tiros_Puerta_Local['Alta']) | (Media_Tiros_Puerta_Local['Baja'] & Media_Tiros_Puerta_Local['Baja']), Result['X'])

			rule7 = ctrl.Rule(((Clasificacion_Visitante['Zona Media Baja'] & Clasificacion_Local['Zona Media Baja']) |
			                  (Clasificacion_Visitante['Zona Media Alta'] & Clasificacion_Local['Zona Media Alta']) |
			                  (Clasificacion_Visitante['Zona Media'] & Clasificacion_Local['Zona Media']) |
			                  (Clasificacion_Visitante['Zona Descenso'] & Clasificacion_Local['Zona Descenso']) |
			                  (Clasificacion_Visitante['Zona Alta'] & Clasificacion_Local['Zona Alta'])) &
			                  (Racha_Local['Buena Racha'] & Racha_Visitante['Mala Racha']),
			                  Result['1'])

			rule8 = ctrl.Rule(((Clasificacion_Visitante['Zona Media Baja'] & Clasificacion_Local['Zona Media Baja']) |
			                  (Clasificacion_Visitante['Zona Media Alta'] & Clasificacion_Local['Zona Media Alta']) |
			                  (Clasificacion_Visitante['Zona Media'] & Clasificacion_Local['Zona Media']) |
			                  (Clasificacion_Visitante['Zona Descenso'] & Clasificacion_Local['Zona Descenso']) |
			                  (Clasificacion_Visitante['Zona Alta'] & Clasificacion_Local['Zona Alta'])) &
			                  (Racha_Visitante['Buena Racha'] & Racha_Local['Mala Racha']),
			                  Result['2'])

			rule9 = ctrl.Rule(((Clasificacion_Visitante['Zona Media Baja'] & Clasificacion_Local['Zona Media Baja']) |
			                  (Clasificacion_Visitante['Zona Media'] & Clasificacion_Local['Zona Media']) |
			                  (Clasificacion_Visitante['Zona Descenso'] & Clasificacion_Local['Zona Descenso'])) &
			                  ((Racha_Visitante['Buena Racha'] & Racha_Local['Buena Racha'])|
			                   (Racha_Visitante['Mala Racha'] & Racha_Local['Mala Racha'])|
			                   (Racha_Visitante['Racha Normal'] & Racha_Local['Racha Normal'])),
			                  Result['X'])

			rule10 = ctrl.Rule(((Clasificacion_Visitante['Zona Media Alta'] & Clasificacion_Local['Zona Media Alta']) |
			                  (Clasificacion_Visitante['Zona Alta'] & Clasificacion_Local['Zona Alta'])) &
			                  ((Racha_Visitante['Mala Racha'] & Racha_Local['Mala Racha'])|
			                   (Racha_Visitante['Racha Normal'] & Racha_Local['Racha Normal'])), 
			                  Result['X'])

			rule11 = ctrl.Rule(((Clasificacion_Visitante['Zona Media Alta'] & Clasificacion_Local['Zona Media Alta']) |
			                  (Clasificacion_Visitante['Zona Alta'] & Clasificacion_Local['Zona Alta'])) &
			                  (Racha_Visitante['Buena Racha'] & Racha_Local['Buena Racha']), 
			                  Result['1'])

			rule12 = ctrl.Rule((Clasificacion_Visitante['Zona Media Baja'] | Clasificacion_Visitante['Zona Descenso']) &
			                  (Clasificacion_Local['Zona Media Alta'] | Clasificacion_Local['Zona Alta'] | Clasificacion_Local['Zona Media']),
			                  Result['1'])

			rule13 = ctrl.Rule((Clasificacion_Local['Zona Media Baja'] | Clasificacion_Local['Zona Descenso']) &
			                  (Clasificacion_Visitante['Zona Media Alta'] | Clasificacion_Visitante['Zona Alta'] | Clasificacion_Visitante['Zona Media']),
			                  Result['2'])

			rule14 = ctrl.Rule(Clasificacion_Local['Zona Media'] | Clasificacion_Visitante['Zona Media'], Result['X'])
			quiniela_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8 , rule9, rule10, rule11, rule12, rule13, rule14])
			self.quiniela = ctrl.ControlSystemSimulation(quiniela_ctrl)

###################################################RESULTADO#######################################

		#def resultado(self):
			self.quiniela.input['Clasificación Local'] = self.equipo_local.get('Ranking')
			self.quiniela.input['Clasificación Visitante'] = self.equipo_visitante.get('Ranking')

			#quiniela.input['Racha Local'] = 0.5
			#quiniela.input['Racha Visitante'] = 1

			self.quiniela.input['Racha Local'] = self.equipo_local.get('Racha de Partidos Ganados') + 0.5 * self.equipo_local.get('Racha de Partidos Empatados')
			self.quiniela.input['Racha Visitante'] = self.equipo_visitante.get('Racha de Partidos Ganados') + 0.5 * self.equipo_visitante.get('Racha de Partidos Empatados')

			#quiniela.input['Media de posesión del balón del local'] = 56.2
			#quiniela.input['Media de posesión del balón del visitante'] = 54.83

			self.quiniela.input['Media de posesión del balón del local'] = self.equipo_local.get('Posesion')
			self.quiniela.input['Media de posesión del balón del visitante'] = self.equipo_visitante.get('Posesion')

			#quiniela.input['Media de tiros a puerta del local'] = 3.6
			#quiniela.input['Media de tiros a puerta del visitante'] = 2.8

			self.quiniela.input['Media de tiros a puerta del local'] = self.equipo_local.get('Tiros a puerta')
			self.quiniela.input['Media de tiros a puerta del visitante'] = self.equipo_visitante.get('Tiros a puerta')

			#quiniela.input['Media de goles por partido del local'] = 2.25
			#quiniela.input['Media de goles por partido del visitante'] = 1.25

			self.quiniela.input['Media de goles por partido del local'] = self.equipo_local.get('Goles')
			self.quiniela.input['Media de goles por partido del visitante'] = self.equipo_visitante.get('Goles')

			#quiniela.input['Número de habitantes de la ciudad del local'] = 3266126
			#quiniela.input['Número de habitantes de la ciudad del visitante'] = 171728

			self.quiniela.input['Número de habitantes de la ciudad del local'] = self.equipo_local.get('Poblacion')
			self.quiniela.input['Número de habitantes de la ciudad del visitante'] = self.equipo_visitante.get('Poblacion')

			# Crunch the numbers
			self.quiniela.compute()

			print(self.quiniela.output['Result'])
			#Result.view(sim=self.quiniela)
			val = self.quiniela.output['Result']
			range = np.arange(1, 9, 1)
			variable = Result['1']
			
			pertenencia1 = fuzz.interp_membership(range, variable.mf, val)
			print('1:', pertenencia1)




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
