# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:        LRMMobileEnvironmentSetup.py
#
# Purpose:     To perform data model changes needed for mobile app workflow.
#              - Stops all GIS web services
#              - Adds GlobalIDs to all datasets
#              - Copies mobile activities and chemicals to sde
#              - Adds GUID fields to activity and chemical datasets
#              - Creates universal domains from CSVs and assigns
#              - Creates propertyOID subtype for Activity feature class
#              - Creates and assigns subtype domains from SQL VTs
#              - Creates ObjectID based relationship classes
#              - Converts relationship classes to use GlobalIDs
#              - Starts all GIS web services
#
# Author:      Dylan Harwell - Resource Data Inc
#
# Created:     12/30/2019
# Updated:     04/10/2020 - Add property boundary geom to property activities
# Updated:     05/01/2020 - Add Planting Species domain creating
# Updated:     05/22/2020 - Removed prop boundary geom part due to schema lock
# -----------------------------------------------------------------------------

import arcpy
import GWRutils
import os
import sys

# Prompt user input in terminal to proceed with script, if run by accident,
# user may abort script.
print('You have started the process to setup a new LRM Mobile Solution ' +
      'environment.\nHave you checked the configuration settings in ' +
      'config.json?')
proceed = input('Proceed?\nPress ENTER to continue, otherwise type "no" ' +
                'to exit...\n')
if proceed.lower() == 'no':
    print('Exiting!')
    sys.exit()
else:
    print('...Proceeding with environment setup!')

# Set paths to config and needed directories
config_path = 'F:\\LRMMobileSolution\\Scripts\\config.json'
domains_dir = 'F:\\LRMMobileSolution\\Domains'
working_dir = 'F:\\LRMMobileSolution\\Working'
log_dir = 'F:\\LRMMobileSolution\\Scripts\\Logs'

# Create new log file
log_name = 'LRMMobileEnvironmentSetup_LOG_' + GWRutils.getTime() + '.txt'
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
sql_procs = GWRutils.configReader(config_path, 'sql_procs')
datasets = GWRutils.configReader(config_path, 'datasets')
properties = GWRutils.configReader(config_path, 'properties')
mobile_datasets = GWRutils.configReader(config_path, 'mobile_datasets')

if not sde_connection:
    print('No sde connection file! Exiting...')
    GWRutils.logMessage(log, 'No sde connection file! Exiting...')
    sys.exit()
if not portal_info:
    print('No portal connection info! Exiting...')
    GWRutils.logMessage(log, 'No portal connection config! Exiting...')
    sys.exit()
if not cnxn_info:
    print('No db connection info! Exiting...')
    GWRutils.logMessage(log, 'No db connection config! Exiting...')
    sys.exit()
if not sql_procs:
    print('No sql procedures! Exiting...')
    GWRutils.logMessage(log, 'No sql procedures! Exiting...')
    sys.exit()
if not datasets:
    print('No datasets! Exiting...')
    GWRutils.logMessage(log, 'No datasets! Exiting...')
    sys.exit()
if not properties:
    print('No properties values! Exiting...')
    GWRutils.logMessage(log, 'No properties config! Exiting...')
    sys.exit()
if not mobile_datasets:
    print('No mobile dataset values! Exiting...')
    GWRutils.logMessage(log, 'No mobile dataset values! Exiting...')
    sys.exit()
GWRutils.logMessage(log, '...All configurations loaded')

# Set workspace and disconnect users
arcpy.env.workspace = sde_connection
arcpy.env.overwriteOutput = True
arcpy.DisconnectUser(sde_connection, 'ALL')

# Ensure all feature classes and tables are valid
for ds in datasets:
    if not arcpy.Exists(datasets[ds]):
        print('Could not find: {0}! Exiting...'.format(datasets[ds]))
        GWRutils.logMessage(log, 'Could not find: {0}! Exiting...'.format(
                                  datasets[ds]))
        sys.exit()
    else:
        print('...Found dataset: {0}'.format(datasets[ds]))
        GWRutils.logMessage(log, '...Found dataset: {0}'.format(datasets[ds]))

# Connect to Portal and stop all services
try:
    portal_cnxn = GWRutils.connectToPortal(portal_info)
    print('...Signed into Portal as ' + portal_cnxn.properties.user.username)
    GWRutils.logMessage(log, '...Signed into Portal as '
                              + portal_cnxn.properties.user.username)
