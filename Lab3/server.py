from socket import *
import select
import sys
import multiprocessing
# Define a porta e o ip
HOST = ''
PORT = 5000

# camada de acesso aos dados


def acesso_dados(nome_arquivo):
    try:
        arquivo = open(nome_arquivo, 'r')  # abre o arquivo pedido
    except:
        # se o arquivo não existe lança uma exception
        raise RuntimeError("Arquivo não existente")
    conteudo = arquivo.read()
    arquivo.close()  # fecha o arquivo
    return conteudo

# Encontra as 5 palavras mais recorrentes no dicionário


def mais_recorrente(dicio):
    top5 = [None, None, None, None, None]  # O vetor começa vazio
    for palavra in dicio:
        for i in range(0, len(top5)):
            if top5[i] == None:  # se a posição está vazia insere o elemento
                top5[i] = palavra
                break
            # se a palavra for mais recorrente que a da posição observada insere
            elif dicio.get(palavra) > dicio.get(top5[i]):
                top5 = insere(palavra, top5, i)
                break
    return top5

# substitui os símbolos no intervalo passado por espaço em branco


def replace_simbols(conteudo, inicio, fim):
    for i in range(inicio, fim):
        conteudo = conteudo.replace(chr(i), " ")

# elimina simbolos não considerados palavras


def parse_conteudo(conteudo):
    conteudo = replace_simbols(conteudo, 33, 48)
    conteudo = replace_simbols(conteudo, 58, 65)
    conteudo = replace_simbols(conteudo, 91, 97)


# Camada de processamento
def processamento(nome_arquivo):
    try:
        conteudo = acesso_dados(nome_arquivo)
    except RuntimeError as err:
        print(err)
        resposta = err
        return resposta
    palavras = conteudo.split()
    dicio = contar(palavras)
    return mais_recorrente(dicio)

# Calcula a quantidade de vezes que uma palavra aparece no arquivo


def contar(palavras):
    dicio = {}
    for palavra in palavras:
        if dicio.get(palavra) != None:
            dicio[palavra] = dicio.get(palavra) + 1
        else:
            dicio[palavra] = 0
    return dicio

# Insere um elemento numa posição e "empurra" os elementos posteriores


def insere(elemento, vetor, pos):
    temp = []
    for i in range(0, len(vetor)):
        if i == pos:
            temp.append(elemento)
        if i != len(vetor)-1:
            temp.append(vetor[i])
    return temp

# inicializa o socket


def init_socket():
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    return s

# executa o processamento do pedido de um cliente


def handle_request(connect, ende):
    # recebe os argumentos do cliente
    pedido = connect.recv(1024).decode("utf-8")
    resposta = processamento(str(pedido))  # executa o processamento do pedido
    print(resposta)
    connect.send(str.encode(str(resposta)))  # envia a resposta para o cliente

def main():
    s = init_socket()
    entradas = [sys.stdin, s]
    clientes = []
    fim = False
    while True:
        (ler, escrever, erro) = select.select(
            entradas, [], [])  # inicializa o select
        for entrada in ler:  # Verifica de qual fonte veio o input
            if entrada == sys.stdin:  # se o input veio do próprio terminal do servidor executa o comando
                cmd = input()
                if cmd == "!":  # avisa que o servidor deve terminar assim que os processos terminarem
                    fim = True
            elif entrada == s:  # se o input é um pedido de um cliente, executa o processamento
                # cria um processo para lidar com o processo do cliente
                cliente = multiprocessing.Process(
                    target=handle_request, args=s.accept())
                cliente.start()
                # adiciona o cliente na lista de processos em andamento
                clientes.append(cliente)

        if fim == True:
            for cliente in clientes:
                cliente.join()
            break
    s.close()
    sys.exit()


main()
