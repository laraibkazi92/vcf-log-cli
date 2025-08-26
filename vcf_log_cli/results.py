import json
import os
import operator
import typer

from datetime import datetime
from pathlib import Path

from vcf_log_cli.lib.custom.formatting import FormatCodes
from vcf_log_cli.lib.custom.utils import writeToResultsFile, printTable
from vcf_log_cli.db import dbTableParser

import logging
logger = logging.getLogger(__name__)

def sddcManager_resultsData():
    content = []
    
    content.append(FormatCodes.title("VCF Environment Summary:"))
    
    # Collecting SDDC Manager information from inventory-sddcmanagercontrollers.log
    content.append(FormatCodes.subtitle('SDDC Manager'))
    try:
        inventory_filePath=os.getcwd()+"/api-logs/domain_manager/inventory-sddcmanagercontrollers.log"
        with open(inventory_filePath,"r") as f:
            data = f.read()
            data_elements = json.loads(data.replace("[","").replace("]",""))
        content.append(f"Hostname: "+data_elements['hostName']+'  |  Management IP: '+data_elements['managementIpAddress'])
        # results.append(f'Management IP: '+data_elements['managementIpAddress'])
        logger.info(f'Parsed inventory-sddcmanagercontrollers.log in ./api-logs/domain_manager/.')
    except Exception as e:
        logger.warn(f'Cannot find inventory-sddcmanagercontrollers.log in ./api-logs/domain_manager/.'+str(e))
        
    # Collecting SDDC Manager information from vcf-summary-result.json
    try:
        with open("vcf-summary-result.json", "r") as f:
            data = json.load(f)
            logger.debug("vcf-summary-result.json file loaded as a python dictionary.")

            try:
                vcfVersion = (data['SDDC Manager']['SDDC Version']).split(".")[0]
                vcfVersionLong = (data['SDDC Manager']['SDDC Version']).split("-")[0]
                logger.info(f'VCF Version is identified as {vcfVersion}.x ({vcfVersionLong})')
            except Exception as e:
                vcfVersion = '3'
                logger.warning('VCF Version not captured in vcf-summary-result.json '+str(e))
            try:
                content.append("Version: "+data['SDDC Manager']['SDDC Version'])
            except Exception as e:
                logger.warning('SDDC Version not captured in vcf-summary-result.json '+str(e))
                content.append("Version: <not found in JSON>")
            try:
                content.append("Current Status: "+data['SDDC Manager']['SDDC Manager Status'])
            except Exception as e:
                logger.warning('SDDC Manager Status not captured in vcf-summary-result.json. '+str(e))
                content.append("Status: <not found in JSON>")
            
            try:
                upgradeHistoryList = data['SDDC Manager']['SDDC Manager Upgrade History'].split(" -> ")
                upgradeHistoryList.sort()
                upgradeHistory = f" -> ".join(upgradeHistoryList)
                content.append(f"Upgrade History: {upgradeHistory}")
            except Exception as e:
                logger.warning('SDDC Manager Upgrade History not captured in vcf-summary-result.json. '+str(e))
                
    except Exception as e:
        logger.warn(f'Unable to parse SDDC Manager data from vcf-summary-result.json. Error: {e}')
        
    # Collecting SDDC Manager information from vcf-service-result.json
    try:
        with open("vcf-service-result.json", "r") as fr:
            uptime = json.load(fr)
            content.append(("Uptime: "+uptime['VCF Service']['VCF SDDC Manager Uptime']).strip().replace("\n"," "))
        logger.info(f'Successfully parsed vcf-service-result.json')
    except Exception as e:
        logger.warn(f'Unable to parse vcf-service-result.json. Error: {e}')   
    
    # Collecting SDDC Manager information for DNS and NTP from the DB
    try:
        primaryDns,secondaryDns,ntps = sddc_dns_ntp_resultsData()
        content.append(f"Primary DNS: {primaryDns} | Secondary DNS: {secondaryDns}")
        content.append(f"NTPs: {ntps}")
        logger.info(f'Successfully parsed public.system_info table')
    except Exception as e:
        logger.warn(f'Unable to parse public.system_info table. Error: {e}')
        
    # Correlating SDDC Manager with Release Notes link
    try:
        releaseNotes_filePath=Path(__file__).parent/"/data/version_releaseNotes"
        with open(releaseNotes_filePath, "r") as fy:
            relNotes = json.load(fy)
            content.append(f'\n  [ Release Notes: '+relNotes[vcfVersionLong]+' ]')
        logger.info(f'Release notes appended for {vcfVersionLong}.')
    except Exception as e:
        logger.warn(f'Unable to capture release notes for {vcfVersionLong}.')
    
    # SOS Bundle Collection Execution Time
    try:
        sos_filePath=os.getcwd()+"/sos.log"
        with open(sos_filePath,"r") as f:
            data = f.readlines()
            for line in data:
                if 'Run Initiated on' in line:
                    sosRunTime = line.split(" Run Initiated on ")[1]
            content.append(f"SoS Bundle Execution Time: {sosRunTime}")
        logger.info(f'sos.log to collect SoS Bundle Data')
    except Exception as e:
        logger.warn(f'Cannot find sos.log to collect SoS Bundle Data.'+str(e))
    
    content.append(" ")
    content = writeToResultsFile(content)

