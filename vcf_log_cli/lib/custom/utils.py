import os
import pwd
import grp
import glob

from vcf_log_cli import __version__
from rich.table import Table
from rich import print as richprint

from vcf_log_cli.lib.custom.formatting import FormatCodes

import logging
logger = logging.getLogger(__name__)

def printIntro():
    #os.system('clear')
    logger.info(f"Running vcf_log_cli {__version__}")
    print("""
 _                 _          _               
| |               (_)        | |              
| | __  __ _  ____ _  ______ | |  ___    __ _ 
| |/ / / _` ||_  /| ||______|| | / _ \  / _` |
|   < | (_| | / / | |        | || (_) || (_| |
|_|\_\ \__,_|/___||_|        |_| \___/  \__, |
                                         __/ |
                                        |___/ 
================================================""")
    print(f"\t\t{FormatCodes.BLUE}Version: {__version__}{FormatCodes.END}\n")
    logger.info("vcf_log_cli intro message printed")

# Function to delete the vcf_log_cli files and directores in the event of a re-run
def deleteExisting(dirName):
    dirPath = f"{os.getcwd()}/{dirName}/*"
    files = glob.glob(dirPath)
    for file in files:
        os.remove(file)
    
    logger.info(f"Deleting dir tree ./{dirName}")
    
def deleteExistingDB(dirName):
    dirPath = f"{os.getcwd()}/{dirName}/*/*"
    files = glob.glob(dirPath)
    for file in files:
        os.remove(file)
    
    logger.info(f"Deleting dir tree ./{dirName}")

# Function to update file ownership to support - Enabling other TSEs to run vcf_log_cli if its already run, or
# if someone else extracted the bundle
def updateFilePermissions():
    uid=pwd.getpwnam("svcdatamover").pw_uid
    gid=grp.getgrnam("om_vmware_support").gr_gid
    path='vcf_log_cli'
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            os.chown(dirpath, uid, gid)
            for filename in filenames:
                os.chown(os.path.join(dirpath, filename), uid, gid)
        logger.info("Changing file and dir permissions to allow write operations by group.")
    except Exception as e:
        logger.error(f"Failed to updates permissions. Error: {e}")

def writeToResultsFile(content):
    with open("vcf_log_cli/results_file.txt", 'a') as resultsWriter:
        #for line in results:
        resultsWriter.write('\n'.join(content))
        #resultsWriter.write('\n')
    content.clear()
    return content

def printTable(tableTitle, columns, rows, file=None):
    table=Table(title=FormatCodes.subtitle(tableTitle), title_justify="left", row_styles=["dim",""])
    for entry in columns:
        table.add_column(entry, overflow="fold")
    for entry in rows:
        table.add_row(*entry)
    
    if file is None:
        with open("vcf_log_cli/results_file.txt", 'a') as tableWriter:
            #print('\n', file=tableWriter)
            richprint(table, file=tableWriter)
    else:
        table.title=tableTitle
        with open(file, 'w') as tableWriter:
            #print('\n', file=tableWriter)
            richprint(table, file=tableWriter)

def displayTable(tableTitle, columns, rows):
    table=Table(title=FormatCodes.subtitle(tableTitle), title_justify="left", row_styles=["dim",""])
    for entry in columns:
        table.add_column(entry, overflow="fold")
    for entry in rows:
        table.add_row(*entry)
    
    richprint(table)
