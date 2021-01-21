import time
import requests
import re
import pandas_datareader.data as web						# Utiliza la versión 0.9.0rc0 de pandas_datareader (pip install pandas_datareader==0.9.0rc0)
import pandas as pd											# Utiliza la versión 0.24.2 de pandas (pip install pandas==0.24.2)
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
from bs4 import BeautifulSoup
import sys

class RecolectorAgent(Agent):

	# Setup del agente RecolectorAgent
	async def setup(self):
		self.dict_team = {}
		print("Instanciado agente RecolectorAgent")
		b = self.GetInfoBehav()
		self.add_behaviour(b)


	# Comportamiento que envía la información recopilada al ReglasDifusasAgent
	class InformBehav(OneShotBehaviour):

		async def on_start(self):
			print('[InformBehav] Iniciando comportamiento encargado de enviar la información recopilada al ReglasDifusasAgent...')
			#print(self.dict_team)
	
		async def run(self):
			print("[InformBehav] Comportamiento encargado de enviar la información recopilada al ReglasDifusasAgent en proceso...")
			print("[InformBehav] Enviando información recopilada...")
			msg = Message(to="reglas_difusas_agente_sma@xmpp.jp")     # Instantiate the message
			msg.set_metadata("performative", "inform")  # Set the "inform" FIPA performative
			msg.set_metadata("ontology", "myOntology")  # Set the ontology of the message content
			msg.set_metadata("language", "OWL-S")       # Set the language of the message content
			#msg.body = "{'Hello': 2}"			        # Set the message content
			msg.body = str(self.agent.dict_team)	

			await self.send(msg)
			print("[InformBehav] Enviado el siguiente mensaje: ")
			print(msg)

			#si hemos hecho las lecturas cesamos el comportamiento
			self.kill(exit_code=10)

		async def on_end(self):
			print('[InformBehav] Finalizando comportamiento encargado de enviar la información recopilada al ReglasDifusasAgent...')

			# Paramos el agente
			print('[InformBehav] Parando el agente RecolectorAgent....')
			await self.agent.stop()


	# Comportamiento encargado de recopilar toda la información
	class GetInfoBehav(OneShotBehaviour):

		async def on_start(self):
			print('[GetInfoBehav] Iniciando comportamiento encargado de recopilar toda la información...')
			self.team_name = sys.argv[-1]
			self.dict_team = {}


		async def run(self):
			print('[GetInfoBehav] Comportamiento comportamiento encargado de recopilar toda la información en proceso...')
			print('[GetInfoBehav] Recopilando información del ' + self.team_name + '...')
			team = []
			
			#Cogemos la informacion de la tabla de ranking,s ino se puede se devuelve una lista vacia
			for t in self.get_ranking_teams():
				if t[1] == self.team_name:
					team.append(t)
			if len(team) == 0:
				team.append([])
				
			#Cogemos las estadisticas del equipo, sino se puede se devuelve una lista vacia
			for t in self.get_statistics():
				if t[0] == self.team_name.upper():
					team.append(t)
			if len(team) == 1:
				team.append([])
				
			#Cogemos la informacion de las rachas del equipo, y en caso de algun error los partidos se dan por perdidos, sino se puede se devuelve una lista vacia
			for t in self.get_rachas_teams():
				if t[0] == self.team_name:
					team.append(t)
			if len(team) == 2:
				team.append([])
			
			#Cogemos la informacion de la poblacion,sino se puede se devuelve una lista vacia
			team.append([self.get_city_population_per_team().get(self.team_name)])

			if team[0]:
				self.dict_team.update({'Ranking' : team[0][0], 'Nombre': team[0][1], 'Ptos': team[0][2], 'Partidos Jugados': team[0][3], 'Partidos Ganados': team[0][4],
				 'Partidos Ganados de Local': team[0][5], 'Partidos Ganados de Visitante': team[0][6], 'Partidos Empatados': team[0][7], 
				 'Partidos Empatados': team[0][8], 'Goles a Favor': team[0][9], 'Goles en Contra': team[0][10]})
			if team[1]:
				self.dict_team.update({'Posesion': team[1][1], 'Tiros': team[1][2], 'Tiros a puerta': team[1][3], 'Goles': team[1][4]})
			if team[2]:
				self.dict_team.update({'Racha de Partidos Ganados': team[2][1], 'Racha de Partidos Empatados': team[2][2], 'Racha de Partidos Perdidos': team[2][3]})
			if team[3]:
				self.dict_team.update({'Poblacion': team[3][0]})


			self.agent.dict_team.update(self.dict_team)
			#Si hemos recopilado toda la información necesaria, finalizamos el comportamiento
			self.kill(exit_code=10)

		
		async def on_end(self):
			print('[GetInfoBehav] Finalizando comportamiento encargado de recopilar toda la información...')
			self.agent.add_behaviour(self.agent.InformBehav())

		##############################################################################################################
		#################################################RACHAS#######################################################
		def get_rachas_teams(self):
			print('[GetInfoBehav] Obteniendo información sobre la racha del equipo...')
			#Definimos la url a la quedeseamos solicitar conexion y realizamos el request correspondiente
			url = 'https://resultados.as.com/resultados/futbol/primera/clasificacion/'
			#url = 'https://resultados.as.com/resultados/futbol/segunda/clasificacion/'

			respuesta = requests.get(
				url,
				headers = {
					'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
				}
			)

			#Procesamos la respuesta dada por el servidor de la pagina con el contenido de está
			contenido_web = BeautifulSoup(respuesta.text, 'lxml')

			#Definimos la variable donde se van a guardar todos los equyipos con su posicion en la liga, puntos, partidos jugados, partidos ganados,
			#partidos empatados y partidos perdidos	
			#Recogemos unicamenete la tabla de clasificación de la liga
			tabla = contenido_web.find('table', attrs={'class':'tabla-datos table-hover'})

			#Nos centramos en el cuerpo de la tabla la cual contienen la información de valor de la tabla
			body = tabla.tbody.find_all('a', attrs={'itemprop':'url'})

			equipos = []

			for a in body: #Saltamos las primeras 25 posicion que corresponden con las cabeceras y recogemos por equipo
				equipos.append(self.get_racha("https://resultados.as.com"+a['href']))
			#Recogemos la información del equipo

			return equipos

		def get_racha(self, url):

			respuesta = requests.get(
				url,
				headers = {
					'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
				}
			)

			#Procesamos la respuesta dada por el servidor de la pagina con el contenido de está
			contenido_web = BeautifulSoup(respuesta.text, 'lxml')

			name = contenido_web.find('h1', attrs={'class':'tit-ppal s-block'}).find('a')['title']

			tables = contenido_web.find('div', attrs={'class':'cont-resultados cf liga-20'})

			tbody = tables.find('tbody')
			tbody = tbody.find_all('tr')

			partidos_ganados = 0
			partidos_empatados = 0
			match1 = tbody[1]
			if self.is_Winner(tbody[1], name):
				partidos_ganados = partidos_ganados + 1

			if self.is_Winner(tbody[3], name):
				partidos_ganados = partidos_ganados + 1

			if self.is_Winner(tbody[5], name):
				partidos_ganados = partidos_ganados + 1

			if self.is_tied(tbody[1], name):
				partidos_empatados = partidos_empatados + 1

			if self.is_tied(tbody[3], name):
				partidos_empatados = partidos_empatados + 1

			if self.is_tied(tbody[5], name):
				partidos_empatados = partidos_empatados + 1

			return([name, partidos_ganados, partidos_empatados, 3 - partidos_empatados - partidos_ganados])

			#print('Ultimos partidos ganados: ', partidos_ganados, '\nUltimos partidos empatados: ', partidos_ganados)
			#print('----------------------------------------------')

		def is_Winner(self, match, team):
			names = match.find_all('span', attrs={'nombre-equipo'})
			result = match.find('a', attrs={'resultado'})
			try:
				if((team == names[0].get_text()) and (result.get_text()[0] > result.get_text()[4])):
					return True
				elif((team == names[1].get_text()) and (result.get_text()[0] < result.get_text()[4])):
					return True
				else:
					return False
			except:
				return False

		def is_tied(self, match, team):
			names = match.find_all('span', attrs={'nombre-equipo'})
			result = match.find('a', attrs={'resultado'})

			try:
				if(result.get_text()[0] == result.get_text()[4]):
					return True
				else:	
					return False
			except:
				return False

		##############################################################################################################
		###########################################CIUDAD/POBLACION###################################################
		def get_city_population_per_team(self):
			
			print('[GetInfoBehav] Obteniendo información sobre el número de habitantes de la ciudad del equipo...')

			# Mediante la librería pandas_datareader, obtenemos los datos de la API de econdb
			df = web.DataReader('dataset=URB_CPOP1&v=TIME&h=Geopolitical entity (declaring)&from=2014-01-01&to=2025-01-01&CITIES=[ES012C1,ES019C1,ES001C1,ES002C1,ES004K1,ES522C1,ES022C1,ES510C1,ES505C1,ES518C1,ES501C1,ES005C1,ES003C1,ES009C1,ES014C1,ES520C1]&FREQ=[A]&INDIC_UR=[DE1001V]', 'econdb')

			# Eliminamos dos de los índices de los datos
			df.columns = df.columns.droplevel('Frequency')
			df.columns = df.columns.droplevel('Urban audit indicator')

			# Definimos un diccionario con la correspondencia entre los equipos y sus respectivas ciudades
			city_team_dict = {
					"Alavés":"Vitoria/Gasteiz",
					"Athletic":"Bilbao",
					"Atlético":"Madrid",
					"Barcelona":"Barcelona",
					"Betis":"Sevilla",
					"Cádiz":"Cádiz",
					"Celta":"Vigo",
					"Eibar":"San Sebastián/Donostia",
					"Elche":"Elche/Elx",
					"Getafe":"Getafe",
					"Granada":"Granada",
					"Huesca":"Zaragoza",
					"Levante":"Valencia",
					"Osasuna":"Pamplona/Iruña",
					"Real Sociedad":"San Sebastián/Donostia",
					"Real Madrid":"Madrid",
					"Real Valladolid":"Valladolid",
					"Sevilla":"Sevilla",
					"Valencia":"Valencia",
					"Villareal":"Castellón de la Plana/Castelló de la Plana",
			}

			# Definimos el diccionario a devolver, y lo construimos	
			citypop_per_team_dict =  {}	
			for k in city_team_dict.keys():
				citypop = df[city_team_dict[k]].iloc[-1]

				# Código expresión regular	
				exp_reg = re.compile('([0-9]*[.])?[0-9]+')		
				if exp_reg.match(str(citypop)):
					citypop_per_team_dict[k] = int(citypop)
				else:
					print("Recuperada información no válida como población: " + str(citypop))	

			return citypop_per_team_dict

		##############################################################################################################
		###############################################STATISTICS#####################################################
		def get_statistics(self):

			print('[GetInfoBehav] Obteniendo información sobre estadísticas del equipo...')

			#Definimos la url a la quedeseamos solicitar conexion y realizamos el request correspondiente
			url = 'https://www.eduardolosilla.es/'

			respuesta = requests.get(
				url,
				headers = {
					'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
				}
			)

			#Procesamos la respuesta dada por el servidor de la pagina con el contenido de está	
			contenido_web = BeautifulSoup(respuesta.text, 'lxml')

			equipos =[['Nombre', 'Posesion', ' Tiros', 'Tiros a puerta', 'Goles']]

			#Recogemos las tabla que contienen las estadisticas de los equipos
			tables = contenido_web.find_all('div', attrs={'class':'c-detalle-partido-simple__estadisticas ng-star-inserted'})

			for p in tables:
				#Para cada tabla recogemos la informacion con los equipos(estos se agrupan de 2 en 2), que contienen el nombre del equipo y la media por partido respecto la posesion, tiros, tiros a puerta y goles
				header = p.find_all('div', attrs={'class':'c-detalle-partido-simple__estadisticas__header'})

				nombres = header[1].find_all('div', attrs={'class':'c-detalle-partido-simple__estadisticas__header__selector m-stat'})
				stats = p.find_all('div', attrs={'class':'c-detalle-partido-simple__estadisticas__contenido ng-star-inserted'})
				posesion = stats[0].find_all('div', attrs={'class':'c-detalle-partido-simple__estadisticas__contenido__stat'})
				tiros = stats[1].find_all('div', attrs={'class':'c-detalle-partido-simple__estadisticas__contenido__stat'})
				tiros_puerta = stats[2].find_all('div', attrs={'class':'c-detalle-partido-simple__estadisticas__contenido__stat'})
				goles = stats[3].find_all('div', attrs={'class':'c-detalle-partido-simple__estadisticas__contenido__stat'})

				#Añadimos ambos equipos
				equipos.append([nombres[0].string , float(posesion[0].string.replace(',','.')), float(tiros[0].string.replace(',','.')), float(tiros_puerta[0].string.replace(',','.')), float(goles[0].string.replace(',','.'))])
				equipos.append([nombres[1].string , float(posesion[1].string.replace(',','.')), float(tiros[1].string.replace(',','.')), float(tiros_puerta[1].string.replace(',','.')), float(goles[1].string.replace(',','.'))])

			return equipos

		##############################################################################################################
		################################################RANKINGS######################################################
		def get_ranking_teams(self):

			print('[GetInfoBehav] Obteniendo información sobre el ranking del equipo...')

			#Definimos la url a la quedeseamos solicitar conexion y realizamos el request correspondiente
			url = 'https://resultados.as.com/resultados/futbol/primera/clasificacion/'
			#url = 'https://resultados.as.com/resultados/futbol/segunda/clasificacion/'

			respuesta = requests.get(
				url,
				headers = {
					'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
				}
			)

			#Procesamos la respuesta dada por el servidor de la pagina con el contenido de está
			contenido_web = BeautifulSoup(respuesta.text, 'lxml')

			#Definimos la variable donde se van a guardar todos los equipos con su posicion en la liga, puntos, partidos jugados, partidos ganados, partidos empatados y partidos perdidos
			ranking = [['Posicion', 'Equipo', 'Ptos', 'Partidos Jugados', 'Partidos Ganados', 'Partidos Ganados de Local', 'Partidos Ganados de Visitante', 'Partidos Empatados', 'Partidos Empatados', 'Goles a Favor', 'Goles en Contra']]
			
			#Recogemos unicamenete la tabla de clasificación de la liga
			tabla = contenido_web.find('table', attrs={'class':'tabla-datos table-hover'})

			#Nos centramos en el cuerpo de la tabla la cual contienen la información de valor de la tabla
			body = tabla.tbody.find_all('td')

			for p in tabla.find_all('th')[26:]: #Saltamos las primeras 25 posicion que corresponden con las cabeceras y recogemos por equipo
				pos = int(p.find('span', attrs={'class':'pos'}).string)			#La posicion en la liga
				equipo = p.find('span', attrs={'class':'nombre-equipo'}).string	#El nombre del equipo
				ptos = int(body[(pos-1)*21].string)								#Puntos en la liga
				pj = int(body[((pos-1)*21)+1].string)							#Partidos Jugados
				pg = int(body[((pos-1)*21)+2].string)							#Partidos Ganados
				pe = int(body[((pos-1)*21)+3].string)							#Partidos Empatados
				pp = int(body[((pos-1)*21)+4].string)							#Partidos Perdidos
				gf = int(body[((pos-1)*21)+5].string)							#Goles a Favor
				gc = int(body[((pos-1)*21)+6].string)							#Goles en Contra
				pgl = int(body[((pos-1)*21)+9].string)							#Partidos Ganados de Local
				pgv = int(body[((pos-1)*21)+16].string)							#Partidos Ganados de Visitante
				ranking.append([pos, equipo, ptos, pj, pg , pgl, pgv, pe, pp, gf, gc])				#Recogemos la información del equipo

			return ranking



equipos_validos = ['Barcelona', 'Villareal', 'Sevilla']

if len(sys.argv) == 2:

	if sys.argv[-1] in equipos_validos:
		senderagent = RecolectorAgent("recolector_agente_sma@xmpp.jp", "sma_mola_mazo")
		senderagent.start()

		while True:
			try:
				time.sleep(1)
			except KeyboardInterrupt:
				senderagent.stop()
				break
		print("Agente finalizado")
	else:
		print("Error, el equipo " + sys.argv[-1] + " no es válido. Prueba a introducir uno de los equipos de la siguiente lista: ")
		print(equipos_validos)
else:
	print("Error, argumentos incorrectos. La sintaxis correcta para lanzar el agente es la siguiente: python3 RecolectorAgent.py <Nombre del equipo>")
