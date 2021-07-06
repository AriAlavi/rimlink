from __future__ import unicode_literals

from rimlink import *
from main import clientSyncFiles

import unittest
import os

class TestFileComparison(unittest.TestCase):
    FILE_LOCATION = "test_files/"

    def test_text_self_comparison(self):
        file = os.path.join(self.FILE_LOCATION, "text_case.txt")
        self.assertTrue(compareFiles(file, file))
    def test_text_same_comparison(self):
        file1 = os.path.join(self.FILE_LOCATION, "text_case.txt")
        file2 = os.path.join(self.FILE_LOCATION, "text_case_copy.txt")
        self.assertTrue(compareFiles(file1, file2))
    def test_text_different_comparison(self):
        file1 = os.path.join(self.FILE_LOCATION, "text_case.txt")
        file2 = os.path.join(self.FILE_LOCATION, "text_case_different.txt")
        self.assertFalse(compareFiles(file1, file2))
    def test_exe_self_comparison(self):
        file = os.path.join(self.FILE_LOCATION, "exe_case.exe")
        self.assertTrue(compareFiles(file, file))
    def test_exe_same_comparison(self):
        file1 = os.path.join(self.FILE_LOCATION, "exe_case.exe")
        file2 = os.path.join(self.FILE_LOCATION, "exe_case_copy.exe")
        self.assertTrue(compareFiles(file1, file2))
    def test_exe_different_comparison(self):
        file1 = os.path.join(self.FILE_LOCATION, "exe_case.exe")
        file2 = os.path.join(self.FILE_LOCATION, "dll_case.dll")
        self.assertFalse(compareFiles(file1, file2))

class FileFolderTest(unittest.TestCase):
    def test_single(self):
        file = FileFolder("test.exe")
        self.assertEqual(file.path(), "test.exe")
    def test_branch(self):
        parent = FileFolder("parent")
        child = FileFolder("child.exe", parent)
        self.assertEqual(child.path(), r"parent\child.exe")
    def test_relative(self):
        head = generateStructure(".")
        for file in head.children:
            assert isinstance(file, FileFolder)
            if file.name == "test_files":
                for inner_file in file.children:
                    assert isinstance(inner_file, FileFolder)
                    if inner_file.name == "text_case.txt":
                        self.assertEqual(inner_file.relativePath(), r"test_files\text_case.txt")
                break

class StructureGenerationTest(unittest.TestCase):
    def test(self):
        structure = "test_files"
        parent = FileFolder(structure)
        result = generateStructure(structure, parent)
        for x in result.children:
            self.assertTrue(os.path.isfile(x.path()) or os.path.isdir(x.path()), "{} does not exist".format(x.path()))
    def test_different_head(self):
        FILE_LOCATION = "test_files/"
        baseHead = generateStructure(".")
        differentHead = generateStructure(FILE_LOCATION)
        self.assertNotEqual(baseHead.path(), differentHead.path())
    def test_different_head_deeper(self):
        FILE_LOCATION = "test_files/RimworldBase/"
        baseHead = generateStructure(".")
        differentHead = generateStructure(FILE_LOCATION)
        self.assertNotEqual(baseHead.path(), differentHead.path())
    def test_weird_file(self):
        FILE_LOCATION = "test_files/WeirdFileTest/"
        parent = generateStructure(FILE_LOCATION)
        self.assertEqual(len(parent.children), 1)
        self.assertTrue(parent.children[0].file)
    def test_non_ascii_folder(self):
        FILE_LOCATION = "test_files/NonAsciiFileTest/"
        parent = generateStructure(FILE_LOCATION)
        self.assertEqual(len(parent.children), 1)
        Spanish = parent.children[0]
        self.assertFalse(Spanish.file)
        self.assertEqual(len(Spanish.children), 2)
        

