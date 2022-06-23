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
AGUARDANDO_RESULTADO = 2
TERMINADA_ELEICAO = 3
identificadoresDisponiveis = list(range(0, MAX_NUMERO_NOS*2))
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
        exposed_pai = None
        numeroEspera = None
        candidato = exposed_identificador
        # jaVotou = False
        estado = 0
        # jaRecebeuResultado = False

        def on_connect(conn):
            return super().on_connect(conn)

        def on_disconnect( conn):
            return super().on_disconnect(conn)
        def shouldEcho(self):
            if self.numeroEspera  == 0:
                return True
            else:
                return False
        def temPai(self):
            if self.pai!=None:
                return True
            else:
                return False
        def sendEcho(self):
            if self.temPai():
                        conexao, raiz = inciarConexao(self.vizinhos[self.pai])
                        rpyc.async_(raiz.echo(self.candidato))
                        self.estado = AGUARDANDO_RESULTADO
                        conexao.close()
            else:
                self.estado = TERMINADA_ELEICAO

        def exposed_probe(self,pai):
            if (self.estado != INICIO):
                self.estado = COMECOU_VOTACAO
                self.pai = pai
                self.numeroEspera = len(self.vizinhos)  - 1 if self.temPai() else len(self.vizinhos)
                for endereco in self.vizinhos.values()
                    try:
                        conexao, raiz =  iniciarConexao(endereco)
                        raiz.exposed_pai = self.exposed_identificador
                        rpyc.async_(raiz.probe())
                        conexao.close()
                    except:
                        self.numeroEspera-=1
                if (self.shouldEcho()):
                    self.sendEcho()

            else:
              if(pai !=None):
                conexao, raiz  = iniciarConexao(self.vizinhos[self.pai])
                raiz.ack()
                conexao.close() 
                
        def exposed_echo(self,candidato):
            self.numeroEspera-=1
            if (candidato > self.candidato):
                self.candidato = candidato
            if(self.shouldEcho()):
                self.sendEcho()
                    
        def exposed_ack(self):
            self.numeroEspera-=1
            if(self.shouldEcho()):
                self.sendEcho()
        def exposed_divulgarResultado(self,vencedor):
            self.lider = vencedor
            for endereco in self.vizinhos.values():
                conexao, raiz = iniciarConexao(endereco)
                raiz.divulgarResultado(vencedor)
                conexao.close()
        def exposed_iniciarEleicao(self)
            self.exposed_probe()
            while self.estado != TERMINOU_ELEICAO:
                time.sleep(0.5)
            self.exposed_divulgarResultado(self.candidato)
        def exposed_mostrarLider(self):
            existeLider =  True if lider!=None else False
            if(existeLider):
                print("Nó " + self.exposed_identificador + "diz que Nó " + self.lider +" é o líder"
            else:
                self.exposed_iniciarEleicao()
            
            
            
    server = threading.Thread(target=iniciarServidor, args=(No, No.porta))
    server.start()  
    server.join()


if __name__ == "__main__":
    for i in range(0, MAX_NUMERO_NOS)
        p = Process(target=processo)
        time.sleep(5)
        p.start()
    p.join()
