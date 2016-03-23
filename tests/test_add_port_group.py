from pysphere import VIMor, MORTypes
from pysphere import VIServer, VIProperty
from pysphere.resources import VimService_services as VI 
from pyactions import *





def add_port_group(name, vlan_id, vswitch, network_system,vCenterserver, username, password):
    s = VIServer()
    s.connect(vCenterserver, username, password)
    request = VI.AddPortGroupRequestMsg()
    _this = request.new__this(network_system)
    _this.set_attribute_type(network_system.get_attribute_type())
    request.set_element__this(_this)
    portgrp = request.new_portgrp()
    portgrp.set_element_name(name)
    portgrp.set_element_vlanId(vlan_id)
    portgrp.set_element_vswitchName(vswitch)
    portgrp.set_element_policy(portgrp.new_policy())
    request.set_element_portgrp(portgrp)
    s._proxy.AddPortGroup(request)