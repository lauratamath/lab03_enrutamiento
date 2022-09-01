# Referencias
# https://slixmpp.readthedocs.io/en/latest/getting_started/sendlogout.html
# https://slixmpp.readthedocs.io/en/latest/event_index.html

import yaml
import networkx as nx
import random

from networkx.algorithms.shortest_paths.generic import shortest_path
from aioconsole import ainput
from getpass import getpass
from colorama import Fore, Style
from client import Client


# Almacenamiento de la topologia de la red

def grafo_final(topologia, nombres):
    grafo = nx.Graph()
    for key, value in nombres["config"].items():
        grafo.add_node(key, jid=value)

    for key, value in topologia["config"].items():
        for i in value:
            weightA = random.uniform(0, 1)
            grafo.add_edge(key, i, weight=weightA)
    
    return grafo
    
# Gestionamiento del cliente
async def main(xmpp: Client):
    menu = True
    # origin = ""
    # destiny = ""
    while menu:
        print("""
        +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+
        -                                      -
        +              ALUMCHAT                +
        -                                      - 
        +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+

            1. Continuar
            2. Salir

        """)

        op_1 = await ainput("Ingresar número correspondiente a la opción deseada >>> "+ Style.RESET_ALL)

        if op_1 == '1':
            print(Fore.BLUE + Style.DIM + "\nRecordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
            user_name = await ainput(Fore.GREEN +"¿Con quién desea chatear? >>> "+ Style.RESET_ALL)

            activo = True
            while activo:
                mensaje = await ainput("Escriba un mensaje >>> ")

                if (xmpp.algoritmo == '1'):
                    mensaje = "msg|" + str(xmpp.jid) + "|" + str(user_name) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
                    for i in xmpp.nodos:
                        xmpp.send_message(
                            mto = xmpp.nombres[i],
                            mbody = mensaje,
                            mtype = 'chat' 
                        )

                elif (xmpp.algoritmo == '2'):
                    mensaje = "msg|" + str(xmpp.jid) + "|" + str(user_name) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
        

                else:
                    xmpp.send_message(
                        mto = user_name,
                        mbody = mensaje,
                        mtype = 'chat' 
                    )

        elif op_1 == '2':
            menu = False
            xmpp.disconnect()
        else:
            pass


if __name__ == "__main__":
    r_t = open("topologia.txt", "r", encoding="utf8").read()
    r_n = open("names.txt", "r", encoding="utf8").read()

    topologia = yaml.load(r_t, Loader=yaml.FullLoader)
    nombres = yaml.load(r_n, Loader=yaml.FullLoader)

    print("\n            Bienvenido al servidor")
    print(Fore.BLUE + Style.DIM + "Recordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
    jid = input(Fore.GREEN + "Usuario >>> "+ Style.RESET_ALL)
    contra = getpass(Fore.GREEN +"Contraseña >>> "+ Style.RESET_ALL)
    print("1. Flooding")
    algoritmo_opt = input("\nElija la opción del algoritmo que desea utilizar: ") 


    for key, value in nombres["config"].items():
        print("no entra ac")
        print('esto es jid ' + jid)
        print('esto es key ' + value)
        if jid == value:
            print("no entra acaaa")
            nodo = key
            nodos = topologia["config"][key]

    xmpp = Client(jid, contra, algoritmo_opt, nodo, nodos, nombres["config"], grafo_final(topologia, nombres))

    xmpp.connect() 
    xmpp.loop.run_until_complete(xmpp.connected_event.wait())
    xmpp.loop.create_task(main(xmpp))
    xmpp.process(forever=False)