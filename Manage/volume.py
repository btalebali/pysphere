'''
Created on 23 mars 2016

@author: btalebali@prologue.fr
'''


from __builtin__ import filter
import json
import mmap
import os
import pypacksrc
from pysphere import  VIProperty, VITask, VIException, FaultTypes
from pysphere import  vi_task
from pysphere import VIServer, MORTypes
from pysphere.ZSI import fault
from pysphere.resources import VimService_services as VI
from pysphere.resources import VimService_services as VI
from pysphere.vi_mor import VIMor
from pysphere.vi_virtual_machine import VIVirtualMachine
import ssl
import sys, re, getpass, argparse, subprocess
import threading
from time import sleep
import time
import urllib2
from urlparse import urlparse


class volumes(object):
  '''
  classdocs
  '''
  def __init__(self, params):
    '''
    Constructor
    '''


  def create(self, params):
#   #########INPUTS ##############
#        :param vm_name: (str): 
#        :param vCenterserver: (str):
#        :param username: (str):
#        :param password: (str):
#        :param DATASTORE_NAME: (str):
#        :param DISK_SIZE_IN_GB: (str): 
#        :param UNIT_NUMBER: (str): 
# #########OUTPUTS ############## 
#          :param response: (str):
#          :param VMDKFILE:(str):
    DATASTORE_NAME = "datastore1"
    DISK_SIZE_IN_GB = 1
    UNIT_NUMBER = int("01")
    
    
    # Get VM
    clone=con.get_vm_by_name(vm_name)
    
    
    request = VI.ReconfigVM_TaskRequestMsg()
    _this = request.new__this(clone._mor)
    _this.set_attribute_type(clone._mor.get_attribute_type())
    request.set_element__this(_this)
    
    spec = request.new_spec()
    #Setup operation
    dc = spec.new_deviceChange()
    dc.Operation = "add"
    dc.FileOperation = "create"
    
    
    hd = VI.ns0.VirtualDisk_Def("hd").pyclass()
    hd.Key = -100
    hd.set_element_unitNumber(UNIT_NUMBER)
    hd.CapacityInKB = DISK_SIZE_IN_GB * 1024 * 1024
    hd.ControllerKey = 1000
    
    
    backing = VI.ns0.VirtualDiskFlatVer2BackingInfo_Def("backing").pyclass()
    backing.FileName = "[%s]" % DATASTORE_NAME
    backing.DiskMode = "persistent"
    backing.Split = False
    backing.WriteThrough = False
    backing.ThinProvisioned = False
    backing.EagerlyScrub = False
    hd.Backing = backing
    
    dc.Device = hd
    spec.DeviceChange = [dc]
    request.Spec = spec
    task = con._proxy.ReconfigVM_Task(request)._returnval
    vi_task = VITask(task, con)
    
    #Wait for task to finish
    status = vi_task.wait_for_state([vi_task.STATE_SUCCESS,
                         vi_task.STATE_ERROR])
    if status == vi_task.STATE_ERROR:
    response = "ERROR CONFIGURING clone:"+ vi_task.get_error_message()
    else:
    response =  "clone CONFIGURED SUCCESSFULLY"
    
    #GET VMDK file
    var = clone._disks
    g=len (var)
    if(g==1):
    print("No disk presented in the Vm")
    
    for i in range(1, g):
    if var[i]['device']['unitNumber']== UNIT_NUMBER:
    VMDKFILE    =var[i]['descriptor']
    



#########################################################################
#########################################################################
####### DETACH DISK: Could be done if disk is unmounted #################
#########################################################################
"""

#########INPUTS ############## 
        :param vm_name: (str): VM name
        :param vCenterserver: (str):
        :param username: (str):
        :param password: (str):
        :param UNIT_NUMBER: (str):

#########OUTPUTS ############## 
        :param response:(str):
"""


UNIT_NUMBER=int("02")
con = VIServer()
con.connect(vCenterserver, username,password,LOG_FILE)


# Get VM
clone=con.get_vm_by_name(vm_name)


#find the device to be removed
dev = [dev for dev in clone.properties.config.hardware.device 
       if dev._type == "VirtualDisk" and dev.unitNumber == UNIT_NUMBER]

if not dev:
    raise Exception("NO DEVICE FOUND")

dev = dev[0]._obj

request = VI.ReconfigVM_TaskRequestMsg()
_this = request.new__this(clone._mor)
_this.set_attribute_type(clone._mor.get_attribute_type())
request.set_element__this(_this)

spec = request.new_spec()
dc = spec.new_deviceChange()
dc.Operation = "remove"

dc.Device = dev

spec.DeviceChange = [dc]
request.Spec = spec

task = con._proxy.ReconfigVM_Task(request)._returnval
vi_task = VITask(task, con)

