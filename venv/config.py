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

#variaveis compartilhadas
# -> variaveis de trava
trava_procurar_jogadores = False
trava_aguardar_jogadores = False
trava_iniciar_jogo = threading.Condition()
#trava_escutar_tcp = 