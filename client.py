import asyncio
import slixmpp
import networkx as nx

from networkx.algorithms.shortest_paths.generic import shortest_path
from datetime import datetime
from colorama import Fore, Style


# Intanciar a un cliente en el servidor
class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, algoritmo, nodo, nodos, nombres, graph):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.received = set()
        self.initialize(jid, password, algoritmo, nodo, nodos, nombres, graph)

        self.schedule(name="echo", callback=self.echo, seconds=10, repeat=True)
        self.schedule(name="update", callback=self.update_g, seconds=10, repeat=True)
        
        self.connected_event = asyncio.Event()
        self.presences_received = asyncio.Event()

        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
        
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0199') # Ping

    async def start(self, event):
        self.send_presence() 
        await self.get_roster()
        self.connected_event.set()

    # Recibir mensajes
    async def message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            await self.rep_mess(msg['body'])

    # Reenvio de mensjaes
    async def rep_mess(self, msg):
        message = msg.split('|')
        if message[0] == 'msg':
            print(Fore.LIGHTMAGENTA_EX + "\n------------- Flooding algorithm  -------------" + Style.RESET_ALL )
            print('\nMensaje de reenvío.. ')
            if self.algoritmo == '1':
                if message[2] == self.jid:
                    print("Mensaje recibido >>> " +  message[6])
                else:
                    shortest_neighbor_node = self.dvr.shortest_path(message[2])
                    if shortest_neighbor_node:
                        if message[3] != '0':
                            lista = message[4].split(",")
                        if self.nodo not in lista:
                            message[4] = message[4] + "," + str(self.nodo)
                            message[3] = str(int(message[3]) - 1)
                            StrMessage = "|".join(message)
                            for i in self.nodes:
                                self.send_message(
                                    mto=self.names[i],
                                    mbody=StrMessage,
                                    mtype='chat' 
                                )  
                        else:
                            pass
                    else:
                        pass

            elif self.algoritmo == '2':

                print(message)
                sendto= message[6].split('*')
                sendto = sendto[1].split('#')
                sendNode = sendto[1]
                
                for (p, d) in self.graph.nodos(data=True):
                    if (p == sendNode):
                        jid_receiver = d['jid']
                print('Enviar a: ', jid_receiver)

                if message[2] == self.jid:
                    print("Mensaje recibido >>> " +  message[6])
                else:
                    if message[3] != '0':
                        lista = message[4].split(",")
                        if self.nodo not in lista:
                            message[4] = message[4] + "," + str(self.nodo)
                            message[3] = str(int(message[3]) - 1)
                            StrMessage = "|".join(message)
                            self.send_message(
                                    mto = jid_receiver,
                                    mbody = StrMessage,
                                    mtype = 'chat' 
                                )  
                            print("Mensaje enviado")
                    else:
                        pass
            else:
                print(Fore.RED + "\nEsta opción no está disponible ): \n"+ Style.RESET_ALL)

        elif message[0] == 'echo':
            # Distancia entre nodos adyacentes
            if message[6] == '':
                now = datetime.now()
                timestamp = datetime.timestamp(now)
                mensaje = msg + str(timestamp)
                self.send_message(
                            mto = message[1],
                            mbody = mensaje,
                            mtype = 'chat' 
                        )
            else:
                difference = float(message[6]) - float(message[4])
                self.graph.nodos[message[5]]['weight'] = difference
        else:
            pass

    def echo(self):
        for i in self.nodos:
            mensaje = "echo|" + str(self.jid) + "|" + str(self.nombres[i]) + "||"+ str(datetime.timestamp(datetime.now())) +"|" + str(i) + "|"
            self.send_message(
                        mto = self.nombres[i],
                        mbody = mensaje,
                        mtype = 'chat' 
                    )

    def update_g(self):
        if self.algoritmo == '2':
            for i in self.nodos:
                self.graph.nodos[i]["neighbors"] = self.graph.neighbors(i)
            neigh_w = nx.graph.get_node_attributes(self.graph,'neighbors')



    # Argumentos para el grafico
    def initialize(self, jid, password, algoritmo, nodo, nodos, nombres, graph):
        self.jid = jid
        self.password = password
        self.algoritmo = algoritmo
        self.nombres = nombres
        self.graph = graph
        self.nodo = nodo
        self.nodos = nodos
