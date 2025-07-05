# server.py
import socket
import threading

HOST = '0.0.0.0'  # принимает соединения со всех IP
PORT = 5555
clients = []

def handle_client(conn, addr):
    print(f"[+] Подключился {addr}")
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            for c in clients:
                if c != conn:
                    c.send(data)
        except:
            break
    print(f"[-] Отключился {addr}")
    clients.remove(conn)
    conn.close()

def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Сервер запущен на {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

start()