except:
    print('Failed to connect to Portal! Exiting...')
    GWRutils.logMessage(log, 'Failed to connect to Portal! Exiting...')
    sys.exit()

stop_services = GWRutils.startOrStopServices(portal_cnxn, 'STOP')
if stop_services:
    print('...Stopped all services')
    GWRutils.logMessage(log, '...Stopped all services')
else:
    print('Failed to stop all services! Exiting...')
    GWRutils.logMessage(log, 'Failed to stop all services! Exiting...')
    sys.exit()

# Set variables for datasets from config needed for domain assignment and
# relationship class creation
activity_fc = datasets['activity_fc']
hv_act_fc = datasets['hv_act_fc']
property_fc = datasets['property_fc']
special_point_fc = datasets['special_point_fc']
special_line_fc = datasets['special_line_fc']
special_poly_fc = datasets['special_poly_fc']
chem_app_table = datasets['chem_app_table']
hv_optprod_table = datasets['hv_optprod_table']
activity_mobile = datasets['activity_mobile']
chem_app_mobile = datasets['chem_app_mobile']

# Add GlobalIDs to all datasets
try:
    for ds in datasets:
        desc = arcpy.Describe(datasets[ds])
        if desc.hasGlobalID:
            pass
        else:
            arcpy.AddGlobalIDs_management(datasets[ds])
    print('...GlobalIDs added to all datasets')
    GWRutils.logMessage(log, '...GlobalIDs added to all datasets')
    
except Exception as e:
    print('Failed to add GlobalIDs to all datasets! Exiting...')
    print(e)
    GWRutils.logMessage(log, 'Failed to add GlobalIDs to all datasets! ' +
                        'Exiting...')
    GWRutils.logMessage(log, str(e))
    sys.exit()

# Copy mobile datasets to SDE
try:
    arcpy.FeatureClassToFeatureClass_conversion(activity_mobile,sde_connection,
                                                'TFM_OP_ACTIVITY_MOBILE')
    arcpy.TableToTable_conversion(chem_app_mobile, sde_connection,
                                  'TFM_ACT_CHEMICAL_APPLICATION_MOBILE')
    print('...Copied mobile datasets to LRM SDE')
    GWRutils.logMessage(log, '...Copied mobile datasets to LRM SDE')
    
except Exception as e:
    print('Failed to copy mobile datasets to LRM SDE! Exiting...')
    print(e)
    GWRutils.logMessage(log, 'Failed to copy mobile datasets to LRM SDE! ' +
                        'Exiting...')
    GWRutils.logMessage(log, str(e))
    sys.exit()

# Add GUID field to Activity and Chemical Application datasets
try:
    arcpy.AddField_management(activity_fc, 'Parent_GUID', 'GUID')
    arcpy.AddField_management(chem_app_table, 'Child_GUID', 'GUID')
    print('...GUID fields added to Activity and Chemical datasets')
    GWRutils.logMessage(log, '...GUID fields added to Activity and Chemical ' +
                        'datasets')
    
except Exception as e:
    print('Failed to add GUID fields to Activity and Chemical datasets! ' +
          'Exiting...')
    print(e)
    GWRutils.logMessage(log, 'Failed to add GUID fields to Activity and ' +
                        'Chemical datasets! Exiting...')
    GWRutils.logMessage(log, str(e))
    sys.exit()

# Set fields needing domains
field_act_status = 'Status'
field_act_supervisor = 'Supervisor'
field_act_contractor = 'Contractor_OID'
field_act_compartment = 'COMPARTMENTOID'
field_act_species = 'REG_Species'
field_act_pattern = 'REG_Pattern'
field_act_stocktype = 'REG_Stock_Type'
field_hua_status = 'Status'
field_s_type = 'type'
field_che_chemical = 'MasterChemOID'

# Set universal csv domain table names
domain_act_status = 'act_status'
domain_act_plant_pattern = 'plant_pattern'
domain_act_plant_stock = 'plant_stock'
domain_harv_status = 'harv_status'
domain_s_point = 'special_point'
domain_s_line = 'special_line'
domain_s_poly = 'special_poly'

# Set variables for sql procedures needed for property specific domains
compartment_proc = sql_procs['compartment_proc']
supervisor_proc = sql_procs['supervisor_proc']
contractor_proc = sql_procs['contractor_proc']
chemOIDs_proc = sql_procs['chemOIDs_proc']
species_proc = sql_procs['species_proc']

# Set code and description fields for domain creation
code_field = 'code'
desc_field = 'description'

