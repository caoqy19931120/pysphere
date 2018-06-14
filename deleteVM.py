# -*- coding: utf-8 -*-

from pysphere import VITask,VIServer,resources
import ssl
import time
import sys,os
import socket
import re
import json
import redis
import pickle,shelve
import logging


def power_off_vm(vm_name):  
    try:  
        vm = server.get_vm_by_name(vm_name)  
        if(vm.is_powered_on()):  
            vm.power_off()  
            print "vm " + vm_name + " power off success."  
        else:  
            print "vm " + vm_name + "is already power off"  
            return False  
    except:  
        print "Power off vm " + vm_name + " error"  
        return False  
    return True

def remove_vm(vm_name):
    vm = server.get_vm_by_name(vm_name)
    request = VI.Destroy_TaskRequestMsg()
    tiger = request.new__this(vm._mor)
    tiger.set_attribute_type(vm._mor.get_attribute_type())
    request.set_element__this(tiger)
    ret = server._proxy.Destroy_Task(request)._returnval
    task = VITask(ret, server)
    status = task.wait_for_state([task.STATE_SUCCESS, task.STATE_ERROR])
    if status == task.STATE_SUCCESS:
        print "VM successfully deleted from disk"
    elif status == task.STATE_ERROR:
        print "Error removing vm:", task.get_error_message()
