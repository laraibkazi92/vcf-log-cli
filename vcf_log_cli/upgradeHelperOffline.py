'''
DEPRECATED as of 2025-08-2026
Needs significant refactoring to allow functionality for VCF 5.x and VCF 9
Until that is implemented (IF ...), this feature will be disabled
'''
import os
import sys
import json
import glob

import yaml

__author__ = 'Laraib Kazi'
__version__ = '3.1.6'

import logging
logger = logging.getLogger(__name__)

CYELLOW = '\033[93m'
CGREEN = '\033[92m'
CRED = '\033[91m'
CBLUE = '\033[96m'
CEND = '\033[0m'
'''
Offline Version of upgradeHelper to run against an SoS bundle
'''
def title():
    head=f'upgradeHelper'
    print(head)
    logger.info(f'-------------- Starting upgradeHelper version: {__version__} ------------------')
      
def loadManifest():
    # Loads Manifest for Current version of SDDC Manager
    try:
        filePath=os.getcwd()+"/api-logs/lcm/v1-manifests.log"
        with open(filePath,"r") as f:
            data = f.read()
        logger.info(f'Parsed v1-manifests.log in ./api-logs/lcm/.')
        return data
    except Exception as e:
        logger.warn(f'Cannot parse v1-manifests.log in ./api-logs/lcm/.'+str(e))

def getAllBundles():
    # Get all bundles known to SDDC Manager.
    try:
        filePath=os.getcwd()+"/api-logs/lcm/bundles.log"
        with open(filePath,"r") as f:
            data = json.load(f)
        logger.info(f'Parsed bundles.log in ./api-logs/lcm/.')
        return data
    except Exception as e:
        logger.warn(f'Cannot parse bundles.log in ./api-logs/lcm/.'+str(e))
        return 'null'

def getBundleValues(bundle):
    componentBundle = {'id':bundle['id'],
              'downloadStatus':bundle['downloadStatus'],
              'toVersion':bundle['bundleElements'][0]['bundleElementVersion'],
              'fromVersion':bundle['bundleElements'][0]['bundleElementPreviousVersion'],
              'component':bundle['bundleElements'][0]['bundleSoftwareType']}
    
    downloadStatus = componentBundle['downloadStatus']
    component = componentBundle['component']
    # if component == 'HOST':
    #     component = 'ESX_HOST'
    bundleId = componentBundle['id']
    
    if 'success' in downloadStatus.lower():
        print(f"  [ {CGREEN}\u2713{CEND} ] {component} \tBundle: {bundleId} | Download Status: {CGREEN}{downloadStatus}{CEND}")    
    else:
        print(f"  [ {CYELLOW}!{CEND} ] {component} \tBundle: {bundleId} | Download Status: {CYELLOW}{downloadStatus}{CEND}")
    
    logger.debug(f'{component} Upgrade Bundle identified: {componentBundle}')   
    return componentBundle
     
def getRequiredBundles(targetVersion):
    allBundles = getAllBundles()
    vcBundle,nsxBundle,esxBundle = None, None, None
    print(f'\n{CBLUE}Checking Status of Required Upgrade Bundles:{CEND}\n')
    for bundle in allBundles:
        if nsxBundle==None:
            if (bundle['bundleElements'][0]['bundleElementVersion'] == targetVersion['nsx']) and (bundle['bundleElements'][0]['imageType'] == 'PATCH'):
                nsxBundle = getBundleValues(bundle)
                continue
        if vcBundle==None:
            if (bundle['bundleElements'][0]['bundleElementVersion'] == targetVersion['vc']) and (bundle['bundleElements'][0]['imageType'] == 'PATCH'):
                vcBundle = getBundleValues(bundle)                
                continue
        if esxBundle==None:
            if (bundle['bundleElements'][0]['bundleElementVersion'] == targetVersion['esx']) and (bundle['bundleElements'][0]['imageType'] == 'PATCH'):
                esxBundle = getBundleValues(bundle)
                continue
        if (vcBundle!=None) and (nsxBundle!=None) and (esxBundle!=None):
            break
    
    if nsxBundle == None:
        print(f"  [ {CRED}\u2717{CEND} ] NSX_T_MANAGER \tBundle: {CRED}Bundle Not Found{CEND}")
        logger.error(f'NSX_T_MANAGER Bundle not found. No Required Previous Version identified.')
    if vcBundle == None:
        print(f"  [ {CRED}\u2717{CEND} ] VCENTER \tBundle: {CRED}Bundle Not Found{CEND}")
        logger.error(f'VCENTER Bundle not found. No Required Previous Version identified.')
    if esxBundle == None:
        print(f"  [ {CRED}\u2717{CEND} ] ESX_HOST \tBundle: {CRED}Bundle Not Found{CEND}")
        logger.error(f'ESX_HOST Bundle not found. No Required Previous Version identified.')
    
    return {'vc':vcBundle, 'nsx':nsxBundle, 'esx':esxBundle}