class StructureComparisonTest(unittest.TestCase):
    FILE_LOCATION = "test_files/"
    BASE_FOLDER = FILE_LOCATION + "RimworldBase/"
    BASE_HEAD = generateStructure(BASE_FOLDER)
    def getResults(self, other_location):
        otherHead = generateStructure(os.path.join(self.FILE_LOCATION, other_location))
        as_objs = compareStructures(self.BASE_HEAD, otherHead)
        return {
            "delete" : [x.relativePath() for x in as_objs['delete']],
            "modify" : [x.relativePath() for x in as_objs['modify']],
            "add" : [x.relativePath() for x in as_objs['add']],
        }
    def test_same_contents(self):
        OTHER_LOCATION = "RimworldBaseCopy/"
        results = self.getResults(OTHER_LOCATION)
        self.assertEqual(results['delete'], [])
        self.assertEqual(results['modify'], [])
        self.assertEqual(results['add'], [])
    def test_missing_bye(self):
        OTHER_LOCATION = "RimworldMissingBye/"
        results = self.getResults(OTHER_LOCATION)
        self.assertEqual(results['delete'], [])
        self.assertEqual(results['modify'], [])
        self.assertEqual(results['add'], ["bye.py"])
    def test_missing_deep(self):
        OTHER_LOCATION = "RimworldMissingDeep/"
        results = self.getResults(OTHER_LOCATION)
        self.assertEqual(results['delete'], [])
        self.assertEqual(results['modify'], [])
        self.assertEqual(results['add'], [r"Interior\deep\hihi.txt"])
    def test_missing_interior(self):
        OTHER_LOCATION = "RimworldMissingInterior/"
        results = self.getResults(OTHER_LOCATION)
        self.assertEqual(results['delete'], [])
        self.assertEqual(results['modify'], [])
        self.assertEqual(results['add'], ["Interior", r"Interior\deep", r"Interior\deep\hihi.txt", r"Interior\empty", r"Interior\hihi.txt"])
    def test_missing_lots(self):
        OTHER_LOCATION = "RimworldMissingInteriorExterior/"
        results = self.getResults(OTHER_LOCATION)
        self.assertEqual(results['delete'], [])
        self.assertEqual(results['modify'], [])
        self.assertEqual(results['add'], ["hi.txt", "Interior", r"Interior\deep", r"Interior\deep\hihi.txt", r"Interior\empty", r"Interior\hihi.txt"])
    def test_extra_file(self):
        OTHER_LOCATION = "RimworldExtraGoodbye/"
        results = self.getResults(OTHER_LOCATION)
        self.assertEqual(results['delete'], ["goodbye.txt"])
        self.assertEqual(results['modify'], [])
        self.assertEqual(results['add'], [])  
    def test_different_file(self):
        OTHER_LOCATION = "RimworldDifferentHi/"
        results = self.getResults(OTHER_LOCATION)
        self.assertEqual(results['delete'], [])
        self.assertEqual(results['modify'], ["hi.txt"])
        self.assertEqual(results['add'], [])   
    def test_different_deep(self):
        OTHER_LOCATION = "RimworldDifferentDeep/"
        results = self.getResults(OTHER_LOCATION)
        self.assertEqual(results['delete'], [])
        self.assertEqual(results['modify'], [r"Interior\deep\hihi.txt"])
        self.assertEqual(results['add'], [])  
    def test_app_data(self):
        TOP_LOCATION = AppDataStructure.getRimworldConfigArea()
        INNER_LOCATION = os.path.join(TOP_LOCATION, "testing")
        try:
            os.mkdir(INNER_LOCATION)
        except FileExistsError:
            pass
        add = os.path.join(TOP_LOCATION, "add.txt")
        add_inner = os.path.join(INNER_LOCATION, "add_inner.txt")
        file = open(add, "w")
        file.write("testing")
        file.close()
        file = open(add_inner, "w")
        file.write("testing")
        file.close()
        base_structure = generateStructure(AppDataStructure.getRimworldConfigArea(), app_data=AppDataStructure.getRimworldConfigArea())

        os.remove(add)
        os.remove(add_inner)

        after_structure = generateStructure(AppDataStructure.getRimworldConfigArea(), app_data=AppDataStructure.getRimworldConfigArea())

        results = compareStructures(base_structure, after_structure)

        try:
            os.remove(INNER_LOCATION)
        except PermissionError:
            pass
        self.assertEqual(results['delete'], [])
        self.assertEqual(results['modify'], [])
        self.maxDiff = None
        self.assertEqual([x.path() for x in results['add']], [add, add_inner])  

    def test_different_app_data(self):
        APP_DATA_BASE = "test_files/FakeAppData1/"
        APP_DATA_DIFFERENT = "test_files/FakeAppData2/"

        file_name = "different.txt"
        file = open(os.path.join(APP_DATA_BASE, file_name), "w")
        file.write("good")
        file.close()
        file = open(os.path.join(APP_DATA_DIFFERENT, file_name), "w")
        file.write("bad")
        file.close()
        AppDataStructure.getRimworldConfigArea = lambda : APP_DATA_BASE
        base_structure = generateStructure(APP_DATA_BASE, app_data=APP_DATA_BASE)
        AppDataStructure.getRimworldConfigArea = lambda : APP_DATA_DIFFERENT
        different_structure = generateStructure(APP_DATA_DIFFERENT, app_data=APP_DATA_DIFFERENT)
        
        results = compareStructures(base_structure, different_structure)
        self.assertEqual(results['modify'][0].path(), 'test_files/FakeAppData2/different.txt')
        to_download = clientSyncFiles(results['delete'], results['add'], results['modify'], testing=True)
        self.assertEqual(to_download[0].relativePath(), "different.txt")