def sddc_dns_ntp_resultsData():
    headerList,tableEntries = dbTableParser("system_info","platform")
    
    for index,header in enumerate(headerList):
        if header.replace(" ","") == 'dns_info':
            dns_info = index
        if header.replace(" ","") == 'ntp_info':
            ntp_info = index
    
    # From DB Dump:
    # COPY public.system_info (id, creation_time, modification_time, dns_info, features, ntp_info, subscription_domain_limit) FROM stdin;
    
    for entry in tableEntries:
        primaryDns = json.loads(entry[dns_info])["primaryDns"]
        secondaryDns = json.loads(entry[dns_info])["secondaryDns"]
        ntps = json.loads(entry[ntp_info])["ntps"]
    
    return primaryDns,secondaryDns,ntps

def vcfServices_resultsData():
    
    requiredHeaders = []
    requiredRows = []
    
    try:
        filePath=os.getcwd()+"/api-logs/inventory/vcfservices.log"
        with open(filePath,"r") as f:
            data = json.load(f)
        
        requiredHeaders = ["Name","Version","Status"]
        
        for service in data:
            # if service["status"] == 'ACTIVE':
            #     status = typer.style(service["status"], fg=typer.colors.GREEN)
            # else:
            #     status = typer.style(service["status"], fg=typer.colors.RED)
            
            requiredRows.append([service["name"], service["version"], service["status"]])
        
        printTable(f"SDDC Manager Services", requiredHeaders, requiredRows)
        
        logger.info(f'Parsed inventory/vcfservices.log')
    except Exception as e:
        logger.warn(f'Cannot parse inventory/vcfservices.log. Error: '+str(e))

def ringTopology_resultsData():
    content = []
    
    # Collecting Ring Topology Check Info
    content.append(FormatCodes.subtitle('Ring Topology Status'))
    try:
        inventory_filePath=os.getcwd()+"/api-logs/domain_manager/ring-topology-status.log"
        with open(inventory_filePath,"r") as f:
            data = json.load(f)
        
        if data["resultStatus"] == "SUCCEEDED":
            status = typer.style(data["resultStatus"], fg=typer.colors.GREEN)
        else:
            status = typer.style(data["resultStatus"], fg=typer.colors.RED)
        
        content.append(f"Description: {data['description']}\nExecution Status: {data['executionStatus']} | Result Status: {data['resultStatus']} ")
        logger.info(f'Parsed ring-topology-status.log in ./api-logs/domain_manager/.')
    except Exception as e:
        logger.warn(f'Cannot parse ring-topology-status.log in ./api-logs/domain_manager/.'+str(e))
    
    content.append(" ")
    content = writeToResultsFile(content)

