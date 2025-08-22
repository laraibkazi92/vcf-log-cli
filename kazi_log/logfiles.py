import os
import gzip
import io

import logging
logger = logging.getLogger(__name__)

from kazi_log.lib.custom.signatures import FalsePositives

# Function to search for the location of the log files        
def searchLogFiles(service,jobDict,allFile_progress):
    cwd = os.getcwd()
    serv_filepath = ''
    logger.debug(f'Searching for log files for service: {service}')
    
    try:
        for dirname, dirs, files in os.walk(cwd):
            for name in dirs:
                if name == service:
                        if 'var/log/vmware' in dirname:
                            for dirname2, dirs2, files2 in os.walk(dirname+'/'+service):
                                if (f'{service}.log') in files2 or (f'vcf-{service}.log') in files2:
                                    #serv_filepath = dirname+'/'+service+'/'
                                    serv_filepath = dirname2+'/'
        logger.info(f'File path for {service} found: {serv_filepath}')
    except Exception as e:
        logger.error(f'Unable to find file path for {service}. ' + str(e))
    allFile_progress.update(jobDict[service], description=f"{service} | Searching for log files", advance=1)
    # print(f"Directory Path: {serv_filepath}")
    # Ignore unwanted files
    ignore_files=["out","activity","backup","event","prev","old","debug"]
    file_list = []

    # Searching for only the specific service *.log files across several dates
    try:
        for file in os.listdir(serv_filepath):
            if ((file.endswith('.log') or file.endswith('.gz')) and all(entry not in file for entry in ignore_files)) and file.__contains__(service):
                logger.debug(f'Adding file: {file} to the file_list to parse logs for.')
                file_list.append(file)
            allFile_progress.update(jobDict[service], advance=0.01)
        logger.info(f'All required log files added to parse file_list.')
        
    except Exception as e:
        logger.error(f'Unable to parse through files in {serv_filepath}. Unable to generate file_list. ' + str(e))

    #print(f"FileList: {file_list}")

    # Sorting file by date (newest at the bottom)
    file_list.sort()
    allFile_progress.update(jobDict[service], description=f"{service} | Log Files found", advance=1)
    
    logger.debug(f'Sorting files by date to have all data sorted by date.')

    return serv_filepath,file_list

def createdotAllFiles(service,serv_filepath,file_list,jobDict,allFile_progress):
    
    filesFordotAll=[]
    try:
        for file in file_list[-10:]:
            filesFordotAll.append(file)
        logger.info(f'10 latest log files determined to be added to .all file.')
    except Exception as e:
        logger.error(f'Unable to get last file files to be appended to .all. '+ str(e))
    
    allFile_progress.update(jobDict[service], advance=1)
    
    
    # if len(file_list)>50:
    #     logger.warn(f'Warning: {len(file_list)} log files found for service {service}. Parsing through only the newest 50 files.')
    #     print(f'Warning: {len(file_list)} log files found for service {service}. Parsing through only the newest 50 files.')
    #     file_list=file_list[-50:]
    
    logger.debug(f'Reading through all required log files for service: {service}')
    allFile_progress.update(jobDict[service], description=f"{service} | Adding Files to .all file")
    
    try:
        for file in filesFordotAll:
            serv_file = serv_filepath+file
            try:
                if file.endswith('.log'):
                    servFile = open(serv_file,"r",errors='ignore')
                elif file.endswith('.gz'):
                    servFile = gzip.GzipFile(serv_file,"r")
                    servFile = io.TextIOWrapper(servFile)
                logger.info(f'Opening file: {servFile}')
            except Exception as e:
                logger.error(f'Unable to open file: {servFile}. '+ str(e))
            
            # Parsing through every line of line to process revelant error message entries
            try:
                with open(f"./kazi_log/{service}.all", "a") as allFile:
                    for line in servFile:
                        allFile.write(line)
                    allFile_progress.update(jobDict[service], advance=1)
                    
            except Exception as e:
                logger.error(f'Failed to add to .all file for file: {file}. '+ str(e))
            
            # if file.endswith('.log'):
            #     servFile.close()
            # if file.endswith('.gz'):
            #     servFile.close()
            servFile.close()
        logger.info(f'All files in file_list for service: {service} parsed successfully.')
    except Exception as e:
        logger.error(f'Unable to parse through file list for service: {service} '+ str(e))
    allFile_progress.update(jobDict[service], description=f"{service} | .all file created", completed=100)
    
def createdotErrorFiles(service,serv_filepath,file_list,errorJobDict,error_progress):
    
    try:
        signatures = FalsePositives(service)
        logger.debug(f'Signatures for {service} loaded: {signatures}')
    except Exception as e:
        signatures = []
        logger.error(f'Failed to load signatures. Error: {e}')
    
    error_progress.update(errorJobDict[service], description=f"{service} | Adding entries to .error file")
    
    try:
        for file in file_list[-40:]:
            serv_file = serv_filepath+file
            try:
                if file.endswith('.log'):
                    servFile = open(serv_file,"r",errors='ignore')
                elif file.endswith('.gz'):
                    servFile = gzip.GzipFile(serv_file,"r")
                    servFile = io.TextIOWrapper(servFile)
                logger.info(f'Opening file: {servFile}')
            except Exception as e:
                logger.error(f'Unable to open file: {servFile}. '+ str(e))
            
            try:
                with open(f'./kazi_log/{service}.error', 'a') as errorFile:
                    for line in servFile:
                        if (line.startswith("20")) and (" ERROR " in line):
                            if all(x not in line for x in signatures):
                                errorFile.write(line)
                    error_progress.update(errorJobDict[service], advance=1)
                        
            except Exception as e:
                logger.error(f'Failed to add to .error file for file: {file}. '+ str(e))
            servFile.close()
        logger.info(f'All files in file_list for service: {service} parsed successfully.')
    except Exception as e:
        logger.error(f'Unable to parse through file list for service: {service} '+ str(e))
    error_progress.update(errorJobDict[service], description=f"{service} | .error file created", completed=100)