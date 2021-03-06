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

Defines the sql schema used by Domogik

Implements
==========

- class DeviceUsage
- class Plugin
- class PluginConfig
- class DeviceType
- class Device
- class DeviceFeature
- class DeviceStats
- class Person
- class UserAccount

@author: Marc SCHNEIDER <marc@domogik.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import time, sys
from exceptions import AssertionError

from sqlalchemy import (
        types, create_engine, Table, Column, Index, Integer, Float, String, Enum,
        MetaData, ForeignKey, Boolean, DateTime, Date, Text,
        Unicode, UnicodeText, UniqueConstraint
)
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref, relationship

from domogik.common.utils import ucode
from domogik.common.configloader import Loader


DEVICE_TYPE_LIST = ['appliance', 'lamp', 'music', 'sensor']
ACTUATOR_VALUE_TYPE_LIST = ['binary', 'range', 'list', 'trigger', 'number', 'string', 'complex',]
SENSOR_VALUE_TYPE_LIST = ['boolean', 'number', 'string']

Base = declarative_base()
metadata = Base.metadata

_cfg = Loader('database')
_config = None
# TODO : if no need
#if len(sys.argv) > 1:
#    _config = _cfg.load(sys.argv[1])
#else:
_config = _cfg.load()
_db_prefix = dict(_config[1])['db_prefix']


# Define objects
class DeviceUsage(Base):
    """Usage of a device (temperature, heating, lighting, music...)"""

    __tablename__ = '%s_device_usage' % _db_prefix
    id = Column(Unicode(80), primary_key=True)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText())
    default_options = Column(UnicodeText())

    def __init__(self, id, name, description=None, default_options=None):
        """Class constructor

        @param id : usage id
        @param name : short name of the usage
        @param description : extended description, optional
        @param default_options : default options, optional

        """
        self.id = ucode(id)
        self.name = ucode(name)
        self.description = ucode(description)
        self.default_options = ucode(default_options)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceUsage(id=%s, name='%s', desc='%s', default opt='%s')>"\
                % (self.id, self.name, self.description, self.default_options)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceUsage.__tablename__


class Plugin(Base):
    """Plugins"""

    __tablename__ = '%s_plugin' % _db_prefix
    id = Column(Unicode(30), primary_key=True, nullable=False)
    description = Column(UnicodeText())
    version = Column(Unicode(30))

    def __init__(self, id, description=None, version=None):
        """Class constructor

        @param id : plugin id (ie x10, plcbus, eibknx...) with no spaces / accents or special characters
        @param description : extended description, optional
        @param version : version number, optional

        """
        self.id = ucode(id)
        self.description = ucode(description)
        self.version = ucode(version)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Plugin(id='%s', desc='%s', version='%s')>" % (self.id, self.description, self.version)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Plugin.__tablename__


class PluginConfig(Base):
    """Configuration for a plugin (x10, plcbus, ...)"""

    __tablename__ = '%s_plugin_config' % _db_prefix
    id = Column(Unicode(30), primary_key=True)
    hostname = Column(Unicode(40), primary_key=True)
    key = Column(Unicode(30), primary_key=True)
    value = Column(Unicode(255), nullable=False)

    def __init__(self, id, hostname, key, value):
        """Class constructor

        @param id : plugin id
        @param hostname : hostname the plugin is installed on
        @param key : key
        @param value : value

        """
        self.id = ucode(id)
        self.hostname = ucode(hostname)
        self.key = ucode(key)
        self.value = ucode(value)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<PluginConfig(id=%s, hostname=%s, (%s, %s))>" % (self.id, self.hostname, self.key, self.value)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return PluginConfig.__tablename__


class DeviceType(Base):
    """Type of a device (x10.Switch, x10.Dimmer, Computer.WOL...)"""

    __tablename__ = '%s_device_type' % _db_prefix
    id = Column(Unicode(80), primary_key=True)
    plugin_id = Column(Unicode(30), ForeignKey('%s.id' % Plugin.get_tablename()), nullable=False)
    plugin = relation(Plugin)
    name = Column(Unicode(80), nullable=False)
    description = Column(UnicodeText())

    def __init__(self, id, name, plugin_id, description=None):
        """Class constructor

        @paral id : device type id
        @param name : short name of the type
        @param description : extended description, optional
        @param plugin_id : plugin id

        """
        self.id = ucode(id)
        self.name = ucode(name)
        self.description = ucode(description)
        self.plugin_id = ucode(plugin_id)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceType(id='%s', name='%s', desc='%s', plugin='%s')>"\
               % (self.id, self.name, self.description, self.plugin)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceType.__tablename__


