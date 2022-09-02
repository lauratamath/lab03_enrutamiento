import uuid
import json
import slixmpp
import json
import time
from colorama import Fore, Style
from slixmpp.exceptions import IqError, IqTimeout

class Client(slixmpp.ClientXMPP):
    # Clase para enlazar a los usuarios y así comunicarse entre ellos 
    def __init__(self, jid, password, giften, message, routing, listening, users, topo):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.giften = giften
        self.listening = listening
        self.msg = message
        self.routing = routing
        self.jid_ = jid
        self.lastid = []
        self.users = users
        self.topo = topo

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("register", self.register)

    # Calcular ruta con los parametros y enviar mensaje de presencia
    async def start(self, event):
        self.send_presence()
        await self.get_roster()

        if(not self.listening and self.routing=="flooding"):
            msg = {}
            msg["Start"] = self.jid_
            msg["Destiny"] = self.giften
            msg["Jumps"] = 0
            msg["Distance"] = 0
            msg["List_of_Nodes"] = []
            msg["Message"] = self.msg
            msg["ID"] = str(uuid.uuid4())
            self.lastid.append(msg["ID"])

            receivers, message = calculate(json.dumps(msg), self.jid_, self.users, self.topo)

            for destiny in receivers:
                print("Mensaje para :",destiny)
                self.send_message(mto=destiny, mbody=message, mtype='chat')
    
    def register(self, iq):
        iq = self.Iq()
        iq['type'] = 'set'
        iq['register']['username'] = self.boundjid.user
        iq['register']['password'] = self.password

        try:
            iq.send()
            print("Autenticación : ", self.boundjid,"\n")
        except IqError as e:
            print(Fore.RED + 'Credenciales incorrectas' + Style.RESET_ALL, e,"\n")
            self.disconnect()
        except IqTimeout:
            print(Fore.RED + 'Error: el servidor tomó demasiado tiempo' + Style.RESET_ALL)
            self.disconnect()
        except Exception as e:
            print(e)
            self.disconnect()

    # Imprimir la ruta del mensaje y enviar a cada receptor de la lista
    def message(self, msg):
        if(self.routing=="flooding"):
            if msg['type'] in ('chat'):
                giften = str(msg['from']).split('/')[0]
                body = msg['body']
                msg = eval(str(body))
                if(msg["ID"] not in self.lastid):
                    self.lastid.append(msg["ID"])

                    print('\n|',giften,"Dice:", msg["Message"],'\nSaltos:', msg["Jumps"],', Distancia:', msg["Distance"],'|\n')

                    receivers, message = calculate(str(body), self.jid_, self.users, self.topo)

                    for destiny in receivers:

                        if(destiny!=giften):
                            print("Mensaje enviado a :",destiny)
                            self.send_message(mto=destiny, mbody=message, mtype='chat')

last_id = None

# Recibe el ID en la topología y devuelve el JID 
def get_JID(users,ID):
	file = open(users, "r")
	file = file.read()
	info = eval(file)
	if(info["type"]=="names"):
		names = info["config"]
		JID = names[ID]
		return(JID)
	else:
		raise Exception(Fore.RED + 'Archivo no encontrado' + Style.RESET_ALL)

# Recibe el JID del alumchat y  devuelve el ID en la topología 
def get_ID(users, JID):
	file = open(users, "r")
	file = file.read()
	info = eval(file)
	if(info["type"]=="names"):
		names = info["config"]
		JIDS = {v: k for k, v in names.items()}
		name = JIDS[JID]
		return(name)
	else:
		raise Exception(Fore.RED + 'Archivo no encontrado' + Style.RESET_ALL)


# Devuelve una lista de los vecino de un nodo dado
def get_neighbors(topo, users, JID):
	ID = get_ID(users, JID)
	file = open(topo, "r")
	file = file.read()
	info = eval(file)
	if(info["type"]=="topo"):
		names = info["config"]
		neighbors_IDs = names[ID]
		neighbors_JIDs = [get_JID(users,i) for i in neighbors_IDs]
		return(neighbors_JIDs)
	else:
		raise Exception(Fore.RED + 'Archivo no encontrado' + Style.RESET_ALL)
	return  

# Calcular la ruta y devolver nodos a enviar el mensaje
def calculate(message, sender, users, topo):
	start_time = time.time()
	info = eval(message)
	info["Jumps"] = info["Jumps"] + 1
	nodes = get_neighbors(topo, users, sender)
	info["List_of_Nodes"] = [info["List_of_Nodes"], nodes]
	info["Distance"] = info["Distance"] - start_time + time.time()
	return (nodes, json.dumps(info))