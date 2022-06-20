from multiprocessing.dummy import Process
import rpyc
import multiprocessing
import threading
from rpyc.utils.server import ThreadedServer
from random import randint
LOCK = multiprocessing.Lock()
MAX_NUMERO_NOS = 5
SERVER = 'localhost'

identificadoresDisponiveis = list(range(0, MAX_NUMERO_NOS))
nosAtivos = {}


def gerarIndice(maximo):
    return randint(0, maximo-1)


def gerarPorta(identificador):
    return 5000 + identificador


def gerarIdentificador():
    # randint(0, len(identificadoresDisponiveis)-1)
    index = gerarIndice(len(identificadoresDisponiveis))
    LOCK.acquire()
    identificador = identificadoresDisponiveis[index]
    identificadoresDisponiveis.remove(identificador)
    nosAtivos[identificador] = gerarPorta(identificador)
    LOCK.release()
    return identificador


def gerarVizinhos(idenficador):
    vizinhos = {}
    if identificador - 1 > 0:
        vizinhos[identificador-1] = gerarPorta(identificador-1)
    if identificador + 1<MAX_NUMERO_NOS:
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
        lider = None
        jaVotou = False
        jaRecebeuResultado = False
        def on_connect(self, conn):
            return super().on_connect(conn)

        def on_disconnect(self, conn):
            return super().on_disconnect(conn)

        def checarLider(self):
            if self.lider == None:
                return False
            try:
                portaLider = nosAtivos[self.lider]
                iniciarConexao(porta=portaLider)
            except:
                return False
            return True
        def(re)
        def exposed_processoELeitoral(self):
            if !jaVotou:
                self.exposed_callToVote(exposed_identificador)
                self.jaVotou = True
                for i  in range(0,len(self.vizinhos)):
                    
                    

            
        def exposed_getVoto(voto):
            

        def exposed_callToVote(self,pai):
            for endereco in vizinhos.values():
                conexao, raiz = iniciarConexao(endereco)
                raiz.calltoVote(pai)
            
        def mostrarLider(self):
            if(self.checarLider()):
                print("processo " + self.exposed_identificador +
                      " diz que o lider é o processo " + self.lider)
            else:
                pass
    server = threading.Thread(target=iniciarServidor, args=(No, No.porta))
    server.start()
    server.join()


if __name__ == "__main__":
    for i in range(0, 5):
        p = Process(target=processo)
        p.start()
        p.join()