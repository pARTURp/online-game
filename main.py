# --- Кооперативный онлайн-шутер (Pygame + Socket) ---
# Клиентская часть: каждый игрок управляет персонажем и стреляет, координаты передаются на сервер.
# Сервер рассылает состояние другим игрокам.

import pygame
import socket
import threading
import json
import math
import os
import uuid

# --- Настройки ---
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
FPS = 60
PORT = 5555
PLAYER_IMG = 'player.png'
BULLET_IMG = 'bullet_game3.png'
BACKGROUND_IMG = 'background_game1.jpg'

# --- Получение IP адреса сервера автоматически (для локальной сети) ---
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

SERVER_IP = input(f"Введите IP сервера (Enter для автопоиска): ") or get_local_ip()
print(f"Подключение к серверу {SERVER_IP}:{PORT}...")

# --- Инициализация Pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Кооперативный шутер")
clock = pygame.time.Clock()
background = pygame.transform.scale(pygame.image.load(BACKGROUND_IMG), (WIDTH, HEIGHT))
FONT = pygame.font.Font(None, 36)

# --- Подключение к серверу ---
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect((SERVER_IP, PORT))
except Exception as e:
    print("Ошибка подключения к серверу:", e)
    exit()

# --- Уникальный ID игрока ---
PLAYER_ID = str(uuid.uuid4())

# --- Группы спрайтов ---
all_players = pygame.sprite.Group()
other_players = {}
bullets = pygame.sprite.Group()

# --- Класс Игрока ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, pid):
        super().__init__()
        self.original_image = pygame.transform.scale(pygame.image.load(PLAYER_IMG), (30, 70))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5
        self.id = pid

    def update(self):
        if self.id == PLAYER_ID:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]: self.rect.y -= self.speed
            if keys[pygame.K_s]: self.rect.y += self.speed
            if keys[pygame.K_a]: self.rect.x -= self.speed
            if keys[pygame.K_d]: self.rect.x += self.speed

        mx, my = pygame.mouse.get_pos()
        dx = mx - self.rect.centerx
        dy = my - self.rect.centery
        angle = math.degrees(math.atan2(-dy, dx)) - 90
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def fire(self):
        mx, my = pygame.mouse.get_pos()
        dx = mx - self.rect.centerx
        dy = my - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 1
        dx /= dist
        dy /= dist
        bullet = Bullet(self.rect.centerx, self.rect.centery, dx, dy)
        bullets.add(bullet)
        send({"type": "bullet", "x": self.rect.centerx, "y": self.rect.centery, "dx": dx, "dy": dy})

# --- Класс Пули ---
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy):
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load(BULLET_IMG), (20, 40))
        angle = math.degrees(math.atan2(-dy, dx)) - 90
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 10
        self.dx = dx
        self.dy = dy

    def update(self):
        self.rect.x += self.dx * self.speed
        self.rect.y += self.dy * self.speed
        if (self.rect.right < 0 or self.rect.left > WIDTH or
            self.rect.bottom < 0 or self.rect.top > HEIGHT):
            self.kill()

# --- Сетевые функции ---
def send(data):
    try:
        client.send(json.dumps(data).encode())
    except:
        pass

def receive():
    while True:
        try:
            msg = client.recv(1024)
            data = json.loads(msg.decode())

            if data["type"] == "player" and data["id"] != PLAYER_ID:
                pid = data["id"]
                if pid not in other_players:
                    p = Player(data["x"], data["y"], pid)
                    other_players[pid] = p
                    all_players.add(p)
                else:
                    other_players[pid].rect.center = (data["x"], data["y"])

            elif data["type"] == "bullet":
                bullet = Bullet(data["x"], data["y"], data["dx"], data["dy"])
                bullets.add(bullet)

        except:
            break

# --- Запуск потока для получения данных ---
threading.Thread(target=receive, daemon=True).start()

# --- Создание локального игрока ---
me = Player(WIDTH//2, HEIGHT//2, PLAYER_ID)
all_players.add(me)

# --- Главный игровой цикл ---
running = True
while running:
    dt = clock.tick(FPS)
    screen.blit(background, (0, 0))

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False
            elif e.key == pygame.K_SPACE:
                me.fire()

    me.update()
    send({"type": "player", "id": PLAYER_ID, "x": me.rect.centerx, "y": me.rect.centery})

    bullets.update()
    all_players.update()
    all_players.draw(screen)
    bullets.draw(screen)

    title = FONT.render("Кооперативный шутер онлайн", True, WHITE)
    screen.blit(title, (10, 10))
    pygame.display.flip()

pygame.quit()
client.close()