def locks_resultsData():
    content = []
    
    # Collecting Deployment lock info
    content.append(FormatCodes.subtitle('Active Locks'))
    try:
        inventory_filePath=os.getcwd()+"/api-logs/domain_manager/locks.log"
        with open(inventory_filePath,"r") as f:
            data = json.load(f)

        if data == []:
            result = "No locks found\n"
            content.append(result)
        else:
            content.append(data)
        
        logger.info(f'Parsed locks.log in ./api-logs/domain_manager/.')
    except Exception as e:
        logger.error(f'Cannot parse locks.log in ./api-logs/domain_manager/.'+str(e))

    content = writeToResultsFile(content)

def domain_resultsData():
    content = []
    content.append(FormatCodes.title('Workload Domains'))
    # Collecting Data per WLD
    try:
        with open("vcf-summary-result.json", "r") as f:
            data = json.load(f)
            logger.debug("vcf-summary-result.json file loaded as a python dictionary.")
            # Iterating through each WLD
            try:
                for entry in data['SDDC Manager']['Domains']:
                    x=list(entry.keys())[0]
                    try:
                        content.append("Domain Name: "+entry[x]['Name'])
                    except Exception as e:
                        logger.warn(f'Domain Name not found. '+str(e))
                        content.append("Domain Name: <not found in JSON>")
                    try:
                        content.append("Domain Type: "+entry[x]['Domain Type'])
                    except Exception as e:
                        logger.warn(f'Domain Type not found. '+str(e))
                        content.append("Domain Type: <not found in JSON>")
                    try:
                        content.append("Domain Status: "+entry[x]['Status'])
                    except Exception as e:
                        logger.warn(f'Domain Status not found. '+str(e))
                        content.append("Domain Status: <not found in JSON>")
                    try:
                        content.append("Domain ID: "+entry[x]['Domain Id'])
                    except Exception as e:
                        logger.warn(f'Domain ID not found. '+str(e))
                        content.append("Domain ID: <not found in JSON>")
                    try:
                        content.append("vCenter Version: "+entry[x]['vCENTER Version'])
                    except Exception as e:
                        logger.warn(f'vCenter Version not found. '+str(e))
                        content.append("vCenter Version: <not found in JSON>")
                    try:
                        content.append("vCenter ID: "+entry[x]['vCENTER Id'])
                    except Exception as e:
                        logger.warn(f'vCenter ID not found. Likely due to VCF 3.x '+str(e))
                        content.append("vCenter ID: <not found in JSON>")
                    try:
                        content.append("ESXi Version: "+entry[x]['Esxi Version'])
                    except Exception as e:
                        logger.warn(f'ESXi Version not found. '+str(e))
                        content.append("ESXi Version: <not found in JSON>")
                    try:
                        nsxVersion = entry[x]['NSX-T Version']
                    except Exception as e:
                        logger.warn(f'NSX-T version not found. '+str(e))
                    try:
                        nsxVersion = entry[x]['NSX Version']
                    except Exception as e:
                        logger.warn(f'NSX-V version not found. '+str(e))
                    try:
                        content.append("NSX Version: "+entry[x]['NSX-Type']+" "+nsxVersion)
                    except Exception as e:
                        logger.warn(f'No NSX infomration found. Please investigate the file manually. '+str(e))

                    # Capturing VxRail Manager version per cluster
                    try:
                        for cluster in entry[x]['Clusters']:
                            y=list(cluster.keys())[0]
                            content.append(f"Cluster: {y} | VxRail Version: {cluster[y]['VxRail Version']}")
                    except Exception as e:
                        logger.warn(f'No VxRail Managers found. '+str(e))
                    content.append(" ")
            except Exception as e:
                logger.warn(f'Unable to parse SDDC Domain JSON Elements.'+str(e))
            
            # Capturing SDDC Manager solution/Aria Data:          
            try:
                content.append("")
                for entry in data['SDDC Manager']['Solution']:
                    if (list(data['SDDC Manager']['Solution'][entry].keys())):
                        content.append(entry+" : "+data['SDDC Manager']['Solution'][entry]['Status']+" "+data['SDDC Manager']['Solution'][entry]['Version'])
                logger.info(f'Solution Data added successfully.')
            except Exception as e:
                logger.warn(f'Unable to record information about any solutions affiliated with SDDC Manager '+str(e))
                    
    except Exception as e:
        logger.error("Failed to read vcf-summary-result.json file. Check file manually. Error: "+str(e))
    
    content = writeToResultsFile(content)

