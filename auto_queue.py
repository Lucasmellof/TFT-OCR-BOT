from http import server
from requests.auth import HTTPBasicAuth
import requests
import urllib3
import json
from time import sleep
from PIL import ImageGrab
import numpy as np
import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def create_lobby(message_queue, client_info):
    payload = {"queueId": 1090}  # Ranked TFT is 1100
    payload = json.dumps(payload)
    try:
        status = requests.post(client_info[1] + "/lol-lobby/v2/lobby/", payload,
                            auth=HTTPBasicAuth('riot', client_info[0]), verify=False)
        if status.status_code == 200:
            return True
        else:
            return False
    except ConnectionError:
        return False


def start_queue(message_queue, client_info):
    try:
        status =requests.post(client_info[1] + "/lol-lobby/v2/lobby/matchmaking/search",
                            auth=HTTPBasicAuth('riot', client_info[0]), verify=False)
        if status.status_code == 204:
            return True
        else:
            return False
    except ConnectionError:
        return False


def accept_queue(client_info):
    requests.post(client_info[1] + "/lol-matchmaking/v1/ready-check/accept",
                  auth=HTTPBasicAuth('riot', client_info[0]), verify=False)


def change_arena_skin(client_info):
    try:
        status = requests.delete(client_info[1] + "/lol-cosmetics/v1/selection/tft-map-skin",
                                auth=HTTPBasicAuth('riot', client_info[0]), verify=False)
        if status.status_code == 204:
            return True
        else:
            return False
    except ConnectionError:
        return False


def get_client(message_queue):
    message_queue.put(("CONSOLE", "[Auto Queue]"))
    file_path = settings.league_client_path + "\\lockfile"
    got_lock_file = False
    while got_lock_file is False:
        try:
            data = open(file_path, "r").read().split(':')
            app_port = data[2]
            remoting_auth_token = data[3]
            server_url = f"https://127.0.0.1:{app_port}"
            got_lock_file = True
        except IOError:
            message_queue.put(("CONSOLE", "Client not open! Trying again in 10 seconds."))
            sleep(10)
    return (remoting_auth_token, server_url)
    

def queue(message_queue):
    client_info = get_client(message_queue)
    while create_lobby(message_queue, client_info) != True:
        sleep(3)

    change_arena_skin(client_info)

    sleep(5) 
    while start_queue(message_queue, client_info) != True:
        sleep(3)

    in_queue = True
    while in_queue:
        accept_queue(client_info)
        in_game = ImageGrab.grab(bbox=(19, 10, 38, 28))
        array = np.array(in_game)
        if (np.abs(array - (27, 79, 66)) <= 2).all(
                axis=2).any():  # Checks the top left of the loading screen for the green circle
            in_queue = False
        sleep(1)
    message_queue.put(("CONSOLE", "Loading screen found! Waiting for round 1-1"))