class IsFileTest(unittest.TestCase):
    def test_is_file(self):
        self.assertTrue(FileFolder("test_files\\dll_case.dll").file)
        self.assertTrue(FileFolder("test_files\\exe_case.exe").file)
        self.assertTrue(FileFolder("test_files\\text_case.txt").file)
        self.assertTrue(FileFolder("test_files\\RimworldBase\\hi.txt").file)
        
    def test_is_not_file(self):
        self.assertFalse(FileFolder("test_files").file)
        self.assertFalse(FileFolder("test_files\\RimworldBase").file)
        self.assertFalse(FileFolder("test_files\\RimworldBase\\Interior").file)
        self.assertFalse(FileFolder("test_files\\RimworldBase\\empty").file)

    def test_file_indirect(self):
        config_location = AppDataStructure.getRimworldConfigArea()
        parent = generateStructure(config_location, app_data=config_location)
        self.assertFalse(parent.file)
        for child in parent.children:
            if "Config" in child.name:
                self.assertFalse(child.file)
            elif "Player.log" in child.name:
                self.assertTrue(child.file)

class SpeedTests(unittest.TestCase):
    def test_speed_of_generate_tree_and_compare_tree(self):
        from shutil import rmtree
        from random import randint, choice
        from string import ascii_letters
        from statistics import mean
        import time
        LOCATION = "test_files/SpeedTest1/"
        LOCATION2 = "test_files/SpeedTest2/"
        ALREADY_DONE = False
        try:
            os.mkdir("test_files/SpeedTest1")
            os.mkdir("test_files/SpeedTest2")
        except FileExistsError:
            ALREADY_DONE = True

        def createSpeedtest(location):
            for x in range(30):
                newFolder = os.path.join(location, str(x))
                try:
                    os.mkdir(newFolder)
                except FileExistsError:
                    pass
                for i in range(randint(0, 20)):
                    fileName = os.path.join(newFolder, "{}.txt".format(i))
                    TEXT = "".join(ascii_letters for i in range(randint(0, 10) ** randint(1, 7)))
                    file = open(fileName, "w")
                    file.write(TEXT)
                    file.close()
            
        if not ALREADY_DONE:
            print("\nMust create speed test tree. This will take some time. This only needs to be ran once.")
            createSpeedtest(LOCATION)
            print(r"50% done creating tree")
            createSpeedtest(LOCATION2)

        TRAIL_COUNT = 5
        RESULTS = []
        for _ in range(TRAIL_COUNT):
            t0 = time.time()
            base_structure = generateStructure(LOCATION)
            other_structure = generateStructure(LOCATION2)
            compareStructures(base_structure, other_structure)
            RESULTS.append(time.time()-t0)
        print("\n{} seconds on the speedtest".format(mean(RESULTS)))

if __name__ == '__main__':
    unittest.main()