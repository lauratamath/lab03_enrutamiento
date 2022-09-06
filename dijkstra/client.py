import asyncio
from asyncio.tasks import sleep
import slixmpp
from aioconsole import ainput
import time
from colorama import Fore, Style
import json


class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, topo_info, names_info):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.received = set()
        self.connected_event = asyncio.Event()
        self.presences_received = asyncio.Event()

        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
    
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0199') # Ping
        
        
        self.topo_info = topo_info
        self.names_info = names_info

        self.network = []
        self.echo_sent = None
        self.LSP = {
            'type': "LSP",
            'from': self.boundjid.bare,
            'sequence': 1,
            'neighbours':{}
        }

        if (names_info["type"] == "names"):
            names = names_info["config"]
            JIDS = {v: k for k, v in names.items()}
            name = JIDS[jid]

        self.id = name
        if (self.topo_info["type"] == "topo"):
            names = self.topo_info["config"]
            nei_id = names[self.id]

        self.neighbours_IDS = nei_id
        self.neighbours = []
        self.neighbours_JID()


    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        self.connected_event.set()

        for neighbour in self.neighbours:
            await self.send_echo_message(neighbour, "ECHO SEND")

        self.network.append(self.LSP) 
        self.loop.create_task(self.send_LSP())
        await sleep(2)

        menu = True
        while menu:
            print(Fore.MAGENTA + """

            +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
            -                                                      -
            +                  LINK STATE ROUTING                  +
            -                                                      - 
            +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

                1. Continuar
                2. Salir

            """ + Style.RESET_ALL)
            op_1 = await ainput(Fore.GREEN+"Ingresar número correspondiente a la opción deseada >>> "+ Style.RESET_ALL)
            if op_1 == '1':
                print(Fore.BLUE + Style.DIM + "\nRecordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
                send = await ainput(Fore.GREEN +"¿Con quién desea chatear? >>> "+ Style.RESET_ALL)
                send += "@alumchat.fun"

                print(Fore.BLUE + Style.DIM + "\n* Escriba salir para regresar al menu principal *"+ Style.RESET_ALL) 
                activo = True

                while activo:
                    message = await ainput(Fore.BLUE +"Escriba un mensaje >>> "+ Style.RESET_ALL)
                                    
                    if (message != 'salir') and len(message) > 0:
                        self.send_chat_message(self.boundjid.bare,send,steps=1,visited_nodes=[self.boundjid.bare],message=message)
                    elif message == 'salir':
                        activo = False
                    else:
                        pass
                    
            elif op_1 == '2':
                menu = False
                print(Fore.MAGENTA+"Adios!!!"+ Style.RESET_ALL)
                self.disconnect()



    def neighbours_JID(self):
        for id in self.neighbours_IDS:
            if (self.names_info["type"] == "names"):
                names = self.names_info["config"]
                JID = names[id]
            neighbour_JID = JID
            self.neighbours.append(neighbour_JID)

    async def message(self, msg):
        body = json.loads(msg['body'])

        if body['type'] == "ECHO SEND":
            await self.send_echo_message(body['from'],"ECHO RESPONSE")

        elif body['type'] == "ECHO RESPONSE":
            distance = time.time()-self.echo_sent
            self.LSP['neighbours'][body['from']] = distance

        elif body['type'] == "LSP":
            new = await self.update_network(body)
            await self.flood_LSP(body, new)

        elif body['type'] == "MESSAGE":
            if body['to'] != self.boundjid.bare:
                self.send_chat_message(source = body['from'],to = body['to'], steps=body['steps'] +1, distance=body['distance'],visited_nodes= body['visited_nodes'].append(self.boundjid.bare),message=body['message'])
            elif body['to'] == self.boundjid.bare:
                print(Fore.MAGENTA+"\nNuevo mensaje! >> " + Style.RESET_ALL +  body['message'])

    
    async def send_echo_message(self, to, type ,steps = 1):
        you = self.boundjid.bare
        to = to 
        json = {
            'type': type,
            'from':you,
            'to': to,
            'steps': steps
        }
        to_send = o_to_j(json)
        self.send_message(mto = to, mbody=to_send, mtype='chat')
        self.echo_sent = time.time()

    async def send_LSP(self):
        while True:
            for neighbour in self.neighbours:
                lsp_to_send = o_to_j(self.LSP)
                self.send_message(mto =neighbour,mbody=lsp_to_send,mtype='chat')
            await sleep(2)
            self.LSP['sequence'] += 1
    
    def send_chat_message(self,source,to,steps=0, distance = 0, visited_nodes = [],message="Hola mundo"):
        body = {
            'type':"MESSAGE",
            'from': source,
            'to': to,
            'steps': steps,
            'distance': distance,
            'visited_nodes':visited_nodes, 
            'message':message
        }
        path = self.calculate_path(self.boundjid.bare, to)
        body['distance'] += self.LSP['neighbours'][path[1]['from']]
        to_send = o_to_j(body)
        self.send_message(mto=path[1]['from'],mbody = to_send,mtype='chat')

    async def update_network(self, lsp):
        for i in range(0,len(self.network)):
            node = self.network[i]
            if lsp['from'] == node['from']:
                if lsp['sequence'] > node['sequence']:
                    node['sequence'] = lsp['sequence']
                    node['neighbours'] = lsp['neighbours']
                    return 1
                if lsp['sequence'] <= node['sequence']:
                    return None
        self.network.append(lsp)
        return 1
    
    def calculate_path(self, source, dest):
        distance = 0
        visited = []
        current_node = self.find_node_in_network(source)
        while current_node['from'] != dest:
            node_distances = [] 
            neighbours = current_node['neighbours']
            for neighbour in neighbours.keys():
                if neighbour == dest:
                    visited.append(current_node)
                    current_node = self.find_node_in_network(neighbour)
                    visited.append(current_node)
                    return visited
                elif neighbour not in visited:
                    distance_to_neighbour = neighbours[neighbour]
                    node_distances.append(distance_to_neighbour)
            min_distance = min(node_distances)
            node_index = node_distances.index(min_distance)
            all_nodes = list(current_node['neighbours'].keys())
            next_node_id = all_nodes[node_index]
            visited.append(current_node)
            next_node = self.find_node_in_network(next_node_id)
            current_node = next_node
            distance += min_distance
        return visited

    def find_node_in_network(self, id):
        for i in range(len(self.network)):
            node = self.network[i]
            if id in node['from']:
                return node
        return False

    async def flood_LSP(self, lsp, new):
        for neighbour in self.neighbours:
            if new and neighbour != lsp['from']:
                    self.send_message(mto =neighbour,mbody= o_to_j(lsp),mtype='chat')
    

def o_to_j(object):
    json_string = json.dumps(object)
    return json_string