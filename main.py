#!/usr/bin/env python3
import subprocess
import time
import os
import signal

from itertools import *
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
        return calculate_wifi_distance(self.power, 2462)

def calculate_wifi_distance(strength, freq):
    # http://rvmiller.com/2013/05/part-1-wifi-based-trilateration-on-android/
    exp = (27.55 - (20*log10(freq)) + abs(strength))/20.0;
    return pow(10.0, exp)

def extract_client_info(output):
    """Extracts MAC and power for each client
    from airodump-ng output."""
    frames = []
    lines = output.splitlines()
    previous_i = -1
    for i, line in reversed(list(enumerate(lines))):
        if "RTS_RX" in line:
            output = "\n".join(lines[i:previous_i-4])
            print(output)
            frames.append(get_info_from_frame(output))
            previous_i = i
    return merge_frames(frames)

def merge_frames(frames):
    """Helper function for extract_client_info() that
    merges client data from all the captured frames into
    one client data object for each MAC address, with
    power equal to the highest power found in the frames."""
    flattened = sorted(chain.from_iterable(frames), key=lambda f: f.mac) # flatten the clients into one list and sort for grouping
    grouped = [list(g[1]) for g in groupby(flattened, lambda f: f.mac)] # group clients by MAC

    merged = []
    for group in grouped:
        MAC = group[0].mac
        power_list = map(lambda f: f.power, group)
        max_power = max(power_list)
        merged.append(Client(MAC, max_power))

    return merged

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
        proc = subprocess.Popen(['airodump-ng', '-c 11', 'mon0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, universal_newlines=True)
        try:
            out, err = proc.communicate(timeout=20)
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
    print("-----------")

def main():
    for _ in range(15):
        find_all_distances()

if __name__=="__main__":
    main()
