"""
Redes de Computadores 1
Jogo distribuido da forca

Author: Rodrigo Oliveira e Hyago Henrique
"""

#npy
#import npyscreen

import socket
from _thread import *
import threading
import time


#portas
anuncio_do_jogo_broadcast = 4000 #porta para anuncio de novo jogo e início do jogo
conexoes_jogo_tcp = 4002 #porta para conexao no jogo sobre TCP



#variaveis de controle
controle_procurando_jogadores = b'procurando'
conectar_ao_jogo = b'conectar'
iniciar_jogo = "init"
tipo_jogo = 0
tipo_jogador = 1

dica_global = " "
#variaveis compartilhadas
evento_iniciar_jogo = threading.Event()
#trava_escutar_tcp = 

#funcao para recuperar ip do host
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
    local_ip_address = s.getsockname()[0]
    return local_ip_address


class Payload:
    def __init__(self, iniciar_jogo = "N", finalizar_jogo = "N", dica = "N", ganhador = "N", palavra = "N", chute ="N", letra = "N", str = "N"):
        self.iniciar_jogo = iniciar_jogo
        self.finalizar_jogo = finalizar_jogo
        self.dica = dica
        self.ganhador = ganhador
        self.palavra = palavra

        self.chute = chute
        self.letra = letra

        if(str != "N"):
            self.new_from_str(str)
    def new_from_str(self, str):
        array = str.split("#")
        self.iniciar_jogo = array[0]
        self.finalizar_jogo = array[1]
        self.dica = array[2]
        self.ganhador = array[3]
        self.palavra = array[4]
        self.chute = array[5]
        self.letra = array[6]
    def __str__(self):
        return self.iniciar_jogo+"#"+self.finalizar_jogo+"#"+self.dica+"#"+self.ganhador+"#"+self.palavra+"#"+self.chute+"#"+self.letra


