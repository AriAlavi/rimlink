from __future__ import unicode_literals

import pyperclip
import asyncio
import re
import os
import time
import pickle
import socket
from shutil import rmtree

from rimlink import generateStructure, compareStructures, getRimworldConfigArea, isAdmin



PORT = 5002
IP_ADDRESS = None

def yesNoValidator(obj):
    if obj in ["y", "n"]:
        return True
    return False

def validateIP(givenIp):
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",givenIp):
        return True
    return False
    

def menu(prompt, validator, useClipboard=False):
    if useClipboard:
        input(prompt)
        result = pyperclip.paste()
    else:
        result = input(prompt + "\n")
    while not validator(result):
        if useClipboard:
            print("{} is invalid".format(pyperclip.paste()))
        else:
            print("Invalid input!")
        if useClipboard:
            input(prompt)
            result = pyperclip.paste()
        else:
            result = input(prompt + "\n")
    return result

def requireRimworldFolder():
    cwd = os.getcwd()
    if "Version.txt" not in os.listdir(cwd):
        return False
    return True


def hangForever():
    print("Execution complete.")
    while True:
        time.sleep(120)

def clientSyncFiles(to_delete, to_add, to_modify):
    to_delete.extend(to_modify)
    to_add.extend(to_modify)
    del to_modify
    folders = []
    for delete in to_delete:
        if not delete.file:
            folders.append(delete)
        else:
            os.remove(delete.relativePath())
    folders.sort(reverse=True, key=lambda x: x.relativePath().count("\\"))
    for folder in folders:
        rmtree(folder.relativePath())

    folders = []
    for add in to_add:
        if not add.file:
            folders.append(add)
    folders.sort(key=lambda x: x.relativePath().count("\\"))
    for folder in folders:
        to_add.remove(folder)
        os.mkdir(folder.relativePath())

    i = 0
    for file_name in to_add:
        s = socket.socket()
        s.connect((IP_ADDRESS, PORT))
        Server.clientRecieveFile(s, file_name.relativePath())
        s.close()
        i += 1
        if i % 100:
            print("{} files downloaded...".format(i))
    print("Done syncing files")
    # Server.clientSendString(s, to_add)

def automaticSync(packets):
    print()
    print("To delete:", ", ".join([x.relativePath() for x in packets['delete']]))
    print("To add:", ", ".join([x.relativePath() for x in packets['add']]))
    print("To replace:", ", ".join(["'" + x.relativePath() + "'" for x in packets['modify']]))
    files_to_modify = len(packets['delete']) + len(packets['add']) + len(packets['modify'])
    print("{} files to modify".format(files_to_modify))
    print()
    if files_to_modify == 0:
        return False
    automayic_sync = menu("Do you want to proceed? \n(y)es\n(n)o", yesNoValidator)
    if automayic_sync == "y":
        return True
    return False

def client():
    sync_config = menu("Do you want to sync config files as well? \n(y)es\n(n)o", yesNoValidator)
    if sync_config == "y":
        if not isAdmin():
            print("In order to sync config files the program must be run with administrator privileges.")
            hangForever()
        sync_config = True
    else:
        sync_config = False

    print("Analyzing rimworld...")
    my_structure = generateStructure(".")
    my_structure_pickled = pickle.dumps(my_structure)
    print("Connecting to host...")
    s = socket.socket()
    try:
        s.connect((IP_ADDRESS, PORT))
    except:
        print("No one is hosting at IP: {}:{}. Please check if the IP is valid and if there are firewalls up".format(IP_ADDRESS, PORT))
        return hangForever()
    print("Syncing files...")
    s.send(b"\x00") # Request comparison of Rimworld files
    Server.clientSendPickle(s, my_structure_pickled) # Send my Rimworld structure
    packets = Server.clientRecievePickle(s) # Recieve differences
    s.close()
    s = socket.socket()
    s.connect((IP_ADDRESS, PORT))
    if sync_config:
        my_config = generateStructure(getRimworldConfigArea(), app_data=getRimworldConfigArea())
        my_config_pickled = pickle.dumps(my_config)
        s.send(b"\02")
        Server.clientSendPickle(s, my_config_pickled)
        config_packets = Server.clientRecievePickle(s)
        packets['delete'].extend(config_packets['delete'])
        packets['add'].extend(config_packets['add'])
        packets['modify'].extend(config_packets['modify'])

    if automaticSync(packets):
        clientSyncFiles(packets['delete'], packets['add'], packets['modify'])
    print("Sync complete")
    hangForever()

