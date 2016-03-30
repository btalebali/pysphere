'''
Created on 23 mars 2016

@author: root
'''
from VM import *



vCenterserver  =  "172.17.117.104"#"159.8.76.54";
username       =  "administrateur"#"administrator@vsphere.local"       #"administrateur"
password       =  "Pr0l0gue2014"#"Ebxjm8+v"   #"Pr0l0gue2014";
LOG_FILE       =  "/var/log/pysphere.log"
maxwait        =  120



template      =  "UBUNTU1204-AMD-64BIT-VMware-tools-cloudinit" #"Ubuntu12.04 LTS 64bits cloud init 1NIC";
resource_pool =  "/Resources/RP-accords" #/Resources/Tests";
vm_name       =  "Manage Network2";
con = vs_connect(vCenterserver, username, password,unverify=True)

hostmor= "host-537"#"host-29"
datastore= "datastore-543" #"datastore-30"



print("Available Templates : ")
template_list = con.get_registered_vms(advanced_filters={'config.template':True})
for t in template_list:
  vm = con.get_vm_by_path(t)
  prop = vm.get_properties()
  print(prop['name'])


template_vm = find_vm(vCenterserver, username, password, template)


if template_vm is None:
  print 'ERROR: %s not found' % template
  sys.exit(1)


resource_pool_mor = get_RP_by_name(vCenterserver, username, password, resource_pool)
if resource_pool_mor is None:
  print 'ERROR: %s not found' % resource_pool
  sys.exit(1)

print ('Resource pool %s found' % resource_pool)



if (find_vm(vCenterserver, username, password, vm_name)):
    print 'ERROR: %s already exists' % vm_name
    sys.exit()
else:

    print template_vm
    clone = template_vm.clone(vm_name, sync_run=True, folder=None, resourcepool=resource_pool_mor, 
                           datastore=datastore, host=hostmor, power_on=False, template=False,snapshot=None, linked=False)

print('clone %s created' % vm_name)
print('Booting clone %s' % vm_name)

clonepath =clone.get_properties()['path']


datacentername='vDC prologue'


print "List network configuration"

## For private NIC
resp = get_dvSwitchs_by_DCname(vCenterserver, username, password, datacentername)
dvSwitchname=resp.keys()[0]

resp= get_portgroup_by_dvSwitchname(vCenterserver, username, password, datacentername,dvSwitchname)
PGname=resp.keys()[6]

## For public NIC
resp=get_standardvS_by_DCname(vCenterserver, username, password, datacentername)
VSSName=resp.keys()[2]


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
## start VM then create second virtual NIC and get IP
result= poweron_vm(vCenterserver, username, password, datacentername, vm_name)

##add public NIC


resp = add_nic_vm_and_connect_to_net(vCenterserver, username, password, datacentername, vm_name,  dvswitch_uuid, portgroupKey, VSSName, nic_type="vmxnet3", network_type="standard")

Netstatus = get_vm_ip_addresses(vCenterserver, username, password,vm_name, ipv6=False, maxwait=120)



privateip = get_NIC_address_per_connected_net(vCenterserver, username, password,vm_name, PGname, ipv6=False, maxwait=120)
publicip  = get_NIC_address_per_connected_net(vCenterserver, username, password,vm_name, VSSName, ipv6=False, maxwait=120)

print (privateip)
print (privateip)















