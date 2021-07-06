from __future__ import unicode_literals

import os
import ctypes
import hashlib
from filecmp import cmp

SCRIPT_LOCATION = ""


def isAdmin():
    try:
        is_admin = (os.getuid() == 0)
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return is_admin

class FileFolder:
    def __init__(self, name, parent=None, **kwargs):
        assert isinstance(name, str)
        assert parent is None or isinstance(parent, FileFolder), "Was {} instead".format(type(parent))
        self.name = name
        self.parent = None
        if parent:
            parent.setChild(self)
        if os.path.isfile(self.path()):
            self.file = True
        else:
            self.file = False
        self.children = []


    def setChild(self, file):
        assert isinstance(file, FileFolder)
        self.children.append(file)
        file.parent = self

    def path(self):
        if self.parent:
            return os.path.join(self.parent.path(), self.name)
        else:
            return self.name
    def relativePath(self):
        if self.parent:
            return os.path.join(self.parent.relativePath(), self.name)
        else:
            return ""

    def __str__(self):
        return self.path()
    def __repr__(self):
        return str(self)




def hashFile(givenFile):
    assert isinstance(givenFile, str)
    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    if os.path.isdir(givenFile):
        return "folder"
    elif os.path.isfile(givenFile):
        try:
            with open(givenFile, 'rb', buffering=0) as f:
                for n in iter(lambda : f.readinto(mv), 0):
                    h.update(mv[:n])
        except:
            return "permission_denied"
    else:
        raise Exception("{} does not exist".format(givenFile))
    return h.hexdigest()

def compareFiles(file1, file2):
    return hashFile(file1) == hashFile(file2)


class HashStructure(FileFolder):
    def __init__(self, name, parent=None, **kwargs):
        super(HashStructure, self).__init__(name, parent, **kwargs)
        if name == ".":
            self.hash = "head"
        else:
            self.hash = hashFile(self.path())

class AppDataStructure(HashStructure):
    def __init__(self, name, parent=None, **kwargs):
        super(AppDataStructure, self).__init__(name, parent, **kwargs)

    def path(self):
        if self.parent:
            return os.path.join(self.parent.path(), self.name)
        else:
            return AppDataStructure.getRimworldConfigArea()
    @staticmethod
    def getRimworldConfigArea():
        roaming = os.getenv("APPDATA")
        app_data = "\\".join(roaming.split("\\")[:-1])
        return os.path.join(os.path.join(os.path.join(app_data, "LocalLow"), "Ludeon Studios"), "RimWorld by Ludeon Studios")


FILE_EXCEPTIONS = {"__pycache__", "Saves", "Scenarios", "MpReplays", "MpDesyncs", "Player.log", "Player-prev.log", ".gitignore", ".git", "rimlink.exe", "MonoBleedingEdge"}

from threading import Thread
from queue import Queue


class StructureBuilder:
    def __init__(self, relativePositionStart, parent=None, **kwargs):
        self.relativePositionStart = relativePositionStart
        self.parent = parent
        self.app_data = kwargs.get("app_data", False)
        self.MAX_THREADS = os.cpu_count() or 8
        self.TO_COMPLETE = Queue()
        if self.app_data:
            self.structureType = AppDataStructure
        else:
            self.structureType = HashStructure


    class SubstructureBuilder:
        def __init__(self, start, mainBuilder, parent):
            assert isinstance(mainBuilder, StructureBuilder)
            self.start = start
            self.mainBuilder = mainBuilder
            self.parent = parent

        @property
        def appData(self):
            return self.mainBuilder.app_data
        @property
        def structureType(self):
            return self.mainBuilder.structureType

        def execute(self):
            for file_name in os.listdir(self.start):
                if file_name in FILE_EXCEPTIONS:
                    continue
                file_name_path = os.path.join(self.start, file_name)
                isDir = os.path.isdir(file_name_path)
                newStructure = self.structureType(file_name, self.parent, app_data=self.appData) # TODO feed in isDir to speed up execution
                if isDir:
                    self.mainBuilder.generateSubstructure(file_name_path, newStructure)

    class StructureExecutor:
        def __init__(self, todoQ):
            self.todoQ = todoQ
        def run(self):
            substructureBuilder = self.todoQ.get()
            substructureBuilder.execute()
                
   
    def generateSubstructure(self, file_name_path, parent=None):
        if not parent:
            parent = self.parent
        self.TO_COMPLETE.put(self.SubstructureBuilder(file_name_path, self, parent))

    def run(self):
        if not self.parent:
            self.parent = self.structureType(self.relativePositionStart, None, app_data=self.app_data)
        self.generateSubstructure(self.relativePositionStart)
        executor = self.StructureExecutor(self.TO_COMPLETE)
        while self.TO_COMPLETE.qsize():
            executor.run()

        # self.TO_COMPLETE.join()
        return self.parent


def generateStructure(relativePositionStart, parent=None, **kwargs):

    builder = StructureBuilder(relativePositionStart, parent, **kwargs)
    return builder.run()
    # app_data = kwargs.get("app_data", False)
    # if app_data:
    #     StructureType = AppDataStructure
    # else:
    #     StructureType = HashStructure
    # if not parent:
    #     parent = StructureType(relativePositionStart, None, app_data=app_data)
    # assert isinstance(relativePositionStart, str)
    # assert isinstance(parent, FileFolder)
    # for file_name in os.listdir(relativePositionStart):
    #     if file_name in FILE_EXCEPTIONS:
    #         continue
    #     file_name_path = os.path.join(relativePositionStart, file_name)
    #     if not(os.path.isfile(file_name_path) or os.path.isdir(file_name_path)):
    #         continue
    #     file_folder = StructureType(file_name, parent, app_data=app_data)
    #     if os.path.isdir(os.path.join(relativePositionStart, file_name)):
    #         generateStructure(os.path.join(relativePositionStart, file_name), file_folder)
    # return parent

def getAllChildren(structure): # Includes the structure which initially calls the function as well
    assert isinstance(structure, FileFolder)
    return_list = [structure,]
    if structure.children:
        for child in structure.children:
            return_list.extend(getAllChildren(child))
    return return_list

def compareStructures(baseStructure, otherStructure, head=True):
    assert isinstance(baseStructure, HashStructure), "got {} instead".format(type(baseStructure))
    assert isinstance(otherStructure, HashStructure), "got {} instead".format(type(otherStructure))

    to_add = []
    to_modify = []
    to_delete = []

    assert isinstance(to_add, list)
    assert isinstance(to_modify, list)
    assert isinstance(to_delete, list)


    other_structure_dict = {}
    for item in otherStructure.children:
        other_structure_dict[item.relativePath()] = item

    for item in baseStructure.children:
        if item.relativePath() in other_structure_dict.keys():
            other_item = other_structure_dict[item.relativePath()]
            item_hash = item.hash
            other_hash = other_item.hash
            if item_hash != other_hash:
                to_modify.append(item)
            del other_structure_dict[item.relativePath()]
            if item.children:
                results = compareStructures(item, other_item, False)
                to_add.extend(results['add'])
                to_modify.extend(results['modify'])
                to_delete.extend(results['delete'])
        else:
            to_add.extend(getAllChildren(item))
            
    for item in other_structure_dict.values():
        to_delete.append(item)

    if head:
        return {
            "delete" : [x for x in to_delete],
            "modify" : [x for x in to_modify],
            "add" : [x for x in to_add],
        }      
    else:
        return {
            "delete" : to_delete,
            "modify" : to_modify,
            "add" : to_add,
        }      


