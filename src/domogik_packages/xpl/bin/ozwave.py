#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}$

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

Support Z-wave technology

Implements
==========

- Zwave

@author: Nico <nico84dev@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys
# sys.path.append("/var/lib/domogik")

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.ozwave import OZWavemanager
from domogik_packages.xpl.lib.ozwave import OZwaveException
# from lib.ozwave import OZWave


class OZwave(XplPlugin):
    """ Implement a listener for Zwave command messages
        and launch background  manager to listening zwave events by callback
    """
    def __init__(self):
        """ Create listener and background zwave manager
        """
        XplPlugin.__init__(self, name = 'ozwave')
        
        # Récupère la config 
        # - device
        self._config = Query(self.myxpl, self.log)
        device = self._config.query('ozwave', 'device')
        ozwlogConf = self._config.query('ozwave', 'ozwlog')
        self._config = Query(self.myxpl, self.log)
        print ('Mode log openzwave :',  ozwlogConf)
        # Recupère l'emplacement des fichiers de configuration OZW
        pathUser = self.get_data_files_directory()  +'/'
        pathConfig = self._config.query('ozwave', 'configpath') + '/'
        # Initialise le manager Open zwave
        try:
            self.myzwave = OZWavemanager(self._config, self.send_xPL, self.sendxPL_trig, self.get_stop(), self.log, configPath = pathConfig,  userPath = pathUser,  ozwlog = ozwlogConf,  msgEndCb = True) # ozwlog="")
        except OZwaveException as e:
            self.log.error(e.value)
            print e.value
            self.force_leave()
            return    
        self.add_stop_cb(self.myzwave.stop)
        # Crée le listener pour les messages de commande xPL traités par les devices zwave
        Listener(self.ozwave_cmd_cb, self.myxpl,{'schema': 'ozwave.basic',
                                                 'xpltype': 'xpl-cmnd'})
        # Validation avant l'ouverture du controleur, la découverte du réseaux zwave prends trop de temps -> RINOR Timeout
        self.enable_hbeat()
        # Ouverture du controleur principal
        self.myzwave.openDevice(device)                  

    def ozwave_cmd_cb(self, message):
        """" Envoie la cmd xpl vers le OZWmanager"""
        print ("commande xpl recue")
        print message
        self.log.debug(message)
        if 'command' in message.data:
            if 'group'in message.data:
                # en provenance de l'UI spéciale
                self.ui_cmd_cb(message)
            else :
                cmd = message.data['command']
                device = message.data['device']
                if cmd == 'level' :
                    print ("appel envoi zwave command %s" %cmd)
                    lvl = message.data['level']
                    self.myzwave.sendNetworkZW(cmd, device, lvl)
                elif cmd == "on"  or cmd == "off" :
                    print ("appel envoi zwave command %s" %cmd)
                    self.myzwave.sendNetworkZW(cmd, device)
                else:
                    self.myzwave.sendNetworkZW(cmd, device)
                    
    def getdict2UIdata(self, UIdata):
        """ retourne un format dict en provenance de l'UI (passage outre le format xPL)"""