def getTargetVersions(manifest,sddcVersion):
    
    lcmData = json.loads(manifest)['releases']
    # count = -1
    for entry in lcmData:
        # count = count + 1
        if entry['version'] == sddcVersion:
            # index = count
            for bomEntry in entry['bom']:
                if bomEntry['name'] == "NSX_T_MANAGER":
                    nsxtVersion=bomEntry['version']
                if bomEntry['name'] == "VCENTER":
                    vcVersion=bomEntry['version']
                if bomEntry['name'] == "HOST":
                    esxVersion=bomEntry['version']          
            targetManifestInfo = {"vc":vcVersion,"esx":esxVersion,"nsx":nsxtVersion}
            logger.debug(f'Manifest Info for Target BoM Version: {targetManifestInfo}')
            break
    return targetManifestInfo        

def asyncPatching_Check():
    # Check if Async Patching is currently enabled in the environment
    
    print(f'\n{CBLUE}Checking Async Patching enabled:{CEND}\n')
    
    # Checking config in each file:
    def checkConfig(file2, config):
        logger.debug(f'Reading file: {file2}')
        try:
            for file in glob.glob(file2):
                with open(file, 'r') as f:
                    fileContents = f.read()
                
                if config in fileContents:
                    logger.debug(f'Config:{config} found in file: {file}')
                    return True
                else:
                    logger.debug(f'Config:{config} not found in file: {file}')
        except Exception as e:
            logger.error(f'Failed to open file. Error: {e}')
    
    # Files to check for Async Patch Configuration
    #file1 = '/opt/vmware/vcf/lcm/lcm-app/conf/application-prod.properties'
    file2 = '/opt/vmware/vcf/sddc-manager-ui-app/server/support/config.properties'
    file2=os.getcwd()+"/sddc-*/opt/vmware/vcf/sddc-manager-ui-app/server/support/config.properties"
    
    # Config entries to check
    #config1 = 'lcm.depot.adapter.enableBundleSignatureValidation=true'
    config2 = 'enableVCFVersionBasedUpdate=false'
    
    asyncConfig = False
    
    if checkConfig(file2,config2) == True:
        asyncConfig = True

    if asyncConfig == True:
        print(f'  [ {CRED}\u2717{CEND} ] Async Patching configuration detected ')
        print('\tPlease disable Async Patching using the command: ')
        print(f'\t{CBLUE}/home/vcf/asyncPatchTool/bin/vcf-async-patch-tool --disableAllPatches --sddcSSOUser administrator@vsphere.local --sddcSSHUser vcf{CEND}\n')
        return 1
    else:
        print(f'  [ {CGREEN}\u2713{CEND} ] Async Patching configuration not detected')
        return 0
         
