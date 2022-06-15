from socket import *

HOST ='localhost' #endereço do passivo
PORT = 3000 # porta do passivo

s = socket(AF_INET, SOCK_STREAM) #inicializa o socket
s.connect((HOST,PORT))  # contecta o ativo com o passivo

msg = input("Digite sua mensagem ou escreva '!' para encerrar o programa: ") # usuário digita a mensagem
while msg != '!':
    s.send(str.encode(msg)) # envia a mensagem para o passivo
    data = s.recv(1024) # recebe a resposta
    print(str(data, encoding='utf-8')) # mostra para o usuário
    print("Digite '!' para encerrar o programa ou digite insira uma nova mensagem")
    msg = input()
s.close()
