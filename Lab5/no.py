import socket
import threading
RECEIV_SIZE = 2048
PORTA_BASE = 5000
MAX_NOS = 5
PRIMARIA = 1
NAO_PRIMARIA = 0
ACK = "ACK"
OK = "OK"
LOCK = threading.Lock()

# inicializa o socket do servidor
def inicializarSocket():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((vizinhos_ip[identificador], vizinhos_portas[identificador]))
    s.listen(4)
    return s

# recebe uma conexão de um cliente
def aceitarConexao(s):
    conexao, end = s.accept()
    LOCK.acquire()
    conexoes.append(conexao)
    LOCK.release()
    return conexao, end

# fica na espera por requisições dos clientes
def esperarRequisisao(s):
    while True:
        conexao, end = aceitarConexao(s)
        request = threading.Thread(target=handleRequest, args=(conexao, end,))
        request.start()
#lida com os pedidos da cópia primária
def handleTokenRequest(identificadorCliente,conexao):
    global token
    LOCK.acquire()
    possuiToken = True if token == PRIMARIA else False
    LOCK.release()
    messagem = None
    if(possuiToken):
        LOCK.acquire()
        token = NAO_PRIMARIA
        token_holder = identificadorCliente
        LOCK.release()
        messagem = (OK,PRIMARIA)
    else:# se não possui a copia primária retorna a localização dela
        messagem = (ACK,token_holder)
    sendMessage(identificadorCliente,messagem,esperaResposta=False,sock=conexao)

def handleRequest(conexao, end):
    pedido = conexao.recv(RECEIV_SIZE)
    pedidoString = pedido.decode("utf-8")
    identificadorCliente, operacao, novoHistorico = eval(pedidoString)
    if operacao == "TOKEN":
        handleTokenRequest(identificadorCliente,conexao)

# envia uma mensagem a um nó
def sendMessage(noAlvo, message, esperaResposta, sock = None):
    existeSock = True if sock != None else False
    if not  existeSock:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((vizinhos_ip[noAlvo], vizinhos_portas[noAlvo]))
    message = str(message)#garante que a mensagem está como string
    messageBytes = str.encode(message)
    sock.send(messageBytes)
    resposta = None
    if esperaResposta:#caso a mensagem necessite de uma resposta aguarda
        resposta = sock.recv(RECEIV_SIZE)
        sock.close()
        resposta = resposta.decode('utf-8')
        resposta = eval(resposta)
    return resposta 

def broadcast():
    for no in range(1,MAX_NOS+1):
        if no != identificador:
            mensagem = (identificador,"BROADCAST",historicoCompartilhado)
            sendMessage(no,mensagem,esperaResposta=False)


def requestToken():
    global token_holder
    global token
    while token != PRIMARIA:#repete o processo até possuir o token 
        mensagem = (identificador, "TOKEN") # envia seu identificador e o tipo da operação
        mensagemString = str(mensagem)
        sitacao, valor = sendMessage(
            token_holder, mensagemString, esperaResposta=True)
        if sitacao == ACK:
            token_holder = valor  # o token mudou de nó
        else:
            token = valor  # token recebe PRIMARIA

#declaração e inicialização de variáveis globais
def inicializarGlobais():
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
    global token_holder
    X = 0
    identificador = int(input("identificador: "))
    token = PRIMARIA if identificador == 1 else NAO_PRIMARIA 
    historicoReplica = []
    historicoCompartilhado = []
    vizinhos_ip = {1: "localhost", 2: "localhost",
                   3: "localhost", 4: "localhost"}
    vizinhos_portas = gerarVizinhos()
    chegadas = []
    threads = []
    conexoes = []
    token_holder = 1

#começa thread responsável pela intervace
def inicializarInterface():
    teclado = threading.Thread(target=interface)
    teclado.start()

#inicializa serverside
def inicializarServer():
    s = inicializarSocket()
    esperarRequisisao(s)

def gerarVizinhos():
    vizinhos = {}
    for i in range(1, MAX_NOS+1):
        vizinhos[i] = PORTA_BASE + i
    return vizinhos

#modifica o valor de X
def alterarX(novo_valor):
    global X
    global historicoReplica
    global historicoCompartilhado
    X = novo_valor
    registro = (identificador, X)#registro a ser guardado no histórico
    historicoReplica.append(registro) #toda operação é marcada no histórico do nó
    historicoExiste  = False if historicoCompartilhado == [] else True
    if historicoExiste and  historicoCompartilhado[-1][0] == identificador:
        historicoCompartilhado[-1] = registro #caso multiplas operações sucessivas seja feitas
    else:
        historicoCompartilhado.append(registro)
    
def handleChange():
    global X
    global historico
    userInput = input("Insira o novo valor de X: ")
    LOCK.acquire()
    possuiPrimaria = True if token == PRIMARIA else False
    LOCK.release()
    if not possuiPrimaria:# verifica se o nó pussui a cópia primária
        requestToken()# senão, pede o a cópia primária
    alterarX(int(userInput))
    broadcast()  # transmite o novo valor para os outros nós

#Mostra o valor de X ao usuário
def showX():
    print("O valor de X é: " + str(X))

#mosta histórico de operações da réplica
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
            handleChange()


if __name__ == "__main__":
    inicializarGlobais()
    inicializarInterface()
    inicializarServer()
