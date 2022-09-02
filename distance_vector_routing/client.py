
import asyncio
from datetime import datetime
import slixmpp
import networkx as nx
import ast
from colorama import Fore, Style

# Intanciar a un cliente en el servidor
class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, algoritmo, nodo, nodes, names, grafo, grafo_pos, source):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.received = set()

        self.algoritmo = algoritmo
        self.names = names
        self.grafo = grafo
        self.source = source
        self.grafo_pos = grafo_pos

        self.vecinos = self.nodo_vecino(self.grafo_pos, self.source)
        self.nodo = nodo
        self.nodes = nodes
        
        self.schedule(name="echo", callback=self.echo_msg, seconds=5, repeat=True)
        self.schedule(name="update", callback=self.nuevo_msg, seconds=10, repeat=True)
        
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
            await self.resp_msg(msg['body'])

    # Reenvio de mensajes
    async def resp_msg(self, msg):
        message = msg.split('|')
        if message[0] == '1':
            if self.algoritmo == '1':
                if message[2] == self.jid:
                    print(Fore.MAGENTA+"Nuevo mensaje! >> " + Style.RESET_ALL+  message[6])
                else:
                    shortest_neighbor_node = self.camino_c(message[2])
                    if shortest_neighbor_node:
                        if shortest_neighbor_node[1] in self.vecinos:
                            # We send the message
                            StrMessage = "|".join(message)
                            self.send_message(
                                mto = message[2],
                                mbody = StrMessage,
                                mtype = 'chat' 
                            )
                        else:
                            pass
                    else:
                        pass

        elif message[0] == '2':
            if self.algoritmo == '1':
                msg_esq = message[6]

                msg_div = msg_esq.split('-')
                nodos = ast.literal_eval(msg_div[0])
                aristas = ast.literal_eval(msg_div[1])

                self.grafo.add_nodes_from(nodos)
                self.grafo.add_weighted_edges_from(aristas)
                act_grafo = {}

                for node in nx.to_dict_of_dicts(self.grafo):
                    act_grafo[node] = {}
                    for neighbor_node in nx.to_dict_of_dicts(self.grafo)[node]:
                        act_grafo[node][neighbor_node] = nx.to_dict_of_dicts(self.grafo)[node][neighbor_node]['weight']

                act_grafo = nx.to_dict_of_dicts(self.grafo)
                
                distance = {}
                predecessor = {}

                for node in act_grafo:
                    distance[node] = float('Inf')
                    predecessor[node] = None
                distance[self.source] = 0
                
                for i in range(len(act_grafo)-1):
                    for u in act_grafo:
                        for v in act_grafo[u]:
                            if distance[v] > distance[u] + act_grafo[u][v]:
                
                                distance[v]  = distance[u] + act_grafo[u][v]
                                predecessor[v] = u

                for u in act_grafo:
                    for v in act_grafo[u]:
                        assert distance[v] <= distance[u] + act_grafo[u][v]

               
                self.vecinos = list(act_grafo[self.source].keys())

                info_vecinos = self.grafo.nodes().data()
                edges_info = self.grafo.edges.data('weight')
                s_nodes = str(info_vecinos) + "-" + str(edges_info)

                for i in list(self.grafo_pos[self.source].keys()):
                    n_msg = "2|" + str(self.jid) + "|" + str(self.names[i]) + "|" + str(self.grafo.number_of_nodes()) + "||" + str(self.nodo) + "|" + s_nodes
                    
                    self.send_message(
                            mto = self.names['config'][i],
                            mbody = n_msg,
                            mtype = 'chat'
                        )

        elif message[0] == '3':
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
                tiempo = float(message[6]) - float(message[4])
                self.grafo[self.nodo][message[5]]['weight'] = tiempo
        else:
            pass

    def camino_c(self, target):
        for key in self.names:
            if self.names[key] == target:
                return nx.bellman_ford_path(self.grafo, self.source, key)
        return None

    def nodo_vecino(self, grafo_pos, source):
            return list(grafo_pos[source].keys())

 # Distancia entre nodos adyacentes
    def echo_msg(self):
        for i in self.nodes:
            now = datetime.now()
            timestamp = datetime.timestamp(now)
            mensaje = "3|" + str(self.jid) + "|" + str(self.names[i]) + "||"+ str(timestamp) +"|" + str(i) + "|"
            self.send_message(
                        mto = self.names[i],
                        mbody = mensaje,
                        mtype = 'chat' 
                    )

    def nuevo_msg(self):

        if self.algoritmo == '1':
            info_vecinos = self.grafo.nodes().data()
            edges_info = self.grafo.edges.data('weight')
            s_nodes = str(info_vecinos) + "-" + str(edges_info)
            for i in self.vecinos:
                n_msg = "2|" + str(self.jid) + "|" + str(self.names[i]) + "|" + str(self.grafo.number_of_nodes()) + "||" + str(self.nodo) + "|" + s_nodes
                self.send_message(
                        mto = self.names[i],
                        mbody = n_msg,
                        mtype = 'chat'
                    )

