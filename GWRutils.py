# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:        GWRutils.py
#
# Purpose:     Helper functions for GreenWood Mobile App scripts.
#
# Author:      Dylan Harwell - Resource Data Inc
#
# Created:     11/15/2019
# -----------------------------------------------------------------------------

import pandas as pd
import pyodbc
import json
import time
import csv
import os
import shutil
from zipfile import ZipFile
from arcgis.gis import GIS
import arcpy


def getTime():
    """Fetches current date and time for logging"""
    date_time = time.strftime('%Y%m%d') + '_' + time.strftime('%H%M%S')
    return date_time


def logMessage(log_path, log_message):
    """Opens and appends a message to a specified log file"""
    with open(log_path, 'a') as log:
        log.write(log_message + '\n')


def validateConfig(config_path):
    """Ensures json.load will not throw exception from invalid json syntax"""
    with open(config_path, 'r') as config:
        try:
            json.load(config)
            return True
        except:        
            exception = 'Invalid config file, check json syntax! Exiting...'
            return exception
        

def configReader(config_path, config_type):
    """Reads properties of config.json file"""
    with open(config_path, 'r') as config:
        data = json.load(config)
        if config_type in data.keys():
            print('...Config loaded for: ' + config_type)
            return data[config_type]


def checkForChanges(change_type):
    """Appends a list to keep track of config properties 'true' values"""
    change_list = []
    for x in change_type:
        if change_type[x]:
            change_list.append(x)
    return change_list


def connectToDB(cnxn_info):
    """Retrieves connection info and connects to database using pyodbc"""
    driver = cnxn_info['driver']
    server = cnxn_info['server']
    database = cnxn_info['database']
    username = cnxn_info['username']
    password = cnxn_info['password']
    return pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' %
                          (driver, server, database, username, password))    


def executeSQLProcToPandasDF(db_connection, sql_proc, param_value=None):
    """Calls SQL stored procedure to retrieve updated category/type/subtype
       table for given propertyOID in same format as Survey123 itemsets.csv"""
    cursor = db_connection.cursor()
    df_list = []
    if param_value:
        sql = """EXEC {0}
                 @propertyOID = {1};
              """.format(sql_proc, param_value)
    else:
        sql = """EXEC {0};
              """.format(sql_proc)
    rows = cursor.execute(sql).fetchall()
    columns = [column[0] for column in cursor.description]
    df_list.append(pd.DataFrame.from_records(rows, columns=columns))
    return df_list


def executeSQLProcStandOverlay(db_connection, sql_proc, param_value):
    """Calls SQL stored procedure that LRM uses to match stand activity with
       stand participating in activity"""
    cursor = db_connection.cursor()
    sql = """EXEC {0}
             @OBJECTID = {1};
          """.format(sql_proc, param_value)
    try:
        rows = cursor.execute(sql)
        while rows.nextset():
            rows.fetchone()
    except:
        return False
    return True


def connectToPortal(portal_info):
    """Retrives Portal info and connects to Portal"""
    url = portal_info['url']
    username = portal_info['username']
    password = portal_info['password']
    return GIS(url, username, password)


def generateUpdatedCSV(pandas_DataFrame, out_path):
    """Converts pandas DatFrame object to csv"""
    pandas_DataFrame.to_csv(
            path_or_buf=out_path, sep=',', na_rep='', float_format=None,
            columns=None, header=True, index=False, index_label=None, mode='w',
            encoding=None, compression='infer', quoting=csv.QUOTE_ALL,
            quotechar='"', line_terminator=None, chunksize=None,
            date_format=None, doublequote=True, escapechar=None, decimal='.')


def downloadAndExtractFormItems(portal_connection, itemIDs, working_dir):
    """Downloads survey form items and extracts to current working directory"""
    for ID in itemIDs:
        item = portal_connection.content.get(ID[1])
        print(item)
        #zipName = item.name
        zipName = str(ID[0]) + '.zip'
        item.download(working_dir, zipName)
        with ZipFile(os.path.join(working_dir, zipName), 'r') as zip_file:
            zip_file.extractall(
                os.path.join(working_dir, zipName.replace('.zip', '')))
        os.remove(os.path.join(working_dir, zipName))


