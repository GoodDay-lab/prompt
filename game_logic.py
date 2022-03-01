import math
import time
import pygame
import json


maps = {0: 'map.json'}


def load_stats(car_id):
    return {'size': (40, 40)}


def load_map(map_id):
    fileName = maps[map_id]
    map_data = json.load(open(fileName, 'r'))
    return map_data


def rads(angle):
    return angle * math.pi / 180


class Player:
    def __init__(self, name, game_map):
        self.name = name
        self.machine = Machine(0)
        self.map = game_map
        self.clicked_keys = {
            'key_up': 0,
            'key_down': 0,
            'key_left': 0,
            'key_right': 0
        }
        self.round = 0
        self.checkpoint = 0
        self.map.add_player(self)
        self.finished = False

    def get_stats(self):
        return {
            'name': self.name,
            'round': self.round,
            'checkpoint': self.checkpoint,
            'machine': self.machine.get_stats()
        }


class Machine:
    def __init__(self, car_id=0):
        stats = load_stats(car_id)
        self.name = 'Audi'  # stats['name']
        self.acceleration = 1.5  # stats['acceleration']
        self.max_speed = 10000  # stats['max_speed']
        # self.max_rotate = stats['max_rotate']
        self.flexibility = 1.2  # stats['flexibility']
        self.size = stats['size']

        self.rect = pygame.rect.Rect(0, 0, *self.size)
        self.angle = 0
        self.speed = 0
        self.car_id = car_id
        self.update_rate = 1 / 25

    def move(self):
        speed = self.speed

        self.rect.x += speed * math.cos(rads(self.angle))
        self.rect.y += speed * math.sin(rads(self.angle))

    def change_speed(self, key_up=0, key_down=0):
        key_up, key_down = bool(key_up), bool(key_down)
        self.speed = min(self.max_speed,
                         round(self.speed + self.acceleration * self.update_rate * (key_up - key_down) -
                               min(0.5 * self.update_rate, self.speed) * (key_up is False and self.speed > 0), 6))

    def change_angle(self, key_right=0, key_left=0):
        key_right, key_left = bool(key_right), bool(key_left)
        self.angle = (self.angle + self.flexibility * (key_right - key_left) *
                      min(2.0, math.sqrt(abs(self.speed)))) % 360

    def get_stats(self):
        return {
            'name': self.name,
            'rect': [self.rect.x, self.rect.y, self.rect.w, self.rect.h],
            'speed': self.speed,
            'angle': round(self.angle, 3),
            'car_id': self.car_id,
        }


class Map:

    update_time = 1 / 25

    def __init__(self, map_id=0):
        stats = load_map(map_id)
        self.name = stats['NAME']
        self.size = stats['SIZE']
        self.file = stats['MAP_NAME']
        self.start_position = stats['START_POS']
        self.start_angle = stats['START_ANGLE']
        self.rounds = stats['ROUNDS']
        self.checkpoints = [CheckPoint(*staff) for staff in stats['CHECKPOINTS']]
        self.max_checkpoint = len(self.checkpoints)
        self.max_players = len(self.start_position)
        self.players = {}
        self.last_update = 0
        self.get_data = []
        self.winners = []
        self.started = False

    def update_players(self):
        self.get_data = []
        for uid in self.players:
            data = self.players[uid].get_stats()
            data['uid'] = uid
            self.get_data.append(data)

    def start_game(self):
        count = 0
        for player in self.players.values():
            player.machine.rect = player.machine.rect.move(*self.start_position[count])
            player.machine.angle = self.start_angle
            count += 1
        self.started = True

    def add_player(self, player):
        if len(self.players) < self.max_players:
            value = (max(self.players.keys()) if len(self.players) else 0)
            self.players[value + 1] = player
            self.update_players()

    def update(self):
        for player in self.players.values():
            if not self.started:
                continue

            keys = player.clicked_keys
            player.machine.change_speed(keys['key_up'], keys['key_down'])
            player.machine.change_angle(keys['key_right'], keys['key_left'])
            for key in player.clicked_keys.keys():
                player.clicked_keys[key] = (player.clicked_keys[key] - 1 if player.clicked_keys[key] else 0)

            cur_checkpoint = player.checkpoint
            if self.checkpoints[cur_checkpoint].is_collide(player.machine):
                player.checkpoint = cur_checkpoint + 1
                if self.max_checkpoint == player.checkpoint:
                    player.checkpoint = 0
                    player.round = player.round + 1
                if player.round >= self.rounds:
                    player.finished = True
            if player in self.winners:
                continue
        self.update_players()
        [player.machine.move() for player in self.players.values()]


class CheckPoint:
    def __init__(self, number, rect):
        self.number = number
        self.rect = pygame.rect.Rect(*rect)

    def is_collide(self, obj: Machine):
        return self.rect.colliderect(obj.rect)


def run_game(gmap):
    gmap.start_game()
    clock = pygame.time.Clock()
    while True:
        gmap.update()
        clock.tick(25)
