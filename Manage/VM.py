from time import sleep
from pysphere import VITask, FaultTypes
from pysphere.vi_virtual_machine import VIVirtualMachine
from pysphere.resources.vi_exception import VIException, VIApiException
from pysphere.vi_mor import VIMor
from pysphere.vi_task import VITask
import ssl
import pypacksrc
import re, subprocess




def vs_connect(host, user, password, unverify=True):
  if unverify:
    try:
      ssl._create_default_https_context = ssl._create_unverified_context
    except:
      pass
  con = VIServer()
  con.connect(host, user,password,'/var/log/pysphere.log')
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
      if re.match('.*%s' % name,path):
          return mor
  return None


def run_post_script(name,ip, post_script):
  retcode = subprocess.call([post_script,name,ip])
  if retcode < 0:
      resp = 'ERROR: %s %s %s : Returned a non-zero result' % (post_script,name,ip)
      return resp




def get_vm_ip_addresses(vCenterserver, username, password,vm_name, ipv6=False, maxwait=120):
  vm_obj = find_vm(vCenterserver, username, password, vm_name)
  net_info = None
  waitcount = 0
  while net_info is None:
      if waitcount > maxwait:
          break
      net_info = vm_obj.get_property('net',False)
      waitcount += 5
      sleep(5)
  if net_info:
    return net_info
  return None




def get_NIC_address_per_connected_net(vCenterserver, username, password,vm_name, net_name, ipv6=False, maxwait=120):
  vm_obj = find_vm(vCenterserver, username, password, vm_name)
  net_info = None
  waitcount = 0
  while net_info is None:
      if waitcount > maxwait:
          break
      net_info = vm_obj.get_property('net',False)
      waitcount += 5
      sleep(5)
  if net_info:
    for i in range(len(net_info)): 
      for ip in net_info[i]['ip_addresses']:
          if ipv6 and re.match('\d{1,4}\:.*',ip) and not re.match('fe83\:.*',ip):
              if(net_info[i]['network']==net_name):
                return ip
          elif not ipv6 and re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',ip) and ip != '127.0.0.1':
              if(net_info[i]['network']==net_name):
                return ip
  return None



def get_dvSwitchs_by_DCname(vCenterserver, username, password, datacentername):
  con = vs_connect(vCenterserver, username, password)
  dcmor = [k for k,v in con.get_datacenters().items() if v==datacentername][0]
  dcprops = VIProperty(con, dcmor)
  nfmor = dcprops.networkFolder._obj
  dvswitch_mors = con._retrieve_properties_traversal(property_names=['name'],from_node=nfmor, obj_type = 'DistributedVirtualSwitch')
  respdict={}
  for dvswitch_mor in dvswitch_mors:
    respdict[dvswitch_mor.PropSet[0]._val] = dvswitch_mor.Obj
  return respdict



def get_dvSwitchuuid_by_dvsname_and_DC(vCenterserver, username, password, datacentername, dvSname):
  con = vs_connect(vCenterserver, username, password)
  dcmor = [k for k,v in con.get_datacenters().items() if v==datacentername][0]
  dcprops = VIProperty(con, dcmor)
  nfmor = dcprops.networkFolder._obj
  dvswitch_mors = con._retrieve_properties_traversal(property_names=['name',"uuid"],from_node=nfmor, obj_type = 'DistributedVirtualSwitch')
  
  for dvswitch_mor in dvswitch_mors:
    if dvswitch_mor.PropSet[0]._val == dvSname: 
      return dvswitch_mor.PropSet[1]._val
  return "Failure, dvswitch not found"




def get_portgroupname_by_ref(vCenterserver, username, password,datacentername, pgRef):
  con = vs_connect(vCenterserver, username, password)
  dcmor = [k for k,v in con.get_datacenters().items() if v==datacentername][0]
  dcprops = VIProperty(con, dcmor)
  nfmor = dcprops.networkFolder._obj
  portgroup_mors = con._retrieve_properties_traversal(property_names=['name','key'],from_node=nfmor, obj_type = 'DistributedVirtualPortgroup')
  for portgroup_mor in portgroup_mors:
    ref=portgroup_mor.get_element_propSet()[0].get_element_val()
    if ref==pgRef:
      return portgroup_mor.get_element_propSet()[1].get_element_val()
  return None




