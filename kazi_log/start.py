import os
import sys
import time
from datetime import datetime
import curses

import logging
logfile = 'kazi-log.log'
logging.basicConfig(filename=logfile, filemode='w', level = logging.DEBUG,
                    format='%(asctime)s [%(levelname)s]: %(message)s', datefmt= '%m-%d-%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

from kazi_log import __serviceLogs__ as serviceLogs
from kazi_log.upgradeHelperOffline import main as upgradeHelperOffline
from kazi_log.lib.custom.utils import deleteExisting,updateFilePermissions, printIntro
from kazi_log.lib.custom.formatting import FormatCodes
from kazi_log.lib.snake_cli.snake import runGame
from kazi_log.logfiles import searchLogFiles, createdotAllFiles, createdotErrorFiles
from kazi_log.results import resultsEnvSummary
from kazi_log.db import generateAllDbFiles, dbNavigator
from kazi_log.workflow import workflow_taskData

import typer
from click import Context
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from typing_extensions import Annotated

class OrderCommands(typer.core.TyperGroup):
  def list_commands(self, ctx: Context):
    return list(self.commands)

app = typer.Typer(add_completion=False,
                  no_args_is_help=True,
                  cls=OrderCommands)

@app.command()
def parseLogs(errorfiles: Annotated[bool, typer.Option(help="Generates .error files for services")] = False,
              snake: Annotated[bool, typer.Option(hidden=True)] = False):
    """
    Creates a .results file and .all files for all services
    """
    
    if snake is True:
        runGame()
        sys.exit(0)
        
    start_time = time.time()
    logger.debug(f'Beginning execution of kazi-log for SDDC Manager at: {start_time}')
    
    printIntro()
    
    if errorfiles is True:
        print(f'{FormatCodes.info(" The --errorfiles flag will aggregate ERROR messages across multiple log files in .error files.")}')
        print(f'{FormatCodes.info(" This process can take several minutes to complete.")}')
        proceed = input("\n Continue (y/n)? ")
        if proceed.lower() != 'y':
            print("\n  Not running kazi_log...")
            print(" .... exiting ....\n")
            logger.info("Decline to run with --errorfiles. Terminating script.")
            exit(0)
    
    # Create output directory and check for existing run
    try:
        os.mkdir("kazi_log")
        logger.info("Creating the 'kazi_log' directory in current working directory.")
    except:
        logger.error("Existing 'kazi_log' directory found ...")
        rerun = input("\n Looks like kazi_log has already been run, would you like to rerun (y/n)? ")
        if rerun.lower() != 'y':
            print("\n  Not running kazi_log...")
            print(" .... exiting ....\n")
            logger.info("Re-run not selected. Terminating script.")
            exit(0)
        try:
            deleteExisting("kazi_log")
            os.mkdir("kazi_log")
            logger.info("Creating the 'kazi_log' directory in current working directory.")
        except Exception as e:
            logger.error(f"Unable to blank out the files. Error: {e}")
    
    print("")
    
    all_progress = Progress("{task.description}",
                                SpinnerColumn(),
                                BarColumn(),
                                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),)
    
    resultsProgress = all_progress.add_task(f"Creating results file", total=15)    
    
    jobDict = {}
    for service in serviceLogs:
        jobDict[service] = all_progress.add_task(f"Creating .all file for {service}", total=18)
        
    #print(f'Error Files: {errorfiles}')   
    if errorfiles is True:
        error_progress = Progress("{task.description}",
                                SpinnerColumn(),
                                BarColumn(),
                                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),)
        
        errorJobDict = {}
        for service in serviceLogs:
            errorJobDict[service] = error_progress.add_task(f"Creating .error file for {service}", total=50)
        
    #total = sum(task.total for task in all_progress.tasks)
    #overall_progress = Progress()
    #overall_task = overall_progress.add_task("All Jobs", total=int(total))

    progress_table = Table.grid()
    
    if errorfiles is True:
            progress_table.add_row(
                Panel.fit(all_progress, title="[b]Results and .all Files", border_style="red", padding=(1, 2)),
                Panel.fit(error_progress, title="[b].error files", border_style="green", padding=(2, 1)),
                )
    else:
        progress_table.add_row(
                Panel.fit(all_progress, title="[b]Results and .all Files", border_style="red", padding=(1, 2)),
        )
    
    
    with Live(progress_table, refresh_per_second=10):
        #while not overall_progress.finished:
        time.sleep(0.1)
        
        # Generating Results file
        try:
            resultsEnvSummary(resultsProgress,all_progress)
            logger.info("'results_file.txt' generated successfully.")
        except Exception as e:
            logger.error(f'Failed to create results_file.txt '+str(e))
        
        for service in serviceLogs:
            logger.info(f'Working on service:{service} defined in service_list.')
            #print(f'\nWorking on Logs for Service: {service}')
            
            # Looking for the var/log/vmware/vcf/lcm directory
            try:
                serv_filepath,file_list = searchLogFiles(service,jobDict,all_progress)
                logger.info(f'Log files and directory found for service:{service}')
                createdotAllFiles(service,serv_filepath,file_list,jobDict,all_progress)
                if errorfiles is True:
                    createdotErrorFiles(service,serv_filepath,file_list,errorJobDict,error_progress)  
            except:
                logger.error(f'Failed to find log directory for service:{service}')
            # print(f"Service: {service}\nFilePath: {serv_filepath}\nFile List:{file_list}")
            
           # completed = sum(task.completed for task in all_progress.tasks)
            #overall_progress.update(overall_task, completed=100)
    
    updateFilePermissions()
    logger.debug("File permissions updated for all files in ./kazi_log")

    print("\nCompleted in %s seconds." % "{:.2f}".format(time.time() - start_time))
    print("Output files available in "+os.getcwd()+"/kazi_log/ \n")
    logger.info("Execution complete. Terminating ...")
    