def tasks_resultsData():
    # Show Last 30 failed tasks
    content=[]
    content.append(FormatCodes.title("Workflows"))
    content = writeToResultsFile(content)
    
    columns = []
    failed_rows = []
    successful_rows = []
    
    try:
        with open("vcf-tasks-summary-result.json", "r") as f:
            data = json.load(f)
        
        formatted_data = [] 
        for entry in data['WorkFlow Tasks']:
            try:
                inputTime = data['WorkFlow Tasks'][entry]['Creation Time']
                creation_time = datetime.strptime((inputTime), '%a, %d %b %Y %H:%M:%S %Z')
            except:
                inputTime = data['WorkFlow Tasks'][entry]['Creation Time']
                inputTime = inputTime[:4]
                creation_time = datetime.strptime((inputTime), '%a, %d %b %Y %H:%M:%S')
            data['WorkFlow Tasks'][entry]["creation_time"] = creation_time
            formatted_data.append(data['WorkFlow Tasks'][entry])

        formatted_data.sort(key=operator.itemgetter("creation_time"), reverse=True)
        
        count_successful=0
        count_failed=0
        try:
            for entry in formatted_data:
                #print(f"{entry = }")
                if count_successful < 30:
                    if (entry['Status']).lower() == "successful":
                        count_successful+=1
                        successful_rows.append([entry["name"], entry["Id"], entry["Status"], entry["Creation Time"]])
                if count_failed < 30:
                    if (entry['Status']).lower() != "successful":
                        count_failed+=1
                        failed_rows.append([entry["name"], entry["Id"], entry["Status"], entry["Creation Time"]])
                if (count_successful >= 30) and  (count_failed >= 30):
                    break
        except Exception as e:
            logger.error(f"Failed to capture tasks. Error: {e}")
        
        columns=['Name', 'Workflow ID', "Status", "Creation Time"]
        
        try:
            #Printing Successful Workflows:
            printTable("Successful Workflows", columns, successful_rows)
                        
            #Printing Failed Workflows:
            printTable("Failed Workflows", columns, failed_rows)

        except Exception as e:
            logger.error(f"Failed to print tasks. Error: {e}")
            
    except Exception as e:
        logger.error(f"Error printing tasks: {e}")

def vc_resultsData():
    headerList,tableEntries = dbTableParser("vcenter","platform")
    
    requiredHeaders = []
    requiredRows = []
    
    for index,header in enumerate(headerList):
        if header.replace(" ","") == 'id':
            id = index
        if header.replace(" ","") == 'status':
            status = index
        if header.replace(" ","") == 'type':
            type = index
        if header.replace(" ","") == 'version':
            version = index
        if header.replace(" ","") == 'vm_hostname':
            vm_hostname = index
        if header.replace(" ","") == 'vm_management_ip_address':
            vm_management_ip_address = index
    
    requiredHeaders = ["ID","FQDN","IP","Version","Type","Status"]
    
    for entry in tableEntries:
        requiredRows.append([entry[id], entry[vm_hostname], entry[vm_management_ip_address],
                             entry[version], entry[type], entry[status]])
    
    printTable("vCenters", requiredHeaders, requiredRows)
    
