# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:        MobileSyncLRM.py
#
# Purpose:     To synchronize mobile copies of activities and chemicals to LRM
#              activities feature class and chemicals table.
# 
# Author:      Dylan Harwell - Resource Data Inc
#
# Created:     12/03/2019
# Updated:     03/03/2020, 04/10/2020
# -----------------------------------------------------------------------------

import GWRutils
import arcpy
import os
import sys

# Set path to config and logs directory, create new log file
config_path = 'F:\\LRMMobileSolution\\Scripts\\config.json'
mobile_gdb = 'F:\\LRMMobileSolution\\LRM_Mobile.gdb'
log_dir = 'F:\\LRMMobileSolution\\Scripts\\Logs'
log_name = 'MobileSyncLRM_LOG_' + GWRutils.getTime() + '.txt'
log = os.path.join(log_dir, log_name)
log_file = open(log, 'w+')
log_file.close()

# Validate config file
is_valid = GWRutils.validateConfig(config_path)
if is_valid == True:
    pass
else:
    print('Invalid config! Exiting...')
    GWRutils.logMessage(log, 'Invalid config! Exiting...')
    sys.exit()

# Retrieve data from config and validate
sde_connection = GWRutils.configReader(config_path, 'sde_connection')
cnxn_info = GWRutils.configReader(config_path, 'cnxn_info')
sql_procs = GWRutils.configReader(config_path, 'sql_procs')
datasets = GWRutils.configReader(config_path, 'datasets')
mobile_datasets = GWRutils.configReader(config_path, 'mobile_datasets')

if not sde_connection:
    print('No sde connection file! Exiting...')
    GWRutils.logMessage(log, 'No sde connection file! Exiting...')
    sys.exit()
if not cnxn_info:
    print('No db connection info! Exiting...')
    GWRutils.logMessage(log, 'No connection config! Exiting...')
    sys.exit()
if not sql_procs:
    print('No sql procedures! Exiting...')
    GWRutils.logMessage(log, 'No sql procedures! Exiting...')
    sys.exit()
if not datasets:
    print('No datasets found! Exiting...')
    GWRutils.logMessage(log, 'No datasets found! Exiting...')
    sys.exit()
if not mobile_datasets:
    print('No mobile_datasets found! Exiting...')
    GWRutils.logMessage(log, 'No mobile_datasets found! Exiting...')
    sys.exit()
GWRutils.logMessage(log, '...All configurations loaded')

# Set sde connection workspace
arcpy.env.workspace = sde_connection
arcpy.env.overwriteOutput = True

# Set paths to needed feature classes and tables
mobile_act_script = datasets['activity_mobile_script']
mobile_chem_script = datasets['chem_app_mobile_script']
target_act = datasets['activity_fc']
target_che = datasets['chem_app_table']
stands = datasets['stand_fc']
property_fc = datasets['property_fc']
mobile_act = mobile_datasets['activity_mobile_copy']
mobile_che = mobile_datasets['chem_app_mobile_copy']

# Ensure all feature classes and tables are valid
feature_list = [mobile_act_script, mobile_chem_script, target_act, target_che, 
                stands, property_fc, mobile_act, mobile_che]
for feature in feature_list:
    if not arcpy.Exists(feature):
        print('Could not find: {0}! Exiting...'.format(feature))
        GWRutils.logMessage(log, 'Could not find: {0}! Exiting...'.format(
                                  feature))
        sys.exit()
    else:
        print('...Found dataset: {0}'.format(feature))
        GWRutils.logMessage(log, '...Found dataset: {0}'.format(feature))

# Determine if new activities were added to mobile dataset
count_act = int(arcpy.GetCount_management(mobile_act)[0])
if count_act > 0:
    # Proceed with script
    print('...{0} new activitie(s) added today'.format(str(count_act)))
    GWRutils.logMessage(log, '...{0} new activitie(s) added today'.format(
                              str(count_act)))
