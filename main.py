# --- Кооперативный онлайн-шутер (Pygame + Socket) ---
# Клиентская часть: каждый игрок управляет персонажем и стреляет, координаты передаются на сервер.
# Сервер рассылает состояние другим игрокам.

import pygame
import socket
import threading
import json
import math
import os

# --- Настройки ---
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
FPS = 60
SERVER_IP = '127.0.0.1'  # если клиент и сервер на одной машине
PORT = 5555
PLAYER_IMG = 'player.png'
BULLET_IMG = 'bullet_game3.png'
BACKGROUND_IMG = 'background_game1.jpg'

# --- Инициализация Pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Кооперативный шутер")
clock = pygame.time.Clock()
background = pygame.transform.scale(pygame.image.load(BACKGROUND_IMG), (WIDTH, HEIGHT))
FONT = pygame.font.Font(None, 36)

# --- Подключение к серверу ---
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, PORT))

# --- Группы спрайтов ---
all_players = pygame.sprite.Group()
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
        keys = pygame.key.get_pressed()
        # Движение только локального игрока
        if self.id == 'me':
            if keys[pygame.K_w]: self.rect.y -= self.speed
            if keys[pygame.K_s]: self.rect.y += self.speed
            if keys[pygame.K_a]: self.rect.x -= self.speed
            if keys[pygame.K_d]: self.rect.x += self.speed

        # Поворот к мышке
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

            if data["type"] == "player":
                pid = data["id"]
                if pid != 'me':
                    other = next((p for p in all_players if p.id == pid), None)
                    if not other:
                        other = Player(data["x"], data["y"], pid)
                        all_players.add(other)
                    other.rect.center = (data["x"], data["y"])

            elif data["type"] == "bullet":
                bullet = Bullet(data["x"], data["y"], data["dx"], data["dy"])
                bullets.add(bullet)

        except:
            break

# Запуск отдельного потока для приёма данных от сервера
threading.Thread(target=receive, daemon=True).start()

# --- Создание локального игрока ---
me = Player(WIDTH//2, HEIGHT//2, 'me')
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
            if e.key == pygame.K_SPACE:
                me.fire()

    # Обновление и отправка координат игрока
    me.update()
    send({"type": "player", "id": "me", "x": me.rect.centerx, "y": me.rect.centery})

    # Обновление пуль и отрисовка
    bullets.update()
    all_players.update()
    all_players.draw(screen)
    bullets.draw(screen)

    # Заголовок
    title = FONT.render("Кооперативный шутер онлайн", True, WHITE)
    screen.blit(title, (10, 10))
    pygame.display.flip()

# Завершение игры
pygame.quit()
client.close()