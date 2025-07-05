# server.py
import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 5555

clients = {}  # {conn: player_id}
player_states = {}  # {player_id: {"x": ..., "y": ..., "angle": ...}}

lock = threading.Lock()

def handle_client(conn, addr):
    print(f"[+] Подключился {addr}")
    player_id = None
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            try:
                message = json.loads(data.decode())
            except json.JSONDecodeError:
                continue

            if message["type"] == "player":
                player_id = message["id"]
                with lock:
                    clients[conn] = player_id
                    player_states[player_id] = {
                        "x": message["x"],
                        "y": message["y"],
                        "angle": message["angle"]
                    }

                broadcast(message, exclude=conn)

            elif message["type"] == "bullet":
                broadcast(message, exclude=conn)

    except Exception as e:
        print(f"[-] Ошибка с {addr}: {e}")
    finally:
        with lock:
            if conn in clients:
                disconnected_id = clients[conn]
                print(f"[-] Отключился: {disconnected_id}")
                del clients[conn]
                if disconnected_id in player_states:
                    del player_states[disconnected_id]

                # Уведомить остальных
                broadcast({
                    "type": "disconnect",
                    "id": disconnected_id
                })
        conn.close()


def broadcast(data, exclude=None):
    msg = json.dumps(data).encode()
    with lock:
        for c in list(clients.keys()):
            if c != exclude:
                try:
                    c.send(msg)
                except:
                    pass

def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Сервер запущен на {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start()
