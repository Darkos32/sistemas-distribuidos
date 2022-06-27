from socket import *
import string

HOST = ''
PORT = 3000 

s = socket(AF_INET, SOCK_STREAM)  # instancia objeto socket
s.bind((HOST, PORT))  # define endereço e porta
s.listen(1)
(ativo_conect, ativo_end) = s.accept()  # socket e endereço do ativo

while True:
    print(ativo_end)
    data = ativo_conect.recv(1024)
    if not data:
        break
    ativo_conect.send(data)
ativo_conect.close()
