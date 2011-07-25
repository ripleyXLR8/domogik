#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

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

Sms Orange Manager

Implements
==========

- SmsOrangeManager

@author: Gizmo - Guillaume MORLET <contact@gizmo-network.fr>
@copyright: (C) 2007-2011 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.sms import Sms
import traceback

class SmsManager(XplPlugin):
    """ Manage Sms
    """

    def __init__(self):
        """ Init manager
        """
        XplPlugin.__init__(self, name = 'sms')

        # Configuration

        self._config = Query(self.myxpl, self.log)
        login = self._config.query('sms', 'login')
        password = self._config.query('sms', 'password')
        phone = self._config.query('sms', 'phone')

	self.log.debug("Init info for sms created")
        ### Create Sms objects
        self.my_sms = Sms(self.log,login,password,phone)
	self.log.debug("Create object for sms created")
        # Create listener
        Listener(self.sms_cb, self.myxpl, {'schema': 'sendmsg.basic','xpltype': 'xpl-cmnd'})
        self.log.debug("Listener for sms created")

        self.enable_hbeat()


    def sms_cb(self, message):
        """ Call sms lib
            @param message : xPL message detected by listener
        """
        # body contains the message
	self.log.debug("Function call back : entry")
        if 'body' in message.data:
            body = message.data['body']
        else:
            self._log.warning("Xpl message : missing 'body' attribute")
            return
        if 'to' in message.data:
            to = message.data['to']
        else:
            self._log.warning("Xpl message : missing 'to' attribute")
            return

        try:
	    self.log.debug("function call back : before send")
            self.my_sms.send(to,body)
	    self.log.debug("function call back : after send")
        except:
	       self.log.error("Error while sending sms : %s" % traceback.format_exc())
               mess = XplMessage()
               mess.set_type('xpl-trig')
               mess.set_schema('sendmsg.confirm')
               mess.add_data({'status' :  'Sms not send'})
               mess.add_data({'error' :  'function send'})
               self.myxpl.send(mess)
               return



        # Send xpl-trig to say plugin receive command
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('sendmsg.confirm')
	if self.my_sms.status_send == 0:
        	mess.add_data({'status' :  'Sms not send'})
		mess.add_data({'error' :  self.my_sms.status_error})
	else:
        	mess.add_data({'status' :  'Sms send'})
	
        self.myxpl.send(mess)

if __name__ == "__main__":
    inst = SmsManager()

