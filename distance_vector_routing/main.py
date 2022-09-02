from client import Client
import yaml
import networkx as nx
from aioconsole import ainput
from colorama import Fore, Style


def nodos_grafo(topo, names, user):
    for key, value in names["config"].items():
        if user == value:
            return key, topo["config"][key]

async def main(xmpp: Client):
    menu = True
    while menu:
        print(Fore.MAGENTA + """

        +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        -                                                      -
        +               DISTANCE VECTOR ROUTING                +
        -                                                      - 
        +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

            1. Continuar
            2. Salir

        """ + Style.RESET_ALL)

        op_1 = await ainput(Fore.GREEN+"Ingresar número correspondiente a la opción deseada >>> "+ Style.RESET_ALL)

        if op_1 == '1':
            print(Fore.BLUE + Style.DIM + "\nRecordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
            user_name = await ainput(Fore.GREEN +"¿Con quién desea chatear? >>> "+ Style.RESET_ALL)

            print(Fore.BLUE + Style.DIM + "\n* Escriba salir para regresar al menu principal *"+ Style.RESET_ALL) 
            activo = True

            while activo:
    
                mensaje = await ainput(Fore.BLUE +"Escriba un mensaje >>> "+ Style.RESET_ALL)

                if (mensaje != 'salir') and len(mensaje) > 0:
                    if xmpp.algoritmo == '1':
                        mensaje = "1|" + str(xmpp.jid) + "|" + str(user_name) + "|" + str(xmpp.grafo.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
                        
                        shortest_neighbor_node = xmpp.camino_c(user_name)
                        if shortest_neighbor_node:
                            if shortest_neighbor_node[1] in xmpp.vecinos:

                                xmpp.send_message(
                                    mto = xmpp.names[shortest_neighbor_node[1]],
                                    mbody = mensaje,
                                    mtype = 'chat' 
                                )
                            else:
                                pass
                        else:
                            pass
                    else:
                        xmpp.send_message(
                            mto = user_name,
                            mbody = mensaje,
                            mtype = 'chat' 
                        )
                elif mensaje == 'salir':
                    activo = False
                else:
                    pass

        elif op_1 == '1':
            menu = False
            xmpp.disconnect()

        else:
            pass


if __name__ == "__main__":

    r_t = open("topologia.txt", "r", encoding="utf8").read()
    r_n = open("names.txt", "r", encoding="utf8").read()

    topologia = yaml.load(r_t, Loader=yaml.FullLoader)
    nombres = yaml.load(r_n, Loader=yaml.FullLoader)

    print(Fore.MAGENTA + """

        +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        -                                                      -
        +                       ALUMCHAT                       +
        -                                                      - 
        +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        """ + Style.RESET_ALL)

    print(Fore.BLUE + Style.DIM + "Recordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
    jid = input(Fore.GREEN + "Usuario >>> "+ Style.RESET_ALL)
    contra = input(Fore.GREEN +"Contraseña >>> "+ Style.RESET_ALL)

    grafo_pos = {}
    source = None

    # se extrae el grafo
    for key, value in topologia['config'].items():
        grafo_pos[key] = {}
        for node in value:
            grafo_pos[key][node] = float('inf')
            if nombres['config'][node] == jid:
                source = node

    # se almacena la topologia de la red en un grafo
    grafo = nx.DiGraph()

    grafo.add_nodes_from(grafo.nodes(data=True))
    grafo.add_edges_from(grafo.edges(data=True))

    for key, value in nombres["config"].items():
        grafo.add_node(key, jid=value)
        
    for key, value in topologia["config"].items():
        for i in value:
            grafo.add_edge(key, i, weight=1)

    
    nodo, nodes = nodos_grafo(topologia, nombres, jid)

    xmpp = Client(jid, contra, "1", nodo, nodes, nombres["config"], grafo, grafo_pos, source)
    xmpp.connect() 
    xmpp.loop.run_until_complete(xmpp.connected_event.wait())
    xmpp.loop.create_task(main(xmpp))
    xmpp.process(forever=False)
    