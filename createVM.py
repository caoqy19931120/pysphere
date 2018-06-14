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
logger = logging.getLogger(__name__)


ssl._create_default_https_context = ssl._create_unverified_context

ENV="prod" 
if ENV == 'dev':
    VC_URL = 'dev.vcenter'
    VC_USER = 'administrator'
    VC_PWD = '1'
    SCRIPT_URL = 'install-dev.sh'
    SCRIPT_TMP = '/tmp/install-dev.sh'
elif ENV == 'prod':
    VC_URL = 'prod.vcenter'
    VC_USER = 'administrator'
    VC_PWD = '1'
    SCRIPT_URL = 'install-prod.sh'
    SCRIPT_TMP = '/tmp/install-prod.sh'



server = VIServer()
server.connect(VC_URL,VC_USER,VC_PWD)

def isGetVM(vm_name):
    try:
        server.get_vm_by_name(vm_name)
        return True
    except resources.vi_exception.VIException:
        logger.debug("Could not find a VM named %s" % vm_name)
        return False


def createVM(app_name,vm_name,template_name):
    if isGetVM(vm_name):
        logger.info("vm: [%s] exist" % vm_name) 

    else:
        logger.info("staring clone [%s] from [%s]" % (vm_name, template_name))
        try:
            template_vmx = server.get_vm_by_name(template_name, datacenter="Datacenter-01")
            clone_vm = template_vmx.clone(vm_name,folder='10.0.0.1',sync_run=True)
        except Exception as e:
            logger.error(e)
        
        while True:
            try:
                clone_vm.login_in_guest('root','1')
                pid = clone_vm.start_process('/usr/bin/curl',args=[SCRIPT_URL,"-o",SCRIPT_TMP],cwd='/root')
                logger.debug("Get script,pid:[%s]" % pid)
                clone_vm.list_files(SCRIPT_TMP)
                pid = clone_vm.start_process('/bin/bash',args=[SCRIPT_TMP,app_name],cwd='/root')
                logger.info("Run script,pid:[%s]" % pid)
                logger.info("Complete !!!")
                break
            except resources.vi_exception.VIApiException:
                logger.debug("FileNotFoundFault")
                continue
            except Exception as e:
                if clone_vm.is_powered_off():
                    clone_vm.is_powered_on()
                logger.warn(e)
                time.sleep(10)



def _check_host_name(app_name):
    # 检查hostname 都要能被访问
    try:
        appname,groupid = re.match(r'(.+)-(\d{1,2}-\d{1,2})',app_name).groups()
        app_host = groupid+'.'+appname
        logger.debug(app_host)
        socket.gethostbyname(app_host)
        return True
    except Exception as e:
        logger.error(app_name)
        logger.error(e)
        return False


def main(file):
    with open(file,'r') as fobj:
        for line in fobj:
            try:
                each = line.strip('\n')
                app_name, template_name, corp_idf = each.split()
                vm_name = app_name+'-'+corp_idf
                if _check_host_name(app_name):
                    createVM(app_name,vm_name,template_name)
            except ValueError as e:
                logger.error(e)
            except Exception as e:
                logger.error(e)
        
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s [%(asctime)s] [%(filename)s L%(lineno)d] %(message)s')

    FILE = "vmlist.txt"
    main(FILE)
