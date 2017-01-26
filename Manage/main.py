# Threading example
from VM import *

def createVM(new_vm_name, VSSName, dvSwitchname, PGname, vm_or_modele_name, os_type, NIC1, NIC2 = None):
  """
  :param new_vm_name:
  :param VSSName:
  :param dvSwitchname:
  :param PGname:
  :param vm_or_modele_name:
  :param os_type:
  :param NIC1:
  :param NIC2:  if None then private deployment
  :return:
  """
  vCenterserver  =  "172.17.117.104"
  username       =  "administrateur"
  password       =  "Pr0l0gue2014";
  LOG_FILE       =  "/var/log/pysphere.log"
  maxwait        =  120
  datacentername = 'vDC prologue'
  hostmor= "host-537"
  datastore= "datastore-543"
  resource_pool_name =  "/Resources/RP-accords"
  hostname='uicb'
  adminpass='Pr0l0gue:2014'


  con = vs_connect(vCenterserver, username, password, unverify=True)



  template_vm = find_vm(vCenterserver, username, password, vm_or_modele_name)



  resource_pool_mor = get_RP_by_name(vCenterserver, username, password, resource_pool_name)
  


  VM = template_vm.clone(new_vm_name, sync_run=True, folder=None, resourcepool=resource_pool_mor, datastore=datastore, host=hostmor, power_on=False, template=False, snapshot=None, linked=False)


  ## LIST DVSwitch for a Virtual DATAcenter
  resp = get_dvSwitchs_by_DCname(vCenterserver, username, password, datacentername)



  ### LIST portgroup for a dvSwitch  and a datacenter
  portgroups = get_portgroup_by_dvSwitchname(vCenterserver, username, password, datacentername,dvSwitchname)


  ## List Public Network
  PubNets = get_standardvS_by_DCname(vCenterserver, username, password, datacentername)



  
  ## List Network configuration on Model/ VM
  nicinfos = get_vm_nics(vCenterserver, username, password, datacentername, new_vm_name)



  ##Remove all NICs in the template
  for i in range(len(nicinfos.keys())):
    resp = remove_nic_vm(vCenterserver, username, password, datacentername, new_vm_name, nicinfos.keys()[i])


    ###########################################
    ### CONFIGURE PRIVATE NIC #################
    ###########################################

  if PGname and dvSwitchname:
    # GET dvswitch uuid
    dvswitch_uuid = get_dvSwitchuuid_by_dvsname_and_DC(vCenterserver, username, password, datacentername, dvSwitchname)


    # Get protgroup key
    portgroupKey  = get_portgroupref_by_name(vCenterserver, username, password, datacentername, PGname)


    resp = add_nic_vm_and_connect_to_net(vCenterserver, username, password, datacentername, new_vm_name, dvswitch_uuid, portgroupKey, nic_type="vmxnet3", network_type="dvs")


    # refresh Nic infos
    nicinfos = get_vm_nics(vCenterserver, username, password, datacentername, new_vm_name)
  

  ###########################################
  ### CONFIGURE Public NIC  #################
  ###########################################
  if VSSName:
    # Add public NIC
    resp = add_nic_vm_and_connect_to_net(vCenterserver, username, password, datacentername, new_vm_name,  dvswitch_uuid, portgroupKey, VSSName, nic_type="vmxnet3", network_type="standard")

  #refresh VM
  VM=con.get_vm_by_name(new_vm_name)



  ## Customize VM ( ip, hostname,)



  result = customizeNICS_settingIP_hostname_password(vCenterserver, username, password, VM._mor, NIC1, NIC2, hostname, adminpass,os_type)



  # Start VM
  result = poweron_vm(vCenterserver, username, password, datacentername, new_vm_name)



  # Get IPs
  if os_type=='WIN':
    import time
    time.sleep(200)
  Netstatus = get_vm_ip_addresses(vCenterserver, username, password,new_vm_name, ipv6=False, maxwait=120)


  print (new_vm_name)
  if PGname:
    privateip = get_NIC_address_per_connected_net(vCenterserver, username, password,new_vm_name, PGname, ipv6=False, maxwait=120)
    print (privateip)
  if VSSName:
    publicip  = get_NIC_address_per_connected_net(vCenterserver, username, password,new_vm_name, VSSName, ipv6=False, maxwait=120)
    print (publicip)

  #refresh VM
  VM=con.get_vm_by_name(new_vm_name)
  return VM

if __name__ == "__main__":
  ### VM1    public linux
  os_type='LINUX'
  vm_or_modele_name = 'ubuntu-server-12.4-64lts'


  dvSwitchname='DSwitchv1'
  PGname='vlan4 static'
  NIC1 = {'IP_SETTING': 'FIXED', 'ip_address': '10.2.3.3', 'netmask': '255.255.255.0', 'gateway': ''}


  VSSName="VM Network"
  NIC2 = {'IP_SETTING': 'DHCP'}

  vm1_name = 'vm test 1'

  vm1 = createVM(vm1_name, VSSName, dvSwitchname, PGname, vm_or_modele_name, os_type, NIC1, NIC2)



  ### VM2    private deployment of VM1
  os_type='LINUX'
  vm_or_modele_name = 'vm test 1'


  dvSwitchname='DSwitchv1'
  PGname='vlan1 dhcp'
  NIC1 = {'IP_SETTING': 'DHCP'}


  VSSName = None
  NIC2 = None

  vm2_name = 'vm test 2'

  vm2 = createVM(vm2_name, VSSName, dvSwitchname, PGname, vm_or_modele_name, os_type, NIC1, NIC2)
  
  



  ###VM3  windows public deployment
  os_type='WIN'
  vm_or_modele_name = 'Windows 2012 R2 x86_64'


  dvSwitchname='DSwitchv1'
  PGname='vlan4 static'
  NIC1 = {'IP_SETTING': 'FIXED', 'ip_address': '10.2.3.4', 'netmask': '255.255.255.0', 'gateway': ''}


  VSSName="VM Network"
  NIC2 = {'IP_SETTING': 'FIXED', 'ip_address': '172.17.117.137', 'netmask': '255.255.0.0', 'gateway': '172.17.0.254'}

  vm3_name = 'vm test 3'

  vm3 = createVM(vm3_name, VSSName, dvSwitchname, PGname, vm_or_modele_name, os_type, NIC1, NIC2)
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  