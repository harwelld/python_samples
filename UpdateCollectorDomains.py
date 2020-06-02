# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:        UpdateCollectorDomains.py
#
# Purpose:     To update universal domains and property-specific domains used
#              by Collector maps.
#
# Usage Notes: Updates (if needed) to the CSV files for the universal domains
#              need to be done manually before running this script.
#              Locate the properties to update the property-specific domains
#              in the config.json file and set them to 'true'. 
#              The script requires a schema lock, so it will stop and then
#              restart all web services on Portal which could take several
#              hours depending on the number of services. Plan ahead.
# 
# Author:      Dylan Harwell - Resource Data Inc
#
# Created:     11/15/2019
# Updated:     03/14/2020
# Updated:     05/01/2020 - Add Planting Species domains
# -----------------------------------------------------------------------------

import GWRutils
import os
import sys
import arcpy

# Prompt user input in terminal to proceed with script, if run by accident,
# user may abort script.
print('\nYou have started the process to update Collector domains which ' +
      'requires an exclusive schema lock.\nAll Portal services will be ' +
      'stopped and then restarted.\n\n' +
      'If needed, have you manually updated the universal domain CSVs?\n' +
      'If needed, have you set properties needing domain updates to "true" ' +
      'in config.json?\n\n')
proceed = input('Press ENTER to continue, otherwise type "no" to exit...\n')
if proceed.lower() == 'no':
    print('Exiting!')
    sys.exit()
else:
    print('...Proceeding with Collector domain updates!')

# Set paths for working and logs directories, create new log file
config_path = 'F:\\LRMMobileSolution\\Scripts\\config.json'
domains_dir = 'F:\\LRMMobileSolution\\Domains'
working_dir = 'F:\\LRMMobileSolution\\Working'
log_dir = 'F:\\LRMMobileSolution\\Scripts\\Logs'
log_name = 'UpdateCollectorDomains_LOG_' + GWRutils.getTime() + '.txt'
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
sde_connection = GWRutils.configReader(config_path, 'sde_connection')
portal_info = GWRutils.configReader(config_path, 'portal_info')
cnxn_info = GWRutils.configReader(config_path, 'cnxn_info')
properties = GWRutils.configReader(config_path, 'properties')
ax_properties = GWRutils.configReader(config_path, 'ax_properties')
sql_procs = GWRutils.configReader(config_path, 'sql_procs')

if not sde_connection:
    print('No sde connection file! Exiting...')
    GWRutils.logMessage(log, 'No sde connection file! Exiting...')
    sys.exit()
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

# Set workspace and disconnect users
arcpy.env.workspace = sde_connection
arcpy.DisconnectUser(sde_connection, 'ALL')

# Connect to Portal and stop all services
try:
    portal = GWRutils.connectToPortal(portal_info)
    print('...Signed into Portal as ' + portal.properties.user.username)
    GWRutils.logMessage(log, '...Signed into Portal as '
                             + portal.properties.user.username)
except:
    print('Failed to connect to Portal! Exiting...')
    GWRutils.logMessage(log, 'Failed to connect to Portal! Exiting...')
    sys.exit()

stop_services = GWRutils.startOrStopServices(portal, 'STOP')
if stop_services:
    print('...Stopped all services')
    GWRutils.logMessage(log, '...Stopped all services')
else:
    print('Failed to stop all services! Exiting...')
    GWRutils.logMessage(log, 'Failed to stop all services! Exiting...')
    sys.exit()

# Set code and description fields for domains
code_field = 'code'
desc_field = 'description'

# Set universal csv domain table names
domain_act_status = 'act_status'
domain_act_plant_pattern = 'plant_pattern'
domain_act_plant_stock = 'plant_stock'
domain_harv_status = 'harv_status'
domain_s_point = 'special_point'
domain_s_line = 'special_line'
domain_s_poly = 'special_poly'

# Updated universal domains in gdb
universal_domains = [domain_act_status, domain_act_plant_pattern, 
                     domain_act_plant_stock, domain_harv_status,
                     domain_s_point, domain_s_line, domain_s_poly]
try:
    for domain in universal_domains:
        domain_path = os.path.join(domains_dir, domain + '.csv')
        arcpy.TableToDomain_management(domain_path, code_field, desc_field,
                                       sde_connection, domain,domain,'REPLACE')
        print('...Overwrote domain: {0}'.format(domain))
        GWRutils.logMessage(log, '...Overwrote domain: {0}'.format(domain))
        
except Exception as e:
    print('Failed to overwrite universal domains! Exiting...')
    print(e)
    GWRutils.logMessage(log, 'Failed to overwrite universal domains! ' +
                        'Exiting...')
    GWRutils.logMessage(log, str(e))
    sys.exit()

# Check for prperties to update in config
props_to_update = GWRutils.checkForChanges(properties)
if not props_to_update:
    print('...No properties to update')
    GWRutils.logMessage(log, '...No properties to update')
else:
    propertyOIDs = [int(x.split(' - ')[0]) for x in props_to_update]
    print('...Properties to update: ' + str(propertyOIDs))
    GWRutils.logMessage(log, '...Properties to update: ' + str(propertyOIDs))

# Connect to db and retrieve compartment, supervisor, contractor, chemical,
# and species domains
compartment_proc = sql_procs['compartment_proc']
supervisor_proc = sql_procs['supervisor_proc']
contractor_proc = sql_procs['contractor_proc']
chemOIDs_proc = sql_procs['chemOIDs_proc']
species_proc = sql_procs['species_proc']

