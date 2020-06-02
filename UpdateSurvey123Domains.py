# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:        UpdatePropertyDomains.py
#
# Purpose:     To update cascading selects activity category/type/subtype, 
#              chemical inventory location/chemical name domains used by a
#              Survey123 survey by creating a new itemsets.csv file for a
#              given property and uploading it to the survey item in Portal.
#              Also updates the chemdefaults.csv lookup table.
#              Only domains used in cascading selects ('external_choices' xls
#              sheet) can be updated by this script.
#
# Usage Notes: Locate the properties to update the property-specific domains
#              in the config.json file and set them to 'true'.           
# 
# Author:      Dylan Harwell - Resource Data Inc
#
# Created:     11/15/2019
# Updated:     03/14/2020
# -----------------------------------------------------------------------------

import GWRutils
import os
import sys

# Prompt user input in terminal to proceed with script, if run by accident,
# user may abort script.
print('You have started the process to update Survey123 form domains.\n\n' +
      'Have you set the properties needing domain updates to "true" in ' +
      'config.json and saved?\n\n')
proceed = input('Press ENTER continue, otherwise type "no" to exit...\n')
if proceed.lower() == 'no':
    print('Exiting!')
    sys.exit()
else:
    print('...Proceeding with Survey123 form domain updates!')

# Set paths for working and logs directories, create new log file
config_path = 'F:\\LRMMobileSolution\\Scripts\\config.json'
working_dir = 'F:\\LRMMobileSolution\\Working'
log_dir = 'F:\\LRMMobileSolution\\Scripts\\Logs'
log_name = 'UpdateSurvey123Domains_LOG_' + GWRutils.getTime() + '.txt'
log = os.path.join(log_dir, log_name)
log_file = open(log, 'w+')
log_file.close()
print('...New log file created')

# Validate config file
is_valid = GWRutils.validateConfig(config_path)
if is_valid == True:
    pass
else:
    print(is_valid)
    GWRutils.logMessage(log, is_valid)
    sys.exit()

# Retrieve data from config and validate
portal_info = GWRutils.configReader(config_path, 'portal_info')
cnxn_info = GWRutils.configReader(config_path, 'cnxn_info')
properties = GWRutils.configReader(config_path, 'properties')
ax_properties = GWRutils.configReader(config_path, 'ax_properties')
sql_procs = GWRutils.configReader(config_path, 'sql_procs')

if not portal_info:
    print('No portal info! Exiting...')
    GWRutils.logMessage(log, 'No portal config! Exiting...')
    sys.exit()
if not cnxn_info:
    print('No db connection info! Exiting...')
    GWRutils.logMessage(log, 'No connection config! Exiting...')
    sys.exit()
if not properties:
    print('No properties values! Exiting...')
    GWRutils.logMessage(log, 'No properties config! Exiting...')
    sys.exit()
if not ax_properties:
    print('No ax property values! Exiting...')
    GWRutils.logMessage(log, 'No ax properties config! Exiting...')
    sys.exit()
if not sql_procs:
    print('No sql procedures! Exiting...')
    GWRutils.logMessage(log, 'No sql procedures! Exiting...')
    sys.exit()
GWRutils.logMessage(log, '...All configurations loaded')

# Check for prperties to update in config
props_to_update = GWRutils.checkForChanges(properties)
if not props_to_update:
    print('No properties to update!')
    GWRutils.logMessage(log, 'No properties to update! Exiting...')
    sys.exit()
else:
    propertyOIDs = [int(x.split(' - ')[0]) for x in props_to_update]
    print('...Properties to update: ' + str(propertyOIDs))
    GWRutils.logMessage(log, '...Properties to update: ' + str(propertyOIDs))

# Connect to Portal
try:
    portal = GWRutils.connectToPortal(portal_info)
    print('...Signed into Portal as ' + portal.properties.user.username)
    GWRutils.logMessage(log, '...Signed into Portal as '
                             + portal.properties.user.username)
except:
    print('Failed to connect to Portal! Exiting...')
    GWRutils.logMessage(log, 'Failed to connect to Portal! Exiting...')
    sys.exit()
    
# Locate survey form items in Portal by property OID
try:
    formItemIDs = []
    portalForms = portal.content.search(query='', item_type='Form')
    for oid in propertyOIDs:
        for form in portalForms:
            if str(oid) in form.title:
                formItemIDs.append([oid, form.id])
                print('...Located Portal form for oid: {0}'.format(str(oid)))
                GWRutils.logMessage(log, '...Located Portal form for oid: ' +
                                         '{0}'.format(str(oid)))
except:
    print('Failed while retrieving form items in Portal! Exiting...')
    GWRutils.logMessage(log, 'Failed while retrieving form items in Portal! '+
                             'Exiting...')

# Identify forms found and not found in Portal
foundOIDs = [ID[0] for ID in formItemIDs]
notFoundOIDs = [f for f in propertyOIDs if f not in foundOIDs]
if not foundOIDs:
    print('No form items located in Portal! Exiting...')
    GWRutils.logMessage(log, 'No form items located in Portal! Exiting...')    