def get_portgroupref_by_name(vCenterserver, username, password,datacentername, PGname):
  con = vs_connect(vCenterserver, username, password)
  dcmor = [k for k,v in con.get_datacenters().items() if v==datacentername][0]
  dcprops = VIProperty(con, dcmor)
  nfmor = dcprops.networkFolder._obj
  portgroup_mors = con._retrieve_properties_traversal(property_names=['name','key'],from_node=nfmor, obj_type = 'DistributedVirtualPortgroup')
  for portgroup_mor in portgroup_mors:
      name = portgroup_mor.get_element_propSet()[1].get_element_val()
      if name==PGname:
        return portgroup_mor.get_element_propSet()[0].get_element_val()
  return None




def  get_portgroup_by_dvSwitchname(vCenterserver, username, password, datacentername, dvSwitchname):
  con = vs_connect(vCenterserver, username, password)
  dcmor = [k for k,v in con.get_datacenters().items() if v==datacentername][0]
  dcprops = VIProperty(con, dcmor)
  nfmor = dcprops.networkFolder._obj
  portgroup_mors = con._retrieve_properties_traversal(property_names=['name','portgroup'],from_node=nfmor, obj_type = 'VmwareDistributedVirtualSwitch')
  RespDic={}
  for portgroup_mor in portgroup_mors:
    if (portgroup_mor.get_element_propSet()[0].get_element_val()==dvSwitchname):
      pgRefs = portgroup_mor.get_element_propSet()[1].get_element_val().ManagedObjectReference
  for pgRef in pgRefs:
    portgroup_mors = con._retrieve_properties_traversal(property_names=['name','key'],from_node=nfmor, obj_type = 'DistributedVirtualPortgroup')
    for portgroup_mor in portgroup_mors:
      ref=portgroup_mor.get_element_propSet()[0].get_element_val()
      if ref==pgRef:
        name = portgroup_mor.get_element_propSet()[1].get_element_val()
    RespDic[name]=pgRef
  return RespDic





from pysphere import MORTypes
from pysphere import VIServer, VIProperty
from pysphere.resources import VimService_services as VI



def create_portgroup_in_host(vCenterserver, username, password, host, pgname, vswitchname, vlan_id):
  resp = "succeeded"
  con = None
  try:
    con = vs_connect(vCenterserver, username, password)
    hostmor = [k for k, v in con.get_hosts().items() if v == host][0]
    prop = VIProperty(con, hostmor)
    network_system = prop.configManager.networkSystem._obj
    request = VI.AddPortGroupRequestMsg()
    _this = request.new__this(network_system)
    _this.set_attribute_type(network_system.get_attribute_type())
    request.set_element__this(_this)
    portgrp = request.new_portgrp()
    portgrp.set_element_name(pgname)
    portgrp.set_element_vlanId(int(vlan_id))
    portgrp.set_element_vswitchName(vswitchname)
    portgrp.set_element_policy(portgrp.new_policy())
    request.set_element_portgrp(portgrp)
    con._proxy.AddPortGroup(request)
  except Exception, error:
    resp = str_remove_specialchars(error)
  if con:
    con.disconnect()
  return resp



def  get_standardvS_by_DCname(vCenterserver, username, password, datacentername):
  con = vs_connect(vCenterserver, username, password)
  dcmor = [k for k,v in con.get_datacenters().items() if v==datacentername][0]
  dcprops = VIProperty(con, dcmor)
  nfmor = dcprops.networkFolder._obj
  dvswitch_mors = con._retrieve_properties_traversal(property_names=['name'],from_node=nfmor, obj_type = 'Network')
  respdict={}
  for dvswitch_mor in dvswitch_mors:
    var=dvswitch_mor.get_element_obj().lower()
    if 'network' in var :
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