@app.command()
def upgradeHelper():
    """
    Runs offline version of upgradeHelper
    """
    printIntro()
    upgradeHelperOffline()
    sys.exit(0)
             
@app.command()
def database(recreate: Annotated[bool, typer.Option(help="Scans the DB dump and re-creates the DB files and directories")] = False):
    """
    Runs a visual Database Table Navigator
    """
    printIntro()
    
    try:
        os.mkdir("kazi_log_db")
        logger.info("Creating the 'kazi_log_db' directory in current working directory.")
        generateAllDbFiles()
    except:
        if recreate is True:
            logger.error("Existing 'kazi_log_db' directory found ...")
            rerun = input("\n Parsed Database files found, would you like to re-create them (y/n)? ")
            if rerun.lower() != 'y':
                print("\n  Not running kazi_log...")
                print(" .... exiting ....\n")
                logger.info("Re-run not selected. Terminating script.")
                exit(0)
            # try:
            #     deleteExistingDB("kazi_log_db")
            #     os.mkdir("kazi_log_db")
            #     logger.info("Creating the 'kazi_log_db' directory in current working directory.")
            # except Exception as e:
            #     logger.error(f"Unable to blank out the files. Error: {e}")
            generateAllDbFiles()
    
    try:
        dbNavigator()
    except Exception as e:
        logger.debug("Interrupted.")
    
    sys.exit(0)
    
@app.command()
def workflow(id: Annotated[str, typer.Option(help="ID of the workflow identified from the results file",prompt="Enter the Workflow ID")] = "",
             as_file: Annotated[bool, typer.Option(help="Generates a file with all sub-task details for a given workflow ID")] = False):
    """
    Collects subtask details for a given workflow ID
    """
    printIntro()
    try:
        workflow_taskData(id, as_file)
    except Exception as e:
        logger.error(f'Failed to get subtask details for Workflow {e}')
    
    sys.exit(0)

if __name__ == '__main__':
    app()
    
# TODO:
# - results - vrslcm
# - results - vrops
# - results - vrli
# - results - wsa
# - results - vra