def getManifestPolling():
    print(f'\n{CBLUE}Checking LCM Manifest Polling status:{CEND}\n')
    file2 = os.getcwd()+"/sddc-*/opt/vmware/vcf/lcm/lcm-app/conf/application-prod.properties"
    try:
        for file in glob.glob(file2):
            with open(file, 'r') as f:
                lines = f.readlines()
                for row in lines:
                    if 'lcm.core.enableManifestPolling' in row:
                        if 'true' in row:
                            logger.debug('LCM Manifest Polling is Enabled')
                            print(f'  [ {CGREEN}\u2713{CEND} ] LCM Manifest Polling is Enabled')
                        else:
                            logger.debug('LCM Manifest Polling is NOT Enabled')
                            print(f'  [ {CRED}\u2717{CEND} ] LCM Manifest Polling is NOT Enabled')
    except Exception as e:
        logger.error(f'Failed to run manifest polling check. Error: {e}')
        
def getSDDCVersion():
    # Current SDDC Manager version:
    try:
        inventory_filePath=os.getcwd()+"/api-logs/domain_manager/inventory-sddcmanagercontrollers.log"
        with open(inventory_filePath,"r") as f:
            data = f.read()
        data_elements = json.loads(data.replace("[","").replace("]",""))
        sddcVersion = data_elements['version'].split("-")[0]
        logger.info(f'Parsed inventory-sddcmanagercontrollers.log in ./api-logs/domain_manager/.')
        
        logger.debug(f'Found SDDC Manager Version : {sddcVersion}')
    
        print(f"\n{CBLUE}SDDC Manager Version:{CEND}\n")
        print("  SDDC Manager: {}".format(sddcVersion))
        
        return sddcVersion
    except Exception as e:
        logger.warn(f'Cannot find inventory-sddcmanagercontrollers.log in ./api-logs/domain_manager/.'+str(e))
   
def getBoMVersionsFromAPI(domainId): 
    
    # Getting vCenter Info
    vcenter=[]
    try:
        filePath=os.getcwd()+"/api-logs/inventory/vcenters.log"
        with open(filePath,"r") as f:
            data = f.read()
        for element in json.loads(data):
            if element['domainId'] == domainId: 
                logger.debug(f'Found VCENTER element : {element}')
                vcenter.extend((element['id'], element['hostName'], element['version'], element['status']))
                break
        logger.info(f'Parsed vcenters.log in ./api-logs/inventory/.')
    except Exception as e:
        logger.warn(f'Cannot parse vcenters.log in ./api-logs/inventory/.'+str(e))
    
    # Getting NSXT Info
    nsxt=[]
    try:
        filePath=os.getcwd()+"/api-logs/inventory/nsxt.log"
        with open(filePath,"r") as f:
            data = f.read()
        for element in json.loads(data):
            if domainId in element['domainIds']: 
                logger.debug(f'Found NSX element : {element}')
                nsxt.extend((element['id'], element['clusterFqdn'], element['version'], element['status']))
                break
        logger.info(f'Parsed nsxt.log in ./api-logs/inventory/.')
    except Exception as e:
        logger.warn(f'Cannot parse nsxt.log in ./api-logs/inventory/.'+str(e))
        
    # Getting Host Info
    host=[]
    try:
        filePath=os.getcwd()+"/api-logs/inventory/hosts.log"
        with open(filePath,"r") as f:
            data = f.read()
        for element in json.loads(data):
            try:
                if element['domainId'] == domainId: 
                    logger.debug(f'Found ESX element : {element}')
                    entry=[]
                    entry.extend((element['id'], element['hostName'], element['version'], element['status']))
                    host.append(entry)
            except Exception as e:
                logger.error(f'Host likely not part of a domain. Error: {e}')      
        logger.info(f'Parsed hosts.log in ./api-logs/inventory/.')
    except Exception as e:
        logger.warn(f'Cannot parse hosts.log in ./api-logs/inventory/.'+str(e))
  
    return vcenter,nsxt,host

