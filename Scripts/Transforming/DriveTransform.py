#!/usr/bin/env python3
'''
 * Author:    Samad Mazarei
 * Created:   10.4.2021
 * 
 * (c) Copyright - If you use my code please credit me.
'''
import os
from subprocess import Popen

ROOT_OF_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_PATH = os.path.join(ROOT_OF_REPO, "Data", "Raw", "Weekly")

def getListOfAllRawFilesRecursively(topLevelDir=RAW_PATH):
    rawFilesList = []
    # Retrieve all json data files under the <ROOT>/Data/Raw directory (Recurse)
    for current_dir, _, files in os.walk(topLevelDir):
        # Skip subdirs since we're only interested in files.
        for filename in files:
            if filename.endswith( '.json' ):
                relative_path = os.path.join( current_dir, filename )
                absolute_path = os.path.abspath( relative_path )
                rawFilesList.append(absolute_path)
    return rawFilesList

def main():
    filesList = getListOfAllRawFilesRecursively()
    # Execute Transform script on all files in files list
    for rawFile in filesList:
        p = Popen(["python3", "./Transform.py", rawFile])  
        p.wait()
 
# Entry point for script
if __name__ == "__main__":
    main()