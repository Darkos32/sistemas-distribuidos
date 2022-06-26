import socket
import threading
PORTA_BASE = 5000
MAX_NOS = 5
PRIMARIA = 1
NAO_PRIMARIA = 0
LOCK = threading.Lock()


def inicializarSocker():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((vizinhos_ip[identificador], vizinhos_portas[identificador]))
    s.listen(4)
    return s


def aceitarConexao(s):
    conexao, end = s.accept()
    LOCK.acquire()
    conexoes[conexao] = end
    LOCK.release()
    return conexao, end


def handleRequest():
    pass


def sendRequest():
    pass


def broadcast():
    pass


def requestToken():
    pass


def inicializar():
    global token
    global identificador
    global X
    global historicoReplica
    global historicoCompartilhado
    global vizinhos_ip
    global vizinhos_portas
    global chegadas
    global threads
    global conexoes
    X = 0
    identificador = int(input("identificador: "))
    token = PRIMARIA if id == 1 else NAO_PRIMARIA
    historicoReplica = []
    historicoCompartilhado = []
    vizinhos_ip = {1: "localhost", 2: "localhost",
                   3: "localhost", 4: "localhost"}
    vizinhos_portas = gerarVizinhos()
    chegadas = []
    threads = []
    conexoes = []
    for i in range(MAX_NOS):
        pass


def gerarVizinhos():
    vizinhos = {}
    for i in range(1, MAX_NOS+1):
        vizinhos[i] = PORTA_BASE + i
    return vizinhos


def alterarX(novo_valor):
    global X
    global historicoReplica
    global historicoCompartilhado
    X = novo_valor
    registro = (identificador, X)
    historicoReplica.append(registro)
    if historicoCompartilhado[-1][0] == identificador:
        historicoCompartilhado[-1] = registro
    else:
        historicoCompartilhado.append(registro)


def handleChange():
    global X
    global historico
    userInput = input("Insira o novo valor de X: ")
    if token == PRIMARIA:
        alterarX(int(userInput))
        broadcast()
    else:
        requestToken()
        alterarX(int(userInput))


def showX():
    print("O valor de X é: " + str(X))


def showHist():
    for registro in historicoReplica:
        print(registro)


def interface():
    while True:
        comando = input("Digite o comando: ")
        if(comando == "fim"):
            break
        elif(comando == "/show"):
            showX()
        elif(comando == "/hist"):
            pass
        elif(comando == "/change"):
            pass


if __name__ == "__main__":
    inicializar()
    teclado = threading.Thread(target=interface)

    teclado.start()