def loadVersionAlias(component):
    try:
        filePath=os.getcwd()+"/api-logs/lcm/v1-system-settings-version-aliases.log"
        with open(filePath,"r") as f:
            data = f.read()
        
        try:
            vaEntries = json.loads(data)["elements"]
            logger.debug(f'Version Alias Entries: {vaEntries}')
        except Exception as e:
            logger.error(f'Error parsing Version Alias Entries via API. Error: {e}')
            return "error"
        
        try:
            for entry in vaEntries:
                if entry['bundleComponentType'] == component:
                    logger.debug(f'For component {component} - versionAliases = {entry["versionAliases"]}')
                    return entry['versionAliases']
        except Exception as e:
            logger.error(f'Error: {e}')
            return "None"
        
        logger.info(f'Parsed v1-system-settings-version-aliases.log in ./api-logs/lcm/.')
        
    except Exception as e:
        logger.warn(f'Cannot parse v1-system-settings-version-aliases.log in ./api-logs/lcm/.'+str(e))
    
    

def hostStatusCheck(host):
    # Check the status of all hosts for a WLD
    isActive = True
    notActiveHosts = []
    for entry in host:
        if entry[3].lower() != 'active':
            logger.debug(f'Host not Active: {entry}')
            notActiveHosts.append(entry)
            isActive = False
    
    return notActiveHosts, isActive
        
def bundleAvailabilityLogic(requiredBundles,manifestTargetVersion,vcenter,nsxt,host,sddcVersion):
    # Get current version of NSX-T, VC and ESXi for chosen domain

    # Version is the 2nd value
    version = 2
    # Status is the 4rd value
    status = 3
    
    logger.info('Printing Current Versions Detected.')
    print(f"\n{CBLUE}Current Versions Detected:{CEND}\n")
    print("  NSX-T: {}".format(nsxt[version]))
    print("  vCenter: {}".format(vcenter[version]))
    print("  ESXi: {}".format(host[0][version]))
    
    print(f"\n  Using VCF {sddcVersion} as the Target VCF BoM.")
    
    logger.info('Checking Status of Products')
    print(f"\n{CBLUE}Current Status Detected:{CEND}\n")
    statusChecker("NSX_T_MANAGER", nsxt[status])
    statusChecker("VCENTER", vcenter[status])
    
    notActiveHosts, isActive = hostStatusCheck(host)
    if isActive == True:
        statusChecker("ESX_HOST", 'ACTIVE')
    else:
        statusChecker("ESX_HOST", 'NotActive')
        print(f'  Following hosts are currently not in ACTIVE state: ')
        for host in notActiveHosts:
            print(f'    - {host[0]} | {host[1]}')
    
    # Perform Version Alias Configuration check
    logger.info(f'Performing Version Alias Checks.')
    print(f"\n{CBLUE}Version Alias Detection:{CEND} ")
    aliasChecker("NSX_T_MANAGER", manifestTargetVersion["nsx"], nsxt[version], requiredBundles['nsx'], sddcVersion)
    aliasChecker("VCENTER", manifestTargetVersion["vc"], vcenter[version], requiredBundles['vc'], sddcVersion)
    aliasChecker("ESX_HOST", manifestTargetVersion["esx"], host[0][version], requiredBundles['esx'], sddcVersion)

def statusChecker(component, status):
    
    logger.debug(f'Component {component} has status {status}')
    if status == "ACTIVE":
        print(f"  [ {CGREEN}\u2713{CEND} ] {component} \t: {CGREEN}ACTIVE{CEND}")
    else:
        print(f"  [ {CRED}\u2717{CEND} ] {component} \t: {CRED}{status}{CEND} -> Please investigate the status of the component and mark as ACTIVE from the database if required.")
    
