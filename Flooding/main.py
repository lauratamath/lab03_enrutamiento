from getpass import getpass
from Client import *
import asyncio
import sys
from colorama import Fore, Style

#Small fix that allows the program to run on windows operating systems due to an error with the asyncio library
if sys.platform == 'win32' and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == '__main__':
    print(Fore.MAGENTA + """

        +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        -                                                      -
        +               DISTANCE VECTOR ROUTING                +
        -                                                      - 
        +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

            1. Continuar
            2. Salir

        """ + Style.RESET_ALL)
    print("\n            Bienvenido al servidor")
    print(Fore.BLUE + Style.DIM + "Recordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
    jid = input(Fore.GREEN + "Usuario >>> "+ Style.RESET_ALL)
    password = getpass(Fore.GREEN +"Contraseña >>> "+ Style.RESET_ALL)
    routing = "flooding"
    
    listening = False
    if routing != "flooding":
        listening = True
        
    names_file = input(Fore.GREEN + "URL relativa del file de names >>> "+ Style.RESET_ALL)
    topology_fil = input(Fore.GREEN + "URL relativa del file de topología: "+ Style.RESET_ALL)

    try:
        recipient = ''
        message = ''

        if(not listening):
            recipient = input(Fore.GREEN + "Destinatario >>> "+ Style.RESET_ALL) 
            message = input(Fore.GREEN + "Mensaje >>> "+ Style.RESET_ALL)

        xmpp = Client(jid, password, recipient, message, routing, listening, names_file, topology_fil)
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0199') # XMPP Ping
        xmpp.register_plugin('xep_0045') # Mulit-User Chat (MUC)
        xmpp.register_plugin('xep_0096') # Jabber Search
        xmpp.register_plugin('xep_0077') ### Band Registration
        xmpp.connect()
        xmpp.process(forever=False)
        
    except KeyboardInterrupt as e:
        pass 