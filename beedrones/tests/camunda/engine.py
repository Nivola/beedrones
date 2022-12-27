# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

import random
from time import sleep
from beedrones.camunda.engine import WorkFlowEngine
from beehive.common.test import runtest, BeehiveTestCase


conn = {
    'host': '10.102.184.67',
    'port': 8080,
    'path': '/engine-rest',
    'proto': 'http'
}

USER = 'admin'
PASSWD = 'camunda'
WFTEST = None


class WorkFlowEngineTestCase(BeehiveTestCase):
    """To execute this test you need a cloudstack instance.
    """
    def setUp(self):
        BeehiveTestCase.setUp(self)

    def intialize(self):
        global WFTEST
        if WFTEST is None:
            WFTEST = WorkFlowEngine(conn, user=USER, passwd=PASSWD)        
        
    def load_config_file(self, filename):
        """
        """
        f = open(filename, 'r')
        config = f.read()
        f.close()
        return config.rstrip()
        
    #
    # deployment
    #
    def test_wf_process_list(self):
        """returns all the running process_definition_list
        """
        self.intialize()
        res = WFTEST.process_definition_list()
        self.logger.info(self.pp.pformat(res))
        
    def test_wf_process_filtered(self):
        """returns a single process_definition_get (the last version) with the given ID filtering with 
        processDefinitionId, process_definition_get key, tenantId 
        """
        self.intialize()
        processDefinitionId = 'Checkmail_simple:1:3adc6768-2107-11e7-beff-061b3800031f'
        res = WFTEST.process_definition_get(processDefinitionId)
        self.logger.info(self.pp.pformat(res))
        res = WFTEST.process_definition_get(key='invoice', tenantId=None)
        self.logger.info(self.pp.pformat(res))         
        res = WFTEST.process_definition_get(deploymentId='3ad95a25-2107-11e7-beff-061b3800031f')
        self.logger.info(self.pp.pformat(res))         

    def test_wf_ping(self):
        self.intialize()
        res = WFTEST.ping()
        self.logger.info(res)
        
    def test_wf_xmlget_filtered(self):
        """returns the last xml version of a process_definition_get, filtering with processDefinitionId,
        process_definition_get key, tenantId
        """
        self.intialize()
        key = 'invoice'
    
        res = WFTEST.process_definition_xml_get(key=key)
        self.logger.info(res)

    def test_wf_xmlpost(self):
        """Create a new deployment
        """
        global WFTEST
        self.intialize()
        
        xml = self.load_config_file('./prova.xml')
        
        res = WFTEST.process_deployment_create(xml, 'Checkmail_simple')
        self.logger.info(self.pp.pformat(res))

    def test_wf_get_deployment(self):
        """
            delete a deployment
        """
        global WFTEST
        self.intialize()
       
        res = WFTEST.process_deployment_get()
        self.logger.info(self.pp.pformat(res))

    def test_wf_delete_deployment(self):
        """
            delete a deployment
        """
        global WFTEST
        self.intialize()
        
        res = WFTEST.process_deployment_delete('3ad95a25-2107-11e7-beff-061b3800031f')
        self.logger.info(self.pp.pformat(res))

    def test_wf_case_definition_get(self):
        """
            get a case def
        """
        global WFTEST
        self.intialize()

        res = WFTEST.case_definition_get()
        self.logger.info(self.pp.pformat(res))

    def test_wf_startproc(self):
        global WFTEST
        self.intialize()
        amount = 1000.0 * random.random()
        parameters = {
            "Random": amount,
            "VariableString": "pippo--" + str(amount),
            "Dictionary": {"key1": "val1", "key2": "val2"}
        }
        res = WFTEST.process_instance_start_processDefinitionId('Checkmail_simple', businessKey='',
                                                                variables=parameters)
        self.logger.info(self.pp.pformat(res))

    def test_wf_delete_process_definition(self):
        """
            delete a process_definition_get definition
        """
        global WFTEST
        self.intialize()
       
        res = WFTEST.process_definition_delete('Checkmail_simple:1:fdff6255-20f8-11e7-beff-061b3800031f')
        self.logger.info(self.pp.pformat(res))

    def test_wf_process_all_instances(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instances_get_all()
        self.logger.info(self.pp.pformat(res))

    def test_wf_process_instance(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instances_list(processDefinitionKey='Checkmail_simple')
        self.logger.info(self.pp.pformat(res))

    def test_wf_get_history_instances(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_history_detail(processInstanceId='9f69862a-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res))

    def test_wf_verify_process_instance_status(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_status(processInstanceId='9f69862a-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res))

    def test_wf_process_instances_delete(self):
        global WFTEST
        self.intialize()
        listProc = ['c24626fa-1525-11e7-a173-061b3800031f','8426fbf4-1525-11e7-a173-061b3800031f']
        res = WFTEST.process_instances_group_delete(processInstanceIds=listProc, deleteReason='this is the reason')
        self.logger.info(self.pp.pformat(res))
        sleep(5)
        res = WFTEST.process_instances_list(processInstanceIds=listProc)
        self.logger.info(self.pp.pformat(res))
     
    def test_wf_process_single_instance_delete(self):
        global WFTEST
        self.intialize()
        processInstanceId = 'd39e596f-1526-11e7-a173-061b3800031f'
        res = WFTEST.process_instance_delete(processInstanceId)
        self.logger.info(self.pp.pformat(res))
        
    def test_wf_process_instance_get_variables(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_variables_list(processInstanceId='938f021d-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res)) 
    
    def test_wf_process_instance_get_variables_ex(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_variables_list_ex(processInstanceId='938f021d-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res)) 

    def test_wf_process_instance_get_single_variable(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_variable_get(processInstanceId='938f021d-259f-11e7-b663-061b3800031f',
                                                   varName='VariableString')
        self.logger.info(self.pp.pformat(res)) 
        
    def test_wf_process_instance_upload_variable(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_variable_file_upload(processInstanceId='938f021d-259f-11e7-b663-061b3800031f', 
                                                           varName='Variable_2', varContent='POEPROEPROEPROEP')
        self.logger.info(self.pp.pformat(res))         

    def test_wf_process_instance_update_variables(self):
        global WFTEST
        self.intialize()
        parameters = {
            "VariableString_2": "POEPROEPROEPROEP",
            "VariableString": {"prova": "val"}
        }        
        res = WFTEST.process_instance_variables_update(processInstanceId='938f021d-259f-11e7-b663-061b3800031f', 
                                                       variables=parameters)
        self.logger.info(self.pp.pformat(res))      

    def test_wf_process_instance_set_variable(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_variable_set(processInstanceId='938f021d-259f-11e7-b663-061b3800031f',
                                                   varName='VariableString_2', varValue={"prova": "val"}, valueInfo={})
        self.logger.info(self.pp.pformat(res))

    def test_wf_process_instance_delete_variable(self):
        global WFTEST
        self.intialize()
        res = WFTEST.process_instance_varariable_delete(processInstanceId='938f021d-259f-11e7-b663-061b3800031f',
                                                        varName='VariableString_2')
        self.logger.info(self.pp.pformat(res))        

    def test_wf_tasks_using_asignee(self):
        global WFTEST
        self.intialize()
        res = WFTEST.tasks_list()
        self.logger.info(self.pp.pformat(res))
        
    def test_wf_tasks_using_process_name(self):
        global WFTEST
        self.intialize()
        fi = {'processInstanceId': '9f69862a-259f-11e7-b663-061b3800031f', 'name': 'verify'}
        res = WFTEST.tasks_list(fi)
        self.logger.info(self.pp.pformat(res))
        
    def test_wf_get_task_id(self):
        global WFTEST
        self.intialize()
        res = WFTEST.task_get(taskId='a9f1719f-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res))                  

    def test_wf_get_task_varibles(self):
        global WFTEST
        self.intialize()
        res = WFTEST.task_variables_get(taskId='a9f1719f-259f-11e7-b663-061b3800031f')
        self.logger.info(self.pp.pformat(res)) 

    def test_wf_complete_task(self):
        global WFTEST
        self.intialize()        
        res = WFTEST.task_complete('a476dc02-259f-11e7-b663-061b3800031f', {'settvar': True})
        self.logger.info(self.pp.pformat(res)) 

    def test_wf_get_batch(self):
        global WFTEST
        self.intialize()
        res = WFTEST.batch_get('c4ca0e16-2053-11e7-9a5c-061b3800031f')
        self.logger.info(self.pp.pformat(res))


tests = [
    # system
    
    # ---------- DEPLOYMENT------------
    # 'test_wf_xmlpost',
    # 'test_wf_get_deployment'
    # 'test_wf_delete_deployment',
    
    # -----------CASE DEFINITION-------
    # 'test_wf_case_definition_get'
              
    # -----------PROCESSES-------------
    'test_wf_process_list',
    'test_wf_ping'
    # 'test_wf_process_filtered',
    # 'test_wf_xmlget',
    # 'test_wf_startproc',
    # 'test_wf_delete_process_definition'
    
    # --------PROCESS INSTANCES--------
    # 'test_wf_process_all_instances',
    # 'test_wf_process_instance',
    # 'test_wf_process_instances_delete',
    # 'test_wf_process_single_instance_delete',
    # 'test_wf_get_history_instances',
    # 'test_wf_verify_process_instance_status',
    
    # ----------VARIABLES--------------
    # 'test_wf_process_instance_get_variables',
    # 'test_wf_process_instance_get_variables_ex',
    # 'test_wf_process_instance_get_single_variable',
    # 'test_wf_process_instance_upload_variable' NOT USED
    # 'test_wf_process_instance_update_variables',
    # 'test_wf_process_instance_set_variable',
    # 'test_wf_process_instance_delete_variable',
    
    # -------------TASKS---------------
    # 'test_wf_tasks_using_asignee',
    # 'test_wf_tasks_using_process_name',
    # 'test_wf_get_task_id',
    # 'test_wf_get_task_varibles',
    # 'test_wf_complete_task',
    
    # -------------BATCHS--------------
    # 'test_wf_get_batch'
            
]
    # return unittest.TestSuite(map(WorkFlowEngineTestCase, tests))

if __name__ == '__main__':
    runtest(WorkFlowEngineTestCase, tests)
