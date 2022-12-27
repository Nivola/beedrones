# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

import gevent
from beedrones.tests.test_util import BeedronesTestCase, runtest
from beedrones.veeam.client import VeeamManager, VeeamJob, VeeamClient, VeeamReplica

import unittest

contid = 14
component = 'NSX'

tests = [
    # system
     # 'test_get_vbrjobs_winrm',
    # 'test_veeam_call',
    # 'test_get_tasks',
    # 'test_get_task_props',

    # Jobs
    # 'test_get_jobs',
    # 'test_get_backups_status',
    # 'test_search_job',
    # 'test_get_job_props',
    # 'test_edit_job',
    # 'test_start_job',
    # 'test_stop_job',
    # 'test_retry_job',
    # 'test_clone_job',
    # 'test_old_create_job',
    # 'test_create_job'
    # 'test_togglescheduleenabled_job',

    # Job Includes ( objs in job )
    # 'test_objsinjob_get_includes',
    # 'test_objsinjob_add',
    # 'test_objsinjob_props',
    # 'test_objsinjob_delete',

    # Replicas
    # 'test_get_esxi_from_vm',
    # 'test_create_replica_job',
    # 'test_create_replica_mapping',
    # 'test_set_replica_schedule'
    # 'test_enable_replica_schedule',
    # 'test_disable_replica_schedule',
    # 'test_disable_replica',
    # 'test_enable_replica',
    # 'test_set_notification_email',
    # 'test_enable_notification_email',
    # 'test_disable_notification_email'
    # 'test_add_replica_reiprule',
    # 'test_add_replica_network_mapping',
    # 'test_add_replica_reiprule',
    # 'test_giro_replica_completo',
    'test_giro_replica_mapping_completo'
]