def aliasChecker(component, manifestTargetVersion, dbVersion, requiredVersions, sddcVersion):
    
    AliasCheck = False
    aliasFound = 0
    print(f"\n {component}:")
    
    logger.debug(f'Component: {component}')
    logger.debug(f'Current Version from DB: {dbVersion}')
    logger.debug(f'Manifest Target Version: {manifestTargetVersion}')
    logger.debug(f'SDDC Manager Version: {sddcVersion}')
    
    # Getting specific build numbers
    dbVersion_build = int(dbVersion.split("-")[1])
    manifestTargetVersion_build = int(manifestTargetVersion.split("-")[1])
    
    if dbVersion == manifestTargetVersion:
        # Check if the versions match current SDDC Version BOM
        logger.debug(f'Current Version from DB: {dbVersion} MATCHES Manifest Target Version: {manifestTargetVersion}. Component is already on target version. No aliasing required.')
        print(f"\n  [ {CGREEN}\u2713{CEND} ] {component} {dbVersion} is already on VCF {sddcVersion} BoM. No aliasing required.")
    else:
        try:
            if dbVersion_build > manifestTargetVersion_build:
                targetVersion = 'N/A'
                baseVersion = requiredVersions['toVersion'] 
                print(f"  [ {CYELLOW}!{CEND} ] {component} version {dbVersion} is a higher build than VCF {sddcVersion} BoM {component} version {baseVersion}.")
            else:    
                targetVersion = requiredVersions['toVersion']
                baseVersion = requiredVersions['fromVersion']
        except:
            logger.error(f'Alias Check failed for component {component}. No upgrade bundle found for product {component} in VCF BoM {sddcVersion}')
            print(f"\n  [ {CRED}\u2717{CEND} ] {CRED}Alias checking failed. Upgrade Bundle not found for product {component}{CEND}.")
            return None
            
        logger.debug(f'Target Version from Required Bundle: {targetVersion}')
        logger.debug(f'Manifest Required Previous Version: {baseVersion}')
        
        # Get Version Aliasing for component
        vaEntries = loadVersionAlias(component)
        if vaEntries == "error":
            print(f"\n  {CRED}Error loading VersionAlias.yml file.{CEND} Please check the file for configuration/syntax errors.")
            sys.exit(1)
        elif vaEntries == "None" or vaEntries == None:
            print(f"\n  [ {CRED}\u2717{CEND} ] {CRED}No entry found for {component} in VersionAlias.yml file.{CEND}")
            print(f"  Please add an entry for {component} with alias version {dbVersion} and base version {baseVersion}.")
        else:
            try:
                for entry in vaEntries:
                    for aliasEntry in entry['aliases']:
                        if aliasEntry == dbVersion:
                            aliasFound += 1
                            logger.debug(f'Alias Entry: {aliasEntry} MATCHES Current Version from DB: {dbVersion}. Updating aliasFound to {aliasFound}')
                            if entry['version'] == baseVersion:
                                logger.debug(f'Base Entry: {entry["version"]} MATCHES Manifest Required Previous Version: {baseVersion}. AliasCheck marked as True.')
                                AliasCheck = True
                            break
                if AliasCheck is True:
                    logger.debug(f'Correct Aliasing Found | Component version {dbVersion} MATCHES Manifest Required Previous Version: {baseVersion}.')
                    print(f"\n  [ {CGREEN}\u2713{CEND} ] {CGREEN}CORRECT ALIAS FOUND{CEND}: Current Version of {component} {dbVersion} is aliased to base version {baseVersion}.")
                elif aliasFound > 0:
                    logger.debug(f'Alias Found, required baseVersion not found. | Base Entry DOES NOT MATCH Manifest Required Previous Version: {baseVersion}. Need to update aliasing to correct base version: {baseVersion}.')
                    print(f"\n  [ {CRED}\u2717{CEND} ] {CRED}INCORRECT BASE VERSION{CEND}: Current Version of {component} {dbVersion} is aliased to an INCORRECT base version.\n  Please edit the base version to {baseVersion}.")
                else:
                    if dbVersion == baseVersion:
                        logger.debug(f'dbVersion == baseVersion. No Alias Entry required.')
                        print(f"\n  [ {CGREEN}\u2713{CEND} ] {CGREEN}NO ALIAS REQUIRED{CEND} for Current Version of {component} {dbVersion}.\n  It is already on the required previous version for upgrade.")
                        return
                    else:
                        logger.debug(f'No Alias Entry found. | Need to ADD an alias entry for {dbVersion} to correct base version: {baseVersion}.')
                        print(f"\n  [ {CRED}\u2717{CEND} ] {CRED}NO ALIAS FOUND{CEND} for Current Version of {component} {dbVersion}.\n  Please add an alias for version {dbVersion} with base version as {baseVersion}.")              
                if aliasFound > 1:
                    logger.debug(f'Multiple base versions detected for alias entry: {dbVersion}. Need to update aliasing to only correct base version: {baseVersion}.')
                    print(f"\n  [ {CRED}!!{CEND} ] Current Version of {component} {dbVersion} is being aliased to multiple base versions.\n  Please only alias it to base version {baseVersion}.")
            except Exception as e:
                logger.error(f'Fatal Exception: {e}')
                print(f'Unknown Exception. Please review logs at /var/log/vmware/vcf/upgradeHelper.log for additional details.')
                sys.exit(1)
        # Check what file has the allowed versions for aliasing
        aliasVersionAllowed(baseVersion, dbVersion, sddcVersion)

