# Referencias
# https://slixmpp.readthedocs.io/en/latest/getting_started/sendlogout.html
# https://slixmpp.readthedocs.io/en/latest/event_index.html

import getpass
import yaml
import networkx as nx
import asyncio
import logging
import slixmpp
import networkx as nx
import random
import sys
import colorama

from networkx.algorithms.shortest_paths.generic import shortest_path
from aioconsole import ainput
from getpass import getpass
from datetime import datetime
from colorama import Fore
from colorama import Style

# Intanciar a un cliente en el servidor
class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, algoritmo, nodo, nodes, names, graph):
        super().__init__(jid, password)
        self.received = set()
        self.initialize(jid, password, algoritmo, nodo, nodes, names, graph)

        self.schedule(name="echo", callback=self.echo, seconds=10, repeat=True)
        self.schedule(name="update", callback=self.tree_update, seconds=10, repeat=True)
        
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
            await self.forward_msg(msg['body'])

    # Reenvio de mensjaes
    async def forward_msg(self, msg):
        message = msg.split('|')
        if message[0] == 'msg':
            print(Fore.LIGHTMAGENTA_EX + "\n------------- Flooding algorithm  -------------" + Style.RESET_ALL )
            print('\nMensaje de reenvío.. ')
            if self.algoritmo == '1':
                if message[2] == self.jid:
                    print("This message is for me >> " +  message[6])
                else:
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
                print(Fore.RED + "\nEsta opción no está disponible ): \n"+ Style.RESET_ALL)

        elif message[0] == 'echo':
            # Distancia entre nodos adyacentes
            if message[6] == '':
                now = datetime.now()
                timestamp = datetime.timestamp(now)
                mensaje = msg + str(timestamp)
                self.send_message(
                            mto=message[1],
                            mbody=mensaje,
                            mtype='chat' 
                        )
            else:
                difference = float(message[6]) - float(message[4])
                self.graph.nodes[message[5]]['weight'] = difference
        else:
            pass

    def echo(self):
        for i in self.nodes:
            mensaje = "echo|" + str(self.jid) + "|" + str(self.names[i]) + "||"+ str(datetime.timestamp(datetime.now())) +"|" + str(i) + "|"
            self.send_message(
                        mto=self.names[i],
                        mbody=mensaje,
                        mtype='chat' 
                    )

    # Argumentos para el grafico
    def initialize(self, jid, password, algoritmo, nodo, nodes, names, graph):
        self.algoritmo = algoritmo
        self.names = names
        self.graph = graph
        self.nodo = nodo
        self.nodes = nodes

# Almacenamiento de la topologia de la red
class Tree():
    def newTree(self, topologia, names):
        G = nx.Graph()
        # Agregando nodos
        for key, value in names["config"].items():
            G.add_node(key, jid=value)
            
        # Asignacion de diferentes pesos y se agregan bordes
        for key, value in topologia["config"].items():
            for i in value:
                weightA = random.uniform(0, 1)
                G.add_edge(key, i, weight=weightA)
        
        return G
    
# Gestionamiento del cliente
async def main(xmpp: Client):
    mainexecute = True
    origin = ""
    destiny = ""
    while mainexecute:
        choice = await ainput("Start chat (y: yes | n: no): ")
        if choice == 'y':
            print(Fore.BLUE + Style.DIM + "Recordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
            to_user = await ainput(Fore.GREEN +"¿Con quién desea chatear? >>> "+ Style.RESET_ALL)
            active = True
            while active:
                mensaje = await ainput("Message >>> ")
                if (len(mensaje) > 0):
                    if (xmpp.algoritmo == '1'):
                        mensaje = "msg|" + str(xmpp.jid) + "|" + str(to_user) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
                        for i in xmpp.nodes:
                            xmpp.send_message(
                                mto=xmpp.names[i],
                                mbody=mensaje,
                                mtype='chat' 
                            )  
                    else:
                        xmpp.send_message(
                            mto=to_user,
                            mbody=mensaje,
                            mtype='chat' 
                        )
        elif choice == 'n':
            mainexecute = False
            xmpp.disconnect()
        else:
            pass


if __name__ == "__main__":
    lector_topo = open("topologia.txt", "r", encoding="utf8")
    lector_names = open("names.txt", "r", encoding="utf8")
    topo_string = lector_topo.read()
    names_string = lector_names.read()
    topologia = yaml.load(topo_string, Loader=yaml.FullLoader)
    names = yaml.load(names_string, Loader=yaml.FullLoader)

    print("\n            Bienvenido al servidor")
    print(Fore.BLUE + Style.DIM + "Recordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
    jid = input(Fore.GREEN + "User>>> "+ Style.RESET_ALL)
    pswd = getpass(Fore.GREEN +"Password >>> "+ Style.RESET_ALL)
    print("1. Flooding")
    alg = input("\nElija la opción del algoritmo que desea utilizar: ") 

    tree = Tree()

    for key, value in names["config"].items():
        print("no entra ac")
        print('esto es jid ' + jid)
        print('esto es key ' + value)
        if jid == value:
            print("no entra acaaa")
            nodo = key
            nodes = topologia["config"][key]

    graph = tree.newTree(topologia, names)
    xmpp = Client(jid, pswd, alg, nodo, nodes, names["config"], graph)
    xmpp.connect() 
    xmpp.loop.run_until_complete(xmpp.connected_event.wait())
    xmpp.loop.create_task(main(xmpp))
    xmpp.process(forever=False)