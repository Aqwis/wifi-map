#!/usr/bin/env python3
import subprocess
import time
import os
import signal
import json

from statistics import mean, median
from itertools import *
from math import log, log10, pow
from timeit import default_timer as timer
from urllib.request import urlopen

vendor_cache = {}

class Client(object):
    def __init__(self, mac, power):
        self.mac = mac
        self.power = power
        self.timestamp = time.clock()

    def __str__(self):
        return "%s (%s), %d: %.2f meter" % (self.mac, self.vendor, self.power, self.distance)

    @property
    def distance(self):
        return calculate_wifi_distance(self.power, 2462)

    @property
    def vendor(self):
        if not self.mac in vendor_cache:
            raw_json = str(urlopen("http://www.macvendorlookup.com/api/v2/" + self.mac).read())[2:-1]
            info = json.loads(raw_json)
            company = info[0]["company"]
            vendor_cache[self.mac] = company
        else:
            company = vendor_cache[self.mac]
        return company

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
        power_list = list(map(lambda f: f.power, group))
        max_power = max(power_list)
        mean_power = median(power_list)
        merged.append(Client(MAC, mean_power))

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

def fetch_data(timeout=10):
    proc = subprocess.Popen(['airodump-ng', '-c 11', 'mon0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, universal_newlines=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGTERM)
        out, err = proc.communicate()
    return err

def find_all_distances():
    ACTUALLY_GET_DATA = False

    client_dict = {}

    if ACTUALLY_GET_DATA:
        output = fetch_data(timeout=20)
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
    for _ in range(8):
        find_all_distances()

if __name__ == "__main__":
    main()