#        retval = UIdata.replace('|', '{').replace('\\', '}')
        retval = UIdata.replace('&quot;', '"').replace('&squot;', "'").replace("&ouvr;", '{').replace("&ferm;", '}') ;
        try :
 #           return  eval(retval.replace(';', ','))
            return eval(retval)
        except :
            print retval
            self.log.debug ("Format data to UI : eval in getdict2UIdata error : " +   retval)
            return {'error': 'invalid format'}
            
    def getUIdata2dict(self, ddict):
        """Retourne le dict formatter pour UI (passage outre le format xPL)"""
  #      return str(ddict).replace('{', '|').replace('}', '\\').replace(',',';').replace('False', 'false').replace('True', 'true').replace('None', "''")
        print "conversion pour transfertvers UI , " , str(ddict)
        for k in ddict :   # TODO: pour passer les 1452 chars dans RINOR, à supprimer quand MQ OK, 
  #          print ('++++',  type(ddict[k]))
            if isinstance(ddict[k], str) :
                ddict[k] = ddict[k].replace("'", "&squot;")  # remplace les caractères interdits pour rinor
   #             print ('****Replace quote : ',  ddict[k])
                if len(str(ddict[k])) >800 : 
                    ddict[k]=ddict[k][:800]
                    print("value raccourccis : ", k, ddict[k])
                    self.log.debug ("Format data to UI : value to large, cut to 800, key : %s, value : %s" % (str(k), str(ddict[k])))
        return str(ddict).replace('{', '&ouvr;').replace('}', '&ferm;').replace('"','&quot;').replace("'",'&quot;').replace('False', 'false').replace('True', 'true').replace('None', '""')
        
    def ui_cmd_cb(self, message):
        """xpl en provenace de l'UI (config/special)"""
        response = True
        info = "essais"
        request = self.getdict2UIdata(message.data['value'])
        print("Commande UI")
        if message.data['group'] =='UI' :
            mess = XplMessage()
            mess.set_type('xpl-trig') 
            mess.set_schema('ozwave.basic')
            if request['request'] == 'ctrlAction' :
                action = dict(request)
                del action['request']
                report = self.myzwave.handle_ControllerAction(action)
                info = self.getUIdata2dict(report)
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'ctrlaction' : request['action'], 
                                    'data': info})
                if request['cmd'] =='getState' and report['cmdstate'] != 'stop' : response = False
            elif request['request'] == 'ctrlSoftReset' :
                info = self.getUIdata2dict(self.myzwave.handle_ControllerSoftReset())
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'data': info})
            elif request['request'] == 'ctrlHardReset' :
                info = self.getUIdata2dict(self.myzwave.handle_ControllerHardReset())
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'data': info})   
            elif request['request'] == 'GetNetworkID' :
                info = self.getUIdata2dict(self.myzwave.getNetworkInfo())
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'node' : 0, 
                                    'data': info})
                print "Refresh network info"
            elif request['request'] == 'GetNodeInfo' :
                info = self.myzwave.getNodeInfos(request['node'])
                gprs = info['Groups']
                del info['Groups']
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'node' : request['node'],
                                    'data': self.getUIdata2dict(info), 
                                    'countgrps': len(gprs)})
                i=0
                for gp in gprs :
                    mbrs=gp['members']
                    del gp['members']
                    mess.add_data({'group%d' %i :  self.getUIdata2dict(gp)})
                    ii=0
                    for m in mbrs :
                        print 'insert member'
                        mess.add_data({'g%dm%d' %(i, ii) : self.getUIdata2dict(m) })
                        ii=ii+1
                    i = i +1
                print "Refresh node :",  request['node'],  mess
            elif  request['request'] == 'SaveConfig':
                info = self.getUIdata2dict(self.myzwave.saveNetworkConfig())
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'node' :0, 
                                    'data': info})
            elif  request['request'] == 'SetNodeNameLoc':
                info = self.getUIdata2dict(self.myzwave.setUINodeNameLoc(request['node'], request['newname'],  request['newloc']))
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'node' : request['node'], 
                                    'data': info})
            elif  request['request'] == 'GetNodeValuesInfo':
                info =self.myzwave.getNodeValuesInfos(request['node'])
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'node' : request['node'], 
                                    'count': len(info['Values']) })
                i=0
                for inf in info['Values']:
                    mess.add_data({'value%d' %i :  self.getUIdata2dict(inf)})
                    i = i +1
                print mess
            elif  request['request'] == 'GetValueInfos':
                valId = long(request['valueid']) # Pour javascript type string
                info =self.getUIdata2dict(self.myzwave.getValueInfos(request['node'], valId))
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'valueid' : request['valueid'], 
                                    'data': info})
                print mess
            elif  request['request'] == 'GetValueTypes':
                info = self.getUIdata2dict(self.myzwave.getValueTypes())
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'listetypes' : 'valuestype', 
                                    'data': info})               
                print mess
            elif  request['request'] == 'GetListCmdsCtrl':
                listeCmd = self.myzwave.getListCmdsCtrl()
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'listetypes' : 'cmdsctrl'})
                i=1
                for item in listeCmd:
                    if item =='error':
                        if listeCmd[item] =='' : mess.add_data({'error' :  'no' })
                        else : mess.add_data({'error' :  listeCmd[item] })
                    else :
                        d = {item: listeCmd[item]}
                        mess.add_data({'item%d'%i : self.getUIdata2dict(d) })
                        i=i+1
                print mess
            elif  request['request'] == 'setValue':
                valId = long(request['valueid']) # Pour javascript type string
                newvalue = request['newValue']
                info = self.getUIdata2dict(self.myzwave.setValue(request['node'], valId, newvalue))
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'listetypes' : 'valuestype', 
                                    'data': info})
                print mess
            elif  request['request'] == 'setGroups':
                info = self.getUIdata2dict(self.myzwave.setMembersGrps(request['node'], request['ngrps']))
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'node' : request['node'], 
                                    'data': info})               
                print mess
            elif  request['request'] == 'GetGeneralStats':
                info = self.myzwave.getGeneralStatistics()
                err = info['error']
                del info['error']
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'error': err if err != '' else "no", 
                                    'data': self.getUIdata2dict(info)})               
                print mess                
            elif  request['request'] == 'GetNodeStats':
                info = self.myzwave.getNodeStatistics(request['node'])
                err = info['error']
                mess.add_data({'command' : 'Refresh-ack', 
                    'group' :'UI', 
                    'node' : request['node'],
                    'error': err if err != '' else "no"})
                if err =='' :
                    ccData = info['ccData']
                    del info['error']
                    del info['ccData']
                    del info['lastReceivedMessage']  # TODO: key supprimée, gerer le message zwave en hex.
                    for  item in info : info[item] = str (info[item]) # Pour etre compatible avec javascript
                    mess.add_data({'data': self.getUIdata2dict(info)})
                    i = 1
                    for item in ccData :
                        item['commandClassId'] = self.myzwave.getCommandClassName(item['commandClassId'] ) + ' (' + hex(item['commandClassId'] ) +')'
                        for  cclass in item: item[cclass] = str (item[cclass])  # Pour etre compatible avec javascript
                        mess.add_data({'item%d' %i  : self.getUIdata2dict(item)})
                        i=i+1
                print mess                             
            else :
                mess.add_data({'command' : 'Refresh-ack', 
                                    'group' :'UI', 
                                    'data': "unknown request", 
                                    'error': "unknown request"})
                print "commande inconnue"
            if response : self.myxpl.send(mess)
                                  
                                    
    def send_xPL(self, header,  msg):
        """ Envoie une commande ou message zwave vers xPL"""
        mess = XplMessage()
        mess.set_type(header['type']) 
        mess.set_schema(header['schema'])
        mess.add_data(header['data'])
   #     for k in msg.keys() : 
        info = self.getUIdata2dict(msg)
        print '********************* Dans send_xPL *****************'
        mess.add_data({'data': info})
        print mess
        self.myxpl.send(mess)
        
    def sendxPL_trig(self, msgtrig):
        mess = XplMessage()
        if 'info' in msgtrig:
            self.log.error ("Error : Node %s unreponsive" % msgtrig['node'])
        elif 'Find' in msgtrig:
            print("node enregistré : %s" % msgtrig['Find'])
        elif 'typexpl' in msgtrig:
            print ("send xpl-trig")
            print msgtrig	
        #    mess.set_type('xpl-trig') # force xpl-trig
            mess.set_type(msgtrig['typexpl'])
            mess.set_schema(msgtrig['schema'])
            if msgtrig['genre'] == 'actuator' :
                if msgtrig['level'] in [0, 'False', False] : cmd ="off"
                elif msgtrig['level'] in [255, 'True',  True]: cmd ="on"
                else: cmd ='level'
                mess.add_data({'device' : msgtrig['device'],
                            'command' : cmd,
                            'level': msgtrig['level']})
                if msgtrig.has_key('type'): mess.add_data({'type' : msgtrig['type'] })
            elif msgtrig['genre'] == 'sensor' :  # tout sensor
                if msgtrig['type'] =='status' :  # gestion du sensor binary pour widget binary
                    mess.add_data({'device' : msgtrig['device'],
                            'type' : msgtrig['type'] ,
                            'current' : 'true' if msgtrig['value']   else 'false'})
                else : mess.add_data({'device' : msgtrig['device'],  
                            'type' : msgtrig['type'] ,
                            'current' : msgtrig['value'] })
            if msgtrig.has_key('units') and msgtrig['units'] !='' : mess.add_data({'units' : msgtrig['units'] })
            print mess
            self.myxpl.send(mess)
        elif 'command' in msgtrig and msgtrig['command'] == 'Info':
            print("Home ID is %s" % msgtrig['Home ID'])

if __name__ == "__main__":
    OZwave()
