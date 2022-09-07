from aioconsole import ainput
import asyncio
from asyncio.tasks import sleep
from colorama import Fore, Style
import json
import slixmpp
import sys
import time

# Soluciona problema de sockets en Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, topology, namesNodes):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.received = set()
        self.connected_event = asyncio.Event()
        self.presences_received = asyncio.Event()

        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
    
        self.register_plugin('xep_0030') # Servicio de deteccion
        self.register_plugin('xep_0045') # Chat para multiples usuatios
        self.register_plugin('xep_0199') # Ping
        
        self.topology = topology
        self.namesNodes = namesNodes

        self.network = []
        self.echo_sent = None
        self.LSP = {
            'type': "LSP",
            'from': self.boundjid.bare,
            'sequence': 1,
            'neighbours':{}
        }

        if (namesNodes["type"] == "names"):
            names = namesNodes["config"]
            JIDS = {v: k for k, v in names.items()}
            name = JIDS[jid]

        self.id = name
        if (self.topology["type"] == "topo"):
            names = self.topology["config"]
            nei_id = names[self.id]

        self.neighbours_IDS = nei_id
        self.neighbours = []
        self.setNeighborsJID()

    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        self.connected_event.set()

        for vert in self.neighbours:
            await self.sendEchoMessage(vert, "ECHO SEND")

        self.network.append(self.LSP) 
        self.loop.create_task(self.sendLSP())
        await sleep(2)

        showMenu = True
        while showMenu:
            print(Fore.MAGENTA + """
            ########################################################
            #              Link State Routing Algorithm            #
            ########################################################
                1. Comenzar
                2. Salir
            """ + Style.RESET_ALL)

            userOptionOne = await ainput(Fore.GREEN+"Ingresar número correspondiente a la opción deseada >>> "+ Style.RESET_ALL)
            if userOptionOne == '1':
                print(Fore.BLUE + Style.DIM + "\nRecordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
                send = await ainput(Fore.GREEN +"¿Con quién desea chatear? >>> "+ Style.RESET_ALL)

                print(Fore.BLUE + Style.DIM + "\n* Escriba salir para regresar al menu principal *"+ Style.RESET_ALL) 
                activo = True

                while activo:
                    message = await ainput(Fore.BLUE +"Escriba un mensaje >>> "+ Style.RESET_ALL)
                                    
                    if (message != 'salir') and len(message) > 0:
                        self.sendChatMessage(self.boundjid.bare, send, steps=1, visitedNodes=[self.boundjid.bare], message=message)
                    elif message == 'salir':
                        activo = False
                    
            elif userOptionOne == '2':
                showMenu = False
                print(Fore.MAGENTA+"Adios!!!"+ Style.RESET_ALL)
                self.disconnect()
            
            else:
                print(Fore.RED+"ERROR: Debe ingresar una opcion valida."+ Style.RESET_ALL)

    def setNeighborsJID(self):
        for id in self.neighbours_IDS:
            if (self.namesNodes["type"] == "names"):
                names = self.namesNodes["config"]
                JID = names[id]
            neighbour_JID = JID
            self.neighbours.append(neighbour_JID)

    # XMPP default message function
    async def message(self, msg):
        body = json.loads(msg['body'])

        if body['type'] == "ECHO SEND":
            await self.sendEchoMessage(body['from'],"ECHO RESPONSE")

        elif body['type'] == "ECHO RESPONSE":
            distance = time.time()-self.echo_sent
            self.LSP['neighbours'][body['from']] = distance

        elif body['type'] == "LSP":
            new = await self.refreshNetwork(body)
            await self.sendFloodLSP(body, new)

        elif body['type'] == "MESSAGE":
            if body['to'] != self.boundjid.bare:
                self.sendChatMessage(source=body['from'], to=body['to'], steps=body['steps']+1, distance=body['distance'], visitedNodes=body['visited_nodes'].append(self.boundjid.bare), message=body['message'])
            elif body['to'] == self.boundjid.bare:
                print(Fore.MAGENTA+"\nNuevo mensaje! >> " + Style.RESET_ALL +  body['message'])

    
    async def sendEchoMessage(self, to, type ,steps = 1):
        you = self.boundjid.bare
        json = {
            'type': type,
            'from':you,
            'to': to,
            'steps': steps
        }
        to_send = parseObjectToJson(json)
        self.send_message(mto = to, mbody=to_send, mtype='chat')
        self.echo_sent = time.time()

    async def sendLSP(self):
        while True:
            for vert in self.neighbours:
                incomingLSP = parseObjectToJson(self.LSP)
                self.send_message(mto=vert, mbody=incomingLSP, mtype='chat')
            await sleep(2)
            self.LSP['sequence'] += 1
    
    def sendChatMessage(self, source, to, steps=0, distance=0, visitedNodes=[], message="Hola mundo"):
        body = {
            'type':"MESSAGE",
            'from': source,
            'to': to,
            'steps': steps,
            'distance': distance,
            'visited_nodes':visitedNodes, 
            'message':message
        }
        path = self.calcShortestPath(self.boundjid.bare, to)
        body['distance'] += self.LSP['neighbours'][path[1]['from']]
        to_send = parseObjectToJson(body)
        self.send_message(mto=path[1]['from'], mbody=to_send, mtype='chat')

    async def refreshNetwork(self, lsp):
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
    
    def calcShortestPath(self, origin, dest):
        visitedNodes = []
        actualNode = self.findCurrentNode(origin)
        distance = 0
        while actualNode['from'] != dest:
            nodeDistances = [] 
            neighbours = actualNode['neighbours']
            for vert in neighbours.keys():
                if vert == dest:
                    visitedNodes.append(actualNode)
                    actualNode = self.findCurrentNode(vert)
                    visitedNodes.append(actualNode)
                    return visitedNodes
                elif vert not in visitedNodes:
                    distance_to_neighbour = neighbours[vert]
                    nodeDistances.append(distance_to_neighbour)
            minDist = min(nodeDistances)
            nodeIndex = nodeDistances.index(minDist)
            nodeList = list(actualNode['neighbours'].keys())
            nodeToVisitID = nodeList[nodeIndex]
            visitedNodes.append(actualNode)
            nodeToVisit = self.findCurrentNode(nodeToVisitID)
            actualNode = nodeToVisit
            distance += minDist
        return visitedNodes

    def findCurrentNode(self, id):
        for i in range(len(self.network)):
            node = self.network[i]
            if id in node['from']:
                return node
        return False

    async def sendFloodLSP(self, lsp, new):
        for vert in self.neighbours:
            if new and vert != lsp['from']:
                    self.send_message(mto=vert, mbody=parseObjectToJson(lsp), mtype='chat')
    

def parseObjectToJson(object):
    json_string = json.dumps(object)
    return json_string