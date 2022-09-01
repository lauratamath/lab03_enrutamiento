from aioconsole import ainput, aprint 
from asyncio.tasks import sleep
from getpass import getpass

import sys
import asyncio
import slixmpp
import time
import json

# Solves conflict with socket dependencies
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def parseJsonToObject(jsonStr):
  obj = json.loads(jsonStr)
  return obj

def parseObjToJson(obj):
  jsonStr = json.dumps(obj)
  return jsonStr

def getServerJID(namesFile,ID):
	file = open(namesFile, "r")
	file = file.read()
	info = eval(file)
	if(info["type"]=="names"):
		names = info["config"]
		JID = names[ID]
		return(JID)
	else:
		raise Exception('Invalid Names file format. Please check its as requested.')

def getTopologyJID(namesFile, JID):
	file = open(namesFile, "r")
	file = file.read()
	info = eval(file)
	if(info["type"]=="names"):
		names = info["config"]
		JIDS = {v: k for k, v in names.items()}
		name = JIDS[JID]
		return(name)
	else:
		raise Exception('Invalid Names file format. Please check its as requested.')

def getNeighbors(topoFile, ID):
	file = open(topoFile, "r")
	file = file.read()
	info = eval(file)
	if (info["type"]=="topologia"):
		names = info["config"]
		neighborIDs = names[ID]
		return(neighborIDs)
	else:
		raise Exception('Invalid Topology file format. Please check its as requested.')

class LSRClient(slixmpp.ClientXMPP):
  def __init__(self, jid, password, topologyFile, nameDictFile):
    slixmpp.ClientXMPP.__init__(self, jid, password)
    self.add_event_handler("session_start", self.start)
    self.add_event_handler("message", self.message)
    
    self.topologyFile = topologyFile
    self.nameDictFile = nameDictFile
    self.network = []
    self.echo_sent = None
    self.LSP = {
      'type': 'LSP',
      'from': self.boundjid.bare,
      'sequence': 1,
      'neighbours':{}
    }
    self.id = getTopologyJID(self.nameDictFile, jid)
    self.neighborIDs = getNeighbors(self.topologyFile, self.id)
    self.neighbours = []
    self.getNeighborsServerJID()

  async def start(self, event):
    self.send_presence()
    await self.get_roster()

    await aprint("Por favor, presione enter para continuar.")
    
    start = await ainput()
    
    for neighbour in self.neighbours:
      await self.sendSalute(neighbour)
    
    for neighbour in self.neighbours:
      await self.sendEchoMessage(neighbour, "ECHO SEND")

    self.network.append(self.LSP) 

    self.loop.create_task(self.sendLSP())

    await sleep(2)

    print("Ingrese el usuario al que desea enviar un mensaje, o espere a recibir uno.")
    send = await ainput()
    if send != None:
      message = await ainput('Ingrese su mensaje: ')

    # Give some time for the network to load
    print("Esperando a que la red termine de cargar...")
    await sleep(17)
    print("La red ha cargado. Enviando mensaje...")

    self.sendChatMessage(self.boundjid.bare, send, steps=1, visitedNodes=[self.boundjid.bare], message=message)
    
    print("Por favor, presione Enter para salir.")
    exit = await ainput()
    self.disconnect()

  def getNeighborsServerJID(self):
    for id in self.neighborIDs:
      neighbour_JID = getServerJID(self.nameDictFile, id)
      self.neighbours.append(neighbour_JID)

  async def message(self, msg):
    body = parseJsonToObject(msg['body'])
    if body['type'] == 'HELLO':
      print("Mensaje de: ", msg['from'])

    elif body['type'] == "ECHO SEND":
      print("Enviando mensaje de vuelta a: ", msg['from'])
      await self.sendEchoMessage(body['from'], "ECHO RESPONSE")

    elif body['type'] == "ECHO RESPONSE":
      distance = time.time()-self.echo_sent
      print("La distancia hacia ", msg['from'], ' es de ', distance)
      self.LSP['neighbours'][body['from']] = distance

    elif body['type'] == 'LSP':
      new = await self.updateNetwork(body)
      await self.floodLSP(body, new)

    elif body['type'] == "MESSAGE":
      if body['to'] != self.boundjid.bare:
        print('Se recibio un mensaje para otro destino, reenviando... ')
        self.sendChatMessage(source=body['from'], dest = body['to'], steps=body['steps']+1, distance=body['distance'], visitedNodes=body['visited_nodes'].append(self.boundjid.bare), message=body['mesage'])
      elif body['to'] == self.boundjid.bare:
        print("######################")
        print('Se recibio un mensaje.')
        print(body['from'], " -> ", body['mesage'])
        print(body)

      
  async def sendSalute(self, dest, steps=1):
    emitter = self.boundjid.bare
    json = {
      'type': 'HELLO',
      'from':emitter,
      'to': dest,
      'steps': steps
    }
    to_send = parseObjToJson(json)
    self.send_message(mto=dest, mbody=to_send, mtype='chat')
  
  async def sendEchoMessage(self, dest, type, steps=1):
    emitter = self.boundjid.bare
    json = {
      'type': type,
      'from':emitter,
      'to': dest,
      'steps': steps
    }
    to_send = parseObjToJson(json)
    self.send_message(mto = dest, mbody=to_send, mtype='chat')
    self.echo_sent = time.time()

  async def sendLSP(self):
    while True:
      for neighbour in self.neighbours:
        lsp_to_send = parseObjToJson(self.LSP)
        self.send_message(mto =neighbour,mbody=lsp_to_send,mtype='chat')
      await sleep(2)
      self.LSP['sequence'] += 1
  
  def sendChatMessage(self, source, dest, steps=0, distance=0, visitedNodes=[], message="Hola Humano"):
    body ={
      'type': "MESSAGE",
      'from': source,
      'to': dest,
      'steps': steps,
      'distance': distance,
      'visited_nodes': visitedNodes, 
      'mesage': message
    }
    path = self.calcShortestPath(self.boundjid.bare, dest)
    body['distance'] += self.LSP['neighbours'][path[1]['from']]
    mesStruct = parseObjToJson(body)
    self.send_message(mto=path[1]['from'], mbody=mesStruct, mtype='chat')

  async def updateNetwork(self, lsp):
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
  
  def calcShortestPath(self, source, dest):
    distance = 0
    visited = []
    currentNode = self.getNodeInCurrentNetwork(source)

    while currentNode['from'] != dest:
      nodeDistances = [] 
      neighbours = currentNode['neighbours']

      for neighbour in neighbours.keys():
        if neighbour == dest:
          visited.append(currentNode)
          currentNode = self.getNodeInCurrentNetwork(neighbour)
          visited.append(currentNode)
          return visited
        elif neighbour not in visited:
          distanceToNeighbor = neighbours[neighbour]
          nodeDistances.append(distanceToNeighbor)

      minDistance = min(nodeDistances)
      nodeIndex = nodeDistances.index(minDistance)
      nodeCollection = list(currentNode['neighbours'].keys())
      nextNodeIndex = nodeCollection[nodeIndex]
      visited.append(currentNode)
      nextNode = self.getNodeInCurrentNetwork(nextNodeIndex)
      currentNode = nextNode
      distance += minDistance

    return visited

  def getNodeInCurrentNetwork(self, id):
    for i in range(len(self.network)):
      node = self.network[i]
      if id in node['from']:
        return node
    return False

  async def floodLSP(self, lsp, new):
    for neighbour in self.neighbours:
      if new and neighbour != lsp['from']:
        self.send_message(mto=neighbour, mbody=parseObjToJson(lsp), mtype='chat')