def wld_resultsData():
    headerList,tableEntries = dbTableParser("domain","platform")
    
    requiredHeaders = []
    requiredRows = []
    
    for index,header in enumerate(headerList):
        if header.replace(" ","") == 'id':
            id = index
        if header.replace(" ","") == 'name':
            name = index
        if header.replace(" ","") == 'organization':
            organization = index
        if header.replace(" ","") == 'status':
            status = index
        if header.replace(" ","") == 'type':
            type = index
        if header.replace(" ","") == 'sso_name':
            sso_name = index
        if header.replace(" ","") == 'is_management_sso_domain':
            is_management_sso_domain = index
    
    # From DB Dump:
    # COPY public.domain (id, creation_time, modification_time, name, organization, status, type, vra_integration_status, vrops_integration_status, vrli_integration_status, sso_id, sso_name, is_management_sso_domain) FROM stdin;
    
    requiredHeaders = ["ID","Name","Organization","Type","Status","SSO Name","Is Management SSO?"]
    
    for entry in tableEntries:
        requiredRows.append([entry[id], entry[name], entry[organization],
                             entry[type], entry[status], entry[sso_name], entry[is_management_sso_domain].replace("\n","")])
    
    printTable("Domains", requiredHeaders, requiredRows)
    
def psc_resultsData():
    headerList,tableEntries = dbTableParser("psc","platform")
    
    requiredHeaders = []
    requiredRows = []
    
    for index,header in enumerate(headerList):
        if header.replace(" ","") == 'id':
            id = index
        if header.replace(" ","") == 'vm_hostname':
            vm_hostname = index
        if header.replace(" ","") == 'vm_management_ip_address':
            vm_management_ip_address = index
        if header.replace(" ","") == 'status':
            status = index
        if header.replace(" ","") == 'sso_domain':
            sso_domain = index
        if header.replace(" ","") == 'version':
            version = index
    
    # From DB Dump:
    # COPY public.psc (id, creation_time, modification_time, bundle_repo_datastore, datastore_name, is_replica, port, ssh_host_key, ssh_host_key_type, sso_domain, status, sub_domain, version, vm_hostname, vm_management_ip_address, vm_name) FROM stdin;
    
    requiredHeaders = ["ID","FQDN","IP","Version","Status","SSO Domain"]
    
    for entry in tableEntries:
        requiredRows.append([entry[id], entry[vm_hostname], entry[vm_management_ip_address],
                             entry[version], entry[status], entry[sso_domain]])
    
    printTable("PSC", requiredHeaders, requiredRows)

def cluster_resultsData(): 
    headerList,tableEntries = dbTableParser("cluster","platform")
    
    requiredHeaders = []
    requiredRows = []
    column_is_image_based = True
    
    for index,header in enumerate(headerList):
        if header.replace(" ","") == 'id':
            id = index
        if header.replace(" ","") == 'datacenter':
            datacenter = index
        if header.replace(" ","") == 'is_default':
            is_default = index
        if header.replace(" ","") == 'is_stretched':
            is_stretched = index
        if header.replace(" ","") == 'name':
            name = index
        if header.replace(" ","") == 'status':
            status = index
        if header.replace(" ","") == 'primary_datastore_name':
            primary_datastore_name = index
        if header.replace(" ","") == 'primary_datastore_type':
            primary_datastore_type = index
        try: # This column is only available in VCF 5.x+
            if header.replace(" ","") == 'is_image_based':
                is_image_based = index
        except:
            logger.error('Column "is_image_based" is not found.')
            column_is_image_based = False
            
        if header.replace(" ","") == 'vcenter_id':
            vcenter_id = index
    
    # From DB Dump:
    # COPY public.cluster (id, creation_time, modification_time, datacenter, ftt, is_default, is_stretched, name, status, vcenter_id, version, vsan_datastore_name, primary_datastore_name, primary_datastore_type, source_id, name_context, datacenter_source_id, primary_datastore_source_id, is_image_based) FROM stdin;
    
    requiredHeaders = ["ID","Name","vCenter ID","Datacenter","Default?","Stretched?","Status","Primary DS",
                       "DS Type", "VLCM?"]
    if column_is_image_based == True:
        for entry in tableEntries:
            requiredRows.append([entry[id], entry[name], entry[vcenter_id],
                                entry[datacenter], entry[is_default], entry[is_stretched],
                                entry[status], entry[primary_datastore_name], entry[primary_datastore_type],
                                entry[is_image_based].replace("\n","")])
    else:
        for entry in tableEntries:
            requiredRows.append([entry[id], entry[name], entry[vcenter_id],
                                entry[datacenter], entry[is_default], entry[is_stretched],
                                entry[status], entry[primary_datastore_name], entry[primary_datastore_type],
                                entry[is_image_based].replace("\n","")])
            
    printTable("Clusters", requiredHeaders, requiredRows)

