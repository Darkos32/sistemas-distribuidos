from multiprocessing.dummy import Process
import time
import rpyc
import multiprocessing
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
candidatos = {}
numEsperas = {}
pais = {}
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
    return conexao


def processo():
    identificador = gerarIdentificador()
    candidatos[identificador] = identificador
    estados[identificador] = INICIO
    pais[identificador] = None
    class No(rpyc.Service):
        identificacao = identificador
        porta = gerarPorta(identificacao)
        vizinhos = gerarVizinhos(identificacao)
        lider = None
        # pai = None
        # numeroEspera = numEspera
        # jaVotou = False
        # estado = 0
        # jaRecebeuResultado = False

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
                # conexao, raiz = iniciarConexao(self.vizinhos[pais[self.identificacao]])
                # rpyc.async_(raiz.echo(candidatos[self.identificacao]))
                estados[self.identificacao] = AGUARDANDO_RESULTADO
                # conexao.close()
            else:
                estados[self.identificacao] = TERMINADA_ELEICAO

        def exposed_probe(self, pai):
            global estados
            global conexoes
            if (estados[self.identificacao] == INICIO):
                estados[self.identificacao] = COMECOU_VOTACAO
                pais[self.identificacao] = pai
                numEsperas[self.identificacao] = len(self.vizinhos) - \
                    1 if self.temPai() else len(self.vizinhos)
                print("no " + str(self.identificacao) +
                      "espera " + str(numEsperas[self.identificacao]))
                conexoes[self.identificacao] = {}
                for vizinho in self.vizinhos:
                    try:
                        endereco = self.vizinhos[vizinho]
                        conexao = iniciarConexao(endereco)
                        conexoes[self.identificacao][vizinho] = conexao
                        #raiz.exposed_pai = self.identificacao
                        # rpyc.async_(raiz.probe(self.identificacao))
                        conexao.root.probe(self.identificacao)
                        # conexao.close()
                    except Exception as e:
                        print(str(e.args) + "\n Nó: " + str(self.identificacao))
                        numEsperas[self.identificacao] -= 1
                if (self.shouldEcho()):
                    self.sendEcho()

            else:
                try:
                    if(pais[self.identificacao] != None):
                        print(self.identificacao)
                        conexoesAtivas = conexoes[self.identificacao]
                        conexaoPai = conexoesAtivas[pais[self.identificacao]]
                        conexaoPai.root.ack()
                        # conexao,raiz = iniciarConexao(self.vizinhos[pais[self.identificacao]])
                        # raiz.ack()
                        # conexao.close()
                except Exception as e :
                    print(e.args)                    
        def exposed_echo(self, candidato):
            numEsperas[self.identificacao] -= 1
            if (candidato > candidatos[self.identificacao]):
                candidatos[self.identificacao] = candidato
            if(self.shouldEcho()):
                self.sendEcho()

        def exposed_ack(self):
            numEsperas[self.identificacao] -= 1
            if(self.shouldEcho()):
                self.sendEcho()

        def exposed_divulgarResultado(self, vencedor):
            if(estados[self.identificacao] != TERMINADA_ELEICAO):
                self.lider = vencedor
                # for endereco in self.vizinhos.values():
                #     conexao, raiz = iniciarConexao(endereco)
                #     raiz.divulgarResultado(vencedor)
                #     conexao.close()
                try:
                    for conexao in conexoes[self.identificacao].values():
                        conexao.root.divulgarResultado(vencedor)
                        conexao.close()
                except Exception as e:
                    print(e.args)

        def exposed_iniciarEleicao(self):
            global estados
            self.exposed_probe(None)
            while estados[self.identificacao] != TERMINADA_ELEICAO:
                pass  # time.sleep(0.5)
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

    # server = threading.Thread(target=iniciarServidor, args=(No, No.porta,))
    # server.start()
    # server.join()
    # iniciarServidor(No,No.porta)
    x = No.porta
    srv = ThreadedServer(No, port=No.porta)
    srv.start()


if __name__ == "__main__":
    for i in range(0, MAX_NUMERO_NOS):
        p = Process(target=processo)
        # time.sleep(5)
        p.start()
    while True:
        noAlvo = input()
        if noAlvo == "fim":
            break
        noAlvo = int(noAlvo)
        conexao = iniciarConexao(6000 + noAlvo)
        conexao.root.mostrarLider()
    p.join()
