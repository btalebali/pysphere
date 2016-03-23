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

import ssl
import json
import pypacksrc
import time
import threading
import os
import urllib2
import mmap
import sys, re, getpass, argparse, subprocess



def vs_connect(host, user, password, unverify=True):
  if unverify:
    try:
      ssl._create_default_https_context = ssl._DEFAULT_CIPHERS
    except:
      pass
  con = VIServer()
  con.connect(host, user,password,None)
  return con




def find_vm(vCenterserver, user, password, name):
    con = vs_connect(vCenterserver, user, password, unverify=True)
    try:
        vm = con.get_vm_by_name(name)
        return vm
    except VIException:
        return None


def get_RP_by_name(host, user, password, name):
    con = vs_connect(host, user, password, unverify=True)
    rps = con.get_resource_pools()
    for mor, path in rps.iteritems():
        print('Parsing RP %s' % path)
        if re.match('.*%s' % name,path):
            return mor
    return None



def run_post_script(name,ip, post_script):
    retcode = subprocess.call([post_script,name,ip])
    if retcode < 0:
        resp = 'ERROR: %s %s %s : Returned a non-zero result' % (post_script,name,ip)
        return resp


def find_ip(vm, ipv6=False, maxwait=120):
    net_info = None
    waitcount = 0
    while net_info is None:
        if waitcount > maxwait:
            break
        net_info = vm.get_property('net',False)
        waitcount += 5
        sleep(5)
    if net_info:
        for ip in net_info[0]['ip_addresses']:
            if ipv6 and re.match('\d{1,4}\:.*',ip) and not re.match('fe83\:.*',ip):
                return ip
            elif not ipv6 and re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',ip) and ip != '127.0.0.1':
                return ip
    return None











def get_dvSwitchs_by_DC(vCenterserver, username, password, datacentername):
  con = vs_connect(vCenterserver, username, password)
  dcmor = [k for k,v in con.get_datacenters().items() if v==datacentername][0]
  dcprops = VIProperty(con, dcmor)
  nfmor = dcprops.networkFolder._obj
  dvswitch_mors = con._retrieve_properties_traversal(property_names=['name'],from_node=nfmor, obj_type = 'DistributedVirtualSwitch')
  respdict={}
  for dvswitch_mor in dvswitch_mors:
    respdict[dvswitch_mor.PropSet[0]._val] = dvswitch_mor.Obj
  return respdict
 



def  get_portgroup_by_dvSwitchname(vCenterserver, username, password, datacentername,dvSwitchname):
  con = vs_connect(vCenterserver, username, password)
  dcmor = [k for k,v in con.get_datacenters().items() if v==datacentername][0]
  dcprops = VIProperty(con, dcmor)
  nfmor = dcprops.networkFolder._obj
  dvswitch_mors = con._retrieve_properties_traversal(property_names=['name','type'],from_node=nfmor, obj_type = 'DistributedVirtualPortgroup')
  respdict={}
  for dvswitch_mor in dvswitch_mors:
    respdict[dvswitch_mor.PropSet[0]._val] = dvswitch_mor.Obj
  return respdict
 
 

def  get_standardvS_by_DC(vCenterserver, username, password, datacentername):
  con = vs_connect(vCenterserver, username, password)
  dcmor = [k for k,v in con.get_datacenters().items() if v==datacentername][0]
  dcprops = VIProperty(con, dcmor)
  nfmor = dcprops.networkFolder._obj
  dvswitch_mors = con._retrieve_properties_traversal(property_names=['name'],from_node=nfmor, obj_type = 'VirtualSwitch')
  respdict={}
  for dvswitch_mor in dvswitch_mors:
    respdict[dvswitch_mor.PropSet[0]._val] = dvswitch_mor.Obj
  return respdict
 
 
 




def vs_find_datacenter_by_name(vCenterserver, user, password, name):
  response = "failure datcenter not found"
  if name.isspace() or not(name) or (name=="None"):
    return "None"
  con = None
  try:
    con = vs_connect(vCenterserver, user, password)
    rps = con.get_datacenters()
    for mor, path in rps.iteritems():
      if re.match('.*%s' % name, mor):
        response = str(path)
        break
  except Exception, error:
    response = str_remove_specialchars( error )
  if con:
    con.disconnect()
  return response





def str_remove_specialchars( s ):
  resp = None
  if hasattr(s, 'status') and hasattr(s, 'message'):
    resp = "provider.status: " + str(s.status) + " provider.message: failure "+ str(s.message)
  else:
    resp = "failure " + str(s)
  response = resp
  response = response.replace(pypacksrc.dcvt_delimiter," ")
  return response










