import gzip
import io
import os
import re
import glob
import csv

import logging
logger = logging.getLogger(__name__)

from kazi_log.lib.custom.formatting import withLoader

from rich.table import Table
from rich.console import Console
from rich import print as richprint
from simple_term_menu import TerminalMenu
import tabview
# ====================================================

#import os
#from simple_term_menu import TerminalMenu


def title(db=None):
    if db:
        db = f"Current DB: {db}"
    else:
        db = ""
    head=f'''=============================================================
____________   _   _             _             _             
|  _  \ ___ \ | \ | |           (_)           | |            
| | | | |_/ / |  \| | __ ___   ___  __ _  __ _| |_ ___  _ __ 
| | | | ___ \ | . ` |/ _` \ \ / / |/ _` |/ _` | __/ _ \| '__|
| |/ /| |_/ / | |\  | (_| |\ V /| | (_| | (_| | || (_) | |   
|___/ \____/  \_| \_/\__,_| \_/ |_|\__, |\__,_|\__\___/|_|   
                                    __/ |                    
                                   |___/                     
=============================================================
    Navigate using the Arrow Keys
    Enter to select | q to Go Back or Quit
    {db}
=============================================================
'''
    logger.info(f'-------------- Starting dbNavigator ------------------')
    return head

def display_file(tableName):
    tablePath = os.getcwd()+"/kazi_log_db/*/"+tableName
    console = Console()
    for filepath in glob.glob(tablePath):
        with open(filepath, "r") as f:
            file_content = csv.reader(f, delimiter="\t")
            
            table=Table(show_lines=True, header_style="bold magenta")
            headerList = next(file_content)
            for entry in headerList:
                table.add_column(entry,overflow="fold")
                
            for entry in file_content:
                table.add_row(*entry)

            with console.capture() as capture:
                console.print(table)
            tableStr = capture.get()
            return tableStr

def listDirs(directory="./kazi_log_db"):
    fileList = []
    for file in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, file)):
            fileList.append(file)
    return fileList

def listFiles(dirName):
    fileList = []
    directory=f"./kazi_log_db/{dirName}"
    for file in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, file)):
            fileList.append(file)
    fileList.sort()
    return fileList

def printFile(tableName):
    tablePath = os.getcwd()+"/kazi_log_db/*/"+tableName
    for filepath in glob.glob(tablePath):
        tabview.view(filepath)

def dbNavigator():

    mainMenu_title = title()
    mainMenu_exit = False
    mainMenu_dbItems = listDirs()
    tableMenu_back = False
    
    mainMenu = TerminalMenu(
        menu_entries=mainMenu_dbItems,
        title=mainMenu_title,
        cycle_cursor=True,
        clear_screen=True,
    )
    
    while not mainMenu_exit:
        dbSelection = mainMenu.show()
        subMenu_tableItems = listFiles(mainMenu_dbItems[dbSelection])
        subMenu = TerminalMenu(subMenu_tableItems, title=title({mainMenu_dbItems[dbSelection]}),
                             preview_command=display_file, preview_size=0.33)
        # subMenu = TerminalMenu(subMenu_tableItems, title=title({mainMenu_dbItems[dbSelection]}),quit_keys=("b") )
        while not tableMenu_back:
            tableSelection = subMenu.show()
            printFile(subMenu_tableItems[tableSelection])
            if tableSelection == None:
                tableMenu_back = True
        if dbSelection == None:
            mainMenu_exit = True
           