class VeeamUtilTestCase(BeedronesTestCase):
    """To execute this test you need a cloudstack instance.
    """
    def setUp(self):
        BeedronesTestCase.setUp(self)

        env = 'tstsddc'
        # print (self.platform)
        params = self.platform.get('veeam').get(env)
        # print (str(params))
        veeamTest = {'uri':'http://tst-veeamsrv.tstsddc.csi.it:9399',
                 'user':'Administrator',
                 'pwd':'', 'verified':False}
        

        # self.util=VeeamManager(veeamTest)

        self.util = VeeamManager({'uri': params.get('uri', None),
                                  'user': params.get('user', None),
                                  'pwd': params.get('pwd',None),
                                  'verified': params.get('verified', None),
                                  'veeamsrv': params.get('veeamsrv', None),
                                  'veeamsrvuser': params.get('veeamsrvuser', None),
                                  'veeamsrvpwd': params.get('veeamsrvpwd', None)
                                  })

        # self.jobs=VeeamJob(self.util,self.client)
        # print params.get('pwd', None)
        

    def tearDown(self):
        BeedronesTestCase.tearDown(self)
 
    '''   
    def wait_task(self, task):
        while task.info.state not in [vim.TaskInfo.State.success,
                                      vim.TaskInfo.State.error]:
            self.logger.info(task.info.state)
            gevent.sleep(1)
            
        if task.info.state in [vim.TaskInfo.State.error]:
            self.logger.info("Error: %s" % task.info.error.msg)
        if task.info.state in [vim.TaskInfo.State.success]:
            self.logger.info("Completed")            
    '''    
    def test_veeam_connection(self):
        res = self.util.ping_veeam()  
        self.assertTrue(res)      
        self.logger.info(res)

    def test_veeam_call(self):
        #base_path="tst-veeamsrv.tstsddc.csi.it:9399"
        method='GET'
        #path='/api/query?type=job&filter=name==Backup_testusr'
        path='http://tst-veeamsrv.tstsddc.csi.it:9399/api/tasks/task-11'
        #path='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312?format=Entity'

        #token=self.util.veeam_token        
        
        
        res=self.util.client.call(path, method,'','', 30, self.util.veeam_token , '')
        self.logger.info(res)
           
    def test_get_tasks(self):
        res=self.util.get_tasks()
        self.assertTrue(res['status']=='OK')

    def test_get_task_props(self):
        taskId='task-70'
        res=self.util.get_task_props(taskId)
        self.assertTrue(res['status']=='OK')

    def test_get_vbrjobs_winrm(self):
        res = self.util.replica.get_vbrjobs_winrm()
        # self.assertTrue(res['status']=='OK')
        #self.logger.debug(res)

    def test_get_jobs(self):
        res=self.util.jobs.get_jobs()
        self.assertTrue(res['status']=='OK')
        #self.logger.debug(res)

    def test_get_backups_status(self):
        res=self.util.jobs.get_backups_status()
        self.assertTrue(res['status']=='OK')
        #self.logger.debug(res)


    def test_search_job(self):
        res=self.util.jobs.search_job('TMPL-NIVOLA-JOB')
        self.assertTrue(res['status']=='OK')
        
        
    def test_get_job_props(self):
        path='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/552763ca-04b7-4b3c-905e-8aa743e63e2e'
        res=self.util.jobs.get_job_props(path)
        self.assertTrue(res['status']=='OK')
                    
    def test_edit_job(self):
        
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312?action=edit'

        XML="""<?xml version="1.0" encoding="utf-8"?>
        <Job Type="Job"  
        xmlns="http://www.veeam.com/ent/v1.0" 
        xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <JobScheduleOptions>
            <RetryOptions>
                <RetryTimes>3</RetryTimes>
                <RetryTimeout>5</RetryTimeout>
                <RetrySpecified>true</RetrySpecified>
            </RetryOptions>        
            <OptionsDaily Enabled="true">
                <Kind>Everyday</Kind>
                <Days>Sunday</Days>
                <Days>Monday</Days>
                <Days>Tuesday</Days>
                <Days>Wednesday</Days>
                <Days>Thursday</Days>
                <Days>Friday</Days>
                <Days>Saturday</Days>
                <Time>22:00:00.0000000</Time>
            </OptionsDaily>        
        </JobScheduleOptions>
        </Job>"""
        
        res=self.util.jobs.edit_job(href,XML)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312?action=editstatus']=='OK')
    
    def test_start_job(self):
        #href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b'
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312'
        res=self.util.jobs.start_job(href)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')

    def test_stop_job(self):
        #href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b'
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312'
        res=self.util.jobs.stop_job(href)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')

    def test_retry_job(self):
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b'
        res=self.util.jobs.retry_job(href)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')

       
    def test_old_create_job(self):
        
        # "urn:veeam:Repository:b03eb865-79eb-4450-bc52-48a7472314ca"
        
        template2Copy='TMPL-NIVOLA-JOB'
        #href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b'
        
        
        res=self.util.jobs.old_create_job(template2Copy,'Crea_backup_from_api','urn:veeam:Repository:b03eb865-79eb-4450-bc52-48a7472314ca','urn:VMware:Vm:7f6b6270-1f3b-4dc6-872f-2d1dfc519c00.vm-3154','boraso2')
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')
        print(res)

    def test_create_job(self):
        
        # "urn:veeam:Repository:b03eb865-79eb-4450-bc52-48a7472314ca"
        
        template2Copy='TMPL-NIVOLA-JOB'
        #href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b'
        
        
        res=self.util.jobs.create_job(template2Copy,'Crea_backup_from_api_Last','urn:veeam:Repository:b03eb865-79eb-4450-bc52-48a7472314ca','urn:VMware:Vm:7f6b6270-1f3b-4dc6-872f-2d1dfc519c00.vm-3154','boraso2')
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')
        print(res)
        
    def test_clone_job(self):
        
        XML="""<?xml version="1.0" encoding="utf-8"?>
        <JobCloneSpec xmlns="http://www.veeam.com/ent/v1.0" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> 
        <BackupJobCloneInfo> <JobName>Prova Cloned Job</JobName> <FolderName>Prova Cloned Job</FolderName> 
        <RepositoryUid>urn:veeam:Repository:b03eb865-79eb-4450-bc52-48a7472314ca
        </RepositoryUid> </BackupJobCloneInfo> </JobCloneSpec>"""
        # "urn:veeam:Repository:b03eb865-79eb-4450-bc52-48a7472314ca"
        #XML='<?xml version="1.0" encoding="utf-8"'
        
        
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/9c23e704-fa20-46b0-9fa1-7e815816933b'
        
        
        res=self.util.jobs.clone_job(href,XML)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')
       
    def test_togglescheduleenabled_job(self):
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/029aa907-b538-4a68-8186-a7cf9033a4e3'
        res=self.util.jobs.togglescheduleenabled_job(href)
        '''
        self.logger.debug("TaskId %s , State %s, Operation %s" % (res['data']['Task']['TaskId'],res['data']['Task']['State'],res['data']['Task']['Operation']))
        self.logger.debug(res['status'])
        self.logger.debug(res['status_code'])
        self.logger.debug(res['data'])
        '''
        self.assertTrue(res['status']=='OK')
        
    def test_objsinjob_get_includes(self):
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312'
        res=self.util.jobobjs.get_includes(href)
        self.assertTrue(res['status']=='OK')
        #self.logger.debug(res)
    def test_objsinjob_props(self):
        href = 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312/includes/4e20ffc5-8382-4ab3-b6c1-7b956889fec8'
        res=self.util.jobobjs.get_includes_props(href)
        self.assertTrue(res['status']=='OK')
    
    def test_objsinjob_add(self):
        href='http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312'
        
        XML="""<?xml version="1.0" encoding="utf-8"?>
            <CreateObjectInJobSpec xmlns="http://www.veeam.com/ent/v1.0"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <HierarchyObjRef>urn:VMware:Vm:7f6b6270-1f3b-4dc6-872f-2d1dfc519c00.vm-1401</HierarchyObjRef>
            <HierarchyObjName>tst-calamari</HierarchyObjName>
            </CreateObjectInJobSpec>
            """
        
        #"urn:VMware:Vm:7f6b6270-1f3b-4dc6-872f-2d1dfc519c00.vm-1401'), ('Name', 'tst-calamari')"
        
        
        res=self.util.jobobjs.add_includes(href,XML)
        self.assertTrue(res['status']=='OK')
        #self.logger.debug(res)

    def test_objsinjob_delete(self):
        href = 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312/includes/4e20ffc5-8382-4ab3-b6c1-7b956889fec8'
        res=self.util.jobobjs.delete_includes(href)
        self.assertTrue(res['status']=='OK')

    def test_create_replica_job(self):
        dest_esxiname = "podvc-vsphere02.site03.nivolapiemonte.it"
        dest_datastore = "SITE03-VSPHERE-VMAX-LUN01"
        dest_folder = "demo_tenant_avz714"
        server_name2replicate = "tst-awx-2016(by beedrones)"
        job_replica_name = "replicajob_tst-awx-2016(by beedrones)"
        replica_suffix = "_replica"
        description = "test replica via api"

        res = self.util.replica.create_replica_job(dest_esxiname, dest_datastore, dest_folder, server_name2replicate,
                                                   job_replica_name, replica_suffix, description)
        # self.assertTrue(res)
        self.logger.info(res)

    def test_get_esxi_from_vm(self):
        vm_name = "zbxsrv"
        res = self.util.replica.get_esxi_from_vm(vm_name)
        print(res)
        # vm_name = "zbxsrv-replicaww"
        # res = self.util.replica.get_esxi_from_vm(vm_name)
        # print res

    def test_create_replica_mapping(self):
        original_vm = "zbxsrv"
        replica_vm = "zbxsrv-replica"
        job_replica_name = "Test_replica_seeding_via_API"
        job_replica_description = "Replica di test creata da beedrone"

        res = self.util.replica.create_replica_mapping(job_replica_name, job_replica_description,
                                                       original_vm, replica_vm)
        self.assertTrue(res)
        self.logger.info(res)

    def test_set_replica_schedule(self):
        href = "http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/5152a6ac-53bb-477e-b220-105806c24a2b"
        # href = 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/4d9bff58-3058-4f31-a998-cffd33bf51d9'

        xml_test_daily = """<?xml version="1.0" encoding="utf-8"?>
                            <Job Type="Job"   
                                xmlns="http://www.veeam.com/ent/v1.0" 
                                xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                                    <JobScheduleOptions>
                                        <Standart>
                                            <RetryOptions>
                                                    <RetryTimes>3</RetryTimes>
                                                    <RetryTimeout>5</RetryTimeout>
                                                    <RetrySpecified>true</RetrySpecified>
                                            </RetryOptions>        
                                            <OptionsDaily Enabled="true">
                                                <Kind>Everyday</Kind>
                                                <Days>Sunday</Days>
                                                <Days>Monday</Days>
                                                <Days>Tuesday</Days>
                                                <Days>Wednesday</Days>
                                                <Days>Thursday</Days>
                                                <Days>Friday</Days>
                                                <Days>Saturday</Days>
                                                <Time>02:00:00.0000000</Time>
                                            </OptionsDaily>             
                                        </Standart>
                                    </JobScheduleOptions>
                                </Job>
                            """
        days = """
        <Days>Sunday</Days>
        <Days>Friday</Days>
        """

        """
        esempi:

        daily : res = self.util.replica.set_replica_schedule(href, '02:00:00', schedule='daily', day_number_in_month='Second',
                                                     day_of_week='Monday')
        weekdays : res = self.util.replica.set_replica_schedule(href, '02:00:00', schedule='weekdays', 
                                                     day_number_in_month='Second',
                                                     day_of_week='Monday')

        selecteddays : res = self.util.replica.set_replica_schedule(href, '02:00:00', schedule='selecteddays', 
                                                    days="<Days>Sunday</Days>/
                                                    <Days>Friday</Days>/
                                                    <Days>Friday</Days>")

        monthly :  res = self.util.replica.set_replica_schedule(href, '14:00:00', schedule='monthly', 
                                                    day_number_in_month="Third", day_of_week="Wednesday")                                                

        monthly (only some months):  res = self.util.replica.set_replica_schedule(href, '14:00:00', schedule='monthly', 
                                                    day_number_in_month="Third", day_of_week="Wednesday",
                                                    months="<Months>April</Months><Months>July</Months><Months>December</Months>")
        """

        res = self.util.replica.set_replica_schedule(href, '15:00:00', schedule='daily')

        self.logger.info(res)

    def test_enable_replica_schedule(self):
        href = "http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/552763ca-04b7-4b3c-905e-8aa743e63e2e"
        res = self.util.replica.enable_replica_schedule(href)
        self.logger.info(res)

    def test_disable_replica_schedule(self):
        href = "http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/552763ca-04b7-4b3c-905e-8aa743e63e2e"
        res = self.util.replica.disable_replica_schedule(href)
        self.logger.info(res)

    def test_enable_replica(self):
        href = "http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/552763ca-04b7-4b3c-905e-8aa743e63e2e"
        res = self.util.replica.enable_replica(href)
        self.logger.info(res)

    def test_disable_replica(self):
        href = "http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/552763ca-04b7-4b3c-905e-8aa743e63e2e"
        res = self.util.replica.disable_replica(href)
        self.logger.info(res)

    def test_set_notification_email(self):
        replica_name = "Test_replica_seeding_via_API"
        email = "xxx@csi.it"

        return self.util.replica.set_notification_email(replica_name, email)

    def test_enable_notification_email(self):
        replica_name = "replica_gui"
        return self.util.replica.enable_notification_email(replica_name)

    def test_disable_notification_email(self):
        replica_name = "replica_gui"
        return self.util.replica.disable_notification_email(replica_name)

    def test_add_replica_reiprule(self):
        replica_job_name = "Test_replica_seeding_via_API"
        return self.util.replica.add_replica_reiprule(replica_job_name, '10.102.184.*', '192.168.214.*',
                                                      '192.168.214.1', dns="10.101.0.10,10.101.0.105")

    def test_add_replica_network_mapping(self):

        # add_replica_network_mapping(self, replica_job_name, source_esxi, source_net, target_esxi, target_net):

        original_vm = "zbxsrv"
        replica_vm = "zbxsrv-replica"
        replica_job_name = "Test_replica_seeding_via_API"

        source_net = "PG_563_DCCTP-tst-mgt"
        target_net = "vxw-dvs-284-virtualwire-1-sid-5002-PrimaLogicalSwiitch"

        # source_esxi ="tst-esx01.tstsddc.csi.it"
        source_esxi = self.util.replica.get_esxi_from_vm(original_vm)

        # target_esxi = dest_esxiname
        target_esxi = self.util.replica.get_esxi_from_vm(replica_vm)

        return self.util.replica.add_replica_network_mapping(replica_job_name, source_esxi, source_net, target_esxi,
                                                             target_net)

    def test_giro_replica_completo(self):
        """
        Questo test simula il giro completo di crezione di una replica tra ambiente di tstsddc verso il podvc
        - crea replica
        - configura network
        - ReIP
        - set schedule
        - set email

        """

        # crea replica

        dest_esxiname = "podvc-vsphere02.site03.nivolapiemonte.it"
        dest_datastore = "SITE03-VSPHERE-VMAX-LUN01"
        dest_folder = "demo_tenant_avz714"
        server_name2replicate = "tst-beedrones2(tenant-demo)"
        replica_job_name = "replicajob_tst-beedrones2(tenant-demo)"
        replica_suffix = "_replica"
        description = "test replica via api"

        res = self.util.replica.create_replica_job(dest_esxiname, dest_datastore, dest_folder, server_name2replicate,
                                                   replica_job_name, replica_suffix, description)

        # configura network
        source_esxi = "tst-esx01.tstsddc.csi.it"
        source_net = "vxw-dvs-74-virtualwire-25-sid-5002-LS-vxlan-TenantDemo"
        target_esxi = dest_esxiname
        target_net = "vxw-dvs-15-virtualwire-7-sid-15006-LS-vxlan1-tenantDEMO"

        res = self.util.replica.add_replica_network_mapping(replica_job_name, source_esxi, source_net, target_esxi,
                                                            target_net)

        # ReIP
        res = self.util.replica.add_replica_reiprule(replica_job_name, '192.168.216.*', '192.168.214.*',
                                                     '192.168.214.1', dns="10.101.0.10,10.101.0.105")

        # set email
        res = self.util.replica.set_notification_email(replica_job_name, 'xxx@csi.it')

        # set schedule
        href = self.util.jobs.search_job(replica_job_name)['data']

        self.util.replica.set_replica_schedule(href, '15:00:00', schedule='daily')

        # enable schedule
        self.util.replica.enable_replica_schedule(href)

        # enable email
        self.util.replica.enable_notification_email(replica_job_name)

        # start replica
        self.util.replica.start_replica(href)

        return

    def test_giro_replica_mapping_completo(self):
        """
        Questo test simula il giro completo di crezione di una replica tra ambiente di tstsddc verso il podvc
        - crea replica
        - configura network
        - ReIP
        - set schedule
        - set email

        """

        # crea replica

        original_vm = "zbxsrv"
        replica_vm = "zbxsrv-replica"
        job_replica_name = "Test_replica_seeding_via_API"
        job_replica_description = "Replica di test creata da beedrone"

        res = self.util.replica.create_replica_mapping(job_replica_name, job_replica_description,
                                                       original_vm, replica_vm)

        # configure network
        source_net = "PG_563_DCCTP-tst-mgt"
        target_net = "vxw-dvs-284-virtualwire-1-sid-5002-PrimaLogicalSwiitch"

        # source_esxi ="tst-esx01.tstsddc.csi.it"
        source_esxi = self.util.replica.get_esxi_from_vm(original_vm)

        # target_esxi = dest_esxiname
        target_esxi = self.util.replica.get_esxi_from_vm(replica_vm)

        res = self.util.replica.add_replica_network_mapping(job_replica_name, source_esxi, source_net, target_esxi,
                                                            target_net)

        # ReIP
        res = self.util.replica.add_replica_reiprule(job_replica_name, '10.102.184.*', '192.168.214.*',
                                                      '192.168.214.1', dns="10.101.0.10,10.101.0.105")

        # set email
        res = self.util.replica.set_notification_email(job_replica_name, 'xxx@csi.it')

        # set schedule
        href = self.util.jobs.search_job(job_replica_name)['data']

        self.util.replica.set_replica_schedule(href, '15:00:00', schedule='daily')

        # enable schedule
        self.util.replica.enable_replica_schedule(href)

        # enable email
        self.util.replica.enable_notification_email(job_replica_name)

        # start replica
        # self.util.replica.start_replica(href)


        return


# def test_suite():
#     tests = [
#          # system
#          #'test_veeam_call',
#          #'test_get_tasks',
#          #'test_get_task_props',
#          # Jobs
#          #'test_get_jobs',
#         'test_get_backups_status',
#          #'test_search_job',
#          #'test_get_job_props',
#          #'test_edit_job',
#          #'test_start_job',
#          #'test_stop_job',
#          #'test_retry_job',
#          #'test_clone_job',
#          #'test_old_create_job',
#          #'test_create_job'
#          #'test_togglescheduleenabled_job',
#
#          # Job Includes ( objs in job )
#          #'test_objsinjob_get_includes',
#          #'test_objsinjob_add',
#          #'test_objsinjob_props',
#          #'test_objsinjob_delete',
#
#     ]
#     return unittest.TestSuite(map(VeeamUtilTestCase, tests))


if __name__ == '__main__':
    # runtest(test_suite())
    runtest(VeeamUtilTestCase, tests)