def add_nic_vm_and_connect_to_net(vCenterserver, username, password, datacentername, vm,  dvswitch_uuid, portgroupKey, network_name="VM Network", nic_type="vmxnet3", network_type="standard"):
  
  ### add a NIC
  # The network Name must be set as the device name to create the NIC.
  # Different network card types are: "VirtualE1000", "VirtualE1000e","VirtualPCNet32", "VirtualVmxnet", "VirtualNmxnet2", "VirtualVmxnet3"
  net_device = None
  con = vs_connect(vCenterserver, username, password)
  vm_obj = con.get_vm_by_name(vm,datacenter=datacentername)
  if not vm_obj:
    raise Exception("VM %s not found" % vm)

  #Find nic device
  for dev in vm_obj.properties.config.hardware.device:
    if dev._type in ["VirtualE1000", "VirtualE1000e","VirtualPCNet32", "VirtualVmxnet","VirtualNmxnet2", "VirtualVmxnet3"]:
      net_device = dev._obj
      break


  request = VI.ReconfigVM_TaskRequestMsg()
  _this = request.new__this(vm_obj._mor)
  _this.set_attribute_type(vm_obj._mor.get_attribute_type())
  request.set_element__this(_this)
  spec = request.new_spec()
  dev_change = spec.new_deviceChange()
  dev_change.set_element_device(net_device)
  #dev_change.set_element_operation("edit")

  if network_name:
    dev_change.set_element_operation("add")

    if nic_type == "e1000":
      nic_ctlr = VI.ns0.VirtualE1000_Def("nic_ctlr").pyclass()
    elif nic_type == "e1000e":
      nic_ctlr = VI.ns0.VirtualE1000e_Def("nic_ctlr").pyclass()
    elif nic_type == "pcnet32":
      nic_ctlr = VI.ns0.VirtualPCNet32_Def("nic_ctlr").pyclass()
    elif nic_type == "vmxnet":
      nic_ctlr = VI.ns0.VirtualVmxnet_Def("nic_ctlr").pyclass()
    elif nic_type == "vmxnet2":
      nic_ctlr = VI.ns0.VirtualVmxnet2_Def("nic_ctlr").pyclass()
    elif nic_type == "vmxnet3":
      nic_ctlr = VI.ns0.VirtualVmxnet3_Def("nic_ctlr").pyclass()

    if network_type == "standard":
      # Standard switch
      nic_backing = VI.ns0.VirtualEthernetCardNetworkBackingInfo_Def("nic_backing").pyclass()
      nic_backing.set_element_deviceName(network_name)
    elif network_type == "dvs":
      nic_backing_port = VI.ns0.DistributedVirtualSwitchPortConnection_Def("nic_backing_port").pyclass()
      nic_backing_port.set_element_switchUuid(dvswitch_uuid)
      nic_backing_port.set_element_portgroupKey(portgroupKey)

      # http://www.vmware.com/support/developer/vc-sdk/visdk400pubs/ReferenceGuide/vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo.html
      nic_backing = VI.ns0.VirtualEthernetCardDistributedVirtualPortBackingInfo_Def("nic_backing").pyclass()
      nic_backing.set_element_port(nic_backing_port)

      # How they do it in powershell
      # http://www.lucd.info/2010/03/04/dvswitch-scripting-part-8-get-and-set-network-adapters/
      # How they do it in ruby
      # https://github.com/fog/fog/pull/1431/files
    nic_ctlr.set_element_addressType("generated")
    nic_ctlr.set_element_backing(nic_backing)
    nic_ctlr.set_element_key(4)
    dev_change.set_element_device(nic_ctlr)
    spec.set_element_deviceChange([dev_change])
    request.set_element_spec(spec)
    ret = con._proxy.ReconfigVM_Task(request)._returnval
    #Wait for the task to finish
    task = VITask(ret, con)
    status = task.wait_for_state([task.STATE_SUCCESS, task.STATE_ERROR])
    if status == task.STATE_SUCCESS:
      return "VM successfully reconfigured"
    elif status == task.STATE_ERROR:
      return "failure reconfiguring vm: " + str(task.get_error_message())
  else:
    return "failure reconfiguring vm network_name is mandatory"


def disconnect_nic_from_network(vCenterserver, username, password, datacentername, vmname, dvswitch_uuid, portgroupKey, network_name="VM Network", nic_type="vmxnet3", network_type="standard"):

  con = vs_connect(vCenterserver, username, password)
  vm_obj = con.get_vm_by_name(vmname, datacenter=datacentername)

  #Disconnect 3rd adaptar if its connected to network "VM Network"
  #network_name = "VM Network"
  device_name = "Network adapter 3"

  #Find Virtual Nic device
  net_device = None
  for dev in vmname.properties.config.hardware.device:
      if (dev._type in ["VirtualE1000", "VirtualE1000e","VirtualPCNet32", "VirtualVmxnet","VirtualNmxnet2", "VirtualVmxnet3"]
      and dev.deviceInfo.label == network_name
      and dev.deviceInfo.summary == device_name):
          net_device = dev._obj
          break

  if not net_device:
      s.disconnect()
      raise Exception("The vm seems to lack a Virtual Nic")

  #Disconnect the device
  net_device.Connectable.Connected = True


  #Invoke ReconfigVM_Task
  request = VI.ReconfigVM_TaskRequestMsg()
  _this = request.new__this(vmname._mor)
  _this.set_attribute_type(vmname._mor.get_attribute_type())
  request.set_element__this(_this)
  spec = request.new_spec()
  dev_change = spec.new_deviceChange()
  dev_change.set_element_device(net_device)
  dev_change.set_element_operation("edit")
  spec.set_element_deviceChange([dev_change])
  request.set_element_spec(spec)
  ret = s._proxy.ReconfigVM_Task(request)._returnval

  #Wait for the task to finish
  task = VITask(ret, s)

  status = task.wait_for_state([task.STATE_SUCCESS, task.STATE_ERROR])
  if status == task.STATE_SUCCESS:
      print "VM successfully reconfigured"
  elif status == task.STATE_ERROR:
      print "Error reconfiguring vm:", task.get_error_message()

  s.disconnect()





























