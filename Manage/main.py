'''
Created on 23 mars 2016

@author: root
'''
from VM import *


if __name__ == '__main__':
  print "test main"


  vCenterserver  =  "159.8.76.54";
  username       =  "administrator@vsphere.local"       #"administrateur"
  password       =  "Ebxjm8+v"   #"Pr0l0gue2014";
  LOG_FILE       =  "/var/log/pysphere.log"
  maxwait        =  120
  
  
  
  template      =  "Ubuntu12.04 LTS 64bits cloud init 1NIC";
  resource_pool =  "/Resources/Tests";
  vm_name       =  "Manage Network";
  con = vs_connect(vCenterserver, username, password,unverify=True)
  
  
  
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
      hosts="host-29"
      datastore="datastore-30"
      print template_vm
      clone = template_vm.clone(vm_name, sync_run=True, folder=None, resourcepool=resource_pool_mor, 
                             datastore=datastore, host=hosts, power_on=False, template=False,snapshot=None, linked=False)
  
  print('clone %s created' % vm_name)
  print('Booting clone %s' % vm_name)
  
  clonepath =clone.get_properties()['path']
  
  
  datacentername='vDC prologue'
  
  
  
  print "test networks"
  
  resp = get_dvSwitchs_by_DC(vCenterserver, username, password, datacentername)
  

  
  dvSwitchnames=resp.keys()
  
  dvSwitchname=dvSwitchnames[0];
  
  resp= get_portgroup_by_dvSwitchname(vCenterserver, username, password, datacentername,dvSwitchname)
  
  
  resp=get_standardvS_by_DC(vCenterserver, username, password, datacentername)
    
  
  
  

















  
  