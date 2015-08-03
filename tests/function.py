import time
import threading
import os
import urllib2
import mmap
import sys, re, getpass, argparse, subprocess
from urlparse import urlparse
from time import sleep
from pysphere import VIServer, MORTypes
from pysphere import  VIProperty, VITask,VIException, FaultTypes

from pysphere.vi_virtual_machine import VIVirtualMachine
from pysphere.resources import VimService_services as VI
from pysphere.vi_mor import VIMor
from pysphere import  vi_task

from pysphere.ZSI import fault


