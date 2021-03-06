#!/usr/bin/python
# Script for restarting archiving device servers
# srubio@cells.es, 2009

import sys,time,os

import PyTango
try: import fandango
except ImportError: import PyTango_utils as fandango
from fandango.servers import ServersDict

hostname = os.getenv('HOST').split('.')[0]

def get_archiving_servers(schema=''):
    astor = ServersDict()
    astor.log.setLogLevel(astor.log.Warning)
    
    #Excluding watchers due to its high CPU usage
    names = len(sys.argv)>2 and sys.argv[2:] or ['ArchivingManager/*']\
        +(schema.lower() in ('hdb','') and ['HdbArchiver*/*','HdbExtractor/*'] or [])\
        +(schema.lower() in ('tdb','') and ['TdbArchiver*/*','TdbExtractor/*'] or [])
    [astor.load_by_name(name) for name in names]
    return astor
    
launch_order = ['archiver','extractor','manager','watcher']

if 'status' in sys.argv:
    print 'Checking the archiving system status ...'
    
    astor = get_archiving_servers()
    astor.update_states()
    
    running = sorted(['\t'.join((d.name,d.host,str(d.level))) for d in astor.values() if d.state == PyTango.DevState.ON and (d.host or d.level)])
    failed = sorted(['\t'.join((d.name,d.host,str(d.level))) for d in astor.values() if d.state != PyTango.DevState.ON and (d.host or d.level)])
    disabled = sorted(['\t'.join((d.name,d.host,str(d.level))) for d in astor.values() if not (d.host or d.level)])
    
    print '\n'
    print "*"*80
    print '\n'
    
    faulty = []
    goods = []
    dedicated = []
    
    if running:
        for s in running:
            server = s.split()[0]
            if server not in astor: continue
            devs = astor[server].get_device_list()
            for d in devs:
                dp = astor.proxies[d]
                try:
                    dp.ping()
                    if dp.state() == PyTango.DevState.FAULT:
                        faulty.append(d)
                    elif s not in goods:
                        goods.append(s)
                    if dp.get_property(['IsDedicated'])['IsDedicated']:
                        dedicated.append(d)
                    
                except:
                    if d not in faulty:
                        faulty.append(d)
    print '\n'
    if goods:
        print "Servers actually running are:"
        print "-"*40
        print '\n'.join(goods)
        print '\n'
    
    if dedicated:
        print "Devices dedicated are:"
        print "-"*40
        print '\n'.join(dedicated)
        print '\n'
    if faulty:
        print "Devices in FAULT state are:"
        print "-"*40
        print '\n'.join(faulty)
        print '\n'
    if failed:
        print "Servers that are not working:"
        print "-"*40
        print '\n'.join(failed)
        print '\n'
    if disabled:
        print "Servers not registered to any server:"
        print "-"*40
        print '\n'.join(disabled)
        print '\n'

elif 'start' in sys.argv:
    print 'Starting the archiving system ...'
    astor = get_archiving_servers()
    for name in launch_order:
        [astor.start_servers(k) for k in sorted(astor) if name in k.lower() and (hostname in astor[k].host)]
    print 'Archiving system started'
    
elif 'start-all' in sys.argv:
    print 'Starting the archiving system ...'
    astor = get_archiving_servers()
    for name in launch_order:
        [astor.start_servers(k) for k in sorted(astor) if name in k.lower()]
    print 'Archiving system started'
    
elif 'start-tdb' in sys.argv:
    print 'Starting the archiving system ...'
    astor = get_archiving_servers('tdb')
    for name in launch_order:
        [astor.start_servers(k) for k in sorted(astor) if name in k.lower()]
    print 'Archiving system started'    
    
elif 'start-hdb' in sys.argv:
    print 'Starting the archiving system ...'
    astor = get_archiving_servers('hdb')
    for name in launch_order:
        [astor.start_servers(k) for k in sorted(astor) if name in k.lower()]
    print 'Archiving system started'       
    
elif 'stop' in sys.argv:
    print 'Stopping the archiving system ...'
    servers = ['dserver/%s'%a for a in list(PyTango.Database().get_host_server_list(hostname)) if 'Archiv' in a]
    for a in sorted(servers):
        print('killing %s'%a)
        try: PyTango.DeviceProxy(a).kill()
        except Exception,e: print('\tfailed: %s'%e)
    print 'Archiving system stopped'

elif 'stop-all' in sys.argv:
    print 'Stopping the archiving system ...'
    servers = PyTango.Database().get_device_exported('dserver/*Archiv*/*')
    for a in sorted(servers):
        print('killing %s'%a)
        try: PyTango.DeviceProxy(a).kill()
        except Exception,e: print('\tfailed: %s'%e)
    print 'Archiving system stopped'
    
elif 'stop-tdb' in sys.argv:
    print 'Stoping the archiving system ...'
    servers = PyTango.Database().get_device_exported('dserver/Tdb*/*')
    for a in sorted(servers):
        print('killing %s'%a)
        try: PyTango.DeviceProxy(a).kill()
        except Exception,e: print('\tfailed: %s'%e)
    print 'Archiving system stop'    
    
elif 'stop-hdb' in sys.argv:
    print 'Stoping the archiving system ...'
    servers = PyTango.Database().get_device_exported('dserver/Hdb*/*')
    for a in sorted(servers):
        print('killing %s'%a)
        try: PyTango.DeviceProxy(a).kill()
        except Exception,e: print('\tfailed: %s'%e)
    print 'Archiving system stop'       
    
elif 'restart' in sys.argv:
    print 'Restarting the archiving system ...'
    astor = get_archiving_servers()
    launch_order.reverse()
    for name in launch_order:
        [astor.stop_servers(k) for k in sorted(astor) if name in k.lower() and (hostname in astor[k].host)]
    launch_order.reverse()
    time.sleep(10)
    for name in launch_order:
        [astor.start_servers(k) for k in sorted(astor) if name in k.lower() and (hostname in astor[k].host)]
    print 'Archiving system restarted'
    
else: 
    print 'Usage of the command is:'
    print '\tarchiving_service.py start-all #Starts all the archiving devices'
    print '\tarchiving_service.py start-tdb #Starts all tdb archiving devices'
    print '\tarchiving_service.py start-hdb #Starts all hdb archiving devices'
    print '\tarchiving_service.py start #Starts archiving devices in this host'
    print '\tarchiving_service.py stop-all #Stops all the archiving devices'
    print '\tarchiving_service.py stop-tdb #Stops all the tdb archiving devices'
    print '\tarchiving_service.py stop-hdb #Stops all the hdb archiving devices'
    print '\tarchiving_service.py stop #Stops archiving devices in this host'
    print '\tarchiving_service.py restart #Restarts all the archiving devices'
    print '\tarchiving_service.py status #Provides an overview of all the archiving devices'
    
