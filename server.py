import socket
import asyncio
import json
import threading

from game_logic import *


def init(address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    sock.bind(address)
    sock.setblocking(True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.listen()
    return sock


async def get_request(sock):
    raw_request = sock.recv(2 ** 11)
    request = json.loads(raw_request)
    return request


async def send_response(sock, response):
    response = json.dumps(response).encode()
    sock.send(response)


async def get_connection():
    sock, addr = SERVER_SOCKET.accept()
    return sock, addr


def route(request):
    action = request['action']
    payload = request['payload']

    if action == 'join':
        name = payload['name']
        car_id = payload['car_id']

        player = Player(name, GAME)
        player.machine = Machine(car_id)
        return True, None, {'uid': max(GAME.players.keys())}

    elif action == 'get_data':
        data = GAME.get_data
        return True, data, {}

    elif action == 'send_data':
        number = payload['uid']
        keys = payload['keys']
        player = GAME.players[number]
        if player.finished:
            return
        for key in keys:
            if keys[key]:
                player.clicked_keys[key] = 5

    elif action == 'start_game':
        global STARTED_YET
        if STARTED_YET:
            return
        threading.Thread(target=run_game, args=(GAME,)).start()
        STARTED_YET = True

    elif action == 'quit_game':
        number = payload['uid']
        del GAME.players[number]

    elif action == 'load_map':
        return True, {'image': GAME.file, 'size': GAME.size}, {}


def make_response(status, data, cookie):
    response = {
        'status': status,
        'data': data,
        'cookie': cookie
    }
    return response


ADDRESS = '192.168.0.122', 4000
SERVER_SOCKET = init(ADDRESS)
GAME = Map(0)
STARTED_YET = False


async def run():
    try:
        while True:
            try:
                user, _ = await get_connection()
            except socket.timeout:
                continue
            try:
                request = await get_request(user)
            except json.decoder.JSONDecodeError:
                continue
            raw_response = route(request)
            if raw_response is None:
                continue
            response = make_response(*raw_response)
            await send_response(user, response)
    finally:
        SERVER_SOCKET.close()


if __name__ == '__main__':
    asyncio.run(run(), debug=True)

