from pysphere.vi_mor import VIMor, MORTypes
from pysphere.vi_virtual_machine import VIVirtualMachine
from pysphere.resources import VimService_services as VI
from pysphere.vi_mor import VIMor
from pysphere import  vi_task
from pysphere import VIServer, MORTypes
from pysphere import  VIProperty, VITask,VIException, FaultTypes
import sys

vCenterServer = "172.17.117.104";
username      = "administrateur"       #"administrateur"
Password      = "Pr0l0gue2014"   #"Pr0l0gue2014";
LOG_FILE      = "/var/log/pysphere.log"


template="Ubuntu12.04-VMware-Tool-64bits"
resource_pool="/Resources/testRessourcePool"
vm_name=  "VM2";



''''Get CPU and Memory usage for a specifi Cluster '''

Cluster="cluster103"
con = VIServer()
con.connect(vCenterServer, username,Password,LOG_FILE)
MORefRPhost= [k for k,v in con.get_clusters().items() if v==Cluster][0]
prop = VIProperty(con, MORefRPhost)
print "*" * 50
print "Stats for", Cluster
dir(prop.summary)
t = prop.summary._values
print "  numHosts:", t['numHosts']
print "  totalCpu:", t['totalCpu']    
print "  effectiveMemory:", t['effectiveMemory'] 
print "  totalMemory:", t['totalMemory']
print "  effectiveCpu:", t['effectiveCpu']

#{'numCpuThreads': 8, 'numVmotions': 0, 'numHosts': 1, 'currentBalance': 0, 'dynamicType': None, 
#'currentFailoverLevel': -1, 'dynamicProperty': [], 'totalCpu': 19192, 'effectiveMemory': 28908, 'totalMemory': 34312003584, 'targetBalance': 282, 'numCpuCores': 8, 'effectiveCpu': 16844, 'overallStatus': 'green', 'numEffectiveHosts': 1}
con.disconnect()



''''Get CPU and Memory usage for a specifi Host '''
Host="172.17.117.103"

con = VIServer()
con.connect(vCenterServer, username,Password,LOG_FILE)
MORefRPhost= [k for k,v in con.get_hosts().items() if v==Host][0]
prop = VIProperty(con, MORefRPhost)
print "*" * 50
print "Stats for host", Host
print "  overall processor usage:", prop.summary.quickStats.overallCpuUsage
print "  overall memory usage:", prop.summary.quickStats.overallMemoryUsage
print "  distributedCpuFairness: ", prop.summary.quickStats.distributedCpuFairness
print "  distributedMemoryFairness: ", prop.summary.quickStats.distributedMemoryFairness
con.disconnect()



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
     Get All properties for a ressource pool : resource_pool
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

