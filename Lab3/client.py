from socket import *
#Define o ip e a porta
HOST = 'localhost'
PORT = 5000

#Inicializa o socket
def init_socket():
    s = socket(AF_INET, SOCK_STREAM)
    s.connect((HOST, PORT))
    return s

#Imprime a resposta do servidor
def print_top5(resposta):
    print("As palavras mais recorrentes são:")
    for palavra in resposta:
        if palavra != None:
            print(palavra)

def main():
    s = init_socket()
    arquivo = input("Diga o nome do arquivo: ")  # recebe o nome do arquivo
    s.send(str.encode(arquivo))  # envia o nome do arquivo para o servidor
    # decodifica a mensagem recebida do servidor. O servidor manda o vetor na forma string, a função eval converte novamente para o vetor
    resposta = eval(s.recv(1024).decode("utf-8"))
    print_top5(resposta)
    s.close()

main()