def loadVersionAliasYml():        
    versionAliasFilePath = os.getcwd()+"/sddc-*/opt/vmware/vcf/lcm/lcm-app/conf/VersionAlias.yml"
    
    try:
        for file in glob.glob(versionAliasFilePath):
            with open(file,"r") as f:
                vaYaml = yaml.safe_load(f)['allowedBaseVersionsForAliasing']
                logger.debug(f'Reading File: {versionAliasFilePath}')
                logger.debug(f'Version Aliases as yaml : {vaYaml}')
                try:
                    return vaYaml
                except Exception as e:
                    logger.error(f'Error: {e}')
                    return "None"
    except Exception as e:
        logger.error(f'Error: {e}')
 

def aliasVersionAllowed(baseVersion, dbVersion, sddcVersion):
    # Function to check if the versions are allowed to be aliased in the 
    # application.properties or application-prod.properties or VersionAlias.yml files
    
    # Coverting SDDC Version to an int value
    sddcVersion = int(sddcVersion.replace('.',''))

    lcmAppConfLocation = "/opt/vmware/vcf/lcm/lcm-app/conf/"
    
    # This will work only for VCF 4.5 and above
    allowedInVersionAlias = True
    
    def printVersionAllowedInfo(version, filename, exists):
        # This function prints the output of findings if the versions are allowed to be aliased
        # depending on the file that info is found in
        if exists==True:
            print(f"\n  [ {CGREEN}\u2713{CEND} ] Version {version} is allowed to be aliased in the {filename} file.")
            logger.debug(f'Version {version} is allowed to be aliased in the {filename} file.')
        else:
            print(f"\n  [ {CRED}\u2717{CEND} ] Version {version} is not allowed to be aliased in the {filename} file.")
            logger.debug(f'Version {version} is not allowed to be aliased in the {filename} file.')

    # Checking if version is allowed to be aliased as per priority of files:
    exists = False
    baseExists = False
    aliasExists = False
    
    if allowedInVersionAlias == True:
        vaAllowedList = loadVersionAliasYml()
        for entry in vaAllowedList:
            if baseVersion in entry:
                logger.info(f'{baseVersion} found in {lcmAppConfLocation}VersionAlias.yml .')
                baseExists = True
                printVersionAllowedInfo(baseVersion,"VersionAlias.yml",baseExists)                
            if dbVersion in entry:
                logger.info(f'{dbVersion} found in {lcmAppConfLocation}VersionAlias.yml .')
                aliasExists = True
                printVersionAllowedInfo(dbVersion,"VersionAlias.yml",aliasExists)
        if (aliasExists == True) and (baseExists == True):
            exists = True
        else:
            if baseExists == False:
                printVersionAllowedInfo(baseVersion,"VersionAlias.yml",baseExists)
            if aliasExists == False:
                printVersionAllowedInfo(baseVersion,"VersionAlias.yml",aliasExists)
                                
    
    if exists == False:

        if allowedInVersionAlias == True:
            print(f'  Please edit the {lcmAppConfLocation}VersionAlias.yml file and add the following entry under "allowedBaseVersionsForAliasing":\n  (Append versions for other components as needed)')
            if baseExists == False:
                print(f' - {baseVersion}')
                logger.debug(f'Add {baseVersion} to {lcmAppConfLocation}VersionAlias.yml .')
            if baseVersion != dbVersion:
                if aliasExists == False:
                    print(f' - {dbVersion}')
                    logger.debug(f'Add {dbVersion} to {lcmAppConfLocation}VersionAlias.yml .')
        else:
            print(f"\n  [ {CRED}\u2717{CEND} ] {CRED}No entry found for allowing the base version to be aliased.{CEND}")
            print(f'  Please edit the {lcmAppConfLocation}VersionAlias.yml file and add the following entry at the top of the VersionAlias.yml file:\n  (Append ONLY versions for other components as needed)')
            print(f'\n  allowedBaseVersionsForAliasing:')
            if baseExists == False:
                print(f' - {baseVersion}')
                logger.debug(f'Add {baseVersion} to {lcmAppConfLocation}VersionAlias.yml .')
            if baseVersion != dbVersion:
                if aliasExists == False:
                    print(f' - {dbVersion}')
                    logger.debug(f'Add {dbVersion} to {lcmAppConfLocation}VersionAlias.yml .')