if props_to_update:
    with GWRutils.connectToDB(cnxn_info) as cnxn:
        print('...Connected to SQL Server')
        GWRutils.logMessage(log, '...Connected to SQL Server')        
        
        for oid in propertyOIDs:
            try:
                # Compartment Collector Domains (423, 427, 881, 882, 883)
                # Changed to include all properties
                ##if oid in ('423', '427', '881', '882', '883'):
                out_compartment = '{0}_compartment.csv'.format(oid)
                out_name_com = out_compartment.split('.')[0]
                out_path_com = os.path.join(working_dir, out_compartment)
                compartment_df = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                          compartment_proc,
                                                          oid)
                if compartment_df[0].shape[0] > 0:
                    GWRutils.generateUpdatedCSV(compartment_df[0],
                                                out_path_com)
                    arcpy.TableToDomain_management(out_path_com,
                                                   code_field,
                                                   desc_field,
                                                   sde_connection,
                                                   out_name_com,
                                                   out_name_com,
                                                   'REPLACE')
                    print('...Compartment domain updated for property: {0}'
                          .format(oid))
                    GWRutils.logMessage(log, '...Compartment domain ' +
                                'updated for property {0}'.format(oid))                
            except:
                print('Failed to overwrite compartment domain! Exiting...')
                GWRutils.logMessage(log, 'Failed to overwrite compartment ' +
                                         'domain! Exiting...')
                sys.exit()
                
            try:
                # Supervisor Collector Domain
                out_supervisor = '{0}_supervisor.csv'.format(oid)
                out_name_sup = out_supervisor.split('.')[0]
                out_path_sup = os.path.join(working_dir, out_supervisor)
                supervisor_df = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                              supervisor_proc,
                                                              oid)
                if supervisor_df[0].shape[0] > 0:
                    GWRutils.generateUpdatedCSV(supervisor_df[0],
                                                out_path_sup)
                    arcpy.TableToDomain_management(out_path_sup,
                                                   code_field,
                                                   desc_field,
                                                   sde_connection,
                                                   out_name_sup,
                                                   out_name_sup,
                                                   'REPLACE')
                print('...Supervisor domain updated for property: {0}'
                      .format(oid))
                GWRutils.logMessage(log, '...Supervisor domain updated for ' +
                                         'property {0}'.format(oid))
            except:
                print('Failed to overwrite supervisor domain! Exiting...')
                GWRutils.logMessage(log, 'Failed to overwrite supervisor ' +
                                         'domain! Exiting...')
                sys.exit()
                
            try:
                # Contractor Collector Domain
                out_contractor = '{0}_contractor.csv'.format(oid)
                out_name_con = out_contractor.split('.')[0]
                out_path_con = os.path.join(working_dir, out_contractor)
                contractor_df = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                              contractor_proc,
                                                              oid)
                if contractor_df[0].shape[0] > 0:
                    GWRutils.generateUpdatedCSV(contractor_df[0],
                                                out_path_con)
                    arcpy.TableToDomain_management(out_path_con,
                                                   code_field,
                                                   desc_field,
                                                   sde_connection,
                                                   out_name_con,
                                                   out_name_con,
                                                   'REPLACE')
                print('...Contractor domain updated for property: {0}'
                      .format(oid))
                GWRutils.logMessage(log, '...Contractor domain updated for ' +
                                         'property {0}'.format(oid))                    
            except:
                print('Failed to overwrite contractor domain! Exiting...')
                GWRutils.logMessage(log, 'Failed to overwrite contractor ' +
                                         'domain! Exiting...')
                sys.exit()
                
            try:
                # Planting Species Domain
                out_species = '{0}_species.csv'.format(oid)
                out_name_spe = out_species.split('.')[0]
                out_path_spe = os.path.join(working_dir, out_species)
                species_df = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                               species_proc,
                                                               oid)
                if species_df[0].shape[0] > 0:
                    GWRutils.generateUpdatedCSV(species_df[0],
                                                out_path_spe)
                    arcpy.TableToDomain_management(out_path_spe,
                                                   code_field,
                                                   desc_field,
                                                   sde_connection,
                                                   out_name_spe,
                                                   out_name_spe,
                                                   'REPLACE')
                print('...Species domain updated for property: {0}'
                      .format(oid))
                GWRutils.logMessage(log, '...Species domain updated for ' +
                                         'property {0}'.format(oid))           
            except:
                print('Failed to overwrite species domain! Exiting...')
                GWRutils.logMessage(log, 'Failed to overwrite species ' +
                                         'domain! Exiting...')
                sys.exit()    
                
            try:
                # Chemical Collector Domain
                out_chemical = '{0}_chemical.csv'.format(oid)
                out_name_che = out_chemical.split('.')[0]
                out_path_che = os.path.join(working_dir, out_chemical)
                chemical_df = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                                chemOIDs_proc,
                                                                oid)
                if chemical_df[0].shape[0] > 0:
                    GWRutils.generateUpdatedCSV(chemical_df[0],
                                                out_path_che)
                    arcpy.TableToDomain_management(out_path_che,
                                                   code_field,
                                                   desc_field,
                                                   sde_connection,
                                                   out_name_che,
                                                   out_name_che,
                                                   'REPLACE')
                print('...Chemical domain updated for property: {0}'
                      .format(oid))
                GWRutils.logMessage(log, '...Chemical domain updated for ' +
                                         'property {0}'.format(oid))           
            except:
                print('Failed to overwrite chemical domain! Exiting...')
                GWRutils.logMessage(log, 'Failed to overwrite chemical ' +
                                         'domain! Exiting...')
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

# Start all services
start_services = GWRutils.startOrStopServices(portal, 'START')
if start_services:
    print('...Started all services')
    GWRutils.logMessage(log, '...Started all services')
else:
    print('Failed to start all services! End of script...')
    GWRutils.logMessage(log, 'Failed to start all services! End of script...') 

print('Finished script at: ' + GWRutils.getTime())
GWRutils.logMessage(log, 'Finished script at: ' + GWRutils.getTime())