if notFoundOIDs:
    print('Could not locate forms in Portal for oid(s): {0}'.format(
          str(notFoundOIDs)))
    GWRutils.logMessage(log, 'Could not locate forms in Portal for oid(s): ' +
                             '{0}'.format(str(notFoundOIDs)))
  
# Download and extract survey form items
try:
    GWRutils.downloadAndExtractFormItems(portal, formItemIDs, working_dir)
    print('...Downloaded and extracted form items to: ' + working_dir)
    GWRutils.logMessage(log, '...Downloaded and extracted form items to: '
                             + working_dir)
except:
    print('Failed while downloading/extracting form items! Exiting...')
    GWRutils.logMessage(log, 'Failed while downloading/extracting form items!'
                             + ' Exiting...')
    sys.exit()

# Connect to db and retrieve category, type, subtype tables for each property
# and other csv tables in media folder
itemsets_proc = sql_procs['itemsets_proc']
chems_proc = sql_procs['chem_defaults_proc']

try:
    with GWRutils.connectToDB(cnxn_info) as cnxn:
        print('...Connected to SQL Server')
        GWRutils.logMessage(log, '...Connected to SQL Server')        
        for oid in foundOIDs:
            out_name1 = str(oid) + 'itemsets.csv'
            out_path1 = os.path.join(working_dir, out_name1)
            out_name2 = str(oid) + 'chemdefaults.csv'
            out_path2 = os.path.join(working_dir, out_name2) 
            
            try:
                # Execute itemsets procedure
                result1 = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                            itemsets_proc, oid)
                print('...SQL procedure 1 executed for property: ' + str(oid))
                GWRutils.logMessage(log, '...SQL procedure 1 executed for'
                                    + ' property: ' + str(oid))
            except:
                print('Failed to execute stored procedure 1! Exiting...')
                GWRutils.logMessage(log, 'Failed to execute stored procedure '
                                         + '1! Exiting...')
                sys.exit()
                
            try:
                # Execute chemdefaults procedure
                result2 = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                            chems_proc, oid)
                print('...SQL procedure 2 executed for property: ' + str(oid))
                GWRutils.logMessage(log, '...SQL procedure 2 executed for'
                                    + ' property: ' + str(oid))
            except:
                print('Failed to execute stored procedure 2! Exiting...')
                GWRutils.logMessage(log, 'Failed to execute stored procedure '
                                         + '2! Exiting...')
                sys.exit()
                
            try:
                # Convert itemsets result to csv
                GWRutils.generateUpdatedCSV(result1[0], out_path1)
                print('...Created updated itemsets.csv')
                GWRutils.logMessage(log, '...Created updated itemsets.csv')
            except:
                print('Failed to convert pandas DataFrame to itemsets.csv!' 
                      + ' Exiting...')
                GWRutils.logMessage(log, 'Failed to convert pandas DataFrame'
                                          + ' to itemsets.csv! Exiting...')
                sys.exit()
                
            try:
                # Convert chemdefaults result to csv
                GWRutils.generateUpdatedCSV(result2[0], out_path2)
                print('...Created updated chemdefaults.csv')
                GWRutils.logMessage(log, '...Created updated chemdefaults.csv')
            except:
                print('Failed to convert pandas DataFrame to chemdefaults.csv!' 
                      + ' Exiting...')
                GWRutils.logMessage(log, 'Failed to convert pandas DataFrame'
                                          + ' to chemdefaults.csv! Exiting...')
                sys.exit()
                                              
except Exception as e:
    print('Failed to connect to SQL Server! Exiting...')
    print(e)
    GWRutils.logMessage(log, 'Failed to connect to SQL Server! Exiting...')
    GWRutils.logMessage(log, str(e))
    sys.exit()
    
# Updated itemsets.csv(s), swap and upload to Portal
try:
    GWRutils.swapCSVandUploadToPortal(portal, formItemIDs, working_dir)
    print('...Swapped csvs and uploaded to portal')
    GWRutils.logMessage(log, '...Swapped csvs and uploaded to portal')
except:
    print('Failed to swap out csvs and upload to Portal! Exiting...')
    GWRutils.logMessage(log, 'Failed to swap out csvs and upload to Portal! ' 
                              + 'Exiting...')
    sys.exit()
    
# Clean up working directory
try:
    GWRutils.cleanWorkingDir(working_dir)
    print('...Cleaned working directory')
    GWRutils.logMessage(log, '...Cleaned working directory')
except:
    print('Failed to clean working directory!')
    GWRutils.logMessage(log, 'Failed to clean working directory!')

# Reset config file to false state
try:
    GWRutils.resetConfig(config_path, ax_properties)
    print('...Config file reset to false state')
    GWRutils.logMessage(log, '...Config file reset to false state')
except:
    print('Failed to reset config file to false state!')
    GWRutils.logMessage(log, 'Failed to reset config file to false state!')
    
print('Finished script at: ' + GWRutils.getTime())
GWRutils.logMessage(log, 'Finished script at: ' + GWRutils.getTime())