class Device(Base):
    """Device"""

    __tablename__ = '%s_device' % _db_prefix
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText())
    reference = Column(Unicode(30))
    address = Column(Unicode(255), nullable=True)
    device_type_id = Column(Unicode(80), ForeignKey('%s.id' % DeviceType.get_tablename()), nullable=True)
    device_type = relation(DeviceType)
    commands = relationship("Command", backref=__tablename__, cascade="all, delete")
    sensors = relationship("Sensor", backref=__tablename__, cascade="all, delete")
    xpl_commands = relationship("XplCommand", backref=__tablename__, cascade="all, delete")
    xpl_stats = relationship("XplStat", backref=__tablename__, cascade="all, delete")

    def __init__(self, name, reference, device_type_id, description=None):
        """Class constructor

        @param name : short name of the device
        @param address : device address (like 'A3' for x10, or '01.123456789ABC' for 1wire)
        @param reference : internal reference of the device (like AM12 for a X10 device)
        @param device_type_id : 'link to the device type (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param description : extended description, optional

        """
        self.name = ucode(name)
        self.reference = ucode(reference)
        self.device_type_id = device_type_id
        self.description = ucode(description)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Device(id=%s, name='%s', desc='%s', ref='%s', type='%s', commands=%s, sensors=%s, xplcommands=%s, xplstats=%s)>"\
               % (self.id, self.name, self.description, self.reference,\
                  self.device_type, self.commands, \
                  self.sensors, self.xpl_commands, self.xpl_stats)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Device.__tablename__

class DeviceStats(Base):
    """Device stats (values that were associated to the device)"""

    __tablename__ = '%s_device_stats' % _db_prefix
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, index=True)
    # This is used for mysql compatibility reasons as timestamps are NOT handled in Unix Time format
    timestamp = Column(Integer, nullable=False)
    skey = Column(Unicode(30), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()), nullable=False)
    device = relation(Device)
    # We have both types for value field because we need an explicit numerical field in case we want to compute
    # arithmetical operations (min/max/avg etc.). If it is a numerical value, both fields are filled in. If it is a
    # character value only 'value' field is filled in.
    __value_num = Column('value_num', Float)
    value = Column('value_str', Unicode(255))
    __table_args__ = (Index('ix_core_device_stats_date_skey_device_id', "date", "skey", "device_id"), )

    def __init__(self, date, timestamp, skey, device_id, value):
        """Class constructor

        @param date : date when the stat was recorded
        @param timestamp : corresponding timestamp
        @param skey : key for the stat
        @param device_id : device id
        @param value : stat value (numerical or string)

        """
        self.date = date
        self.timestamp = timestamp
        self.skey = ucode(skey)
        try:
            self.__value_num = float(value)
        except ValueError:
            pass
        self.value = ucode(value)
        self.device_id = device_id

    def get_date_as_timestamp(self):
        """Convert DateTime value to timestamp"""
        return time.mktime(self.date.timetuple())

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceStats(%s, date='%s', (%s, %s), device=%s)>" % (self.id, self.date, self.skey, self.value,
                                                                      self.device)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceStats.__tablename__

class Person(Base):
    """Persons registered in the app"""

    __tablename__ = '%s_person' % _db_prefix
    id = Column(Integer, primary_key=True)
    first_name = Column(Unicode(20), nullable=False)
    last_name = Column(Unicode(20), nullable=False)
    birthdate = Column(Date)
    user_accounts = relation("UserAccount", backref=__tablename__, cascade="all, delete")

    def __init__(self, first_name, last_name, birthdate):
        """Class constructor

        @param first_name : first name
        @param last_name : last name
        @param birthdate : birthdate

        """
        self.first_name = ucode(first_name)
        self.last_name = ucode(last_name)
        self.birthdate = birthdate

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Person(id=%s, first_name='%s', last_name='%s', birthdate='%s')>"\
               % (self.id, self.first_name, self.last_name, self.birthdate)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Person.__tablename__