def nsxTManagers_resultsData():
    headerList,tableEntries = dbTableParser("nsxt","platform")
    
    requiredHeaders = []
    requiredRows = []
    
    for index,header in enumerate(headerList):
        if header.replace(" ","") == 'id':
            id = index
        if header.replace(" ","") == 'status':
            status = index
        if header.replace(" ","") == 'version':
            version = index
        if header.replace(" ","") == 'cluster_fqdn':
            cluster_fqdn = index
        if header.replace(" ","") == 'cluster_ip_address':
            cluster_ip_address = index
        if header.replace(" ","") == 'is_shared':
            is_shared = index
        if header.replace(" ","") == 'nsxt_cluster_details':
            nsxt_cluster_details = index
    
    # From DB Dump:
    # COPY public.nsxt (id, creation_time, modification_time, status, version, cluster_ip_address, cluster_fqdn, is_shared, nsxt_cluster_details, configuration) FROM stdin;
        
    requiredHeaders = ["ID","FQDN","IP","Version","Status","Shared?"]
    
    for entry in tableEntries:
        requiredRows.append([entry[id], entry[cluster_fqdn], entry[cluster_ip_address],
                             entry[version], entry[status], entry[is_shared]])
        nsxConfig = entry[nsxt_cluster_details]
        
        for manager in json.loads(nsxConfig):
            requiredRows.append([f' > {manager["id"]}', f' > {manager["fqdn"]}', manager["ipAddress"],
                             "", "", ""])
    
    printTable("NSX Managers", requiredHeaders, requiredRows)
   
def hosts_resultsData():
    headerList,tableEntries = dbTableParser("host","platform")
    
    requiredHeaders = []
    requiredRows = []
    
    for index,header in enumerate(headerList):
        if header.replace(" ","") == 'id':
            id = index
        if header.replace(" ","") == 'dirty':
            dirty = index
        if header.replace(" ","") == 'hostname':
            hostname = index
        if header.replace(" ","") == 'management_ip_address':
            management_ip_address = index
        if header.replace(" ","") == 'status':
            status = index
        if header.replace(" ","") == 'version':
            version = index
        if header.replace(" ","") == 'vmotion_ip_address':
            vmotion_ip_address = index
        if header.replace(" ","") == 'vsan_ip_address':
            vsan_ip_address = index
            
    # From DB Dump:
    # COPY public.host (id, creation_time, modification_time, bundle_repo_datastore, cidr, datastores, dirty, gateway, host_attributes, hostname, management_ip_address, name, nfs_vmknic_ip_address, private_ip_address, ssh_host_key, ssh_host_key_type, status, subnet, version, vmotion_ip_address, vsan_ip_address, iscsi_vmknic_ip_address, source_id) FROM stdin;
    
    requiredHeaders = ["ID","FQDN","IP","Version","Status","Dirty?","vMotion vmk","vSAN vmk"]
    
    for entry in tableEntries:
        requiredRows.append([entry[id], entry[hostname], entry[management_ip_address],
                             entry[version], entry[status], entry[dirty], entry[vmotion_ip_address], entry[vsan_ip_address]])
    
    printTable(f"ESXi Hosts ({str(len(requiredRows)+1)} Hosts)", requiredHeaders, requiredRows)

