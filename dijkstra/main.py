from getpass import getpass
from linkStateRouting import *

# Driver and program starting point.
if __name__ == '__main__':
    print("## Chat de Link State Routing ##\n")
    jid = input('Ingresar el jid: ')
    pswd = getpass('Ingresar contraseña: ')
    namesFileName = input('Ingresar el nombre del archivo que contiene los nombres: ')
    topologyFileName = input('Ingresar el nombre del archivo de la topología: ')

    xmpp = LSRClient(jid, pswd, topologyFileName, namesFileName)
    xmpp.connect()
    xmpp.process(forever=False)