class Server:
    @staticmethod
    def clientSendPickle(socket, pickled_data):
        assert isinstance(pickled_data, bytes)
        pickle_length = len(pickled_data)
        pickle_length_as_bytes = pickle_length.to_bytes(8, byteorder="big")
        socket.send(pickle_length_as_bytes)
        time.sleep(.1)
        socket.send(pickled_data)
        print("Data sent")

    @staticmethod
    def clientRecievePickle(socket):
        data_length_in_bytes = socket.recv(8)
        data_length = int.from_bytes(data_length_in_bytes, byteorder="big")
        BYTES_PER_TICK = 1024
        bytes_got = 0
        chunks = []
        while bytes_got < data_length:
            bytes_to_get = min(BYTES_PER_TICK, data_length - bytes_got)
            current = socket.recv(bytes_to_get)
            chunks.append(current)
            bytes_got += len(current)
        pickled_recieve = b"".join(chunks)
        unpickled_data = pickle.loads(pickled_recieve)
        return unpickled_data

    @staticmethod
    def clientSendString(socket, givenString):
        assert isinstance(givenString, str)
        encoded_string = givenString.encode()
        string_length = len(encoded_string)
        string_length_in_bytes = string_length.to_bytes(8, byteorder="big")
        socket.send(string_length_in_bytes)
        time.sleep(.1)
        socket.send(encoded_string)

    @staticmethod
    def clientRecieveFile(socket, filename):
        socket.send(b"\x01")
        Server.clientSendString(socket, filename)
        file_size_bytes = socket.recv(8)
        file_size = int.from_bytes(file_size_bytes, byteorder="big")
        bytes_recieved = 0
        file = open(filename, "wb")
        while bytes_recieved < file_size:
            current = socket.recv(1024)
            bytes_recieved += len(current)
            file.write(current)
        file.close()

    async def sendPickle(self, pickled_data, w):
        assert isinstance(pickled_data, bytes)
        pickle_length = len(pickled_data)
        pickle_length_as_bytes = pickle_length.to_bytes(8, byteorder="big")
        w.write(pickle_length_as_bytes)
        await w.drain()
        w.write(pickled_data)
        await w.drain()
        print("Data sent")

    async def recievePickle(self, r):
        pickled_recieve = await self.recieveData(r)
        unpickled_data = pickle.loads(pickled_recieve)
        return unpickled_data

    async def comparison(self, r, w):
        assert isinstance(r, asyncio.StreamReader)
        assert isinstance(w, asyncio.StreamWriter)
        other_structure = await self.recievePickle(r)
        differences = compareStructures(self.base_structure, other_structure)
        pickled_differences = pickle.dumps(differences)
        await self.sendPickle(pickled_differences, w)
        print("Seeking rimworld differences for {}".format(w.get_extra_info("peername")))

    async def recieveData(self, r):
        data_length_in_bytes = await r.read(8)
        data_length = int.from_bytes(data_length_in_bytes, byteorder="big")
        BYTES_PER_TICK = 1024
        bytes_got = 0
        chunks = []
        while bytes_got < data_length:
            bytes_to_get = min(BYTES_PER_TICK, data_length - bytes_got)
            current = await r.read(bytes_to_get)
            chunks.append(current)
            bytes_got += len(current)
        return b"".join(chunks)

    async def sendFile(self, r, w):
        file_name = await self.recieveData(r)
        file_name = file_name.decode()
        file_obj = open(file_name, "rb")
        file_bytes = file_obj.read()
        file_size = os.stat(file_name).st_size
        file_size_in_bytes = file_size.to_bytes(8, byteorder="big")
        w.write(file_size_in_bytes)
        await w.drain()
        w.write(file_bytes)
        await w.drain()
        file_obj.close()
        print("Sent {} to {}".format(file_name, w.get_extra_info("peername")))
            
    async def configComparison(self, r, w):
        other_structure = await self.recievePickle(r)
        differences = compareStructures(self.base_app_data_structure, other_structure)
        pickled_differences = pickle.dumps(differences)
        await self.sendPickle(pickled_differences, w)
        print("Seeking config differences for {}".format(w.get_extra_info("peername")))
    async def _handle_client(self, r, w):
        assert isinstance(r, asyncio.StreamReader)
        assert isinstance(w, asyncio.StreamWriter)
        # print("Connection recieved from {}".format(w.get_extra_info("peername")))
        BYTE_MAP = {
            b"\x00" : self.comparison,
            b"\x01" : self.sendFile,
            b"\x02" : self.configComparison,
        }
        try:
            what_you_want = await r.read(1)
            await BYTE_MAP[what_you_want](r, w)
        except ConnectionResetError:
            pass

    async def run(self):
        print("Analyzing rimworld...")
        self.base_structure = generateStructure(".")
        self.base_app_data_structure = generateStructure(getRimworldConfigArea(), app_data=getRimworldConfigArea())
        print("Ready to receive connections on {}:{}".format(IP_ADDRESS, PORT))
        await asyncio.start_server(self._handle_client, IP_ADDRESS, PORT)


def server():
    loop = asyncio.get_event_loop()
    server = Server()
    loop.run_until_complete(server.run())
    loop.run_forever()


def main():
    global IP_ADDRESS
    if not requireRimworldFolder():
        print("You must put this file into the top directory of the rimworld folder")
        time.sleep(3)
        return
    host = menu("Are you hosting the rimworld server?\n(y)es\n(n)o", yesNoValidator)
    if host == "y":
        ip_prompt = "your"
    else:
        ip_prompt ="the host's"
    IP_ADDRESS = menu("Please copy {} ip address into your clipboard and press enter".format(ip_prompt), validateIP, True)
    if host == "y":
        return server()
    else:
        return client()

if __name__ == "__main__":
    main()
