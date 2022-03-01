import json
import socket
import time
import pygame


TARGET = '192.168.0.122', 4000

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
clock = pygame.time.Clock()


class Client:
    def __init__(self, address):
        self.address = address
        self.cookie = {}
        self.con_sock = None

    def send_request(self, request):
        self.con_sock = socket.socket()
        self.con_sock.connect(self.address)
        self.con_sock.send(json.dumps(request).encode())
        time.sleep(0.001)

    def parse_response(self, response):
        response = json.loads(response)
        if response['cookie'] is not None:
            for key in response['cookie']:
                self.cookie[key] = response['cookie'][key]
        return response

    def start_game(self):
        request = {'action': 'start_game', 'payload': ''}
        self.send_request(request)

    def join_game(self, name, car_id):
        request = {'action': 'join', 'payload': {'name': name, 'car_id': car_id}}
        self.send_request(request)
        self.parse_response(self.con_sock.recv(2 ** 11))

    def get_data(self):
        request = {'action': 'get_data', 'payload': {}}
        self.send_request(request)
        response = self.parse_response(self.con_sock.recv(2 ** 14))
        return response

    def send_data(self, keys):
        request = {'action': 'send_data', 'payload': {'uid': self.cookie['uid'],
                                                      'keys': keys}}
        self.send_request(request)

    def quit(self):
        request = {'action': 'quit_game', 'payload': {'uid': self.cookie['uid']}}
        self.send_request(request)

    def load_map(self):
        request = {'action': 'load_map', 'payload': {}}
        self.send_request(request)
        response = self.parse_response(self.con_sock.recv(2 ** 11))
        return response


class Player(pygame.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.car_id = kwargs['machine']['car_id']
        self.speed = kwargs['machine']['speed']
        self.angle = kwargs['machine']['angle']
        self.image = pygame.transform.rotate(pygame.image.load('image/index.jpg'), -self.angle + 90)
        self.image.set_colorkey('white')
        self.rect = self.image.get_rect()
        aspx, aspy = (self.rect.w - kwargs['machine']['rect'][2]) / 2, (self.rect.h - kwargs['machine']['rect'][3]) / 2
        self.rect = self.rect.move(kwargs['machine']['rect'][0] - aspx, kwargs['machine']['rect'][1] - aspy)


class Map(pygame.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.fileName = kwargs['filename']
        self.size = kwargs['size']
        self.image = pygame.image.load('image/{}'.format(self.fileName))
        self.image = pygame.transform.scale(self.image, self.size)
        self.rect = self.image.get_rect()


class Camera:
    def __init__(self):
        self.dx, self.dy = 0, 0
        self.height = 3

    @property
    def yasp(self):
        return 3 / self.height

    def catch(self, obj):
        self.dx = WIDTH * 0.5 - obj.rect.w / 2 - obj.rect.x
        self.dy = HEIGHT * 0.5 - obj.rect.h / 2 - obj.rect.y

    def show(self, surface, objs):
        for obj in objs:
            size = obj.rect.w * self.yasp, obj.rect.h * self.yasp
            aspx, aspy = (obj.rect.w - size[0]) / 2, (obj.rect.h - size[1]) / 2
            surface.blit(pygame.transform.scale(obj.image, size),
                         (obj.rect.x + self.dx + aspx, obj.rect.y + self.dy + aspy))


client = Client(TARGET)
resp = client.load_map()
file = resp['data']['image']
map_size = resp['data']['size']
client.join_game('Quattro', 0)
camera = Camera()

static_group = pygame.sprite.Group()
Map(static_group, filename=file, size=map_size)
c1 = pygame.sprite.Sprite(static_group)
c1.image = pygame.surface.Surface((40, 40))
c1.rect = c1.image.get_rect()
c1.rect = c1.rect.move(10, 10)
c2 = pygame.sprite.Sprite(static_group)
c2.image = pygame.surface.Surface((40, 40))
c2.rect = c2.image.get_rect()
c2.rect = c2.rect.move(100, 100)
try:
    while True:
        me = None
        screen.fill('black')
        t1 = time.time()
        keys = pygame.key.get_pressed()
        players_group = pygame.sprite.Group()
        [exit(127) for e in pygame.event.get() if e.type == pygame.QUIT]
        if keys[pygame.K_1]:
            client.start_game()
        camera.height += 1 / 30 * keys[pygame.K_a]
        camera.height -= 1 / 30 * keys[pygame.K_s]
        client.send_data({'key_up': keys[pygame.K_UP], 'key_down': keys[pygame.K_DOWN],
                          'key_right': keys[pygame.K_RIGHT], 'key_left': keys[pygame.K_LEFT]})
        response = client.get_data()
        for resp in response['data']:
            p = Player(players_group, **resp)
            if resp['uid'] == client.cookie['uid']:
                me = p
        if me is not None:
            camera.catch(me)
        camera.show(screen, static_group)
        camera.show(screen, players_group)
        pygame.display.flip()
        clock.tick(30)
finally:
    client.quit()
