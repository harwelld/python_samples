# -*- coding: utf-8 -*-

import sys
from arcgis.gis import GIS

# Prompt user input in terminal to proceed with script
print('You have started the process to start or stop all GIS services')
proceed = input('If you wish to proceed, click ENTER, otherwise type "No" ' +
                'to exit...\n')
if proceed.lower() == 'no':
    print('Exiting!')
    sys.exit()
else:
    print('...Proceeding')

action = input('Please type "START" or "STOP" and click ENTER to either ' +
               'start or stop all services...\n')
if action.lower() not in ('start', 'stop'):
    raise Exception('Invalid service_action! Valid values are ' +
                    '"START" or "STOP"')

portal_url = 'https://gis.gwrglobal.com/arcgis'
username = 'siteadmin'
password = 'ForestTime21'
gis = GIS(portal_url, username, password)

server = gis.admin.servers.list()[0]
folders = ['Hosted', 'LRMMobileSolution']
service_list = [s for s in server.services.list()]
for f in folders:
    for s in server.services.list(f):
        service_list.append(s)
        
for s in service_list:
    if action.lower() == 'start':
        s.start()
        print('...Started service: {0}'.format(s.properties.serviceName))
    elif action.lower() == 'stop':
        s.stop()
        print('...Stopped service: {0}'.format(s.properties.serviceName))