# Function to parse DB and create files per table
@withLoader(" Creating DB Tables and Files ... ")
def generateAllDbFiles():
    # Regex to get string between "(...)"
    regex_Bracket = r'\(.*?\)'
    # dbTableSkip = ['databasechangelog','databasechangeloglock','execution']
    try:
        logger.debug(f'Beginning to parse the DB from postgres-db-dump')
        # vcfVersion = vcfVersion
        try:
            dbDump = open("postgres-db-dump", "r")
            logger.info(f'File: postgres-db-dump opened successfully')
        except Exception as e:
            logger.warn(f'Failed to read postgres-db-dump file. Checking if gzipped file exists... ' + str(e))
        
        try:
            dbDump = gzip.GzipFile("postgres-db-dump.gz","r")
            dbDump = io.TextIOWrapper(dbDump)
            logger.info(f'File: postgres-db-dump.gz opened successfully')
        except Exception as e:
            logger.warn(f'Failed to read postgres-db-dump.gz file.' + str(e))
        
        try:
            for line in dbDump:
                # Search for line starting with "-- Data for Name"
                # For example: " -- Data for Name: vrslcm_operation; Type: TABLE DATA; Schema: public; Owner: platform "
                if ('Data for Name: ' in line):
                    line_split = line.split(";")
                    table_name = line_split[0].split(": ")[1]
                    schema_name = line_split[2].split(": ")[1]
                    db_name = line_split[3].split(": ")[1].replace("\n","")
                    # print(f'Working on Table: {table_name} | DB: {db_name}')
                    # Make the directories based on DB names
                    try:
                        logger.info(f"Creating the 'kazi_log_db/{db_name}' directory in current working directory.")
                        os.makedirs("kazi_log_db/"+db_name)
                    except:
                        logger.warning(f"Existing 'kazi_log_db/{db_name}' directory found ...")
                    try:    
                        while True:
                            entry = dbDump.readline()
                            if "COPY " in entry:
                                headerList = re.findall(regex_Bracket, entry)[0].replace("(","").replace(")","").replace(",","\t")
                                tableEntryMatrix = []
                                tableName = "kazi_log_db/"+db_name+"/"+table_name
                                while True:
                                    tableEntry = dbDump.readline()
                                    if '\.' in tableEntry:
                                        break
                                    tableEntryMatrix.append(tableEntry)

                                try:
                                    # table=Table(show_lines=True, header_style="bold magenta")
                                    # for entry in headerList:
                                    #     table.add_column(entry,overflow="fold")
                                        
                                    # for entry in tableEntryMatrix:
                                    #     table.add_row(*entry)
                                    
                                    with open(tableName, 'w') as tableWriter:
                                        tableWriter.write(headerList)
                                        tableWriter.write('\n')
                                        tableWriter.writelines(tableEntryMatrix)
                                except Exception as e:
                                    logger.error(f"Failed to write table. Error: {e}")
                                break
                    except Exception as e:
                        logger.error(f'Logic BooBoo. Error: {str(e)}')
                        #sys.exit(1)                                             
        except Exception as e:
            logger.error(f'Failed to generate dataframe. Error: {str(e)}')
        dbDump.close()
        logger.info(f'DB from postgres-db-dump parse completed.')
    except Exception as e:
        logger.error(f'Failed to read any postgres-db-dump files. Check if the file(s) exist. ' + str(e))
    print('\n All DB files and directories created. \n')

def dbTableParser(tableName, dbName):
    regex_Bracket = r'\(.*?\)'
    try:
        logger.debug(f'Beginning to parse the DB from postgres-db-dump')
        # vcfVersion = vcfVersion
        try:
            dbDump = open("postgres-db-dump", "r")
            logger.info(f'File: postgres-db-dump opened successfully')
        except Exception as e:
            logger.warn(f'Failed to read postgres-db-dump file. Checking if gzipped file exists... ' + str(e))
        
        try:
            dbDump = gzip.GzipFile("postgres-db-dump.gz","r")
            dbDump = io.TextIOWrapper(dbDump)
            logger.info(f'File: postgres-db-dump.gz opened successfully')
        except Exception as e:
            logger.warn(f'Failed to read postgres-db-dump.gz file.' + str(e))
        
        tableEntryMatrix = []
        headerList = ""
        try:
            for line in dbDump:
                # Search for line starting with "-- Data for Name"
                # For example: " -- Data for Name: vrslcm_operation; Type: TABLE DATA; Schema: public; Owner: platform "
                if ('Data for Name: ' in line) and (tableName in line) and (dbName in line):
                    line_split = line.split(";")
                    table_name = line_split[0].split(": ")[1]
                    db_name = line_split[3].split(": ")[1].replace("\n","")
                    if (tableName == table_name) and (db_name == dbName):
                        while True:
                            entry = dbDump.readline()
                            if "COPY " in entry:
                                headerList = re.findall(regex_Bracket, entry)[0].replace("(","").replace(")","").split(",")
                                tableEntryMatrix = []
                                while True:
                                    tableEntry = dbDump.readline()
                                    if '\.' in tableEntry:
                                        break
                                    tableEntryMatrix.append(tableEntry.split("\t"))
                                return headerList,tableEntryMatrix
                    else:
                        continue
                    
        except Exception as e:
            logger.error(f'Failed to generate dataframe. Error: {str(e)}')

        dbDump.close()
        logger.info(f'DB from postgres-db-dump parse completed.')   
    except Exception as e:
        logger.error(f'Failed to read any postgres-db-dump files. Check if the file(s) exist. ' + str(e))