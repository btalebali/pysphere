from pysphere import VIMor, MORTypes
from pysphere import VIServer, VIProperty
from pysphere.resources import VimService_services as VI 
from pyactions import *

vCenterServer = "172.17.117.103";
username      = "root"       #"administrateur"
Password      = "prologue"   #"Pr0l0gue2014";

s = VIServer()
s.connect(vCenterServer, username, Password)

host_system = s.get_hosts().keys()[0]
prop = VIProperty(s, host_system)
propname = prop.configManager._obj.get_element_networkSystem()
vswitch = prop.configManager.networkSystem.networkInfo.vswitch[0].name
#vswitch = prop.configManager.networkSystem.networkInfo.vswitch[0]
network_system = VIMor(propname, MORTypes.HostServiceSystem)
name='vlantest'
vlan_id="8"
add_port_group(name, vlan_id, vswitch, network_system,vCenterServer, username, Password)

