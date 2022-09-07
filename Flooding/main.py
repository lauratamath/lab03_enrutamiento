import sys
from client import *

if __name__ == '__main__':

    print(Fore.BLUE + Style.DIM + "Recordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
    jid = input(Fore.GREEN + "Usuario >>> "+ Style.RESET_ALL)
    jid += "@alumchat.fun"
    password = input(Fore.GREEN +"Contraseña >>> "+ Style.RESET_ALL)

    r_n = open("names.txt", "r").read()
    r_t = open("topologia.txt", "r").read()
    names_info = eval(r_n)
    topo_info = eval(r_t)

    user_name = ''
    message = ''
    
    menu = True
    
    print(Fore.MAGENTA + """

    +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    -                                                      -
    +                   FLOODING ROUTING                   +
    -                                                      - 
    +-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        1. Continuar
        2. Salir

    """ + Style.RESET_ALL)

    op_1 = input(Fore.GREEN+"Ingresar número correspondiente a la opción deseada >>> "+ Style.RESET_ALL)
    
    if op_1 == '1':
        print(Fore.BLUE + Style.DIM + "\nRecordatorio: usuario + @alumchat.fun"+ Style.RESET_ALL) 
        user_name = input(Fore.GREEN +"¿Con quién desea chatear? >>> "+ Style.RESET_ALL) 
        user_name += "@alumchat.fun"

        print(Fore.BLUE + Style.DIM + "\n* Escriba salir para regresar al menu principal *"+ Style.RESET_ALL) 
        
        message = input(Fore.BLUE +"Escriba un mensaje >>> "+ Style.RESET_ALL)
            
    elif op_1 == '2':
        print(Fore.MAGENTA+"Adios!!!"+ Style.RESET_ALL)
        sys.exit()

    else:
        pass

    xmpp = Client(jid, password, user_name, message, names_info, topo_info)
    xmpp.connect()
    xmpp.loop.run_until_complete(xmpp.connected_event.wait())
    xmpp.process(forever=False)
        