def get_vm_nics(vCenterserver, username, password, datacentername, vm_name):
  " To reteive status VM should vm power on "
  
  con = vs_connect(vCenterserver, username, password)
  net_device = None
  vm_obj = con.get_vm_by_name(vm_name,datacenter=datacentername)
  if not vm_obj:
    raise Exception("VM %s not found" % vm_name)
  respdict ={}
  sVSName = None
  dvs = None
  #Find nic device
  for dev in vm_obj.properties.config.hardware.device:
    if (dev._type in ["VirtualE1000", "VirtualE1000e","VirtualPCNet32", "VirtualVmxnet","VirtualNmxnet2", "VirtualVmxnet3"]
    and hasattr(dev, "backing") and hasattr(dev.backing, "deviceName")):
      label = dev.deviceInfo.label
      sVSName = str(dev.backing.deviceName)
      net_device = dev._obj
      status= net_device.Connectable.Connected
      respdict[label]=[sVSName,status]
    
    if (dev._type in ["VirtualE1000", "VirtualE1000e","VirtualPCNet32", "VirtualVmxnet","VirtualNmxnet2", "VirtualVmxnet3"]
    and hasattr(dev, "backing") and hasattr(dev.backing, "port")):
      label = dev.deviceInfo.label
      #label=unicode(label1, "utf-8")
      pgRef = str(dev.backing.port.portgroupKey)
      PGname = get_portgroupname_by_ref(vCenterserver, username, password,datacentername, pgRef)
      net_device = dev._obj
      status = net_device.Connectable.Connected
      respdict[label]=[PGname,status]
    
    if (dev._type in ["VirtualE1000", "VirtualE1000e","VirtualPCNet32", "VirtualVmxnet","VirtualNmxnet2", "VirtualVmxnet3"]
  and not hasattr(dev.backing, "deviceName")
  and not hasattr(dev.backing, "port")
  ):
      label = dev.deviceInfo.label
      respdict[label]=["No connexion","no status"]
      
  return respdict



def remove_nic_vm(vCenterserver, username, password, datacentername, vm_name, networklabel):
  con = vs_connect(vCenterserver, username, password)
  net_device = None
  vm_obj = con.get_vm_by_name(vm_name,datacenter=datacentername)
  if not vm_obj:
    raise Exception("VM %s not found" % vm_name)
  
    #Find nic device
  
  for dev in vm_obj.properties.config.hardware.device:
    if (dev._type in ["VirtualE1000", "VirtualE1000e","VirtualPCNet32", "VirtualVmxnet","VirtualNmxnet2", "VirtualVmxnet3"]
    and hasattr(dev, "backing")  
    and dev.deviceInfo.label == networklabel):
      net_device = dev._obj
      break
  
  if not net_device:
    raise Exception("The vm_name seems to lack a Virtual Nic")

  request = VI.ReconfigVM_TaskRequestMsg()
  _this = request.new__this(vm_obj._mor)
  _this.set_attribute_type(vm_obj._mor.get_attribute_type())
  request.set_element__this(_this)
  spec = request.new_spec()
  dev_change = spec.new_deviceChange()
  dev_change.set_element_operation("remove")
  dev_change.set_element_device(net_device)
  # Submit the device change
  spec.set_element_deviceChange([dev_change])
  request.set_element_spec(spec)
  ret = con._proxy.ReconfigVM_Task(request)._returnval

  # Wait for the task to finish
  task = VITask(ret, con)

  status = task.wait_for_state([task.STATE_SUCCESS, task.STATE_ERROR])
  if status == task.STATE_SUCCESS:
     return "VM successfully reconfigured"
  elif status == task.STATE_ERROR:
      return "failure reconfiguring vm_name: " + str(vm_obj, task.get_error_message())
  else:
    return " failure VM not found"