# Create dictionary of property OIDs and names
props_dict = {k.split(' - ')[0]:k.split(' - ')[1] for k in properties.keys()}

# Create universal domains in gdb
universal_domains = [domain_act_status, domain_act_plant_pattern, 
                      domain_act_plant_stock, domain_harv_status,
                      domain_s_point, domain_s_line, domain_s_poly]
try:
    for domain in universal_domains:
        domain_path = os.path.join(domains_dir, domain + '.csv')
        arcpy.TableToDomain_management(domain_path, code_field, desc_field,
                                      sde_connection, domain, domain,'REPLACE')
        print('...Domain created for: {0}'.format(domain))
        GWRutils.logMessage(log, '...Domain created for: {0}'.format(domain))
        
except Exception as e:
    print('Failed to create domains from universal domain csvs! Exiting...')
    print(e)
    GWRutils.logMessage(log, 'Failed to create domains from universal domain' +
                        ' csvs! Exiting...')
    GWRutils.logMessage(log, str(e))
    sys.exit()

# Assign universal domains to corresponding datasets
try:
    arcpy.AssignDomainToField_management(activity_fc,
                                          field_act_status,
                                          domain_act_status)
    
    arcpy.AssignDomainToField_management(activity_fc,
                                          field_act_pattern,
                                          domain_act_plant_pattern)
    
    arcpy.AssignDomainToField_management(activity_fc,
                                          field_act_stocktype,
                                          domain_act_plant_stock)
    
    arcpy.AssignDomainToField_management(hv_act_fc,
                                          field_hua_status,
                                          domain_harv_status)
    
    arcpy.AssignDomainToField_management(special_point_fc,
                                          field_s_type,
                                          domain_s_point)
    
    arcpy.AssignDomainToField_management(special_line_fc,
                                          field_s_type,
                                          domain_s_line)
    
    arcpy.AssignDomainToField_management(special_poly_fc,
                                          field_s_type,
                                          domain_s_poly)
    
    print('...Assigned all universal domains to fields')
    GWRutils.logMessage(log, '...Assigned all universal domains to fields')
    
except Exception as e:
    print('Failed to assign universal domains to fields! Exiting...')
    print(e)
    GWRutils.logMessage(log, 'Failed to assign universal domains to fields! ' +
                        'Exiting...')
    GWRutils.logMessage(log, str(e))
    sys.exit()

# Create subtypes in Activity and Chemical tables based on propertyOID
try:
    arcpy.SetSubtypeField_management(activity_fc, 'PropertyOID')
    arcpy.SetSubtypeField_management(chem_app_table, 'PropertyOID')
    for prop in props_dict:
        arcpy.AddSubtype_management(activity_fc, prop, props_dict[prop])
        arcpy.AddSubtype_management(chem_app_table, prop, props_dict[prop])
    print('...Created propertyOID subtypes in Activity and Chemical datasets')
    GWRutils.logMessage(log, '...Created propertyOID subtypes in Activity ' +
                        'and Chemical datasets')
    
except Exception as e:
    print('Failed to create propertyOID subtypes in Activity and Chemical ' +
          'datasets! Exiting...')
    print(e)
    GWRutils.logMessage(log, 'Failed to create propertyOID subtypes in ' +
                        'Activity and Chemical datasets! Exiting...')
    GWRutils.logMessage(log, str(e))
    sys.exit()