payload = Payload()
class Jogo:
    #construtor
    #passando por parâmetro ao construir objeto
    #palavra do jogo e dica inicial
    def __init__(self, palavra, dica_inicial):
        self.palavra = palavra
        self.dica_inicial = dica_inicial
        self.dicas = []
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

        self.jogadores = []
        self.ganhador = ""
        self.evento_procurar_jogadores = threading.Event()
        self.evento_aguardar_jogadores = threading.Event()
        self.evento_fim_do_jogo = threading.Event()
        self.evento_enviar_payload = threading.Event()


    def procurar_jogadores(self):
        global evento_procurar_jogadores
        message = get_ip().encode('ascii')
        while True:
            if self.evento_procurar_jogadores.is_set():
                #print("debug: trava ativada, saindo e desativando trava.\n")
                break
            self.broadcast.sendto(message, ('<broadcast>', anuncio_do_jogo_broadcast))
            #print("debug: mensagem de broadcast enviada.\n")
            time.sleep(5)
        self.evento_procurar_jogadores.clear()
        self.broadcast.close()
    
    def aguardar_jogadores(self):
        global evento_aguardar_jogadores
        #coloca socket pra escutar
        self.tcp_socket.listen(5)

        while True:
            if self.evento_aguardar_jogadores.is_set():
                # caso a variável de trava seja acionada
                print("debug: trava ativada, saindo e desativando trava.\n")
                break

            #realiza conexão em nova thread
            client, address = self.tcp_socket.accept() 
            print("debug: conectou tcp aguardar_jogadores.\n")
            self.jogadores.append(address)
            novaThread = threading.Thread(target=self.conectar_ao_jogador,  args=(client, address))
            novaThread.start()
            
        self.evento_aguardar_jogadores.clear()

    def conectar_ao_jogador(self, client, address):
        global dica_global
        dicasEnviadas = []
        #print("Conectado com: %s, aguardando início do jogo."%client.getpeername())
        evento_iniciar_jogo.wait()
        #payload enviado com dica inicial e iniciando o jogo
        fpayload = Payload("1", "N", self.dica_inicial)
        print("Payload:", fpayload)
        try:
            client.send(str(fpayload).encode('ascii'))
            print("PAYLOAD ENVIADO")
        except:
            print("erro no socket ao conectar ao jogador")
        while True:
            print("esperando requisições")
            data = client.recv(1024)
            if not data:
                print("Conexão finalizada.")
                break
            else:
                if self.evento_fim_do_jogo.is_set():
                    ganhador = Payload(ganhador=str(self.ganhador), palavra=self.palavra)
                    client.send(str(ganhador).encode('ascii'))
                    #REMOVER DO ARRAY DE JOGADORES
                    print("JOGO ACABOU")
                payload = Payload(str = data.decode('ascii'))
                #print("entrou no elseeeee")
                if(payload.chute != "N"):
                    if payload.chute == self.palavra:
                        ganhador = Payload(ganhador="1", palavra=self.palavra)
                        self.ganhador = address
                        client.send(str(ganhador).encode('ascii'))
                        self.evento_fim_do_jogo.set()
                    else:
                        response = Payload(chute="0")
                        client.send(str(response).encode('ascii'))
                
    def iniciar_jogo(self):
        evento_iniciar_jogo.set()


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
            data = self.tcp_socket.recv(1024)
            print("Iniciando jogo... \nDica inicial: {0}".format(Payload(str=data.decode('ascii')).dica))
            while True:
                escolha = input("Escolha uma opção: Letra = 0, Chute = 1")
                if escolha == "0":
                    letra = input("Digite a letra: ")
                    fpayload = Payload(letra=letra)
                    print("Payload:", fpayload)
                    self.tcp_socket.send(str(fpayload).encode('ascii'))
                    self.tcp_socket.recv(1024)
                elif escolha == "1":
                    chute = input("Digite o chute: ")
                    fpayload = Payload(chute=chute)
                    print("Payload:", fpayload)
                    self.tcp_socket.send(str(fpayload).encode('ascii'))
                    data = self.tcp_socket.recv(1024)
                    recebido = Payload(str=data.decode('ascii'))
                    if(recebido.ganhador != "N"):
                        if(recebido.ganhador == "1"):
                            print("Você acertou a palavra: {0}, finalizando jogo".format(recebido.palavra))
                            break
                        else:
                            print("{0} acertou a palavra, jogo finalizado.".format(recebido.ganhador))
                            break
                    elif(recebido.chute == "0"):
                        print("Você errou o chute.")
                
            
        except:
            print("ERRO! Não foi possível conectar ao jogo. ")



if __name__ == "__main__":
    #global evento_aguardar_jogadores
   # global evento_procurar_jogadores
    tipo = input("Digite o tipo: C - Coordenador, J - Jogador.")
    if tipo == "C":
        jogo = Jogo("casa","novaDica")
        print("Novo jogo criado...")
        tempo = int(input("Digite por quanto tempo aguardar jogadores (segundos): "))
        print("Aguardando jogadores...")
        novaThread = threading.Thread(target=jogo.aguardar_jogadores)
        novaThread.start()
        novaThread = threading.Thread(target=jogo.procurar_jogadores)
        novaThread.start()
        
        for x in range(0, tempo//5):
            time.sleep(5)
            print("Jogadores conectados:")
            print(jogo.jogadores)

        
        #finalizar threads
        print("Finalizando threads:")
        jogo.evento_procurar_jogadores.set()
        jogo.evento_aguardar_jogadores.set()
        jogo.iniciar_jogo()
        while True:
            opcao = input("Selecione uma opção: ")
            if opcao == "1":
                dica = input("Digite a dica: ")
                dica_global = dica
                jogo.evento_enviar_payload.set()
                


    elif tipo =="J":
        jogador = Jogador()
        print("Procurando jogo...")
        jogador.procurarJogo()
        #while True:
    else:
        print("Opção inválida, saindo")
        exit()
            