def connect_publicNIC_to_publicNet(vCenterserver, username, password, datacentername, vm_name, network_name, netlabel):
  '''
  Switch existing NIC to a different network
  con: VIServer object
  datacentername: datacenter name
  vm_name: VIVirtualMachine name
  network_name: network name
  '''
  
  con = vs_connect(vCenterserver, username, password)
  net_device = None
  vm_obj = con.get_vm_by_name(vm_name,datacenter=datacentername)
  if not vm_obj:
    raise Exception("VM %s not found" % vm_name)
  
  #Find nic device
  for dev in vm_obj.properties.config.hardware.device:
    if (dev._type in ["VirtualE1000", "VirtualE1000e","VirtualPCNet32", "VirtualVmxnet","VirtualNmxnet2", "VirtualVmxnet3"] 
    and hasattr(dev, "deviceInfo")
    and (dev.deviceInfo.label == netlabel)):
      net_device = dev._obj
  if not net_device:
    raise Exception("The vm_name seems to lack a Virtual Nic")
  
  if hasattr(net_device.Backing,"DeviceName"):
    net_device.Connectable.Connected = True
    net_device.Backing.set_element_deviceName(network_name)
  
  if hasattr(net_device.Backing,"Port"):
    #TODO convert device baching
    net_device.Connectable.Connected = True
  
  request = VI.ReconfigVM_TaskRequestMsg()
  _this = request.new__this(vm_obj._mor)
  _this.set_attribute_type(vm_obj._mor.get_attribute_type())
  request.set_element__this(_this)
  spec = request.new_spec()
  dev_change = spec.new_deviceChange()
  dev_change.set_element_device(net_device)
  dev_change.set_element_operation("edit")
  spec.set_element_deviceChange([dev_change])
  request.set_element_spec(spec)
  
  ret = con._proxy.ReconfigVM_Task(request)._returnval
  
  #Wait for the task to finish
  task = VITask(ret, con)
  status = task.wait_for_state([task.STATE_SUCCESS, task.STATE_ERROR])
  if status == task.STATE_SUCCESS:
    return "VM successfully reconfigured"
  elif status == task.STATE_ERROR:
    return "failure reconfiguring vm_name: " + str(task.get_error_message())






def disconnect_publicNIC_from_publicNet(vCenterserver, username, password, datacentername, vm_name, netlabel):
  '''
  Switch existing NIC to a different network
  con: VIServer object
  datacentername: datacenter name
  vm_name: VIVirtualMachine name
  '''
  
  
  con = vs_connect(vCenterserver, username, password)
  net_device = None
  vm_obj = con.get_vm_by_name(vm_name,datacenter=datacentername)
  if not vm_obj:
    raise Exception("VM %s not found" % vm_name)
  
  #Find nic device
  for dev in vm_obj.properties.config.hardware.device:
    if (dev._type in ["VirtualE1000", "VirtualE1000e","VirtualPCNet32", "VirtualVmxnet","VirtualNmxnet2", "VirtualVmxnet3"] 
    and hasattr(dev, "deviceInfo")
    and (dev.deviceInfo.label == netlabel)):
      net_device = dev._obj
  if not net_device:
    raise Exception("The vm_name seems to lack a Virtual Nic")
  
  if hasattr(net_device.Backing,"DeviceName"):
    net_device.Connectable.Connected = False
  
  if hasattr(net_device.Backing,"Port"):
    net_device.Connectable.Connected = False

    #TODO convert device baching

  request = VI.ReconfigVM_TaskRequestMsg()
  _this = request.new__this(vm_obj._mor)
  _this.set_attribute_type(vm_obj._mor.get_attribute_type())
  request.set_element__this(_this)
  spec = request.new_spec()
  dev_change = spec.new_deviceChange()
  dev_change.set_element_device(net_device)
  dev_change.set_element_operation("edit")
  spec.set_element_deviceChange([dev_change])
  request.set_element_spec(spec)
  
  ret = con._proxy.ReconfigVM_Task(request)._returnval

  #Wait for the task to finish
  task = VITask(ret, con)
  status = task.wait_for_state([task.STATE_SUCCESS, task.STATE_ERROR])
  if status == task.STATE_SUCCESS:
    return "VM successfully reconfigured"
  elif status == task.STATE_ERROR:
    return "failure reconfiguring vm_name: " + str(task.get_error_message())





