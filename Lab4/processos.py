import os
import rpyc
import multiprocessing
from multiprocessing.dummy import Process
from rpyc.utils.server import ThreadedServer
from random import randint
LOCK = multiprocessing.Lock()
MAX_NUMERO_NOS = 4 #nº de nós no sistema
SERVER = 'localhost'
PORTA_BASE = 6000 #porta da ao nó de id 0
ACK = -1 #constante de ACK
#### Constantes representados os estados que um nó pode estar ####
INICIO = 0 # Não está em eleição
COMECOU_VOTACAO = 1 # Começou a realizar probe
AGUARDANDO_RESULTADO = 2 # Espera o nó que iniciou a eleição divulgar o vencedor (Exclusivo para os nós que não começaram a eleição)
DIVULGANDO_RESULTADO = 3 # Nó recebeu todos os echos (Exclusivo para o nó que começou a eleição)
TERMINADA_ELEICAO = 4 #Recebeu o novo líder
identificadoresDisponiveis = list(range(0, MAX_NUMERO_NOS))
nosAtivos = {}
estados = {}
conexoes = {}
candidatos = {}
numEsperas = {}
pais = {}

#gera um número entre (máximo - 1) e 0
def gerarIndice(maximo):
    return randint(0, maximo-1)

#gera a porta que hospeda o nó baseado em seu id
def gerarPorta(identificador):
    return PORTA_BASE + identificador

#escolhe um id para o nó a partir dos possíveis valores ainda não escolhidos
def gerarIdentificador():
    index = gerarIndice(len(identificadoresDisponiveis))
    LOCK.acquire()
    identificador = identificadoresDisponiveis[index]
    identificadoresDisponiveis.remove(identificador)
    nosAtivos[identificador] = gerarPorta(identificador)
    LOCK.release()
    return identificador

#O vizinhos de um nó são definidos como o nó de id anterior (se possível) e sucessor (se possível)
def gerarVizinhos(identificador):
    vizinhos = {}
    if identificador - 1 >= 0: #verifica se existe id válido anterior
        vizinhos[identificador-1] = gerarPorta(identificador-1)
    if identificador + 1 < MAX_NUMERO_NOS:#verifica se existe id válido sucessor
        vizinhos[identificador+1] = gerarPorta(identificador+1)
    return vizinhos

# inicia a conexão com um servidor
def iniciarConexao(porta):
    conexao = rpyc.connect(SERVER, port=porta)
    return conexao

def iniciarServidor(classe,porta):
    srv = ThreadedServer(classe, port=porta)
    srv.start()


#Definição de valores de um nó que devem ser inicializados antes de uma eleição
def inicializarNo(identificador):
    candidatos[identificador] = identificador
    estados[identificador] = INICIO
    pais[identificador] = None

#Retorna certos valores de um um nó ao estado pré eleição
def reset():
    for identificador in range(MAX_NUMERO_NOS):
        candidatos[identificador] = identificador
        estados[identificador] = INICIO
        pais[identificador] = None


def processo():
    identificador = gerarIdentificador()
    inicializarNo(identificador)

    class No(rpyc.Service):
        identificacao = identificador #identificador do nó
        porta = gerarPorta(identificacao) # porta do nó
        vizinhos = gerarVizinhos(identificacao) # nós vizinhos
        lider = None # lider da aplicação
      
        def on_connect(self, conn):
            return super().on_connect(conn)

        def on_disconnect(self, conn):
            return super().on_disconnect(conn)

        def shouldEcho(self):
            if numEsperas[self.identificacao] == 0:
                return True
            else:
                return False

        def temPai(self):
            if pais[self.identificacao] != None:
                return True
            else:
                return False

        def sendEcho(self):
            global estados
            if self.temPai():
                conexoesAtivas = conexoes[self.identificacao]
                conexaoPai = conexoesAtivas[pais[self.identificacao]]
                conexaoPai.root.echo(candidatos[self.identificacao])
                estados[self.identificacao] = AGUARDANDO_RESULTADO
            else:
                estados[self.identificacao] = DIVULGANDO_RESULTADO

        def exposed_probe(self, pai):
            global estados
            global conexoes
            if (estados[self.identificacao] == INICIO):
                estados[self.identificacao] = COMECOU_VOTACAO #muda o estado do nó
                pais[self.identificacao] = pai
                numEsperas[self.identificacao] = len(self.vizinhos) #len(self.vizinhos) - 1 if self.temPai() else len(self.vizinhos)
                conexoes[self.identificacao] = {}
                for vizinho in self.vizinhos:
                    endereco = self.vizinhos[vizinho]
                    conexao = iniciarConexao(endereco)
                    conexoes[self.identificacao][vizinho] = conexao
                for conexao in conexoes[self.identificacao].values(): 
                    try:
                        if(conexao.root.probe(self.identificacao)==ACK):
                            self.exposed_ack()
                    except Exception as e:
                        print(str(e.args) + "\n Nó: " +
                              str(self.identificacao))
                        numEsperas[self.identificacao] -= 1
                if (self.shouldEcho()):
                    self.sendEcho()

            else:
                return ACK
                # try:
                #     if(pais[self.identificacao] != None):
                #         print(self.identificacao)
                #         conexoesAtivas = conexoes[self.identificacao]
                #         conexaoPai = conexoesAtivas[pai]
                #         conexaoPai.root.ack()
                # except Exception as e:
                #     print(e.args)
                    

        def exposed_echo(self, candidato):
            numEsperas[self.identificacao] -= 1
            if (candidato > candidatos[self.identificacao]):
                candidatos[self.identificacao] = candidato
            if(self.shouldEcho()):
                self.sendEcho()
        #método de ACK
        def exposed_ack(self):
            numEsperas[self.identificacao] -= 1
            if(self.shouldEcho()):
                self.sendEcho()

        def exposed_divulgarResultado(self, vencedor):
            if(estados[self.identificacao] == DIVULGANDO_RESULTADO or estados[self.identificacao] == AGUARDANDO_RESULTADO):
                estados[self.identificacao] = TERMINADA_ELEICAO #muda o estado do nó
                self.lider = vencedor # atualiza o lider
                try:
                    for conexao in conexoes[self.identificacao].values(): # passa o resultado adiante
                        conexao.root.divulgarResultado(vencedor)
                        conexao.close()
                except Exception as e:
                    print(e.args)

        def exposed_iniciarEleicao(self):
            global estados
            self.exposed_probe(None)
            while estados[self.identificacao] != DIVULGANDO_RESULTADO: # aguarda receber todos os ECHOS
                pass 
            self.lider = candidatos[self.identificacao]
            self.exposed_divulgarResultado(candidatos[self.identificacao])

        def exposed_mostrarLider(self):
            existeLider = True if self.lider != None else False
            if(existeLider):
                print("Nó " + str(self.identificacao) +
                      "diz que Nó " + str(self.lider) + " é o líder")
            else:
                self.exposed_iniciarEleicao()
                print("Nó " + str(self.identificacao) +
                      " diz que Nó " + str(self.lider) + " é o líder")
                reset()
    # server = threading.Thread(target=iniciarServidor, args=(No,No.porta,))
    # server.start()
    srv = ThreadedServer(No, port=No.porta)
    srv.start()


if __name__ == "__main__":
    for i in range(0, MAX_NUMERO_NOS):
        p = Process(target=processo)
        p.start()
    while True:
        noAlvo = input()
        if noAlvo == "fim":
            os._exit(0)
        
        noAlvo = int(noAlvo)
        conexao = iniciarConexao(PORTA_BASE + noAlvo)
        conexao.root.mostrarLider()
