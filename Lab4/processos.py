from glob import glob
from multiprocessing.dummy import Process
import time
import rpyc
import multiprocessing
import threading
from rpyc.utils.server import ThreadedServer
from random import randint
LOCK = multiprocessing.Lock()
MAX_NUMERO_NOS = 2
SERVER = 'localhost'
INICIO = 0
COMECOU_VOTACAO = 1
AGUARDANDO_RESULTADO = 2
TERMINADA_ELEICAO = 3
identificadoresDisponiveis = list(range(0, MAX_NUMERO_NOS))
nosAtivos = {}
estados = {}
conexoes = {}

def gerarIndice(maximo):
    return randint(0, maximo-1)


def gerarPorta(identificador):
    return 6000 + identificador


def gerarIdentificador():
    # randint(0, len(identificadoresDisponiveis)-1)
    index = gerarIndice(len(identificadoresDisponiveis))
    LOCK.acquire()
    identificador = identificadoresDisponiveis[index]
    identificadoresDisponiveis.remove(identificador)
    nosAtivos[identificador] = gerarPorta(identificador)
    LOCK.release()
    return identificador


def gerarVizinhos(identificador):
    vizinhos = {}
    if identificador - 1 >= 0:
        vizinhos[identificador-1] = gerarPorta(identificador-1)
    if identificador + 1 < MAX_NUMERO_NOS:
        vizinhos[identificador+1] = gerarPorta(identificador+1)
    return vizinhos


def iniciarServidor(classe, porta):
    srv = ThreadedServer(classe, port=porta)
    srv.start()


def iniciarConexao(porta):
    conexao = rpyc.connect(SERVER, port=porta)
    raiz = conexao.root
    return conexao, raiz


def processo():
    identificador = gerarIdentificador()
    numeroVotos = None
    numEspera = None
    candidate = identificador
    estados[identificador] = INICIO
    class No(rpyc.Service):
        identificacao = identificador
        porta = gerarPorta(identificacao)
        vizinhos = gerarVizinhos(identificacao)
        numVotos =numeroVotos
        lider = None
        exposed_pai = None
        numeroEspera = numEspera
        candidato = candidate
        # jaVotou = False
        # estado = 0
        # jaRecebeuResultado = False

        def on_connect(self,conn):
            return super().on_connect(conn)

        def on_disconnect(self,conn):
            return super().on_disconnect(conn)

        def shouldEcho(self):
            if self.numeroEspera == 0:
                return True
            else:
                return False

        def temPai(self):
            if self.pai != None:
                return True
            else:
                return False

        def sendEcho(self):
            global estados
            if self.temPai():
                conexao, raiz = iniciarConexao(self.vizinhos[self.pai])
                rpyc.async_(raiz.echo(self.candidato))
                estados[self.identificacao] = AGUARDANDO_RESULTADO
                conexao.close()
            else:
                estados[self.identificacao] = TERMINADA_ELEICAO

        def exposed_probe(self, pai):
            global estados
            global conexoes
            if (estados[self.identificacao] == INICIO):
                estados[self.identificacao] = COMECOU_VOTACAO
                self.pai = pai
                self.numeroEspera = len(self.vizinhos) - \
                    1 if self.temPai() else len(self.vizinhos)
                print("no " + str(self.identificacao) + "espera " + str(self.numeroEspera))
                conexoes[self.identificacao] = []
                for endereco in self.vizinhos.values():
                    try:
                        conexao, raiz = iniciarConexao(endereco)
                        conexoes[self.identificacao].append(conexao)
                        #raiz.exposed_pai = self.identificacao
                        #rpyc.async_(raiz.probe(self.identificacao))
                        #raiz.probe(self.identificacao)
                        conexao.close()
                    except Exception as  e:
                        print(e.args)
                        self.numeroEspera -= 1
                if (self.shouldEcho()):
                    self.sendEcho()

            else:
                if(pai != None):
                    print(self.identificacao)
                    conexao, raiz = iniciarConexao(self.vizinhos[self.pai])
                    raiz.ack()
                    conexao.close()

        def exposed_echo(self, candidato):
            self.numeroEspera -= 1
            if (candidato > self.candidato):
                self.candidato = candidato
            if(self.shouldEcho()):
                self.sendEcho()

        def exposed_ack(self):
            self.numeroEspera -= 1
            if(self.shouldEcho()):
                self.sendEcho()

        def exposed_divulgarResultado(self, vencedor):
            self.lider = vencedor
            for endereco in self.vizinhos.values():
                conexao, raiz = iniciarConexao(endereco)
                raiz.divulgarResultado(vencedor)
                conexao.close()

        def exposed_iniciarEleicao(self):
            global estados
            self.exposed_probe(None)
            while estados[self.identificacao] != TERMINADA_ELEICAO:
                pass #time.sleep(0.5)
            self.exposed_divulgarResultado(self.candidato)

        def exposed_mostrarLider(self):
            existeLider = True if self.lider != None else False
            if(existeLider):
                print("Nó " + str(self.identificacao) +
                      "diz que Nó " + str(self.lider) + " é o líder")
            else:
                self.exposed_iniciarEleicao()
                print("Nó " + str(self.identificacao) +
                      " diz que Nó " + str(self.lider) + " é o líder")

    # server = threading.Thread(target=iniciarServidor, args=(No, No.porta,))
    # server.start()
    # server.join()
    #iniciarServidor(No,No.porta)
    x = No.porta
    srv = ThreadedServer(No, port=No.porta)
    srv.start()



if __name__ == "__main__":
    for i in range(0, MAX_NUMERO_NOS):
        p = Process(target=processo)
        #time.sleep(5)
        p.start()
    while True:
        noAlvo = input()
        if noAlvo == "fim":
            break
        noAlvo = int(noAlvo)
        conexao, raiz =iniciarConexao(6000 + noAlvo)
        raiz.mostrarLider()
    p.join()
