from vcf_log_cli.db import dbTableParser
from vcf_log_cli.lib.custom.utils import displayTable, printTable

def workflow_taskData(wID, as_file):
    # The given workflow could be in the processing_context table
    # of either the domainmanager DB or the opsmgr db.
    # So we will need to check both 
    
    # Checking the domainmanager DB
    headerList,tableEntries = dbTableParser("processing_context","domainmanager")
    
    requiredHeaders = []
    requiredRows = []
    
    for index,header in enumerate(headerList):
        if header.replace(" ","") == 'id':
            id = index
        if header.replace(" ","") == 'processed_resource_type':
            processed_resource_type = index
        if header.replace(" ","") == 'processing_state_name':
            processing_state_name = index
        if header.replace(" ","") == 'processing_state_description':
            processing_state_description = index
        if header.replace(" ","") == 'status':
            status = index
        if header.replace(" ","") == 'execution_errors':
            execution_errors = index
        if header.replace(" ","") == 'execution_id':
            execution_id = index
            
    
    requiredHeaders = ["Sub-Task ID","Type","Sub-Task Name","Sub-Task Description","Sub-Task Status","Errors"]
    
    # headers=['Sub-Task ID','Type','Sub-Task Name', 'Sub-Task Description', 'Sub-Task Status', 'Errors']
    
    # COPY public.processing_context (id, execution_order, dal_version, execution_errors, execution_id, meta, next_processing_state, previous_processing_state, processed_resource_type, processing_state_description, processing_state_name, recipe_version, ref_id, sddc_id, status) FROM stdin;
    
    for entry in tableEntries:
        if wID == entry[execution_id]:
            requiredRows.append([entry[id], entry[processed_resource_type], entry[processing_state_name],
                             entry[processing_state_description], entry[status], entry[execution_errors]])
    
    # Check if no results from domainmanager DB
    # and then check against opsmgr
    if not requiredRows:
        headerList,tableEntries = dbTableParser("processing_context","opsmgr")
        
        for entry in tableEntries:
            if wID == entry[execution_id]:

                requiredRows.append([entry[id], entry[processed_resource_type], entry[processing_state_name],
                                entry[processing_state_description], entry[status], entry[execution_errors]])
        
    # Sorting by sub-task id:
    requiredRows = sorted(requiredRows, key=lambda x: x[0])
    
    if as_file is True:
        outputFileName = f"workflowSubtasks_{wID}.txt"
        printTable(f"Sub-Tasks for ID:{wID}", requiredHeaders, requiredRows, file=outputFileName)
    else:
        displayTable(f"Sub-Tasks for ID:{wID}", requiredHeaders, requiredRows)