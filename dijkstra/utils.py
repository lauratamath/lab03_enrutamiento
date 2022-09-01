import json

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
	# else:
	# 	raise Exception('Invalid Names file format. Please check its as requested.')

def getTopologyJID(namesFile, JID):
	file = open(namesFile, "r")
	file = file.read()
	info = eval(file)
	if(info["type"]=="names"):
		names = info["config"]
		JIDS = {v: k for k, v in names.items()}
		name = JIDS[JID]
		return(name)
	# else:
	# 	raise Exception('Invalid Names file format. Please check its as requested.')

def getNeighbors(topoFile, ID):
	file = open(topoFile, "r")
	file = file.read()
	info = eval(file)
	if (info["type"]=="topologia"):
		names = info["config"]
		neighborIDs = names[ID]
		return(neighborIDs)
	# else:
	# 	raise Exception('Invalid Topology file format. Please check its as requested.')