else:
    print('No new activities added today! Exiting...')
    GWRutils.logMessage(log, 'No new activities added today! Exiting...')
    sys.exit()
        
# Create dictionaries of property activities, stand activities and chemicals
prop_act = {}
stand_act = {}
chems = {}

fields_act = ['OBJECTID', 'Parent_GUID', 'prop_or_stand', 'PropertyOID',
              'standOID']
with arcpy.da.SearchCursor(mobile_act, fields_act) as sCur:
    for row in sCur:
        if row[2] == 'prop':
            prop_act[row[0]] = row[3]
        if row[2] == 'stand':
            stand_act[row[0]] = [row[1], row[4]]
            
fields_che = ['OBJECTID', 'Child_GUID']
if int(arcpy.GetCount_management(mobile_che)[0]) > 0:      
    with arcpy.da.SearchCursor(mobile_che, fields_che) as sCur:
        for row in sCur:
            chems[row[0]] = row[1]
            
# Create dictionary with GlobalID from Property feature class
prop_act_new = {}
fields_prop = ['ObjectID', 'GlobalID']
for item in prop_act.items():
    with arcpy.da.SearchCursor(property_fc, fields_prop) as sCur:
        for row in sCur:
            if item[1] == row[0]:
                prop_act_new[item[0]] = [row[0], row[1]]

# ----------------------- Property Activities --------------------------------#
if not prop_act:
    print('...No new property activities to add')
    GWRutils.logMessage(log, '...No new property activities to add')
else:
    print('...{0} new property activitie(s) to add'.format(str(len(prop_act))))
    GWRutils.logMessage(log, '...{0} new property activitie(s) to add'.format(
                              str(len(prop_act))))

    try:  
        # Append records from Activity Mobile to Target Activity table
        fields = GWRutils.customFieldMapper(mobile_act_script, mobile_act)
        for item in prop_act.items():
            where = """{0} = {1}""".format(arcpy.AddFieldDelimiters(
                                            sde_connection,'OBJECTID'),
                                            item[0])
            arcpy.MakeFeatureLayer_management(mobile_act, 'prop_act', where)
            with arcpy.da.SearchCursor('prop_act', fields) as sCur:
                with arcpy.da.InsertCursor(mobile_act_script, fields) as iCur:
                    for srow in sCur:
                        iCur.insertRow(srow)
                        print('...Appended property activity to intermediate'+
                              ' activity feature')
                        GWRutils.logMessage(log, '...Appended property ' + 
                                                  'activity to intermediate '+
                                                  'activity feature')

        # Update intermediate activity TFM_CMN_PROPERTY_GlobalID field
        fields = ['PropertyOID', 'TFM_CMN_PROPERTY_GlobalID']
        for item in prop_act_new.items():
            with arcpy.da.UpdateCursor(mobile_act_script, fields) as uCur:
                for row in uCur:
                    if row[0] == item[1][0]:
                        row[1] = item[1][1]
                    uCur.updateRow(row)
        print('...Added property GlobalIDs to intermediate activity feature')
        GWRutils.logMessage(log, '...Added property GlobalIDs to ' +
                            'intermediate activity feature')
        
        # Add property boundary geometry to intermediate property activities
        propOIDs = [prop_act[k] for k in prop_act]
        addGeom = GWRutils.addPropertyActivityGeometry(propOIDs, 
                                                       property_fc, 
                                                       mobile_act_script)
        if addGeom:
            print('...Copied property boundary geometry to intermediate ' +
                  'property activities')
            GWRutils.logMessage(log, '...Copied property boundary geometry ' +
                                'to intermediate property activities')
        else:
            print('Failed to copy property boundary geometry to intermediate '+
                  'property activities! Exiting...')
            GWRutils.logMessage(log, 'Failed to copy property boundary ' +
                                'geometry to intermediate property ' +
                                'activities! Exiting...')
            sys.exit()
        
        # Append intermediate property activities to target activities
        arcpy.Append_management(mobile_act_script, target_act, 'NO_TEST')
        print('...Appended property activities to target activity feature')
        GWRutils.logMessage(log, '...Appended property activities to target '+
                            'activity feature')        
        
        # Reset mobile_act_script dataset by clearing all records
        result = GWRutils.resetMobileFeatures([mobile_act_script])
        print('...Cleared mobile activity script dataset')

    except Exception as e:
        print('Failed while appending property activity to target activity ' +
              'feature! Exiting...')
        print(e)
        GWRutils.logMessage(log, 'Failed while appending property activity ' +
                            'to target activity feature! Exiting...')
        GWRutils.logMessage(log, str(e))
        sys.exit()

