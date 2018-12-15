"""
Redes de Computadores 1
Jogo distribuido da forca

Author: Rodrigo Oliveira e Hyago Henrique
"""

#npy
import npyscreen

import socket
from _thread import *
import threading
import time


#portas
anuncio_do_jogo_broadcast = 4000 #porta para anuncio de novo jogo e início do jogo
conexoes_jogo_tcp = 4001 #porta para conexao no jogo sobre TCP



#variaveis de controle
controle_procurando_jogadores = b'procurando'
conectar_ao_jogo = b'conectar'
tipo_jogo = 0
tipo_jogador = 1

#variaveis compartilhadas
# -> variaveis de trava
trava_procurar_jogadores = False
trava_aguardar_jogadores = False
trava_iniciar_jogo = threading.Condition()
#trava_escutar_tcp = 

#funcao para recuperar ip do host
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
    local_ip_address = s.getsockname()[0]
    return local_ip_address


#interfaces
class Inicio(npyscreen.Form):
    def create(self):
       self.tipo_de_par = self.add(npyscreen.TitleSelectOne, name= "Você deseja: ", values = ["Jogar","Coordenar"], scroll_exit=True)
    
    def activate(self):
        self.edit()
        if self.tipo_de_par.value[0] == 0:
            self.parentApp.setNextForm(PROCURANDO_JOGADORES)


class ProcurandoJogadores(npyscreen.Form):
    def create(self):
        self.texto_procurando_jogadores = self.add(npyscreen.TitleText, name="Procurando jogadores... ",)
        self.texto_jogadores_conectados = self.add(npyscreen.FixedText, name="Jogadores conectados: \n\tlocalhost:4556 \n\tlocalhost:4984 ",)
    
    def activate(self):
        self.edit()
        self.parentApp.setNextForm(None)


#app
class Forca(npyscreen.NPSAppManaged):
   def onStart(self):
       self.addForm('MAIN', Inicio, name='Forca p2p')
       self.addForm('PROCURANDO_JOGADORES', ProcurandoJogadores, name="Procurando jogadores")
       # A real application might define more forms here.......
       



    

    





class Jogo:
    #construtor
    #passando por parâmetro ao construir objeto
    #palavra do jogo e dica inicial
    def __init__(self, palavra, dica_inicial):
        self.palavra = palavra
        self.dica_inicial = dica_inicial
        #cria sockets

        #UDP
        #define socket como IPV4, usando Datagramas, protocolo UDP
        self.broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        #adiciona opção de broadcast ao socket
        self.broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        #adiciona opção para poder reusar o endereço 
        self.broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ##timeout
        self.broadcast.settimeout(0.2)

        #TCP
        #criando socket tcp
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind(("", conexoes_jogo_tcp))

    def procurar_jogadores(self):
        global trava_procurar_jogadores
        message = get_ip().encode('ascii')
        while True:
            if trava_procurar_jogadores:
                #print("debug: trava ativada, saindo e desativando trava.\n")
                break
            self.broadcast.sendto(message, ('<broadcast>', anuncio_do_jogo_broadcast))
            #print("debug: mensagem de broadcast enviada.\n")
            time.sleep(5)
        trava_procurar_jogadores = False
        self.broadcast.close()
    
    def aguardar_jogadores(self):
        global trava_aguardar_jogadores
        #coloca socket pra escutar
        self.tcp_socket.listen(5)

        while True:
            if trava_aguardar_jogadores:
                # caso a variável de trava seja acionada
                print("debug: trava ativada, saindo e desativando trava.\n")
                break

            #realiza conexão em nova thread
            client, address = self.tcp_socket.accept() 
            print("debug: conectou tcp aguardar_jogadores.\n")
            novaThread = threading.Thread(target=self.conectar_ao_jogador,  args=(client, address))
            novaThread.start()
            
        trava_aguardar_jogadores = False

    def conectar_ao_jogador(self, client, address):
        print("\nJogando com: ", client.getpeername())
        while True:
            data = client.recv(1024)
            print("%s" %data.decode('ascii'))
            time.sleep(4)
            self.tcp_socket.send("Pong".encode('ascii'))
        #trava_iniciar_jogo.wait()
        #iniciar jogo...
        #fechar sockets

    def iniciar_jogo(self):
        trava_iniciar_jogo.notify_all()


class Jogador:
    #construtor
    def __init__(self):
        #UDP
        
        self.udp_sockt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.udp_sockt.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # opção para poder reusar o endereço -> ler mais sobre
        self.udp_sockt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_sockt.bind(("", anuncio_do_jogo_broadcast))

        #TCP
        #criando socket tcp
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def procurarJogo(self):
        try:
            data, addr = self.udp_sockt.recvfrom(1024)
            print("Jogo encontrado...\n Conectando...")
            endereco = data.decode('ascii')
            print("Endereço para conexão: %s:%s"%(endereco, conexoes_jogo_tcp))
            novaThread = threading.Thread(target=self.jogar, args=(data, ))
            novaThread.start()
        except:
            print("ERRO AO PROCURAR JOGO")
        


    def jogar(self, endereco):
        try:
            self.tcp_socket.connect((endereco, conexoes_jogo_tcp))
            print("Conectado!")
            while True:
                self.tcp_socket.send("Ping".encode('ascii'))
                data = self.tcp_socket.recv(1024)
                print("%s" %data.decode('ascii'))
        except:
            print("ERRO! Não foi possível conectar ao jogo. ")



        
    







if __name__ == "__main__":

    TestApp = Forca().run()


    
    """
    tipo = input("Digite o tipo: C - Coordenador, J - Jogador.")
    if tipo == "C":
        jogo = Jogo("helloWorld","novaDica")
    else:
        jogador = Jogador()
    while True:
        opcao = int(input("Digite a opcao desejada:"))
        if opcao == 0 and tipo == "C":
            novaThread = threading.Thread(target=jogo.procurar_jogadores)
            novaThread.start()
        if opcao == 1 and tipo == "C":
            trava_procurar_jogadores = True
        if opcao == 2 and tipo == "C":
            novaThread = threading.Thread(target=jogo.aguardar_jogadores)
            novaThread.start()
        if opcao == 3 and tipo == "C":
            trava_aguardar_jogadores = True
        if opcao == 4 and tipo == "J":
            jogador.procurarJogo()
    """
            