def vds_resultsData():
    headerList,tableEntries = dbTableParser("vds","platform")
    
    requiredHeaders = []
    requiredRows = []
    
    for index,header in enumerate(headerList):
        if header.replace(" ","") == 'id':
            id = index
        if header.replace(" ","") == 'mtu':
            mtu = index
        if header.replace(" ","") == 'name':
            name = index
        # if header.replace(" ","") == 'port_groups':
        #     port_groups = index
        if header.replace(" ","") == 'version':
            version = index
        if header.replace(" ","") == 'is_used_by_nsxt':
            is_used_by_nsxt = index
        if header.replace(" ","") == 'nsxt_switch_config':
            nsxt_switch_config = index
    
    # From DB Dump:
    # COPY public.vds (id, creation_time, modification_time, mtu, name, niocs, port_groups, status, version, is_used_by_nsxt, source_id, nsxt_switch_config) FROM stdin;
    
    requiredHeaders = ["ID","Name","MTU","Version","Used by NSX?",
                       "Transport Zone ID", "Transport Zone Type"]
    
    for entry in tableEntries:
        requiredRows.append([entry[id], entry[name], entry[mtu],
                             entry[version], entry[is_used_by_nsxt], " ", " "])
        try:
            nsxtSwConfig = json.loads(entry[nsxt_switch_config])
            for tz in nsxtSwConfig['transportZones']:
                requiredRows.append([" "," "," "," "," ",f' > {tz["id"]}', f' > {tz["transportType"]}'])
        except:
            logger.debug("Nothing in field 'nsxt_switch_config'.")
    
    printTable("VDS", requiredHeaders, requiredRows)

def nsxEdge_resultsData():
    headerList,tableEntries = dbTableParser("nsxt_edge_cluster","platform")
    
    requiredHeaders = []
    requiredRows = []
    
    for index,header in enumerate(headerList):
        if header.replace(" ","") == 'id':
            id = index
        if header.replace(" ","") == 'status':
            status = index
        if header.replace(" ","") == 'name':
            name = index
        if header.replace(" ","") == 'nsxt_edge_nodes':
            nsxt_edge_nodes = index
        if header.replace(" ","") == 'source_id':
            source_id = index
    
    # From DB Dump:
    # COPY public.nsxt_edge_cluster (id, creation_time, modification_time, status, name, nsxt_edge_nodes, source_id, is_tier0managed_by_system, skip_tep_routability_check) FROM stdin;
    
    requiredHeaders = ["ID","Cluster Name","Status","Source ID",
                       "EdgeNode ID","EdgeNode Name","EdgeNode IP"]
    
    for entry in tableEntries:
        requiredRows.append([entry[id], entry[name], entry[status], entry[source_id], 
                             " ", " ", " "])
        edgeNodes = entry[nsxt_edge_nodes]
        for edge in json.loads(edgeNodes):
            requiredRows.append([" ", " ", " ", f' > {edge["sourceId"]}', f' > {edge["id"]}', f' > {edge["vmHostname"]}',
                                 edge["vmManagementIpAddress"]])
    
    printTable("NSX-T Edge Clusters", requiredHeaders, requiredRows)

