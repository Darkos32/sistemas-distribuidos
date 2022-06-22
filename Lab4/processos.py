from multiprocessing.dummy import Process
import time
import rpyc
import multiprocessing
import threading
from rpyc.utils.server import ThreadedServer
from random import randint
LOCK = multiprocessing.Lock()
MAX_NUMERO_NOS = 5
SERVER = 'localhost'
INICIO = 0
COMECOU_VOTACAO = 1
TERMINOU_VOTACAO = 2
AGUARDANDO_RESPOSTA = 3
VOTACAO_ENCERRADA = 4
identificadoresDisponiveis = list(range(0, MAX_NUMERO_NOS))
nosAtivos = {}


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
    if identificador - 1 > 0:
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
    class No(rpyc.Service):
        exposed_identificador = gerarIdentificador()
        porta = gerarPorta(exposed_identificador)
        vizinhos = gerarVizinhos(exposed_identificador)
        numeroVotos = None
        lider = None
        pai = None
        candidato = exposed_identificador
        # jaVotou = False
        estado = 0
        # jaRecebeuResultado = False

        def on_connect(conn):
            return super().on_connect(conn)

        def on_disconnect( conn):
            return super().on_disconnect(conn)

        def checarLider():
            if No.lider == None:
                return False
            try:
                portaLider = nosAtivos[No.lider]
                iniciarConexao(porta=portaLider)
            except:
                return False
            return True
        # def exposed_votar():

        def exposed_votacao(pai):
            if No.estado == INICIO:
                No.estado = COMECOU_VOTACAO
                No.numeroVotos = 0
                No.pai = pai
                for endereco in No.vizinhos.values():
                    try:
                        conexao, raiz = iniciarConexao(endereco)
                        raiz.votacao(No.exposed_identificador)
                        conexao.close()
                        No.numeroVotos += 1
                    except:
                        continue

        def exposed_voto():
            if(No.estado == COMECOU_VOTACAO and No.numeroVotos ==0):
                No.estado = TERMINOU_VOTACAO if No.pai != None else VOTACAO_ENCERRADA
            if(No.estado == TERMINOU_VOTACAO):
                conexao, raiz = iniciarConexao(No.vizinhos[No.pai])
                if(No.candidato > raiz.candidato):
                    raiz.candidato = No.candidato
                    raiz.numeroVotos -= 1
                    No.estado = AGUARDANDO_RESPOSTA
                conexao.close()
            else:
                for endereco in No.vizinhos.values():
                    try:
                        conexao,raiz = iniciarConexao(endereco)
                        raiz.voto()
                        conexao.close()
                    except:
                        continue

        # def exposed_getVoto(voto):

        # def exposed_callToVote(No,pai):
        def reset():
            No.pai = None
            No.estado = INICIO
            No.candidato = No.exposed_identificador
        def exposed_divulgarResultado(vencedor):
            No.reset()
            No.lider = vencedor
            for endereco in No.vizinhos.values():
                try:
                    conexao, raiz = iniciarConexao(endereco)
                    raiz.divulgarResultado(vencedor)
                    conexao.close()
                except:
                    continue
                


        def mostrarLider():
            if(No.checarLider() and No.estado == INICIO):
                print("processo " + No.exposed_identificador +
                      " diz que o lider é o processo " + No.lider)
            else:
                No.exposed_votacao(None)
                while No.estado ==TERMINOU_VOTACAO:
                    No.exposed_voto()
                No.exposed_divulgarResultado(No.candidato)
    server = threading.Thread(target=iniciarServidor, args=(No, No.porta))
    server.start()
    
    for i in range(10):
        No.mostrarLider()
    server.join()


if __name__ == "__main__":
    for i in range(0, 1):
        p = Process(target=processo)
        time.sleep(5)
        p.start()
    p.join()
