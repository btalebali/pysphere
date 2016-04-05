#!/usr/bin/python
import sys, re, getpass, argparse, subprocess
from time import sleep
from pysphere import MORTypes, VIServer, VITask, VIProperty, VIMor, VIException
from pysphere.vi_virtual_machine import VIVirtualMachine

def print_verbose(message):
    if verbose:
        print message

def find_vm(name):
    try:
        vm = con.get_vm_by_name(name)
        return vm
    except VIException:
        return None

def get_RP_by_name(name):
    rps = con.get_resource_pools()
    for mor, path in rps.iteritems():
        print_verbose('Parsing RP %s' % path)
        if re.match('.*%s' % name,path):
            return mor
    return None

def run_post_script(name,ip):
    print_verbose('Running post script: %s %s %s' % (post_script,name,ip))
    retcode = subprocess.call([post_script,name,ip])
    if retcode < 0:
        print 'ERROR: %s %s %s : Returned a non-zero result' % (post_script,name,ip)
        sys.exit(1)

def findip(vm,ipv6=False):
    net_info = None
    waitcount = 0
    while net_info is None:
        if waitcount > maxwait:
            break
        net_info = vm.get_property('net',False)
        print_verbose('Waiting 5 seconds ...')
        waitcount += 5
        sleep(5)
    if net_info:
        for ip in net_info[0]['ip_addresses']:
            if ipv6 and re.match('\d{1,4}\:.*',ip) and not re.match('fe83\:.*',ip):
                print_verbose('IPv6 address found: %s' % ip)
                return ip
            elif not ipv6 and re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',ip) and ip != '127.0.0.1':
                print_verbose('IPv4 address found: %s' % ip)
                return ip
    print_verbose('Timeout expired: No IP address found')
    return None

parser = argparse.ArgumentParser(description="Deploy a template into multiple clone's")
parser.add_argument('-6', '--six', required=False, help='Get IPv6 address for VMs instead of IPv4', dest='ipv6', action='store_true')
parser.add_argument('-b', '--basename', nargs=1, required=True, help='Basename of the newly deployed VMs', dest='basename', type=str)
parser.add_argument('-c', '--count', nargs=1, required=False, help='Starting count, the name of the first clone deployed will be <basename>-<count>, the second will be <basename>-<count+1> (default=1)', dest='count', type=int, default=[1])
parser.add_argument('-n', '--number', nargs=1, required=False, help='Amount of VMs to deploy (default=1)', dest='amount', type=int, default=[1])
parser.add_argument('-p', '--post-script', nargs=1, required=False, help='Script to be called after each clone is created and booted. Arguments passed: name ip-address', dest='post_script', type=str)
parser.add_argument('-r', '--resource-pool', nargs=1, required=False, help='The resource pool in which the new VMs should reside', dest='resource_pool_name', type=str)
parser.add_argument('-s', '--server', nargs=1, required=True, help='The vCenter or ESXi server to connect to', dest='server', type=str)
parser.add_argument('-t', '--template', nargs=1, required=True, help='Template to deploy', dest='template', type=str)
parser.add_argument('-u', '--user', nargs=1, required=True, help='The username with which to connect to the server', dest='username', type=str)
parser.add_argument('-v', '--verbose', required=False, help='Enable verbose output', dest='verbose', action='store_true')
parser.add_argument('-w', '--wait-max', nargs=1, required=False, help='Maximum amount of seconds to wait when gathering information (default 120)', dest='maxwait', type=int, default=[120])

args = parser.parse_args()

ipv6        = args.ipv6
amount         = args.amount[0]
basename     = args.basename[0]
count         = args.count[0]
post_script     = None
if args.post_script: 
    post_script = args.post_script[0]
resource_pool_name     = None
if args.resource_pool:
    resource_pool_name = args.resource_pool[0]
server         = args.server[0]
template     = args.template[0]
username     = args.username[0]
verbose        = args.verbose
maxwait     = args.maxwait[0]

# Asking Users password for server
#password=getpass.getpass(prompt='Enter password for vCenter %s for user %s: ' % (server,username))
password="Pr0l0gue2014"
# Connecting to server
print_verbose('Connecting to server %s with username %s' % (server,username))
con = VIServer()
con.connect(server,username,password)
print_verbose('Connected to server %s' % server)
print_verbose('Server type: %s' % con.get_server_type())
print_verbose('API version: %s' % con.get_api_version())

# Verify the template exists
print_verbose('Finding template %s' % template)
template_vm = find_vm(template)
if template_vm is None:
    print 'ERROR: %s not found' % template
    sys.exit(1)
print_verbose('Template %s found' % template)

# Verify the target Resource Pool exists
print_verbose('Finding resource pool %s' % resource_pool_name)
resource_pool_mor = get_RP_by_name(resource_pool_name)
if resource_pool_mor is None:
    print 'ERROR: %s not found' % resource_pool_name
    sys.exit(1)
print_verbose('Resource pool %s found' % resource_pool_name)

# List with clone name elements for post script processing
vms_to_ps = []
# Looping through amount that needs to be created
for a in range(1,amount+1):
    print_verbose('================================================================================')
    vm_name = '%s-%i' % (basename,count)
    print_verbose('Trying to clone %s to clone %s' % (template,vm_name))
    if find_vm(vm_name):
        print 'ERROR: %s already exists' % vm_name
    else:
        clone = template_vm.clone(vm_name, True, None, resource_pool_mor, None, None, False)
        print_verbose('clone %s created' % vm_name)
        
        print_verbose('Booting clone %s' % vm_name)
        clone.power_on()
        
        if post_script:
            vms_to_ps.append(vm_name)
    count += 1

# Looping through post scripting if necessary
if post_script:
    for name in vms_to_ps:
            vm = find_vm(name)
            if vm:
                ip = get_vm_ip_addresses(vm,ipv6)
                if ip:
                    run_post_script(name,ip)
                else: 
                    print 'ERROR: No IP found for clone %s, post processing disabled' % name
            else:
                print 'ERROR: clone %s not found, post processing disabled' % name



###### Stop clone
vm = find_vm("Deployed-clone-1");
#Finding clone's ip
ip = get_vm_ip_addresses(vm,ipv6)
print ("clone's IP= ",ip)

print("powering off VMs");
vm.power_off();
sleep(15)
print("powering on VMs ....");
vm.power_on();
sleep(15)

print("resetting VMs ....");
vm.reset();
sleep(15)

print("suspend VMs ....");
vm.suspend();
sleep(15)


print("Delete VMs ....");
vm.destroy(); 
sleep(15)



# Disconnecting from server
con.disconnect()