s = VIServer()
s.connect(vCenterServer, username,Password,LOG_FILE)
MORefRP= [k for k,v in s.get_resource_pools().items() if v==resource_pool][0]
properties=["summary.quickStats.overallCpuUsage" #Basic CPU performance statistics, in MHz.
            ,"summary.quickStats.overallCpuDemand" #Basic CPU performance statistics, in MHz.
            ,"summary.quickStats.guestMemoryUsage"#Guest memory utilization statistics, in MB. This is also known as active guest memory. The number can be between 0 and the configured memory size of a virtual machine.
            ,"summary.quickStats.hostMemoryUsage"#Host memory utilization statistics, in MB. This is also known as consummed host memory. This is between 0 and the configured resource limit. Valid while a virtual machine is running. This includes the overhead memory of a virtual machine.
            ,"summary.quickStats.distributedCpuEntitlement"#This is the amount of CPU resource, in MHz, that this VM is entitled to, as calculated by DRS. Valid only for a VM managed by DRS.
            ,"summary.quickStats.distributedMemoryEntitlement"#This is the amount of memory, in MB, that this VM is entitled to, as calculated by DRS. Valid only for a VM managed by DRS.
            ,"summary.quickStats.staticCpuEntitlement"#The static CPU resource entitlement for a virtual machine. This value is calculated based on this virtual machine's resource reservations, shares and limit, and doesn't take into account current usage. This is the worst case CPU allocation for this virtual machine, that is, the amount of CPU resource this virtual machine would receive if all virtual machines running in the cluster went to maximum consumption. Units are MHz.
            ,"summary.quickStats.staticMemoryEntitlement"#The static memory resource entitlement for a virtual machine. This value is calculated based on this virtual machine's resource reservations, shares and limit, and doesn't take into account current usage. This is the worst case memory allocation for this virtual machine, that is, the amount of memory this virtual machine would receive if all virtual machines running in the cluster went to maximum consumption. Units are MB.
            ,"summary.quickStats.privateMemory"#The portion of memory, in MB, that is granted to a virtual machine from non-shared host memory.
            ,"summary.quickStats.sharedMemory"#The portion of memory, in MB, that is granted to a virtual machine from host memory that is shared between VMs.
            ,"summary.quickStats.swappedMemory"#The portion of memory, in MB, that is granted to a virtual machine from the host's swap space. This is a sign that there is memory pressure on the host.
            ,"summary.quickStats.balloonedMemory"#The size of the balloon driver in a virtual machine, in MB. The host will inflate the balloon driver to reclaim physical memory from a virtual machine. This is a sign that there is memory pressure on the host.
            ,"summary.quickStats.overheadMemory"#The amount of memory resource (in MB) that will be used by a virtual machine above its guest memory requirements. This value is set if and only if a virtual machine is registered on a host that supports memory resource allocation features. For powered off VMs, this is the minimum overhead required to power on the VM on the registered host. For powered on VMs, this is the current overhead reservation, a value which is almost always larger than the minimum overhead, and which grows with time.See QueryMemoryOverheadEx
            ,"summary.quickStats.consumedOverheadMemory"#The amount of overhead memory, in MB, currently being consumed to run a VM. This value is limited by the overhead memory reservation for a VM, stored in overheadMemory .
            ,"summary.quickStats.compressedMemory"#The amount of compressed memory currently consumed by VM, in KB.
            ]
results = s._retrieve_properties_traversal(property_names=properties,obj_type=MORTypes.ResourcePool)
print "*" * 50
print "Stats for RessourcePool", resource_pool
for item in results:
    if(item.Obj==MORefRP):
        for p in item.PropSet:
            print p.Name, "=>", p.Val







'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
     Get All properties for a virtual Machine : VM
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

s = VIServer()
s.connect(vCenterServer, username,Password,LOG_FILE)
vm=s.get_vm_by_name(vm_name)
properties=["name"
            ,"summary.quickStats.balloonedMemory"
            ,"summary.quickStats.consumedOverheadMemory"
            ,"summary.quickStats.distributedCpuEntitlement"#Basic CPU performance statistics, in MHz. Valid while the virtual machine is running.
            ,"summary.quickStats.distributedMemoryEntitlement"#Host memory utilization statistics, in MB. This is also known as consummed host memory. This is between 0 and the configured resource limit. Valid while the virtual machine is running.
            ,"summary.quickStats.ftLatencyStatus"
            ,"summary.quickStats.ftLogBandwidth"
            ,"summary.quickStats.ftSecondaryLatency"
            ,"summary.quickStats.guestHeartbeatStatus"
            ,"summary.quickStats.guestMemoryUsage"#Guest operating system heartbeat metric. See guestHeartbeatStatus for a description.
            ,"summary.quickStats.hostMemoryUsage" #The fairness of distributed memory resource entitlement on the virtual machine. Units are thousandths. For example, 12 represents 0.012.
            ,"summary.quickStats.overallCpuDemand"
            ,"summary.quickStats.privateMemory"
            ,"summary.quickStats.sharedMemory"
            ,"summary.quickStats.staticCpuEntitlement"
            ,"summary.quickStats.staticMemoryEntitlement"
            ,"summary.quickStats.swappedMemory"
            ]

print "*" * 50
print "Stats for VM", vm_name
results = s._retrieve_properties_traversal(property_names=properties,obj_type=MORTypes.VirtualMachine)
for item in results:
    if(item.Obj==vm._mor):
        for p in item.PropSet:
            print p.Name, "=>", p.Val

'''  GET datastore capacity '''



datastore='Disque2Tera'
server = VIServer() 
server.connect(vCenterServer, username,Password,LOG_FILE) 
MORefdatastore= [k for k,v in server.get_datastores().items() if v==datastore][0]
props = VIProperty(server, MORefdatastore) 
print "DATASTORE:", datastore 
print "  Type:", props.summary.type 
print "  Capacity:", props.summary.capacity 
print "  Free space:", props.summary.freeSpace 
server.disconnect() 