def add_new_nic(server, datacentername, vm, network_name):
  '''
  add new NIC to a VM
  server: VIServer object
  datacentername: datacenter name
  vm: VIVirtualMachine name
  network_name: network name
  '''
  net_device = None
  vm_obj = server.get_vm_by_name(vm,datacenter=datacentername)
  if not vm_obj:
    raise Exception("VM not found")

  request = VI.ReconfigVM_TaskRequestMsg()
  _this = request.new__this(vm_obj._mor)
  _this.set_attribute_type(vm_obj._mor.get_attribute_type())
  request.set_element__this(_this)
  spec = request.new_spec()

  #add a nic.
  dev_change = spec.new_deviceChange()
  dev_change.set_element_operation("add")
  nic_ctlr = VI.ns0.VirtualPCNet32_Def("nic_ctlr").pyclass()
  nic_backing = VI.ns0.VirtualEthernetCardNetworkBackingInfo_Def("nic_backing").pyclass()
  nic_backing.set_element_deviceName(network_name)
  nic_ctlr.set_element_addressType("generated")
  nic_ctlr.set_element_backing(nic_backing)
  nic_ctlr.set_element_key(4)
  dev_change.set_element_device(nic_ctlr)

  spec.set_element_deviceChange([dev_change])
  request.set_element_spec(spec)
  ret = server._proxy.ReconfigVM_Task(request)._returnval

  #Wait for the task to finish
  task = VITask(ret, server)
  status = task.wait_for_state([task.STATE_SUCCESS, task.STATE_ERROR])
  if status == task.STATE_SUCCESS:
    return "VM successfully reconfigured"
  elif status == task.STATE_ERROR:
    return "failure reconfiguring vm: " + str(task.get_error_message())



def get_network_interfaces(vm_obj):
  vif_types = ["VirtualEthernetCard", "VirtualE1000", "VirtualE1000e", "VirtualPCNet32", "VirtualVmxnet"]
  vifs = []
  for device in vm_obj.properties.config.hardware.device:
    if device._type in vif_types:
      vifs.append(device)
  return vifs



def change_dvs_net(server, datacentername, vm, pg_map):
  """
  Reconfigure dVS portgroups according to the mappings in the pg_map dict
  server: VIServer object
  datacentername: datacenter name
  vm_obj: VIVirtualMachine object
  pg_map: dict must contain the source portgroup as key and the destination portgroup as value
  """
  vm_obj = server.get_vm_by_name(vm,datacenter=datacentername)
  if not vm_obj:
    raise Exception("VM %s not found" % vm)
  #Find virtual NIC devices
  if vm_obj:
    net_device = []
    for dev in vm_obj.properties.config.hardware.device:
      if dev._type in ["VirtualE1000", "VirtualE1000e","VirtualPCNet32", "VirtualVmxnet","VirtualNmxnet2", "VirtualVmxnet3"]:
        net_device.append(dev)

  # Throw an exception if there is no NIC found
  if len(net_device) == 0:
    raise Exception("The vm seems to lack a Virtual Nic")
  # Use pg_map to set the new Portgroups
  for dev in net_device:
    old_portgroup = dev.Backing.Port.PortgroupKey
    if pg_map.has_key(old_portgroup):
      dev.backing.port._obj.set_element_portgroupKey(pg_map[old_portgroup])
      dev.backing.port._obj.set_element_portKey('')

  # Invoke ReconfigVM_Task
  request = VI.ReconfigVM_TaskRequestMsg()
  _this = request.new__this(vm_obj._mor)
  _this.set_attribute_type(vm_obj._mor.get_attribute_type())
  request.set_element__this(_this)

  # Build a list of device change spec objects
  devs_changed = []
  for dev in net_device:
    spec = request.new_spec()
    dev_change = spec.new_deviceChange()
    dev_change.set_element_device(dev._obj)
    dev_change.set_element_operation("edit")
    devs_changed.append(dev_change)

  # Submit the device change list
  spec.set_element_deviceChange(devs_changed)
  request.set_element_spec(spec)
  ret = server._proxy.ReconfigVM_Task(request)._returnval

  # Wait for the task to finish
  task = VITask(ret, server)

  status = task.wait_for_state([task.STATE_SUCCESS, task.STATE_ERROR])
  if status == task.STATE_SUCCESS:
     return "VM successfully reconfigured"
  elif status == task.STATE_ERROR:
      return "failure reconfiguring vm: " + str(task.get_error_message())
  else:
    return " failure VM not found"

def poweron_vm(vCenterserver, username, password,datacentername,vm_name):
  con = vs_connect(vCenterserver, username, password)
  vm_obj = con.get_vm_by_name(vm_name,datacenter=datacentername)
  vmstatus=vm_obj.get_status()
  if (vmstatus=='POWERED OFF'):
    vm_obj.power_on()
    return "VM successfully powered on"
  return "VM on uncorrect status:  "+ vmstatus


