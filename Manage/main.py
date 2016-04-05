# Threading example
from VM import *

def createVM(vm_name, VSSName, PGname):

  vCenterserver  =  "159.8.76.54";#"172.17.117.104"
  username       =  "administrator@vsphere.local"  #"administrateur"
  password       =  "Ebxjm8+v"   #"Pr0l0gue2014";
  LOG_FILE       =  "/var/log/pysphere.log"
  maxwait        =  120
  datacentername = 'vDC prologue'
  
  template      =  "Ubuntu12.04 LTS 64bits  tools cloud init 2NICS"; #"UBUNTU1204-AMD-64BIT-VMware-tools-cloudinit" #
  resource_pool_name =  "/Resources/Tests" #/Resources/RP-accords"
  if not vm_name:
    vm_name       =  "VM02testvlan1";
  con = vs_connect(vCenterserver, username, password,unverify=True)
  
  hostmor= "host-29"         #"host-537"#"host-29"
  datastore= "datastore-30"  #"datastore-543" #"datastore-30"
  
  resp = list_available_template(vCenterserver, username, password)
  template_vm = find_vm(vCenterserver, username, password, template)
  resource_pool_mor = get_RP_by_name(vCenterserver, username, password, resource_pool_name)
  
  
  clone = template_vm.clone(vm_name, sync_run=True, folder=None, resourcepool=resource_pool_mor,
              datastore=datastore, host=hostmor, power_on=False, template=False,snapshot=None, linked=False)
  ## For private NIC
  resp = get_dvSwitchs_by_DCname(vCenterserver, username, password, datacentername)
  dvSwitchname=resp.keys()[0]
  
  resp= get_portgroup_by_dvSwitchname(vCenterserver, username, password, datacentername,dvSwitchname)
  if(not PGname):
    PGname="vlan1"#resp.keys()[6]
  
  ## For public NIC
  resp=get_standardvS_by_DCname(vCenterserver, username, password, datacentername)
  if not VSSName:
    VSSName="VM Network"  #resp.keys()[2]
  
  
  print "Configure Network"
  
  #List Network configuration on Model
  nicinfos = get_vm_nics(vCenterserver, username, password, datacentername, vm_name)
  
  #remove all network configuration in the template
  for i in range(len(nicinfos.keys())):
    resp = remove_nic_vm(vCenterserver, username, password, datacentername, vm_name, nicinfos.keys()[i])
  
  
  ##Create private NIC and connect to specific vlan
  
  
  dvswitch_uuid = get_dvSwitchuuid_by_dvsname_and_DC(vCenterserver, username, password, datacentername, dvSwitchname)
  portgroupKey  = get_portgroupref_by_name(vCenterserver, username, password, datacentername, PGname)
  
  resp = add_nic_vm_and_connect_to_net(vCenterserver, username, password, datacentername, vm_name,  dvswitch_uuid, portgroupKey, network_name="VM Network", nic_type="vmxnet3", network_type="dvs")
  
  ###update nic infos
  nicinfos = get_vm_nics(vCenterserver, username, password, datacentername, vm_name)
  
  
  
  ### For public Deployment : 
  ##add public NIC
  resp = add_nic_vm_and_connect_to_net(vCenterserver, username, password, datacentername, vm_name,  dvswitch_uuid, portgroupKey, VSSName, nic_type="vmxnet3", network_type="standard")
  
  ## start VM then create second virtual NIC and get IP
  result= poweron_vm(vCenterserver, username, password, datacentername, vm_name)
  Netstatus = get_vm_ip_addresses(vCenterserver, username, password,vm_name, ipv6=False, maxwait=120)
  
  
  privateip = get_NIC_address_per_connected_net(vCenterserver, username, password,vm_name, PGname, ipv6=False, maxwait=120)
  publicip  = get_NIC_address_per_connected_net(vCenterserver, username, password,vm_name, VSSName, ipv6=False, maxwait=120)
  
  
  print (vm_name)
  print (privateip)
  print (publicip)
  return [privateip,publicip]
  

if __name__ == "__main__":
  vm1 = createVM("VMpublicnet_vlan1103","Public Network portableIP","vlan1103")
  vm2 = createVM("VMprivatenet_vlan1103","Private Network portable IP","vlan1103")

  vm3 = createVM("VMpublicnet_vlan1104","Public Network portableIP","vlan1104")
  vm4 = createVM("VMprivatenet_vlan1104","Private Network portable IP","vlan1104")
  
  vm5 = createVM("VMpublicnet_vlan1105","Public Network portableIP","vlan1105")
  vm6 = createVM("VMprivatenet_vlan1105","Private Network portable IP","vlan1105")
  
  vm7 = createVM("VMpublicnet_vlan1106","Public Network portableIP","vlan1106")
  vm8 = createVM("VMprivatenet_vlan1106","Private Network portable IP","vlan1106")
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  