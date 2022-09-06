import asyncio
import uuid
import slixmpp
from colorama import Fore, Style
import json
import time

class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, recipient, message,routing, listening, names_info, topo_info):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.received = set()

        self.recipient = recipient
        self.listening = listening
        self.msg = message
        self.routing = routing

        self.jid_ = jid
        self.lastid = []
        self.names_info = names_info
        self.topo_info = topo_info

        self.connected_event = asyncio.Event()
        self.presences_received = asyncio.Event()

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0199') # Ping

    async def start(self, event):
        self.send_presence()
        await self.get_roster()
    
        if(not self.listening and self.routing=="flooding"):
            msg = {}
            msg["Start"] = self.jid_
            msg["Destiny"] = self.recipient
            msg["Jumps"] = 0
            msg["Distance"] = 0
            msg["List_of_Nodes"] = []
            msg["Message"] = self.msg
            msg["ID"] = str(uuid.uuid4())
            self.lastid.append(msg["ID"])

            
            receivers, message = self.calculate(json.dumps(msg), self.jid_)
            
            if (message != 'salir') and len(message) > 0:
                for receiver in receivers:
                    self.send_message(mto=receiver, mbody=message, mtype='chat')
            elif message == 'salir':
                print(Fore.MAGENTA+"Adios!!!"+ Style.RESET_ALL)
                self.disconnect
            else:
                pass

    async def message(self, msg):
        if(self.routing == "flooding"):
            if msg['type'] in ('normal', 'chat'):
                recipient = str(msg['from']).split('/')[0]
                body = msg['body']
                msg = eval(str(body))
                if(msg["ID"] not in self.lastid):
                    self.lastid.append(msg["ID"])

                    print(Fore.MAGENTA + "Nuevo mensaje! >> " + Style.RESET_ALL, msg["Message"])
                    # print(Fore.MAGENTA + "Nuevo mensaje! >> " + Style.RESET_ALL, msg["Message"], Fore.GREEN + '\nSaltos:'  + Style.RESET_ALL, msg["Jumps"], Fore.GREEN + ' Distancia:'  + Style.RESET_ALL, msg["Distance"],'\n')

                    receivers, message = self.calculate(str(body), self.jid_)

                    for receiver in receivers:

                        if(receiver!=recipient):
                            self.send_message(mto=receiver, mbody=message, mtype='chat')

    def get_JID(self,ID):
        if(self.names_info["type"]=="names"):
            names = self.names_info["config"]
            JID = names[ID]
            return JID

    def calculate(self, message, sender):
        start_time = time.time()
        info = eval(message)
        info["Jumps"] = info["Jumps"] + 1
        
        if(self.names_info["type"]=="names"):
            names = self.names_info["config"]
            JIDS = {v: k for k, v in names.items()}
            name = JIDS[sender]

        if(self.topo_info["type"]=="topo"):
            names = self.topo_info["config"]
            neighbors_IDs = names[name]
            neighbors_JIDs = [self.get_JID(i) for i in neighbors_IDs]
        
        nodes = neighbors_JIDs
        info["List_of_Nodes"] = [info["List_of_Nodes"], nodes]
        info["Distance"] = info["Distance"] - start_time + time.time()
        return nodes, json.dumps(info)