# Create and assign property specific domains
# Need to check for empty CSV domains because TableToDomain treats them as text
# and throws error when assigned to integer field
for prop in props_dict:
    try:
        with GWRutils.connectToDB(cnxn_info) as cnxn:
            
            # Supervisor Domain
            out_supervisor = '{0}_supervisor.csv'.format(prop)
            out_name_sup = out_supervisor.split('.')[0]
            out_path_sup = os.path.join(working_dir, out_supervisor)
            arcpy.CreateDomain_management(sde_connection,
                                          out_name_sup,
                                          out_name_sup,
                                          'TEXT',
                                          'CODED')
            arcpy.AssignDomainToField_management(activity_fc,
                                                  field_act_supervisor,
                                                  out_name_sup,
                                                  prop)
            supervisor_df = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                              supervisor_proc,
                                                              prop)
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
            
            print('...Supervisor domain created for property: {0}'
                  .format(prop))
            GWRutils.logMessage(log, '...Supervisor domain created for ' +
                                      'property {0}'.format(prop))
            
            # Contractor Domain
            out_contractor = '{0}_contractor.csv'.format(prop)
            out_name_con = out_contractor.split('.')[0]
            out_path_con = os.path.join(working_dir, out_contractor)
            arcpy.CreateDomain_management(sde_connection,
                                          out_name_con,
                                          out_name_con,
                                          'LONG',
                                          'CODED')
            arcpy.AssignDomainToField_management(activity_fc,
                                                  field_act_contractor,
                                                  out_name_con,
                                                  prop)
            contractor_df = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                              contractor_proc,
                                                              prop)
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
            
            print('...Contractor domain created for property: {0}'
                  .format(prop))
            GWRutils.logMessage(log, '...Contractor domain created for ' +
                                      'property {0}'.format(prop))
            
            # Compartment Domain: Only properties 423, 427, 881, 882, 883
            # # Changed to include all properties
            ##if prop in ('423', '427', '881', '882', '883'):
            out_compartment = '{0}_compartment.csv'.format(prop)
            out_name_com = out_compartment.split('.')[0]
            out_path_com = os.path.join(working_dir, out_compartment)
            arcpy.CreateDomain_management(sde_connection,
                                          out_name_com,
                                          out_name_com,
                                          'LONG',
                                          'CODED')
            arcpy.AssignDomainToField_management(activity_fc,
                                                  field_act_compartment,
                                                  out_name_com,
                                                  prop)
            compartment_df = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                          compartment_proc,
                                                                prop)
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
        
            print('...Compartment domain created for property: ' +
                  '{0}'.format(prop))
            GWRutils.logMessage(log, '...Compartment domain created for ' +
                                      'property {0}'.format(prop))
            
            # Planting Species Domain
            out_species = '{0}_species.csv'.format(prop)
            out_name_spe = out_species.split('.')[0]
            out_path_spe = os.path.join(working_dir, out_species)
            arcpy.CreateDomain_management(sde_connection,
                                          out_name_spe,
                                          out_name_spe,
                                          'TEXT',
                                          'CODED')
            arcpy.AssignDomainToField_management(activity_fc,
                                                  field_act_species,
                                                  out_name_spe,
                                                  prop)
            species_df = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                            species_proc,
                                                            prop)
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
            
            print('...Species domain created for property: {0}'
                  .format(prop))
            GWRutils.logMessage(log, '...Species domain created for ' +
                                      'property {0}'.format(prop))
            
            # Chemical Domain
            out_chemical = '{0}_chemical.csv'.format(prop)
            out_name_che = out_chemical.split('.')[0]
            out_path_che = os.path.join(working_dir, out_chemical)
            arcpy.CreateDomain_management(sde_connection,
                                          out_name_che,
                                          out_name_che,
                                          'LONG',
                                          'CODED')
            arcpy.AssignDomainToField_management(chem_app_table,
                                                  field_che_chemical,
                                                  out_name_che,
                                                  prop)
            chemical_df = GWRutils.executeSQLProcToPandasDF(cnxn,
                                                            chemOIDs_proc,
                                                            prop)
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
            
            print('...Chemical domain created for property: {0}'
                  .format(prop))
            GWRutils.logMessage(log, '...Chemical domain created for ' +
                                      'property {0}'.format(prop))
                
    except Exception as e:
        print('Failed to create a domain for property: {0}! Exiting...'
              .format(prop))
        print(e)
        GWRutils.logMessage(log, 'Failed to create a domain for property: ' +
                            '{0}! Exiting...'.format(prop))
        GWRutils.logMessage(log, str(e))
        sys.exit()

# Create needed relationship classes
rel_classes = ['Property_PropAct', 'Activity_Chemical_Existing',
                'Activity_Chemical_New', 'HVunit_OPTproduct']

# Property_PropAct
try:
    arcpy.CreateRelationshipClass_management(property_fc,
                                              activity_fc,
                                              rel_classes[0],
                                              'SIMPLE',
                                              'forward',
                                              'backward',
                                              'NONE',
                                              'ONE_TO_MANY',
                                              'NONE',
                                              'ObjectID',
                                              'PropertyOID')
    print('...Relationship class created: {0}'.format(rel_classes[0]))
    GWRutils.logMessage(log, '...Relationship class created: {0}'
                        .format(rel_classes[0]))
    
except Exception as e:
    print('Failed to create relationship class: {0}! Exiting...'
          .format(rel_classes[0]))
    print(e)
    GWRutils.logMessage(log, 'Failed to create relationship class: {0}! ' +
                        'Exiting...'.format(rel_classes[0]))
    GWRutils.logMessage(log, str(e))
    sys.exit()