def poweroff_vm(vCenterserver, username, password,datacentername,vm_name):
  con = vs_connect(vCenterserver, username, password)
  vm_obj = con.get_vm_by_name(vm_name,datacenter=datacentername)
  vmstatus=vm_obj.get_status()
  if (vmstatus=='POWERED ON'):
    vm_obj.power_off()
    return "VM successfully powerer off"
  return "VM on uncorrect status:  "+ vmstatus


def delete_vm(vCenterserver, username, password,datacentername,vm_name):
  con = vs_connect(vCenterserver, username, password)
  vm_obj = con.get_vm_by_name(vm_name,datacenter=datacentername)
  vmstatus=vm_obj.get_status()
  if (vmstatus=='POWERED OFF'):
    vm_obj.destroy()
    return "VM successfully deleted"
  return "VM on uncorrect status:  "+ vmstatus
 
def reboot_vm(vCenterserver, username, password,datacentername,vm_name):
  con = vs_connect(vCenterserver, username, password)
  vm_obj = con.get_vm_by_name(vm_name,datacenter=datacentername)
  vmstatus=vm_obj.get_status()
  if (vmstatus=='POWERED ON'):
    vm_obj.reboot_guest()
    return "VM successfully rebooted"
  return "VM on uncorrect status:  "+ vmstatus



def list_available_template(vCenterserver, username, password):
  resp=[]
  con = vs_connect(vCenterserver, username, password)
  template_list = con.get_registered_vms(advanced_filters={'config.template':True})
  for t in template_list:
    vm = con.get_vm_by_path(t)
    prop = vm.get_properties()
    resp.append(prop['name'])
  return resp




def list_snapshotname_per_vm(vCenterserver, username, password,datacentername,vm_name):
  con = vs_connect(vCenterserver, username, password)
  vm = con.get_vm_by_name(vm_name,datacenter=datacentername)
  resp=[]
  if vm:
    snapshots = vm.get_snapshots()
    for snapshot in snapshots:
      name= snapshot.get_name()
      resp.append(name)
  return resp

def list_snapshotpath_per_vm(vCenterserver, username, password,datacentername,vm_name):
  con = vs_connect(vCenterserver, username, password)
  vm = con.get_vm_by_name(vm_name,datacenter=datacentername)
  resp=[]
  if vm:
    snapshots = vm.get_snapshots()
    for snapshot in snapshots:
      path= snapshot.get_path()
      resp.append(path)
  return resp


def createsnapshot_per_vm(vCenterserver, username, password,datacentername,vm_name,snapshotname):
  con = vs_connect(vCenterserver, username, password)
  vm = con.get_vm_by_name(vm_name, datacenter=datacentername)
  if vm:
    r = vm.create_snapshot(name=snapshotname)
  snapshots = list_snapshotname_per_vm(vCenterserver, username, password,datacentername,vm_name)
  if(snapshotname in snapshots):
    return "snapshot creation succeeded" 
  return "Failure"



def delete_snapshot_per_snapshotpath(vCenterserver, username, password, datacentername, vm_name, path):
  con = vs_connect(vCenterserver, username, password)
  vm = con.get_vm_by_name(vm_name, datacenter = datacentername)
  if vm:
    r = vm.delete_snapshot_by_path(path = path)
  paths = list_snapshotpath_per_vm(vCenterserver, username, password, datacentername, vm_name)
  if(not(path in paths)):
    return "snapshot deletion succeeded" 
  return "Failure"


def delete_snapshot_per_snapshotname(vCenterserver, username, password, datacentername, vm_name, name):
  con = vs_connect(vCenterserver, username, password)
  vm = con.get_vm_by_name(vm_name, datacenter = datacentername)
  if vm:
    r = vm.delete_named_snapshot(name = name)
  names = list_snapshotname_per_vm(vCenterserver, username, password, datacentername, vm_name)
  if(not(name in names)):
    return "snapshot deletion succeeded" 
  return "Failure"


#revert_to_named_snapshot

def revert_to_snapshot_per_snapshotname(vCenterserver, username, password, datacentername, vm_name, snapshotname):
  con = vs_connect(vCenterserver, username, password)
  vm = con.get_vm_by_name(vm_name, datacenter = datacentername)
  if vm:
    try:
      r = vm.revert_to_named_snapshot(name = snapshotname)
      return r
    except VIException:
      return "failure"
  return "failure"