# ---------------------------- Stand Activities ------------------------------#
if not stand_act:
    print('...No new stand activities to add')
    GWRutils.logMessage(log, '...No new stand activities to add')
else:
    print('...{0} new stand activitie(s) to add'.format(str(len(stand_act))))
    GWRutils.logMessage(log, '...{0} new stand activitie(s) to add'.format(
                              str(len(stand_act))))
    
    try:
        # Append stand activities to intermediate feature
        fields = GWRutils.customFieldMapper(mobile_act_script, mobile_act)
        for item in stand_act.items():
            where = """{0} = {1}""".format(arcpy.AddFieldDelimiters(
                                            sde_connection,'OBJECTID'), item[0])
            arcpy.MakeFeatureLayer_management(mobile_act, 'stand_act', where)        
            print('...Layer created for mobile stand activity oid: {0}'.format(
                    str(item[0])))
            GWRutils.logMessage(log, '...Mobile stand activity layer created')

            # Append mobile activity record to intermediate activity table
            with arcpy.da.SearchCursor('stand_act', fields) as sCur:
                with arcpy.da.InsertCursor(mobile_act_script, fields) as iCur:
                    for row in sCur:
                        iCur.insertRow(row)
                        print('...Appended record to intermediate feature')
                        GWRutils.logMessage(log, '...Appended record to ' +
                                                  'intermediate feature')
      
            # Select stand by its OID from mobile activity and copy geometry
            where = """{0} = {1}""".format(arcpy.AddFieldDelimiters(
                                            sde_connection, 'ObjectID'),
                                            item[1][1])
            arcpy.MakeFeatureLayer_management(stands, 'temp_stands', where)
            print('...Selected stand with activity')
            GWRutils.logMessage(log, '...Selected stand with activity')
            
            # Copy stand geometry and GUID field to intermediate feature
            where = """{0} = '{1}'""".format(arcpy.AddFieldDelimiters(
                                              mobile_gdb, 'Parent_GUID'),
                                              item[1][0])
            fields_stand = ['OID@', 'SHAPE@']
            fields_int = ['Parent_OID', 'SHAPE@']
            with arcpy.da.SearchCursor('temp_stands', fields_stand) as sCur:
                with arcpy.da.UpdateCursor(mobile_act_script,
                                            fields_int,where) as uCur:
                    for srow in sCur:
                        for urow in uCur:
                            urow[0] = srow[0]
                            urow[1] = srow[1]
                            uCur.updateRow(urow)
                            print('...Geometry and GUID copied')
                            GWRutils.logMessage(log, '...Geometry and GUID ' +
                                                      'copied')

    except Exception as e:
        print('Failed during steps to append stand activty to intermediate '
              'feature! Exiting...')
        print(e)
        GWRutils.logMessage(log, 'Failed during steps to append stand activty'+
                                  ' to intermediate feature! Exiting...')
        GWRutils.logMessage(log, str(e))
        sys.exit()
    
    try:
        # Append intermediate features to target activity features  
        new_fields = GWRutils.customFieldMapper(target_act, mobile_act_script)
        new_fields.append('SHAPE@')
        edit = arcpy.da.Editor(arcpy.env.workspace)
        edit.startEditing(False, True)
        edit.startOperation()         
        with arcpy.da.SearchCursor(mobile_act_script, new_fields) as sCur:
            with arcpy.da.InsertCursor(target_act, new_fields) as iCur:
                for row in sCur:
                    iCur.insertRow(row)
                    print('...Appended to target activities')
                    GWRutils.logMessage(log, '...Appended to target' +
                                              ' activities')
        edit.stopOperation()
        edit.stopEditing(True)

    except Exception as e:
        print('Failed during steps to append to target activity records! ' +
              'Exiting...')
        print(e)
        GWRutils.logMessage(log, 'Failed during steps to append to target ' +
                                  'activity records! Exiting...')
        GWRutils.logMessage(log, str(e))
        GWRutils.abortEditOperation(edit)
        sys.exit()

    # After append, search target activities and retrieve new activity OIDs
    try:
        activityOIDs = []
        target_fields = ['OID@', 'Parent_GUID']
        for item in stand_act.items():
            where = """{0} = '{1}'""".format(arcpy.AddFieldDelimiters(
                                      sde_connection, 'Parent_GUID'),
                                      item[1][0])
            with arcpy.da.SearchCursor(target_act,target_fields,where) as sCur:
                for srow in sCur:
                    activityOIDs.append(srow[0])
                    print('...Retrieved target activity OID: {0}'.format(
                          str(srow[0])))
                    GWRutils.logMessage(log, '...Retrieved target activity ' +
                                              'OID: {0}'.format(str(srow[0])))
                    
    except Exception as e:
        print('Failed while retrieving target activity OID! Exiting...')
        print(e)
        GWRutils.logMessage(log, 'Failed while retrieving target activity ' +
                                  'OID! Exiting...')
        GWRutils.logMessage(log, str(e))
        sys.exit()

    # Connect to db and execute stand overly procedure for each activity OID
    overlay_proc = sql_procs['stand_overlay_proc']
    try:
        with GWRutils.connectToDB(cnxn_info) as cnxn:
            print('...Connected to SQL Server')
            GWRutils.logMessage(log, '...Connected to SQL Server')
            for oid in activityOIDs:
                execute = GWRutils.executeSQLProcStandOverlay(cnxn, 
                                                              overlay_proc,
                                                              oid)
                if execute:
                    print('...Stand overlay proc executed for oid: {0}'
                          .format(str(oid)))
                    GWRutils.logMessage(log, '...Stand overlay proc executed '+
                                              'for oid: {0}'.format(str(oid)))
                else:
                    print('Failed to execute stand overlay proc! Exiting...')
                    GWRutils.logMessage(log, 'Failed to execute stand ' +
                                              'overlay proc! Exiting...')
                    sys.exit()

    except Exception as e:
        print('Failed to connect to SQL Server! Exiting...')
        print(e)
        GWRutils.logMessage(log, 'Failed to connect to SQL Server! Exiting...')
        GWRutils.logMessage(log, str(e))
        sys.exit()

