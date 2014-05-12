#!/usr/bin/env python3
import subprocess
import time
import os
import signal

from math import log, log10, pow
from timeit import default_timer as timer

class Client(object):
    def __init__(self, mac, power):
        self.mac = mac
        self.power = power
        self.timestamp = time.clock()

    def __str__(self):
        return "%s, %d: %.2f meter" % (self.mac, self.power, self.distance)

    @property
    def distance(self):
        return calculate_wifi_distance(self.power, 2400)

def calculate_wifi_distance(strength, freq):
    exp = (27.55 - (20*log10(freq)) - strength)/20.0;
    return pow(10.0, exp)

def find_distance():
    strength = input("Styrke: ")
    freq = raw_input("Frekvens (standard er 2400): ")
    if not freq:
        freq = 2400
    else:
        freq = eval(freq)
    print(calculate_wifi_distance(strength, freq))

def extract_client_info(output):
    """Extracts MAC and power for each client
    from airodump-ng output."""
    frames = []
    previous_i = -1
    for i, line in reversed(list(enumerate(output.splitlines()))):
        if "RTS_RX" in line:
            output = "\n".join(output.splitlines()[i:previous_i])
            frames.append(output)
            previous_i = i
    print(frames[1])
    return get_info_from_frame(frames[0])

def get_info_from_frame(frame):
    """Extracts MAC and power from a single frame."""
    MAC_BLACKLIST = ["04:00"]
    clients = frame.splitlines()[2:]
    info = []
    for client in clients:
        c_info = client.split()
        for MAC in MAC_BLACKLIST:
            if MAC in c_info[0]:
                continue
        info.append(Client(c_info[0], int(c_info[2])))
    return info

def find_all_distances():
    ACTUALLY_GET_DATA = True

    client_dict = {}

    if ACTUALLY_GET_DATA:
        proc = subprocess.Popen(['airodump-ng', 'mon0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, universal_newlines=True)
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            out, err = proc.communicate()
        output = err
        with open("test.txt", "w") as f:
            f.write(output)
    else:
        with open("test.txt", "r") as f:
            output = f.read()

    clients = extract_client_info(output)
    for client in clients:
        print(client)

def main():
    find_all_distances()

if __name__=="__main__":
    main()
