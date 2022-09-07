from client import Client
from colorama import Fore, Style

if __name__ == '__main__':

    r_n = open("./dijkstra/names.txt", "r").read()
    r_t = open("./dijkstra/topologia.txt", "r").read()
    names_info = eval(r_n)
    topo_info = eval(r_t)

    print(Fore.MAGENTA + """
        ########################################################
        #                     ALUMCHAT.FUN                     #
        ########################################################
        """ + Style.RESET_ALL)

    print(Fore.BLUE + Style.DIM + "Recordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
    jid = input(Fore.GREEN + "Usuario >>> "+ Style.RESET_ALL)
    contra = input(Fore.GREEN +"Contraseña >>> "+ Style.RESET_ALL)

    xmpp = Client(jid, contra, topo_info, names_info)
    xmpp.connect()
    xmpp.process(forever=False)
