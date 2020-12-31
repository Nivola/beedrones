# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

from time import sleep
import os
from beedrones.tests.test_util import BeedronesTestCase, runtest
from beedrones.openstack.client import OpenstackManager

oid = None
name = None
user_id = None
project_id = None
role_id = None

tests = [
    'test_authorize',
    'test_ping',
    'test_version',
    'test_get_token',
    'test_validate_token',

    'test_get_services',
    'test_get_endpoints',
    'test_endpoint',

    # ----- system -------
    'test_compute_api',
    'test_compute_services',
    'test_compute_zones',
    'test_compute_hosts',
    'test_compute_host_aggregates',
    'test_compute_server_groups',
    'test_compute_hypervisors',
    'test_compute_hypervisors_statistics',
    'test_compute_agents',
    'test_storage_services',
    'test_network_agents',
    'test_network_service_providers',
    'test_orchestrator_services',

    # ----- identity role -------
    'test_identity_role_list',
    'test_identity_role_get_by_name',
    'test_identity_role_get',
    'test_identity_role_assignments',

    # ----- identity user -------
    'test_identity_user_list',
    'test_identity_user_get',
    'test_identity_user_create',
    'test_identity_user_by_name',
    'test_identity_user_update',
    'test_identity_user_delete',

    # ----- project -------
    'test_project_list',
    'test_project_get',
    'test_project_create',
    'test_project_by_name',
    'test_project_get_quotas',
    'test_project_get_default_quotas',
    'test_project_update_quota',
    'test_project_get_limits',
    'test_project_get_members',
    'test_project_assign_member',
    'test_project_remove_member',
    'test_project_update',
    'test_project_delete',

    # ----- keypair -------
    'test_keypair_list',
    'test_add_keypair',
    'test_get_keypair',
    'test_delete_keypair',

    # ----- image -------
    'test_image_list',
    'test_image_get',
    'test_image_get_by_name',

    # ----- flavor -------
    'test_flavor_list',
    'test_flavor_get',
    'test_flavor_get_by_tenant',

    # ----- server -------
    'test_server_list',
    'test_get_server',
    'test_server_create',
    'test_get_server_by_name',
    'test_get_server_diagnostic',
    'test_get_server_security_groups',
    'test_add_server_port_interface',
    'test_get_server_port_interfaces',
    'test_delete_server_port_interface',
    'test_get_server_ips',
    'test_add_server_volume',
    'test_get_server_volumes',
    'test_delete_server_volume',
    'test_get_vnc_console',
    'test_get_server_metadata',
    'test_get_server_actions',
    'test_get_server_action',
    'test_server_stop',
    'test_server_start',
    'test_server_delete'

    # ----- volume -------
    'test_volume_list',
    'test_volume_get',
    'test_volume_create',
    'test_volume_get_by_name',
    'test_volume_delete'
]


class OpenstackClientTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()

        env = 'test'
        params = cls.platform.get('openstack').get(env)
        cls.client = OpenstackManager(uri=params.get('uri', None), default_region=params.get('region', None))

        cls.user = params.get('user', None)
        cls.pwd = params.get('pwd', None)
        cls.region = params.get('region', None)
        cls.project = params.get('project', None)
        cls.domain = params.get('domain', None)
        cls.service = 'nova'

        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)
        cls.test_files_path = dir_path + '/hot'
        cls.test_files_url = params.get('hor_url', None)

    def test_ping(self):
        res = self.client.ping()

    def test_version(self):
        res = self.client.version()

    def test_authorize(self):
        self.client.authorize(self.user, self.pwd, project=self.project, domain=self.domain, key=self.fernet)
    
    #
    # token
    #
    def test_get_token(self):
        res = self.client.identity.get_token(self.user, self.pwd, self.project, self.domain)
        self.logger.debug('Token: %s' % res)
        
    def test_validate_token(self):
        self.client.identity.validate_token(self.client.identity.token)
        
    def test_release_token(self):
        self.client.identity.release_token()

    #
    # services
    #
    def test_get_services(self):
        res = self.client.identity.get_services()
        self.logger.debug(self.pp.pformat(res))
        
    def test_get_endpoints(self):
        res = self.client.identity.get_endpoints()
        self.logger.debug(self.pp.pformat(res))
    
    def test_endpoint(self):
        res = self.client.endpoint(self.service)
        self.logger.debug(self.pp.pformat(res))
    
    #
    # system
    #
    def test_compute_api(self):
        res = self.client.system.compute_api()
        self.logger.debug(self.pp.pformat(res))    
    
    def test_compute_services(self):
        res = self.client.system.compute_services()
        self.logger.debug(self.pp.pformat(res))
    
    def test_compute_zones(self):
        res = self.client.system.compute_zones()
        self.logger.debug(self.pp.pformat(res))
    
    def test_compute_hosts(self):
        res = self.client.system.compute_hosts()
        self.logger.debug(self.pp.pformat(res))
    
    def test_compute_host_aggregates(self):
        res = self.client.system.compute_host_aggregates()
        self.logger.debug(self.pp.pformat(res))
    
    def test_compute_server_groups(self):
        res = self.client.system.compute_server_groups()
        self.logger.debug(self.pp.pformat(res))
    
    def test_compute_hypervisors(self):
        res = self.client.system.compute_hypervisors()
        self.logger.debug(self.pp.pformat(res))
    
    def test_compute_hypervisors_statistics(self):
        res = self.client.system.compute_hypervisors_statistics()
        self.logger.debug(self.pp.pformat(res))
    
    def test_compute_agents(self):
        res = self.client.system.compute_agents()
        self.logger.debug(self.pp.pformat(res))
    
    def test_storage_services(self):
        res = self.client.system.storage_services()
        self.logger.debug(self.pp.pformat(res))
    
    def test_network_agents(self):
        res = self.client.system.network_agents()
        self.logger.debug(self.pp.pformat(res))
        
    def test_network_service_providers(self):
        res = self.client.system.network_service_providers()
        self.logger.debug(self.pp.pformat(res))
        
    def test_orchestrator_services(self):
        res = self.client.system.orchestrator_services()
        self.logger.debug(self.pp.pformat(res))             
    
    #
    # roles
    #
    def test_identity_role_list(self):
        res = self.client.identity.role.list(detail=False)
        self.logger.debug(self.pp.pformat(res))    
    
    def test_identity_role_get_by_name(self):
        global role_id
        res = self.client.identity.role.list(detail=False, name='admin')
        self.logger.debug(self.pp.pformat(res))
        role_id = res[0]['id']
        
    def test_identity_role_get(self):
        global role_id
        res = self.client.identity.role.get(oid=role_id)
        self.logger.debug(self.pp.pformat(res))    
    
    def test_identity_role_assignments(self):
        global role_id
        res = self.client.project.get(name='admin')
        project = res['id']
        res = self.client.identity.role.assignments(role=role_id,
                                                    group=None,
                                                    user=None,
                                                    project=project,
                                                    domain=None)
        self.logger.debug(self.pp.pformat(res))    
    
    #
    # users
    #
    def test_identity_user_list(self):
        global user_id
        res = self.client.identity.user.list(detail=False, name=None)
        self.logger.debug(self.pp.pformat(res))
        user_id = res[0]['id']
    
    def test_identity_user_by_name(self):
        global user_id
        res = self.client.identity.user.list(detail=False, name='prova')
        self.logger.debug(self.pp.pformat(res))
        user_id = res[0]['id']
        
    def test_identity_user_get(self):
        global user_id
        res = self.client.identity.user.get(oid=user_id)
        self.logger.debug(self.pp.pformat(res))      
    
    def test_identity_user_create(self):
        res = self.client.project.get(name='demo')
        project = res['id']
        res = self.client.identity.user.create('prova', 'prova@dd.it', project, 'default', 'prova', '')
        self.logger.debug(self.pp.pformat(res))
        
    def test_identity_user_update(self):
        global user_id
        res = self.client.identity.user.update(user_id, password='prova2')
        self.logger.debug(self.pp.pformat(res))    
        
    def test_identity_user_delete(self):
        global user_id
        res = self.client.identity.user.delete(user_id)
        self.logger.debug(self.pp.pformat(res))        
    
    # credentials
    def get_credentials(self):
        res = self.client.identity.get_credentials()
        self.logger.debug(self.pp.pformat(res))
    
    def get_credential(self):
        res = self.client.identity.get_credentials()
        self.logger.debug(self.pp.pformat(res))  
    
    # groups
    def get_groups(self):
        res = self.client.identity.get_groups()
        self.logger.debug(self.pp.pformat(res))
    
    def get_group(self):
        res = self.client.identity.get_groups(oid='')
        self.logger.debug(self.pp.pformat(res))     
    
    # policies
    def get_policies(self):
        res = self.client.identity.get_policies()
        self.logger.debug(self.pp.pformat(res))
    
    def get_policy(self):
        res = self.client.identity.get_policies(oid='')
        self.logger.debug(self.pp.pformat(res))
    
    # regions
    def get_regions(self):
        res = self.client.identity.get_regions()
        self.logger.debug(self.pp.pformat(res))
    
    def get_region(self):
        res = self.client.identity.get_regions(oid='RegionOne')
        self.logger.debug(self.pp.pformat(res))    
    
    # tenants
    def test_get_tenants(self):
        res = self.client.identity.get_tenants()
        self.logger.debug(self.pp.pformat(res))
        
    #
    # domains
    #
    def get_domains(self):
        res = self.client.domain.list()
        self.logger.debug(self.pp.pformat(res))
    
    def get_domain(self):
        res = self.client.domain.get(oid='default')
        self.logger.debug(self.pp.pformat(res))          
        
    #
    # projects
    #
    def test_project_list(self):
        global project_id
        res = self.client.project.list()
        project_id = res[0]['id']

    def test_project_get(self):
        global project_id
        res = self.client.project.get(oid=project_id)
        self.logger.debug(self.pp.pformat(res))

    def test_project_by_name(self):
        global project_id
        res = self.client.project.get(name='prova-project')
        self.logger.debug(self.pp.pformat(res))
        project_id = res['id']
    
    def test_project_create(self):
        res = self.client.project.create('prova-project', 'default', False, parent_id=None)
        self.logger.debug(self.pp.pformat(res))
        
    def test_project_update(self):
        global project_id
        res = self.client.project.update(project_id, description='prova-update')
        self.logger.debug(self.pp.pformat(res))    
        
    def test_project_delete(self):
        global project_id
        res = self.client.project.delete(project_id)
        self.logger.debug(self.pp.pformat(res))
        
    def test_project_get_quotas(self):
        global project_id
        res = self.client.project.get_quotas(oid=project_id)
        self.logger.debug(self.pp.pformat(res))
        
    def test_project_get_default_quotas(self):
        res = self.client.project.get_default_quotas()
        self.logger.debug(self.pp.pformat(res))        
        
    def test_project_update_quota(self):
        global project_id
        res = self.client.project.update_quota(project_id, 'block', 'backup_gigabytes', '1000')
        self.logger.debug(self.pp.pformat(res))  
    
    def test_project_get_limits(self):
        res = self.client.project.get_limits()
        self.logger.debug(self.pp.pformat(res))
        
    def test_project_get_members(self):
        global project_id
        res = self.client.project.get_members(project_id)
        self.logger.debug(self.pp.pformat(res))
        
    def test_project_assign_member(self):
        global project_id
        user = self.client.identity.user.list(name='admin')[0]
        role = self.client.identity.role.list(name='admin')[0]
        res = self.client.project.assign_member(project_id, user['id'], role['id'])
        self.logger.debug(self.pp.pformat(res))
        
    def test_project_remove_member(self):
        global project_id
        user = self.client.identity.user.list(name='admin')[0]
        role = self.client.identity.role.list(name='admin')[0]
        res = self.client.project.remove_member(project_id, user['id'], role['id'])
        self.logger.debug(self.pp.pformat(res))  
    
    #
    # keypair
    #
    def test_keypair_list(self):
        res = self.client.keypair.list()
        self.logger.debug(self.pp.pformat(res))
        
    def test_get_keypair(self):
        res = self.client.keypair.get('key_prova')
        self.logger.debug(self.pp.pformat(res))
    
    def test_add_keypair(self):
        res = self.client.keypair.create('key_prova')
        self.logger.debug(self.pp.pformat(res))
        
    def test_delete_keypair(self):
        res = self.client.keypair.delete('key_prova')
        self.logger.debug(self.pp.pformat(res))            
    
    #
    # server
    #
    def server_status(self, server, accepted_status=None):
        if accepted_status is None:
            accepted_status = ['ACTIVE', 'ERROR']
        status = self.client.server.get(oid=server)['status']
        while status not in accepted_status:
            sleep(2)
            status = self.client.server.get(oid=server)['status']

    def test_server_list(self):
        global oid
        res = self.client.server.list(detail=True)
        self.logger.debug(self.pp.pformat(res))
        oid = res[0]['id']
        
    def test_get_server(self):
        global oid
        res = self.client.server.get(oid=oid)
        self.logger.debug(self.pp.pformat(res))
        
    def test_server_create(self):
        name = 'server-prova'
        image = self.client.image.get(name='centos7_lvm')['id']
        flavor = self.client.flavor.get(2)['id']
        boot_volume_id = None
        networks = [{'uuid': self.client.network.get(name='566')['id']}]
        # create server   
        res = self.client.server.create(name, flavor, accessipv4=None, accessipv6=None, networks=networks,
                                        boot_volume_id=boot_volume_id, adminpass='mypass', description='',
                                        metadata=None, image=image, security_groups=['default'], personality=None,
                                        user_data=None, availability_zone=None)
        self.server_status(res['id'])
        self.logger.debug(self.pp.pformat(res))

    def test_get_server_by_name(self):
        global oid
        res = self.client.server.get(name='server-prova')
        self.logger.debug(self.pp.pformat(res))
        oid = res['id']

    def test_get_server_diagnostic(self):
        global oid
        res = self.client.server.diagnostics(oid)
        self.logger.debug(self.pp.pformat(res))
        
    def test_get_server_security_groups(self):
        global oid
        res = self.client.server.security_groups(oid)
        self.logger.debug(self.pp.pformat(res))
        
    def test_get_server_port_interfaces(self):
        global oid
        res = self.client.server.get_port_interfaces(oid)
        self.logger.debug(self.pp.pformat(res))
        
    def test_add_server_port_interface(self):
        global oid
        net_id = self.client.network.get(name='565')['id']
        res = self.client.server.add_port_interfaces(oid, net_id)
        self.logger.debug(self.pp.pformat(res))         
        
    def test_delete_server_port_interface(self):
        global oid
        net_id = self.client.network.get(name='565')['id']
        port_id = self.client.network.port.list(network=net_id)[0]['id']
        res = self.client.server.remove_port_interfaces(oid, port_id)
        self.logger.debug(self.pp.pformat(res))

    def test_get_server_ips(self):
        global oid
        res = self.client.server.get_ips(oid)
        self.logger.debug(self.pp.pformat(res))        
        
    def test_get_server_volumes(self):
        global oid
        res = self.client.server.get_volumes(oid)
        self.logger.debug(self.pp.pformat(res))
        
    def test_add_server_volume(self):
        global oid
        volume = self.client.volume_v3.create(size=20, multiattach=False, snapshot_id=None, name='volume-prova-01')
        volume_id = volume['id']
        self.volume_status(volume_id)
        res = self.client.server.add_volume(oid, volume_id)
        self.volume_status(volume_id, accepted_status=['in-use'])
        self.logger.debug(self.pp.pformat(res))
        
    def test_delete_server_volume(self):
        global oid
        volume_id = self.client.volume_v3.get(name='volume-prova-01')['id']
        res = self.client.server.remove_volume(oid, volume_id)
        self.volume_status(volume_id)
        self.client.volume_v3.delete(volume_id)
        self.logger.debug(self.pp.pformat(res))

    def test_get_vnc_console(self):
        global oid, name
        res = self.client.server.get_vnc_console(oid)
        self.logger.debug(self.pp.pformat(res))
        
    def test_get_server_metadata(self):
        global oid, name
        res = self.client.server.get_metadata(oid)
        self.logger.debug(self.pp.pformat(res))
        
    def test_get_server_actions(self):
        global oid, action_id
        res = self.client.server.get_actions(oid)
        self.logger.debug(self.pp.pformat(res))
        action_id = res[0]['request_id']
        
    def test_get_server_action(self):
        global oid, action_id
        res = self.client.server.get_actions(oid, action_id=action_id)
        self.logger.debug(self.pp.pformat(res))         

    def test_server_start(self):
        global oid
        res = self.client.server.start(oid)
        self.server_status(oid)
        self.logger.debug(self.pp.pformat(res))
        
    def test_server_stop(self):
        global oid
        res = self.client.server.stop(oid)
        self.server_status(oid, accepted_status=['SHUTOFF'])
        self.logger.debug(self.pp.pformat(res))

    def test_server_delete(self):
        global oid
        res = self.client.server.delete(oid)
        self.logger.debug(self.pp.pformat(res))

    #
    # volume
    #
    def volume_status(self, volume, accepted_status=None):
        if accepted_status is None:
            accepted_status = ['available', 'error']
        status = self.client.volume_v3.get(oid=volume)['status']
        while status not in accepted_status:
            sleep(2)
            status = self.client.volume_v3.get(oid=volume)['status']

    def test_volume_list(self):
        global oid
        res = self.client.volume_v3.list(detail=True)
        self.logger.debug(self.pp.pformat(res))
        oid = res[0]['id']

    def test_volume_get(self):
        global oid
        res = self.client.volume_v3.get(oid=oid)
        self.logger.debug(self.pp.pformat(res))

    def test_volume_create(self):
        image = self.client.image.get(name='centos7_lvm')['id']
        project = self.client.project.get(name='demo')['id']
        res = self.client.volume_v3.create(size=20, availability_zone=None, source_volid=None, description='',
                                           multiattach=False, snapshot_id=None, name='volume-prova-01', imageRef=image,
                                           volume_type=None, metadata=None, source_replica=None,
                                           consistencygroup_id=None, scheduler_hints=None, tenant_id=project)
        status = self.client.volume_v3.get(oid=res['id'])['status']
        while status not in ['available', 'error']:
            sleep(2)
            status = self.client.volume_v3.get(oid=res['id'])['status']
        self.logger.debug(self.pp.pformat(res))
        
    def test_volume_get_by_name(self):
        global oid
        res = self.client.volume_v3.get(name='volume-prova-01')
        self.logger.debug(self.pp.pformat(res))
        oid = res['id']

    def test_volume_delete(self):
        global oid
        res = self.client.volume_v3.delete(oid)
        self.logger.debug(self.pp.pformat(res))

    #
    # image
    #
    def test_image_list(self):
        global oid
        res = self.client.image.list(detail=False)
        self.logger.debug(self.pp.pformat(res))
        oid = res[0]['id']
        
    def test_image_get(self):
        global oid
        res = self.client.image.get(oid=oid)
        self.logger.debug(self.pp.pformat(res))
        
    def test_image_get_by_name(self):
        res = self.client.image.get(name='cirros')
        self.logger.debug(self.pp.pformat(res))
        
    #
    # flavor
    #
    def test_flavor_list(self):
        res = self.client.flavor.list(detail=False)
        self.logger.debug(self.pp.pformat(res))
        
    def test_flavor_get(self):
        res = self.client.flavor.get(1)
        self.logger.debug(self.pp.pformat(res))
        
    def test_flavor_get_by_tenant(self):
        project = self.client.project.get(name='demo')['id']
        res = self.client.flavor.list(tenant=project)
        self.logger.debug(self.pp.pformat(res))


if __name__ == '__main__':
    runtest(OpenstackClientTestCase, tests)