def swapCSVandUploadToPortal(portal_connection, itemIDs, working_dir):
    """Switches out the updated itemsets.csv in the media folder of each
       survey, zips the folder and uploads to Portal"""
    itemsets_path = '\\esriinfo\\media\\itemsets.csv'
    chems_path = '\\esriinfo\\media\\chemdefaults.csv'
    in_working_dir = os.listdir(working_dir)    
    updated_csvs = [name for name in in_working_dir if name.endswith('.csv')]
    for ID in itemIDs:
        item = portal_connection.content.get(ID[1])
        old_itemsets_path = os.path.join(working_dir,
                                         str(ID[0]) + itemsets_path)
        old_chems_path = os.path.join(working_dir,
                                         str(ID[0]) + chems_path)
        for csv_name in updated_csvs:
            if str(ID[0]) + 'itemsets.csv' in csv_name:
                new_itemsets_path = os.path.join(working_dir, 
                                                 str(ID[0]) + 'itemsets.csv')
                os.remove(old_itemsets_path)
                new_renamed_path1 = os.path.join(working_dir,
                                                str(ID[0]) + itemsets_path)
                shutil.move(new_itemsets_path, new_renamed_path1)
            if str(ID[0]) + 'chemdefaults.csv' in csv_name:
                new_chems_path = os.path.join(working_dir, 
                                                 str(ID[0])+'chemdefaults.csv')
                os.remove(old_chems_path)
                new_renamed_path2 = os.path.join(working_dir,
                                                str(ID[0]) + chems_path)
                shutil.move(new_chems_path, new_renamed_path2)
                #print('Swapped out updated itemsets.csv for: ' + str(ID[0]))
            out_zip = os.path.join(working_dir, str(ID[0]) + '.zip')
            with ZipFile(out_zip, 'w') as zf:
                os.chdir(os.path.join(working_dir, str(ID[0])))
                for dirname, subdirs, files in os.walk('esriinfo'):
                    for filename in files:
                        zf.write(os.path.join(dirname, filename))
            os.chdir(working_dir)
            #print('Compressed folder: ' + str(ID[0]))
            item.update(item_properties=None, data=out_zip)
            #print('Updated form item: ' + item.title)


def cleanWorkingDir(working_dir):
    """Deletes all folders and files from working directory"""
    for file in os.listdir(working_dir):
        file_path = os.path.join(working_dir, file)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def resetConfig(config_path, props_to_ignore=None):
    """Resets properties of config.json file back to false"""
    with open(config_path, 'r') as config:
        data = json.load(config)
    if (props_to_ignore):
        for k, v in data['properties'].items():
            if k[:3] in props_to_ignore:
                pass
            else:
                data['properties'][k] = False
    else:
        data['properties'] = {x: False for x in data['properties']}
    with open(config_path, 'w') as config:
        json.dump(data, config, indent=4)


def resetMobileFeatures(features):
    """Clears all records from a list of datasets"""
    for feature in features:
        try:
            arcpy.TruncateTable_management(feature)
        except:
            return False
    return True
     

def customFieldMapper(target_feature, source_feature):
    """Returns a list of fields to map for use with update/insert cursors"""
    ignore = ['OBJECTID', 'Shape', 'SHAPE', 'GlobalID', 'Shape.STArea()',
              'Shape.STLength()', 'STArea()', 'STLength()']
    target_fields = [f for f in arcpy.ListFields(target_feature)
                     if f.name not in ignore]
    source_fields = [f for f in arcpy.ListFields(source_feature)
                     if f.name not in ignore]
    fields_to_map = []
    for a in source_fields:
        for t in target_fields:
            if a.name.lower() == t.name.lower():
                fields_to_map.append(a.name)
    return fields_to_map


def abortEditOperation(edit_operation_object):
    """If an exception occurs during an edit session, stop without saving"""
    if edit_operation_object.isEditing:
        try:
            edit_operation_object.stopOperation()
        except:
            pass
        edit_operation_object.stopEditing(False)
        return True
    else:
        return False
       

def startOrStopServices(portal_connection, service_action):
    """Starts or stops all GIS services"""
    try:
        server = portal_connection.admin.servers.list()[0]
        folders = ['LRMMobileSolution']
        service_list = [s for s in server.services.list()]
        for f in folders:
            for s in server.services.list(f):
                service_list.append(s)
        for s in service_list:
            if service_action.lower() == 'start':
                s.start()
                print('...Started service: {0}'
                      .format(s.properties.serviceName))
            elif service_action.lower() == 'stop':
                s.stop()
                print('...Stopped service: {0}'
                      .format(s.properties.serviceName))
            else:
                raise Exception('Invalid service_action! Valid values are ' +
                                '"START" or "STOP"')
    except Exception as e:
        print(e)
        return False
    return True


def addPropertyActivityGeometry(propOIDs, property_fc, activity_fc):
    """Adds boundary geometry to property activities based on property OID"""
    try:
        # Create list of fields needed
        activity_fields = ['PropertyOID', 'SHAPE@']
        property_fields = ['ObjectID', 'SHAPE@']
        for prop in propOIDs:
            # Select property activities with where clause
            where_activity = """PropertyOID = {0} AND Category IN 
            ('Property', 'PropertyE', 'PropertyH', 'PropertyM')""".format(prop)
            arcpy.MakeFeatureLayer_management(activity_fc, 'temp_act',
                                              where_activity)
            print('Property activities selected for {0}'.format(prop))
            
            # Begin search cursor, select property boundary with where clause
            where_property = """ObjectID = {0}""".format(prop)
            with arcpy.da.SearchCursor(property_fc, property_fields,
                                        where_property) as sCur:
                print('Property boundary selected for {0}'.format(prop))
                
                # Begin update cursor on selected property activities
                with arcpy.da.UpdateCursor('temp_act',activity_fields) as uCur:
                    for sRow in sCur:
                        for uRow in uCur:
                            if uRow[0] == sRow[0]:
                                uRow[1] = sRow[1]
                                uCur.updateRow(uRow)
                            else:
                                print('OIDs do not match!')
                                print(sRow[0])
                                print(uRow[0])
                        print('Geometries copied for {0}'.format(prop))
        
    except Exception as e:
        print(e)
        return False
    return True

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    pass