def vxrail_resultsData():
    headerList,tableEntries = dbTableParser("vx_manager","platform")
    
    if headerList == []:
        return
    
    requiredHeaders = []
    requiredRows = []
    
    for index,header in enumerate(headerList):
        if header.replace(" ","") == 'id':
            id = index
        if header.replace(" ","") == 'cluster_id':
            cluster_id = index
        if header.replace(" ","") == 'status':
            status = index
        if header.replace(" ","") == 'version':
            version = index
        if header.replace(" ","") == 'vm_hostname':
            vm_hostname = index
        if header.replace(" ","") == 'vm_management_ip_address':
            vm_management_ip_address = index
        if header.replace(" ","") == 'vm_name':
            vm_name = index
            
    # From DB Dump:
    # COPY public.vx_manager (id, creation_time, modification_time, bundle_copy_path, cluster_id, status, version, vm_hostname, vm_management_ip_address, vm_name) FROM stdin;
    
    requiredHeaders = ["ID","FQDN","IP","VM Name","Cluster ID","Version","Status"]
    
    for entry in tableEntries:
        requiredRows.append([entry[id], entry[vm_hostname], entry[vm_management_ip_address],
                             entry[vm_name].replace("\n",""), entry[cluster_id], entry[version], entry[status]])
    
    printTable(f"VxRail Managers", requiredHeaders, requiredRows)

def inventory_resultsData(resultsProgress,all_progress):
    
    content=[]
    content.append(FormatCodes.title("Inventory Data"))
    content = writeToResultsFile(content)
    
    try:
        wld_resultsData()
    except Exception as e:
        logger.error(f'Failed to capture WLD data. Error: {e}')
    all_progress.update(resultsProgress, advance=1)
    
    try:
        psc_resultsData()
    except Exception as e:
        logger.error(f'Failed to capture PSC data. Error: {e}')
    all_progress.update(resultsProgress, advance=1)
    
    try:
        vc_resultsData()
    except Exception as e:
        logger.error(f'Failed to capture VC data. Error: {e}')
    all_progress.update(resultsProgress, advance=1)
    
    try:
        cluster_resultsData()
    except Exception as e:
        logger.error(f'Failed to capture Cluster data. Error: {e}')
    all_progress.update(resultsProgress, advance=1)
    
    try:
        vds_resultsData()
    except Exception as e:
        logger.error(f'Failed to capture VDS data. Error: {e}')
    all_progress.update(resultsProgress, advance=1)
    
    try:
        nsxTManagers_resultsData()
    except Exception as e:
        logger.error(f'Failed to capture NSX Manager data. Error: {e}')
    all_progress.update(resultsProgress, advance=1)
    
    try:
        nsxEdge_resultsData()
    except Exception as e:
        logger.error(f'Failed to capture NSX Edge data. Error: {e}')
    all_progress.update(resultsProgress, advance=1)
    
    try:
        hosts_resultsData()
    except Exception as e:
        logger.error(f'Failed to capture Host data. Error: {e}')
    all_progress.update(resultsProgress, advance=1)
    
    
    try:
        vxrail_resultsData()
        all_progress.update(resultsProgress, advance=1)
    except:
        logger.debug("No VxRail Manager Table in Platform DB.")
    
#@withLoader(" Generating Results File ...")
def resultsEnvSummary(resultsProgress,all_progress):
    
    all_progress.update(resultsProgress, description="RESULTS | Collecting SDDC Manager Data")
    sddcManager_resultsData()
    all_progress.update(resultsProgress, advance=1)
    
    vcfServices_resultsData()
    all_progress.update(resultsProgress, advance=1)
    ringTopology_resultsData()
    all_progress.update(resultsProgress, advance=1)
    locks_resultsData()
    all_progress.update(resultsProgress, advance=1)
    domain_resultsData()
    all_progress.update(resultsProgress, advance=1)
    
    all_progress.update(resultsProgress, description="RESULTS | Collecting Task and Workflow Data")
    tasks_resultsData()
    all_progress.update(resultsProgress, advance=1)
    
    all_progress.update(resultsProgress, description="RESULTS | Collecting Inventory Data from DB")
    inventory_resultsData(resultsProgress,all_progress)
    
    
    all_progress.update(resultsProgress, description=f"RESULTS | .all file created", completed=100)
    
    
    
    