class UserAccount(Base):
    """User account for persons : it is only used by the UI"""

    __tablename__ = '%s_user_account' % _db_prefix
    id = Column(Integer, primary_key=True)
    login = Column(Unicode(20), nullable=False, unique=True)
    __password = Column("password", Unicode(255), nullable=False)
    person_id = Column(Integer, ForeignKey('%s.id' % Person.get_tablename()))
    person = relation(Person)
    is_admin = Column(Boolean, nullable=False, default=False)
    skin_used = Column(Unicode(80), nullable=False)

    def __init__(self, login, password, is_admin, skin_used, person_id):
        """Class constructor

        @param login : login
        @param password : password
        @param person_id : id of the person associated to this account
        @param is_admin : True if the user has administrator privileges
        @param skin_used : skin used in the UI (default value = 'default')

        """
        self.login = ucode(login)
        self.__password = ucode(password)
        self.person_id = person_id
        self.is_admin = is_admin
        self.skin_used = ucode(skin_used)

    def set_password(self, password):
        """Set a password for the user"""
        self.__password = ucode(password)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<UserAccount(id=%s, login='%s', is_admin=%s, person=%s)>"\
               % (self.id, self.login, self.is_admin, self.person)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return UserAccount.__tablename__

class Command(Base):
    __tablename__ = '%s_command' % _db_prefix
    id = Column(Integer, primary_key=True) 
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()), primary_key=True)
    name = Column(Unicode(255))
    reference = Column(Unicode(64))
    return_confirmation = Column(Boolean)
    xpl_command = relation("XplCommand", backref=__tablename__, cascade="all, delete", uselist=False)
    params = relationship("CommandParam", backref=__tablename__, cascade="all, delete")

    def __init__(self, device_id, name, reference, return_confirmation):
        self.device_id = device_id
        self.name = ucode(name)
        self.return_confirmation = return_confirmation
        self.reference = ucode(reference)
   
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Command(id=%s device_id=%s reference='%s' name='%s' return_confirmation=%s params=%s xpl_command=%s)>"\
               % (self.id, self.device_id, self.reference, self.name, self.return_confirmation, self.params, self.xpl_command)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Command.__tablename__

class CommandParam(Base):
    __tablename__ = '%s_command_param' % _db_prefix
    cmd_id = Column(Integer, ForeignKey('%s.id' % Command.get_tablename()), primary_key=True, nullable=False, autoincrement='ignore_fk') 
    key = Column(Unicode(32), nullable=False, primary_key=True, autoincrement='ignore_fk')
    data_type = Column(Unicode(32), nullable=False)
    conversion = Column(Unicode(255), nullable=True)
    UniqueConstraint('cmd_id', 'key', name='uix_1')

    def __init__(self, cmd_id, key, data_type, conversion):
        self.cmd_id = cmd_id
        self.key = ucode(key)
        self.data_type = ucode(data_type)
        self.conversion = ucode(conversion)
   
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<CommandParam(cmd_id=%s key='%s' data_type='%s' conversion='%s')>"\
               % (self.cmd_id, self.key, self.data_type, self.conversion)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return CommandParams.__tablename__

class Sensor(Base):
    __tablename__ = '%s_sensor' % _db_prefix
    id = Column(Integer, primary_key=True) 
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()), index=True)
    name = Column(Unicode(255))
    reference = Column(Unicode(64))
    data_type = Column(Unicode(32), nullable=False)
    conversion = Column(Unicode(255), nullable=True)
    last_value = Column(Unicode(32), nullable=True)
    last_received = Column(Integer, nullable=True)
    params = relationship("XplStatParam", backref=__tablename__, cascade="all, delete") 

    def __init__(self, device_id, name, reference, data_type, conversion):
        self.device_id = device_id
        self.name = ucode(name)
        self.reference = ucode(reference)
        self.data_type = ucode(data_type)
        self.conversion = ucode(conversion)
   
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Sensor(id=%s device_id=%s reference='%s' name='%s' data_type='%s' conversion='%s')>"\
               % (self.id, self.device_id, self.reference, self.name, self.data_type, self.conversion)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Sensor.__tablename__