def customizeNICS_settingIP_hostname_password(vCenterserver, username, password, vm_mor, NIC1,NIC2,hostname,adminpass ,os_type):
  """
  :param vCenterserver:
  :param username:
  :param password:
  :param vm_mor:
  :param NIC1:
  :param NIC2:
  :param os_type:
  :param hostname:
  :param adminpass:
  :return:
  """
  con = vs_connect(vCenterserver, username, password, unverify=True)
  request = VI.CustomizeVM_TaskRequestMsg()
  _this = request.new__this(vm_mor)
  _this.set_attribute_type(vm_mor.get_attribute_type())
  request.set_element__this(_this)
  spec = request.new_spec()
  if os_type=="LINUX":
    identity = VI.ns0.CustomizationLinuxPrep_Def("identity").pyclass()
    identity.set_element_domain("domain name")
    hostName = VI.ns0.CustomizationFixedName_Def("hostName").pyclass()
    hostName.set_element_name(hostname)
    identity.set_element_hostName(hostName)
    spec.set_element_identity(identity)
    request.set_element_spec(spec)
    # TODO configure root password for linux os
  if os_type == "WIN":
    # customization = spec.new_customization()
    # spec.set_element_customization(customization)
    # globalIPSettings = customization.new_globalIPSettings()
    # customization.set_element_globalIPSettings(globalIPSettings)
    identity = VI.ns0.CustomizationSysprep_Def("identity").pyclass()
    spec.set_element_identity(identity)
    guiUnattended = identity.new_guiUnattended()
    guiUnattended.set_element_autoLogon(True)
    guiUnattended.set_element_autoLogonCount(1)
    if adminpass:
      passw = guiUnattended.new_password()
      guiUnattended.set_element_password(passw)
      passw.set_element_value(adminpass)
      passw.set_element_plainText(True)
  # http://msdn.microsoft.com/en-us/library/ms912391(v=winembedded.11).aspx
    guiUnattended.set_element_timeZone(85) # GMT Standard Time
    identity.set_element_guiUnattended(guiUnattended)
    userData = identity.new_userData()
    userData.set_element_fullName("PySphere")
    userData.set_element_orgName("PySphere")
    userData.set_element_productId("")
    computerName = VI.ns0.CustomizationFixedName_Def(hostname).pyclass()
    computerName.set_element_name(hostname.replace("_", ""))
    userData.set_element_computerName( computerName )
    identity.set_element_userData(userData)
    identification = identity.new_identification()
      # TODO JOIN DOAMIN
    # identification.set_element_domainAdmin("MyDomainAdminUser")
    # domainAdminPassword = identification.new_domainAdminPassword()
    # domainAdminPassword.set_element_plainText(True)
    # domainAdminPassword.set_element_value("MyDomainAdminPassword")
    # identification.set_element_domainAdminPassword(domainAdminPassword)
    # identification.set_element_joinDomain("MyDomain")
    identity.set_element_identification(identification)
  globalIPSettings = spec.new_globalIPSettings()
  spec.set_element_globalIPSettings(globalIPSettings)
  if NIC1 and NIC2:
    nicSetting1 = spec.new_nicSettingMap()
    nicSetting2 = spec.new_nicSettingMap()
    spec.set_element_nicSettingMap([ getnicSetting(nicSetting1,NIC1), getnicSetting(nicSetting2,NIC2)])
  elif  NIC1:
    nicSetting1 = spec.new_nicSettingMap()
    spec.set_element_nicSettingMap([getnicSetting(nicSetting1, NIC1), ])
  request.set_element_spec(spec)
  task = con._proxy.CustomizeVM_Task(request)._returnval
  vi_task = VITask(task, con)
  status = vi_task.wait_for_state([vi_task.STATE_SUCCESS, vi_task.STATE_ERROR])
  return status



def getnicSetting(nicSetting,NIC):
  adapter = nicSetting.new_adapter()
  if NIC['IP_SETTING'] == "FIXED":
    fixedip = VI.ns0.CustomizationFixedIp_Def("ipAddress").pyclass()
    fixedip.set_element_ipAddress(NIC['ip_address'])
    adapter.set_element_ip(fixedip)
    adapter.set_element_subnetMask(NIC['netmask'])
    if NIC['gateway']:
      adapter.set_element_gateway([NIC['gateway']])
  if NIC['IP_SETTING']== "DHCP":
    dhcpip = VI.ns0.CustomizationDhcpIpGenerator_Def("ipAddress").pyclass()
    adapter.set_element_ip(dhcpip)
  nicSetting.set_element_adapter(adapter)
  return nicSetting