# ------------------------------- Chemicals ----------------------------------#
if not chems:
    print('...No new chemical applications to add')
    GWRutils.logMessage(log, '...No new chemical applications to add')
    pass
else:
    print('...{0} new chemical application(s) to add'.format(str(len(chems))))
    GWRutils.logMessage(log,'...{0} new chemical application(s) to add'.format(
                        str(len(chems))))
    
    try:
        # Append chemical mobile records to chem app table
        chem_fields = GWRutils.customFieldMapper(target_che, mobile_che)
        edit = arcpy.da.Editor(arcpy.env.workspace)
        edit.startEditing(False, True)
        edit.startOperation()
        with arcpy.da.SearchCursor(mobile_che, chem_fields) as sCur:
            with arcpy.da.InsertCursor(target_che, chem_fields) as iCur:
                for row in sCur:
                    iCur.insertRow(row)
                    print('...Appended chemical records to target')
                    GWRutils.logMessage(log, '...Appended chemical records ' +
                                        'to target')
        edit.stopOperation()
        edit.stopEditing(True)

    except Exception as e:
        print('Failed while appending chemical records to target! Exiting...')
        print(e)
        GWRutils.logMessage(log, 'Failed while appending chemical records ' +
                                  'to target! Exiting...')
        GWRutils.logMessage(log, str(e))
        GWRutils.abortEditOperation(edit)
        sys.exit()
    
    try:
        # Apped a copy to chem app script table, change status to active then 
        # append to chem app table
        context = ['Activity_ContextID']
        chem_fields = GWRutils.customFieldMapper(mobile_chem_script,mobile_che)
        with arcpy.da.SearchCursor(mobile_che, chem_fields) as sCur:
            with arcpy.da.InsertCursor(mobile_chem_script,chem_fields) as iCur:
                for row in sCur:
                    iCur.insertRow(row)
                    print('...Appended chemical records to chem script table')
                    GWRutils.logMessage(log, '...Appended chemical records ' +
                                        'to chem script table')
        with arcpy.da.UpdateCursor(mobile_chem_script, context) as uCur:
            for row in uCur:
                row[0] = 1440
                uCur.updateRow(row)
                print('...Changed contextID to 1440')
                GWRutils.logMessage(log, '...Changed contextID to 1440')
        arcpy.Append_management(mobile_chem_script, target_che, 'NO_TEST')
        print('...Copied actual record to target chems')
        GWRutils.logMessage(log, '...Copied actual record to target chems')
        
    except Exception as e:
        print('Failed while creating actual chem record! Exiting...')
        print(e)
        GWRutils.logMessage(log, 'Failed while creating actual chem record! '+
                            'Exiting...')
        GWRutils.logMessage(log, str(e))
        sys.exit()
    
    try:
        # Retrive ActivityOIDs and GlobalIds based on GUID
        act_oids_globalIds = {}
        for guid in chems.values():
            where = """{0} = '{1}'""".format(arcpy.AddFieldDelimiters(
                                              sde_connection,'Parent_GUID'), 
                                              guid)
            field_act = ['OID@', 'GlobalID']
            with arcpy.da.SearchCursor(target_act, field_act, where) as sCur:
                for row in sCur:
                    act_oids_globalIds[row[0]] = (guid, row[1])

        edit = arcpy.da.Editor(arcpy.env.workspace)
        edit.startEditing(False, True)
        edit.startOperation() 
        for item in act_oids_globalIds.items():
            where = """{0} = '{1}'""".format(arcpy.AddFieldDelimiters(
                                              sde_connection,'Child_GUID'),
                                              item[1][0])
            field_che = ['ActivityOID', 'TFM_OP_ACTIVITY_GlobalID']
            with arcpy.da.UpdateCursor(target_che, field_che, where) as uCur:
                for urow in uCur:
                    urow[0] = item[0]
                    urow[1] = item[1][1]
                    uCur.updateRow(urow)
                    print('...ActivityOID and GlobalID copied to chem table')
                    GWRutils.logMessage(log, '...ActivityOID and GlobalId ' +
                                             'copied to chem app table')
        edit.stopOperation()
        edit.stopEditing(True)

    except Exception as e:
        print('Failed while copying ActivityOID/GlobalId to chem table! ' +
              'Exiting...')
        print(e)
        GWRutils.logMessage(log, 'Failed while copying ActivityOID/GLobalID '+
                                 'to chem table! Exiting...')
        GWRutils.logMessage(log, str(e))
        GWRutils.abortEditOperation(edit)
        sys.exit()    

# -------------------------------- Clean Up ----------------------------------#
# Reset mobile datasets by clearing all records
result = GWRutils.resetMobileFeatures([mobile_act, mobile_che,
                                        mobile_act_script, mobile_chem_script])
if result:
    print('...Cleared mobile datasets')
    GWRutils.logMessage(log, '...Cleared mobile datasets')
else:
    print('Failed to clear mobile datasets!')
    GWRutils.logMessage(log, 'Failed to clear mobile datasets!')
  
arcpy.ClearWorkspaceCache_management()
print(GWRutils.getTime())