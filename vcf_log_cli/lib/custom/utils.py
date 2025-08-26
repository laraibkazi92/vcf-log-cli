import os
import pwd
import grp
import glob

from vcf_log_cli import __version__
from rich.table import Table
from rich import print as richprint
from rich.console import Console

from vcf_log_cli.lib.custom.formatting import FormatCodes

import logging
logger = logging.getLogger(__name__)

def printIntro():
    #os.system('clear')
    logger.info(f"Running vcf_log_cli {__version__}")
    print("""
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                    │
│  ██╗   ██╗ ██████╗███████╗    ██╗      ██████╗  ██████╗        ██████╗██╗     ██╗  │
│  ██║   ██║██╔════╝██╔════╝    ██║     ██╔═══██╗██╔════╝       ██╔════╝██║     ██║  │
│  ██║   ██║██║     █████╗█████╗██║     ██║   ██║██║  ███╗█████╗██║     ██║     ██║  │
│  ╚██╗ ██╔╝██║     ██╔══╝╚════╝██║     ██║   ██║██║   ██║╚════╝██║     ██║     ██║  │
│   ╚████╔╝ ╚██████╗██║         ███████╗╚██████╔╝╚██████╔╝      ╚██████╗███████╗██║  │
│    ╚═══╝   ╚═════╝╚═╝         ╚══════╝ ╚═════╝  ╚═════╝        ╚═════╝╚══════╝╚═╝  │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
 """)
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

def writeToResultsFile(content):
    with open("vcf_log_cli/results_file.txt", 'a') as resultsWriter:
        # for line in results:
        ## resultsWriter.write('\n'.join(content))
        # resultsWriter.write('\n')

        console = Console(file=resultsWriter, force_terminal=True)
        for line in content:
            console.print(line)
    
    # Debug: Log content after writing
    logger.debug(f"Content written to file. File exists: {os.path.exists('vcf_log_cli/results_file.txt')}")
    
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