status = vi_task.wait_for_state([vi_task.STATE_SUCCESS, vi_task.STATE_ERROR])
if (status == vi_task.STATE_ERROR):
    raise Exception("Error detaching hdd from vm:"+ str(vi_task.get_error_message()))
else:
    response = "Hard drive successfully detached"



#########################################################################
####### ATTACH existing DISK
#########################################################################

    """
#########INPUTS ############## 
        :param vm_name: (str): VM name
        :param vCenterserver: (str):
        :param username: (str):
        :param password: (str):
        :param DISK_SIZE_IN_GB: (str):
        :param UNIT_NUMBER: (str):
        :param VMDK FILE: (str):
        :param mode:(str)   

#########OUTPUTS ##############

        :param response:(str):        
        """


UNIT_NUMBER = int("02")
VMDKFILE = '[datastore1] FirstVMusingPysphere/FirstVMusingPysphere_1.vmdk'
CapacityInKB= int("1048576")
mode="persistent"

con = VIServer()
con.connect(vCenterserver, username,password,LOG_FILE)

# Get VM
clone=con.get_vm_by_name(vm_name)


request = VI.ReconfigVM_TaskRequestMsg()
_this = request.new__this(clone._mor)
_this.set_attribute_type(clone._mor.get_attribute_type())
request.set_element__this(_this)


spec = request.new_spec()

dc = spec.new_deviceChange()
dc.Operation = "add"


hd = VI.ns0.VirtualDisk_Def("hd").pyclass()
hd.Key = -100
hd.UnitNumber = UNIT_NUMBER
hd.CapacityInKB = int(DISK_SIZE_IN_GB) * 1024 * 1024
hd.ControllerKey = 1000


backing = VI.ns0.VirtualDiskFlatVer2BackingInfo_Def("backing").pyclass()
backing.FileName = VMDKFILE
backing.DiskMode = mode
backing.ThinProvisioned = False
hd.Backing = backing


connectable = hd.new_connectable()
connectable.StartConnected = True
connectable.AllowGuestControl = False
connectable.Connected = True
hd.Connectable = connectable

dc.Device = hd

spec.DeviceChange = [dc]
request.Spec = spec

task = con._proxy.ReconfigVM_Task(request)._returnval
vi_task = VITask(task, con)


#Wait for task to finish
status = vi_task.wait_for_state([vi_task.STATE_SUCCESS,
                                 vi_task.STATE_ERROR])


if status == vi_task.STATE_ERROR:
    response = "ERROR CONFIGURING VM:"+ vi_task.get_error_message()
else:
    response = "VM CONFIGURED SUCCESSFULLY"



#########################################################################
####### DELETE DISK: Should be done if volume is detached    ############
#########################################################################
    """
        delete detach disk from datastore
       
        :param vm_name: (str): VM name
        :param vCenterserver: (str):
        :param username: (str):
        :param password: (str):
        :param UNIT_NUMBER: (str):
        :param VMDK FILE: (str):
        :param DISK_SIZE_IN_GB: (str)
        :param mode:(str)  
         
#########OUTPUTS ##############

        :param response:(str):           
        """

UNIT_NUMBER = int("02")
VMDKFILE = '[datastore1] FirstVMusingPysphere/FirstVMusingPysphere_1.vmdk'

mode="persistent"
DISK_SIZE_IN_GB="1"

con = VIServer()
con.connect(vCenterserver, username,password,LOG_FILE)


request = VI.ReconfigVM_TaskRequestMsg()
_this = request.new__this(clone._mor)
_this.set_attribute_type(clone._mor.get_attribute_type())
request.set_element__this(_this)


spec = request.new_spec()

dc = spec.new_deviceChange()

dc.FileOperation = "destroy"


hd = VI.ns0.VirtualDisk_Def("hd").pyclass()
hd.Key = -100
hd.UnitNumber = UNIT_NUMBER
hd.CapacityInKB = int(DISK_SIZE_IN_GB) * 1024 * 1024
hd.ControllerKey = 1000


backing = VI.ns0.VirtualDiskFlatVer2BackingInfo_Def("backing").pyclass()
backing.FileName = VMDKFILE
backing.DiskMode = mode
backing.ThinProvisioned = False
hd.Backing = backing


connectable = hd.new_connectable()
connectable.StartConnected = True
connectable.AllowGuestControl = False
connectable.Connected = True
hd.Connectable = connectable

dc.Device = hd

spec.DeviceChange = [dc]
request.Spec = spec

task = con._proxy.ReconfigVM_Task(request)._returnval
vi_task = VITask(task, con)


#Wait for task to finish
status = vi_task.wait_for_state([vi_task.STATE_SUCCESS,
                                 vi_task.STATE_ERROR])


if status == vi_task.STATE_ERROR:
    response = "ERROR CONFIGURING VM:"+ vi_task.get_error_message()
else:
    response = "VM CONFIGURED SUCCESSFULLY"



#########################################################################
#########################################################################
    