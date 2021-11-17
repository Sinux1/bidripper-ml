#!/usr/bin/env python3

import os


ROOT_OF_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLEAN_PATH = os.path.join(ROOT_OF_REPO, "Data", "Clean", "Quartiles", "Weekly")
OUT_FILE_DIR = os.path.join(ROOT_OF_REPO, "MLPipeline", "training", "train")
os.makedirs(OUT_FILE_DIR, exist_ok=True)
OUT_FILE_PATH = os.path.join(OUT_FILE_DIR, "trainingData.csv")

def getListOfAllCleanFilesRecursively(topLevelDir=CLEAN_PATH):
    rawFilesList = []
    for current_dir, _, files in os.walk(topLevelDir):
        # Skip subdirs since we're only interested in files.
        for filename in files:
            if filename.endswith( '.csv' ):
                relative_path = os.path.join( current_dir, filename )
                absolute_path = os.path.abspath( relative_path )
                rawFilesList.append(absolute_path)
    return rawFilesList

def main():
    # Get list of clean csv files and sort them in ascending order (File names are dates, this effectively puts the files in order by date)
    cleanList = sorted(getListOfAllCleanFilesRecursively())
    with open(OUT_FILE_PATH, 'w') as of:
        for f in cleanList:
            with open(f, 'r') as rf:
                contents = rf.read()
                of.write(f'{contents}')

if __name__ == "__main__":
    main()