def domainSelector():
    # Getting Domain Info
    
    try:
        filePath=os.getcwd()+"/api-logs/inventory/domains.log"
        with open(filePath,"r") as f:
            data = f.read()
        logger.info(f'Parsed inventory/domains.log')
        logger.debug(f'Found Domains:\n{json.loads(data)}')
        domains=[]
        for element in json.loads(data):
            entry=[]
            entry.extend((element['id'], element['name'], element['type'], element['status']))
            domains.append(entry)

        print(f"\n{CBLUE}VCF Domains found:{CEND}")
        count = -1
        for element in domains:
            count = count + 1
            domainChoice = (f'[{str(count)}] {element[0]} | {element[1]} | {element[2]} | {element[3]}')
            print(domainChoice)
            logger.info(f'Domain Choice: {domainChoice}')

        print("")
        print("Select the Domain to run bundle availability checks:")
        while True:
            ans_file = input("Select Number: ")
            logger.info(f'Input Selection: {ans_file}')
            # If Selection is beyond the list displayed
            if int(ans_file) > count:
                logger.error(f"Invalid selection: {ans_file}")
                continue
            else:
                selection = int(ans_file)
                print(f"\nDomain selected is : {domains[selection][1]} ") 
                logger.info(f"Domain selected is : {domains[selection]}")
                break
        return domains[selection][0]
    except Exception as e:
        logger.warn(f'Cannot parse inventory/domains.log. Error: '+str(e))
        

def main():
    
    title()
    
    logger.info('Getting SDDC Manager version from localhost/inventory API')
    sddcVersion = getSDDCVersion()
   
    logger.info('Checking status of Async Patching')
    ap_error = asyncPatching_Check()
    
    logger.info('Checking status of lcm manifest polling')
    getManifestPolling()
    
        
    
    logger.info('Starting Domain Selection')
    domainId = domainSelector()
    logger.info('Getting all Component versions from localhost/inventory API')
    vcenter,nsxt,host=getBoMVersionsFromAPI(domainId)
    
    logger.info('Loading Manifest')
    manifest = loadManifest()
    
    logger.info('Getting Target Versions of BoM Components')
    manifestTargetVersion = getTargetVersions(manifest, sddcVersion)
    
    logger.info('Checking Status of Required Upgrade Bundles and getting previous required versions')
    requiredBundles = getRequiredBundles(manifestTargetVersion) 
    
    logger.info('Starting bundle availability logic')
    bundleAvailabilityLogic(requiredBundles,manifestTargetVersion,vcenter,nsxt,host,sddcVersion)
    print()
    logger.info('Execution Complete. Exiting upgradeHelper ...')