# Activity_Chemical_Existing
try:
    arcpy.CreateRelationshipClass_management(activity_fc,
                                              chem_app_table,
                                              rel_classes[1],
                                              'SIMPLE',
                                              'forward',
                                              'backward',
                                              'NONE',
                                              'ONE_TO_MANY',
                                              'NONE',
                                              'OBJECTID',
                                              'ActivityOID')
    print('...Relationship class created: {0}'.format(rel_classes[1]))
    GWRutils.logMessage(log, '...Relationship class created: {0}'
                        .format(rel_classes[1]))

except Exception as e:
    print('Failed to create relationship class: {0}! Exiting...'
          .format(rel_classes[1]))
    print(e)
    GWRutils.logMessage(log, 'Failed to create relationship class: {0}! ' +
                        'Exiting...'.format(rel_classes[1]))
    GWRutils.logMessage(log, str(e))
    sys.exit()
    
# Activity_Chemical_New
activity_mobile_copy = mobile_datasets['activity_mobile_copy']
chem_app_mobile_copy = mobile_datasets['chem_app_mobile_copy']
try:
    arcpy.CreateRelationshipClass_management(activity_mobile_copy,
                                              chem_app_mobile_copy,
                                              rel_classes[2],
                                              'SIMPLE',
                                              'forward',
                                              'backward',
                                              'NONE',
                                              'ONE_TO_MANY',
                                              'NONE',
                                              'Parent_GUID',
                                              'Child_GUID')
    print('...Relationship class created: {0}'.format(rel_classes[2]))
    GWRutils.logMessage(log, '...Relationship class created: {0}'
                        .format(rel_classes[2]))

except Exception as e:
    print('Failed to create relationship class: {0}! Exiting...'
          .format(rel_classes[2]))
    print(e)
    GWRutils.logMessage(log, 'Failed to create relationship class: {0}! ' +
                        'Exiting...'.format(rel_classes[2]))
    GWRutils.logMessage(log, str(e))
    sys.exit()

# HVunit_OPTproduct
try:
    arcpy.CreateRelationshipClass_management(hv_act_fc,
                                              hv_optprod_table,
                                              rel_classes[3],
                                              'SIMPLE',
                                              'forward',
                                              'backward',
                                              'NONE',
                                              'ONE_TO_MANY',
                                              'NONE',
                                              'ObjectID',
                                              'HUOID')
    print('...Relationship class created: {0}'.format(rel_classes[3]))
    GWRutils.logMessage(log, '...Relationship class created: {0}'
                        .format(rel_classes[3]))
    
except Exception as e:
    print('Failed to create relationship class: {0}! Exiting...'
          .format(rel_classes[3]))
    print(e)
    GWRutils.logMessage(log, 'Failed to create relationship class: {0}! ' +
                        'Exiting...'.format(rel_classes[3]))
    GWRutils.logMessage(log, str(e))
    sys.exit()

# Convert relationship classes to use GlobalIDs except Activity_Chemical_New
try:
    for rel_class in rel_classes:
        if rel_class != 'Activity_Chemical_New':
            arcpy.MigrateRelationshipClass_management(rel_class)
    print('...Converted all relationship classes to use GlobalIDs')
    GWRutils.logMessage(log, '...Converted all relationship classes to use ' +
                        'GlobalIDs')

except Exception as e:
    print('Failed to convert relationship classes to use GlobalIDs! ' +
          'Exiting...')
    print(e)
    GWRutils.logMessage(log, 'Failed to convert relationship classes to use ' +
                        'GlobalIDs! Exiting...')
    GWRutils.logMessage(log, str(e))
    sys.exit()

# Clean up working directory
try:
    GWRutils.cleanWorkingDir(working_dir)
    print('...Cleaned working directory')
    GWRutils.logMessage(log, '...Cleaned working directory')
except Exception as e:
    print('Failed to clean working directory!')
    print(e)
    GWRutils.logMessage(log, 'Failed to clean working directory!')   
    GWRutils.logMessage(log, str(e))     

# Start all services
start_services = GWRutils.startOrStopServices(portal_cnxn, 'START')
if start_services:
    print('...Started all services')
    GWRutils.logMessage(log, '...Started all services')
else:
    print('Failed to start all services! End of script...')
    GWRutils.logMessage(log, 'Failed to start all services! End of script...')