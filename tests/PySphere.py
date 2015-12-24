import time
import threading
import os
import urllib2
import mmap
import sys, re, getpass, argparse, subprocess
from urlparse import urlparse
from time import sleep
from pysphere import VIServer, MORTypes
from pysphere import  VIProperty, VITask,VIException, FaultTypes

from pysphere.vi_virtual_machine import VIVirtualMachine
from pysphere.resources import VimService_services as VI
from pysphere.vi_mor import VIMor
from pysphere import  vi_task

from pysphere.resources import VimService_services as VI

from pysphere.ZSI import fault
from __builtin__ import filter



vCenterServer = "172.17.117.104";
username      = "administrateur"       #"administrateur"
Password      = "Pr0l0gue2014"   #"Pr0l0gue2014";
LOG_FILE      = "/var/log/pysphere.log"
maxwait       =  120


template="Ubuntu12.04-VMware-Tool-64bits";
resource_pool="/Resources/RP-accords";
vm_name=  "vmforvolumetesting";


con = VIServer()
con.connect(vCenterServer, username,Password,LOG_FILE)

print('Connected to Server ');
print('Server type: %s' % con.get_server_type());
print('API version: %s' % con.get_api_version());


# List available ressources
print (con.get_hosts());
print(con.get_datastores());
print(con.get_clusters())
print(con.get_datacenters());
print(con.get_resource_pools());
print("\n");



######################List Available template ############################################

print("Available Templates : ")
template_list = con.get_registered_vms(advanced_filters={'config.template':True})
for t in template_list:
    vm = con.get_vm_by_path(t)
    prop = vm.get_properties()
    print(prop['name'])



def find_vm(name):
    try:
        vm = con.get_vm_by_name(name)
        return vm
    except VIException:
        return None


###################### Create Virtual Machine from a Template #############################
print("creating Virtual Machine");


def find_resource_pool(name):
    rps = con.get_resource_pools()
    for mor, path in rps.iteritems():
        print('Parsing RP %s' % path)
        if re.match('.*%s' % name,path):
            return mor
    return None

post_script="\n"
def run_post_script(name,ip):
    print('Running post script: %s %s %s' % (post_script,name,ip))
    retcode = subprocess.call([post_script,name,ip])
    if retcode < 0:
        print 'ERROR: %s %s %s : Returned a non-zero result' % (post_script,name,ip)
        sys.exit(1)

def find_ip(vm,ipv6=False):
    net_info = None
    waitcount = 0
    while net_info is None:
        if waitcount > maxwait:
            break
        net_info = vm.get_property('net',False)
        print('Waiting 5 seconds ...')
        waitcount += 5
        sleep(5)
    if net_info:
        for ip in net_info[0]['ip_addresses']:
            if ipv6 and re.match('\d{1,4}\:.*',ip) and not re.match('fe83\:.*',ip):
                print('IPv6 address found: %s' % ip)
                return ip
            elif not ipv6 and re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',ip) and ip != '127.0.0.1':
                print('IPv4 address found: %s' % ip)
                return ip
    print('Timeout expired: No IP address found')
    return None



###########################################Creating clone #######"


### finding template
template_vm = find_vm(template)


if template_vm is None:
    print 'ERROR: %s not found' % template
    sys.exit(1)

print('Template %s found' % template)


#### Finding ressource pool

print('Finding resource pool %s' % resource_pool)
resource_pool_mor = find_resource_pool(resource_pool)
if resource_pool_mor is None:
    print 'ERROR: %s not found' % resource_pool
    sys.exit(1)

print ('Resource pool %s found' % resource_pool)



if (find_vm(vm_name)):
    print 'ERROR: %s already exists' % vm_name
    sys.exit()
else:
    hosts="host-537"
    datastore="datastore-543"
    print template_vm
    clone = template_vm.clone(vm_name, sync_run=True, folder=None, resourcepool=resource_pool_mor, 
                           datastore=datastore, host=hosts, power_on=False, template=False,snapshot=None, linked=False)

print('clone %s created' % vm_name)
print('Booting clone %s' % vm_name)

clonepath =clone.get_properties()['path']





#########################################################################
###### CREATE and ATTACH DISK: Could be done whatever VM is on or off####
###### action="volume" in uic    ########################################
#########################################################################

""" 
#########INPUTS ############## 
        :param vm_name: (str): 
        :param vCenterServer: (str):
        :param username: (str):
        :param Password: (str):
        :param DATASTORE_NAME: (str):
        :param DISK_SIZE_IN_GB: (str):        
        :param UNIT_NUMBER: (str):

#########OUTPUTS ############## 
        :param response: (str):
        :param VMDKFILE:(str):
"""


DATASTORE_NAME = "Disque2Tera"
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
        :param vCenterServer: (str):
        :param username: (str):
        :param Password: (str):
        :param UNIT_NUMBER: (str):

#########OUTPUTS ############## 
        :param response:(str):
"""


NIT_NUMBER=int("01")
con = VIServer()
con.connect(vCenterServer, username,Password,LOG_FILE)


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
        :param vCenterServer: (str):
        :param username: (str):
        :param Password: (str):
        :param DISK_SIZE_IN_GB: (str):
        :param UNIT_NUMBER: (str):
        :param VMDK FILE: (str):
        :param mode:(str)   

#########OUTPUTS ##############

        :param response:(str):        
        """


UNIT_NUMBER = int("02")
VMDKFILE = '[Disque2Tera] vmforvolumetesting/vmforvolumetesting_1.vmdk'
CapacityInKB= int("1048576")
mode="persistent"

con = VIServer()
con.connect(vCenterServer, username,Password,LOG_FILE)

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
        :param vCenterServer: (str):
        :param username: (str):
        :param Password: (str):
        :param UNIT_NUMBER: (str):
        :param VMDK FILE: (str):
        :param DISK_SIZE_IN_GB: (str)
        :param mode:(str)  
         
#########OUTPUTS ##############

        :param response:(str):           
        """

UNIT_NUMBER = int("02")
VMDKFILE = '[Disque2Tera] vmforvolumetesting/vmforvolumetesting_1.vmdk'

mode="persistent"
DISK_SIZE_IN_GB="1"

con = VIServer()
con.connect(vCenterServer, username,Password,LOG_FILE)


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