class SensorHistory(Base):
    __tablename__ = '%s_sensor_history' % _db_prefix
    id = Column(Integer, primary_key=True) 
    sensor_id = Column(Integer, ForeignKey('%s.id' % Sensor.get_tablename()), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    value_num = Column(Float, nullable=True)
    value_str = Column(Unicode(32), nullable=False)

    def __init__(self, sensor_id, date, value):
        self.sensor_id = sensor_id
        self.date = date
        try:
            self.value_num = float(value)
        except ValueError:
            pass
        except TypeError:
            pass
        self.value_str = ucode(value)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<SensorHistory(sensor_id=%s date=%s value_str='%s' value_num=%s)>"\
               % (self.sensor_id, self.date, self.value_str, self.value_num)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return SensorHistory.__tablename__

class XplStat(Base):
    __tablename__ = '%s_xplstat' % _db_prefix
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()))
    json_id = Column(Unicode(64))
    name = Column(Unicode(64))
    schema = Column(Unicode(32))
    params = relationship("XplStatParam", backref=__tablename__, cascade="all, delete")
    
    def __init__(self, device_id, name, schema, json_id):
        self.device_id = device_id
        self.name = ucode(name)
        self.schema = ucode(schema)
        self.json_id = ucode(json_id)
   
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<XplStat(id=%s device_id=%s name='%s' schema='%s' params=%s json_id=%s)>"\
               % (self.id, self.device_id, self.name, self.schema, self.params, self.json_id)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return XplStat.__tablename__


class XplStatParam(Base):
    __tablename__ = '%s_xplstat_param' % _db_prefix
    xplstat_id = Column(Integer, ForeignKey('%s.id' % XplStat.get_tablename()), primary_key=True, nullable=False, autoincrement='ignore_fk') 
    key = Column(Unicode(32), nullable=False, primary_key=True, autoincrement=False)
    value = Column(Unicode(255))
    static = Column(Boolean)
    sensor_id = Column(Integer, ForeignKey('%s.id' % Sensor.get_tablename()), nullable=True) 
    ignore_values = Column(Unicode(255), nullable=True)
    UniqueConstraint('xplstat_id', 'key', name='uix_1')

    def __init__(self, xplstat_id, key, value, static, sensor_id, ignore_values):
        self.xplstat_id = xplstat_id
        self.key = ucode(key)
        self.value = ucode(value)
        self.static = static
        self.sensor_id = sensor_id
        self.ignore_values = ucode(ignore_values)
    
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<XplStatParam(stat_id=%s key='%s' value='%s' static=%s sensor_id=%s ignore='%s')>"\
               % (self.xplstat_id, self.key, self.value, self.static, self.sensor_id, self.ignore_values)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return XplStatParam.__tablename__


class XplCommand(Base):
    __tablename__ = '%s_xplcommand' % _db_prefix
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()))
    cmd_id = Column(Integer, ForeignKey('%s.id' % Command.get_tablename()))
    json_id = Column(Unicode(64))
    name = Column(Unicode(64))
    schema = Column(Unicode(32))
    stat_id = Column(Integer, ForeignKey('%s.id' % XplStat.get_tablename()), nullable=True)
    stat = relation("XplStat", backref=__tablename__, cascade="all, delete")
    params = relationship("XplCommandParam", backref=__tablename__, cascade="all, delete")

    def __init__(self, name, device_id, cmd_id, json_id, schema, stat_id):
        self.name = ucode(name)
        self.device_id = device_id
        self.cmd_id = cmd_id
        self.schema = ucode(schema)
        self.stat_id = stat_id
        self.json_id = json_id
    
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<XplCommand(id=%s device_id=%s cmd_id=%s name='%s' json_id='%s' schema='%s' stat_id=%s params=%s)>"\
               % (self.id, self.device_id, self.cmd_id, self.name, self.json_id, self.schema, self.stat_id, self.params)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return XplCommand.__tablename__


class XplCommandParam(Base):
    __tablename__ = '%s_xplcommand_param' % _db_prefix
    xplcmd_id = Column(Integer, ForeignKey('%s.id' % XplCommand.get_tablename()), primary_key=True, nullable=False, autoincrement='ignore_fk') 
    key = Column(Unicode(32), nullable=False, primary_key=True, autoincrement=False)
    value = Column(Unicode(255))
    UniqueConstraint('xplcmd_id', 'key', name='uix_1')

    def __init__(self, cmd_id, key, value):
        self.xplcmd_id = cmd_id
        self.key = ucode(key)
        self.value = ucode(value)
    
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<XplCommandParam(cmd_id=%s key='%s' value='%s')>"\
               % (self.xplcmd_id, self.key, self.value)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return XplCommandParam.__tablename__
