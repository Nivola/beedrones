# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from time import sleep
import gevent
from beecell.types.type_dict import dict_get
from beedrones.vsphere.client import VsphereManager
from pyVmomi import vim
from beedrones.tests.test_util import BeedronesTestCase, runtest

edgeid = 'edge-5'
ruleid = '196609'

tests = [
    ## system
    # 'test_ping_vsphere',
    # 'test_ping_nsx',
    # 'test_ping',
    # 'test_version',

    ## datacenter
    # 'test_list_datacenters',
    # 'test_get_datacenter',

    ## cluster
    # 'test_list_clusters',
    # 'test_get_cluster',
    # 'test_list_hosts',
    # 'test_get_host',
    # 'test_list_resource_pools',
    # 'test_get_resource_pool',
    # 'test_get_resource_pool_servers',
    # 'test_create_resource_pool',
    # 'test_update_resource_pool',
    # 'test_delete_resource_pool',
    # 'test_list_cluster_servers',

    ## datastore
    # 'test_list_datastores',
    # 'test_get_datastore',
    # 'test_get_datastore_hosts',

    ## folder
    # 'test_list_folders',
    # 'test_create_folder',
    # 'test_get_folder',
    # 'test_update_folder',
    # 'test_remove_folder',

    ## virtual app
    # 'test_list_virtualapp',
    # 'test_get_virtualapp',

    ## server
    # 'test_list_servers',
    # 'test_get_server',
    # 'test_get_server_hardware',
    # 'test_get_server_devices',
    # 'test_get_server_guest_info',
    # 'test_get_server_runtime',
    # 'test_get_server_usage',
    # ## 'test_assign_server_tag',
    # ## 'test_get_server_tags',
    # 'test_get_server_permissions',
    # 'test_get_server_remote_console',
    # 'test_get_server_security_groups',
    # 'test_get_server_by_dnsname',
    # 'test_get_server_by_ip',
    # 'test_get_server_network',

    ## server create, delete
    # 'test_create_server',
    # 'test_remove_server',
    ## 'test_create_linked_clone'
    # 'test_create_from_template',
    # 'test_update_server',
    # 'test_start_server',
    # 'test_stop_server',
    # 'test_start_server',

    ## server guest
    # 'test_server_guest_info',
    # 'test_server_guest_list_process',
    # 'test_server_guest_execute_command',
    # 'test_server_guest_read_environment_variable',
    ## 'test_server_guest_setup_network',

    ## server hw
    # 'test_add_server_disk',
    # 'test_remove_server_disk',
    # 'test_add_server_network',
    # 'test_update_server_network',
    # 'test_remove_server_network',
    # 'test_update_server_cdrom',

    ## sever snapshot
    # 'test_take_server_snapshot',
    # 'test_list_server_snapshot',
    # 'test_get_current_server_snapshot',
    # 'test_get_server_snapshot',
    # ## 'test_rename_server_snapshot',
    # 'test_revert_server_snapshot',
    # 'test_delete_server_snapshot',

    ## remove server
    # 'test_remove_server',

    ## network
    # 'test_list_distributed_virtual_switches',
    # 'test_get_distributed_virtual_switch',
    # 'test_list_networks',
    # 'test_get_network',
    # 'test_get_network_servers',
    # 'test_create_network',
    # 'test_delete_network',

    ## nsx manager
    # 'test_nsx_global_info',
    #'test_nsx_summary_info',

    ## VPNSSL
    # 'test_sslvpn_get',
    # 'test_sslvpn_user_get',
    # 'test_sslvpn_disable',
    #'test_sslvpn_enable',
    # 'test_sslvpn_session_get',
    # 'test_sslvpn_user_modify',
    'test_sslvpn_private_network_modify',

    ## 'test_nsx_reboot_appliance',
    # 'test_nsx_query_appliance_cpu',
    # 'test_nsx_query_appliance_uptime',
    # 'test_nsx_query_appliance_memory',
    # 'test_nsx_query_appliance_storage',
    # 'test_nsx_query_appliance_network',

    # 'test_nsx_configure_appliance_dns',
    # 'test_nsx_delete_appliance_dns',

    # 'test_nsx_query_appliance_time_settings',
    # 'test_nsx_configure_appliance_time_settings',
    # 'test_nsx_delete_appliance_time_settings',

    # 'test_nsx_query_appliance_local',
    # 'test_nsx_configure_appliance_local',

    # 'test_nsx_query_appliance_syslog',
    # 'test_nsx_configure_appliance_syslog',
    # 'test_nsx_delete_appliance_syslog',

    # 'test_nsx_components_summary',
    # 'test_nsx_query_appliance_components',
    # 'test_nsx_query_appliance_component',
    # 'test_nsx_query_appliance_component_dependency',
    # 'test_nsx_query_appliance_component_status',
    # 'test_nsx_toggle_appliance_component_status',
    # 'test_nsx_restart_appliance_webapp',

    # 'test_nsx_get_system_events',
    # 'test_nsx_get_system_audit_logs',
    #
    # 'test_get_nsx_transport_zones',
    # 'test_list_controllers',

    ## network nsx logical switch
    # 'test_nsx_list_logical_switches',
    # 'test_nsx_list_logical_switch',
    # 'test_nsx_create_logical_switch',
    # 'test_nsx_delete_logical_switch',

    ## network nsx security group
    # 'test_nsx_list_security_group',
    # 'test_nsx_list_security_group_by_server',
    # 'test_nsx_security_group_create',
    # 'test_nsx_get_security_group',
    # 'test_nsx_get_allowed_member_type',
    # 'test_nsx_security_group_add_member',
    # 'test_nsx_security_group_delete_member',
    # 'test_nsx_update_security_group',
    # 'test_nsx_security_group_delete',

    ## network nsx ippool
    # 'test_nsx_list_ippool',
    # 'test_nsx_get_ippool',
    # 'test_nsx_create_ippool',
    # 'test_nsx_ippool_allocate_ip',
    # 'test_nsx_ippool_allocations',
    # 'test_nsx_ippool_release_ip',
    # 'test_nsx_update_ippool',
    # 'test_nsx_delete_ippool',

    ## network nsx ipset
    # 'test_nsx_create_ipset',
    # 'test_nsx_list_ipset',
    # 'test_nsx_get_ipset',
    # 'test_nsx_update_ipset',
    # 'test_nsx_delete_ipset',

    ## network nsx service
    # 'test_nsx_create_service',
    # 'test_nsx_list_service',
    # 'test_nsx_get_service',
    # 'test_nsx_delete_service',

    ## network nsx dfw
    # 'test_nsx_list_all_dfw_rules',
    # # 'test_nsx_get_sections',
    # # 'test_nsx_get_dfw_section',
    # # 'test_nsx_get_dfw_rule',
    # # 'test_nsx_filter_dfw_rules',
    # 'test_nsx_create_dfw_section',
    # 'test_nsx_create_dfw_rule',
    # ## 'test_nsx_create_dfw_rule_deny_isolotti',
    # ## 'test_nsx_create_dfw_rule_158',
    # ## 'test_nsx_create_dfw_rule_allow_demo',
    # 'test_nsx_update_dfw_rule',
    # ## 'test_nsx_move_dfw_rule',
    # 'test_nsx_delete_dfw_rule',
    # 'test_nsx_delete_dfw_section',

    # 'test_nsx_get_exclusion_list',

    ## network nsx dlr
    # 'test_nsx_list_all_dlr',
    # 'test_nsx_get_dlr',

    ## network nsx edge
    # 'test_nsx_list_all_edge',
    # 'test_nsx_get_edge',
    # 'test_nsx_add_edge',
    # 'test_nsx_get_edge_detail',
    # 'test_nsx_get_edge_appliances',
    # 'test_nsx_get_edge_reset_pwd',
    # 'test_nsx_add_edge_vnic',

    ## network nsx vpn firewall
    # 'test_nsx_get_edge_firewall_rules',
    # 'test_nsx_add_edge_firewall_rules',
    # 'test_nsx_del_edge_firewall_rules',

    ## network nsx vpn nat
    # 'test_nsx_get_edge_nat_rules',
    # 'test_nsx_add_edge_nat_rules',
    # 'test_nsx_del_edge_nat_rules',

    ## network nsx vpn route
    # 'test_nsx_get_edge_routing',
    # 'test_nsx_add_edge_default_route',
    # 'test_nsx_add_edge_static_route',
    # 'test_nsx_del_edge_static_route',

    ## network nsx vpn ssl

    ## network nsx vpn ipsec

    ## network nsx LB ( load balancing )
    # 'test_nsx_edge_lb_get_config',
    # 'test_nsx_edge_lb_enable_true',
    # 'test_nsx_edge_lb_enable_false',
    # 'test_nsx_edge_lb_list_app_profile',
    # 'test_nsx_edge_lb_get_app_profiles',
    # 'test_nsx_edge_lb_add_app_profile',
    # 'test_nsx_edge_lb_update_app_profile',
    # 'test_nsx_edge_lb_del_app_profile',
    # 'test_nsx_edge_lb_configure',
    # 'test_nsx_edge_lb_del_all_app_profiles',
    # 'test_nsx_edge_lb_list_pools',
    # 'test_nsx_edge_lb_get_pool',
    # 'test_nsx_edge_lb_add_pool',
    # 'test_nsx_edge_lb_add_pool_member',
    # 'test_nsx_edge_lb_delete_pool',
    # 'test_nsx_edge_lb_delete_all_pools',
    # 'test_nsx_edge_lb_list_virtual_servers',
    # 'test_nsx_edge_lb_get_virtual_server'
    # 'test_nsx_edge_lb_delete',

    ## delete edge

    # 'test_nsx_delete_edge',
]


class VsphereClientTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()
        env = 'test'
        # env = 'podvc'
        # print("sono qui" + env)
        # print(cls.platform)
        params = cls.platform.get('vsphere').get(env)
        # params = cls.platform
        # print("params -->" + params)
        cls.params = params
        cls.client = VsphereManager(params.get('vcenter', None), params.get('nsxmanager', None), key=None)

    def tearDown(self):
        BeedronesTestCase.tearDown(self)

    def wait_task(self, task):
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            self.logger.info(task.info.state)
            gevent.sleep(1)

        if task.info.state in [vim.TaskInfo.State.error]:
            self.logger.info("Error: %s" % task.info.error.msg)
        if task.info.state in [vim.TaskInfo.State.success]:
            self.logger.info("Completed")

    #
    # system nsx
    #
    def test_nsx_global_info(self):
        res = self.client.system.nsx.global_info()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_summary_info(self):
        res = self.client.system.nsx.summary_info()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_reboot_appliance(self):
        res = self.client.system.nsx.reboot_appliance()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_cpu(self):
        res = self.client.system.nsx.query_appliance_cpu()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_uptime(self):
        res = self.client.system.nsx.query_appliance_uptime()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_memory(self):
        res = self.client.system.nsx.query_appliance_memory()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_storage(self):
        res = self.client.system.nsx.query_appliance_storage()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_network(self):
        res = self.client.system.nsx.query_appliance_network()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_configure_appliance_dns(self):
        res = self.client.system.nsx.configure_appliance_dns()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_delete_appliance_dns(self):
        res = self.client.system.nsx.delete_appliance_dns()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_time_settings(self):
        res = self.client.system.nsx.query_appliance_time_settings()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_configure_appliance_time_settings(self):
        res = self.client.system.nsx.configure_appliance_time_settings()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_delete_appliance_time_settings(self):
        res = self.client.system.nsx.delete_appliance_time_settings()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_local(self):
        res = self.client.system.nsx.query_appliance_local()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_configure_appliance_local(self):
        res = self.client.system.nsx.configure_appliance_local()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_syslog(self):
        res = self.client.system.nsx.query_appliance_syslog()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_configure_appliance_syslog(self):
        res = self.client.system.nsx.configure_appliance_syslog()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_delete_appliance_syslog(self):
        res = self.client.system.nsx.delete_appliance_syslog()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_components_summary(self):
        res = self.client.system.nsx.components_summary()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_components(self):
        res = self.client.system.nsx.query_appliance_components()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_component(self):
        component = 'NSX'
        res = self.client.system.nsx.query_appliance_component(component)
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_component_dependency(self):
        component = 'NSX'
        res = self.client.system.nsx.query_appliance_component_dependency(component)
        self.logger.info(self.pp.pformat(res))

    def test_nsx_query_appliance_component_status(self):
        component = 'NSX'
        res = self.client.system.nsx.query_appliance_component_status(component)
        self.logger.info(self.pp.pformat(res))

    def test_nsx_toggle_appliance_component_status(self):
        component = 'NSX'
        res = self.client.system.nsx.toggle_appliance_component_status(component)
        self.logger.info(self.pp.pformat(res))

    def test_nsx_restart_appliance_webapp(self):
        res = self.client.system.nsx.restart_appliance_webapp()
        self.logger.info(self.pp.pformat(res))

    def test_nsx_get_system_events(self):
        res = self.client.system.nsx.get_system_events(page_size=5)
        self.logger.info(self.pp.pformat(res))

    def test_nsx_get_system_audit_logs(self):
        res = self.client.system.nsx.get_system_audit_logs()
        self.logger.info(self.pp.pformat(res))

    def test_get_nsx_transport_zones(self):
        res = self.client.system.nsx.list_transport_zones()
        self.logger.info(res)

    #
    # nsx controller
    #
    def test_list_controllers(self):
        res = self.client.system.nsx.list_controllers()
        self.logger.info(res)

    #
    # nsx SSLVPN
    #
    def test_sslvpn_get(self):
        global edgeid
        res = self.client.network.nsx.edge.sslvpn(edgeid)
        self.logger.info(res)

    def test_sslvpn_enable(self):
        global edgeid
        res = self.client.network.nsx.edge.sslvpn_enable(edgeid)
        self.logger.info(res)

    def test_sslvpn_disable(self):
        global edgeid
        res = self.client.network.nsx.edge.sslvpn_disable(edgeid)
        self.logger.info(res)

    def test_sslvpn_session_get(self):
        global edgeid
        res = self.client.network.nsx.edge.sslvpn_session_get(edgeid)
        self.logger.info(res)

    def test_sslvpn_user_get(self):
        global edgeid
        res = self.client.network.nsx.edge.sslvpn_user_get(edgeid)
        self.logger.info(res)

        pass

    def test_sslvpn_user_modify(self):
        global edgeid
        user = 'mikovpn'

        res = self.client.network.nsx.edge.sslvpn_user_modify(edgeid, user,
                                                              description='CSI User', last_name='Bello')
        self.logger.info(res)

    def test_sslvpn_private_network_modify(self):
        global edgeid

        res = self.client.network.nsx.edge.sslvpn_private_network_modify(edgeid, network_cidr='172.25.6.0/24',
                                                                         optimize=True)
        self.logger.info(res)


        pass


    # test_sslvpn_enable

    #
    # network
    #
    def test_list_distributed_virtual_switches(self):
        res = self.client.network.list_distributed_virtual_switches()
        self.logger.info(self.pp.pformat(res))

    def test_get_distributed_virtual_switch(self):
        res = self.client.network.get_distributed_virtual_switch('dvs-21')
        self.logger.info(self.pp.pformat(res))
        self.logger.info(self.client.network.detail_distributed_virtual_switch(res))

    def test_list_networks(self):
        res = self.client.network.list_networks()
        self.logger.info(self.pp.pformat(res))

    def test_get_network(self):
        network = self.client.network.get_network('dvportgroup-12133')
        info = self.client.network.detail_network(network)
        self.logger.info(self.pp.pformat(info))

    def test_get_network_servers(self):
        servers = self.client.network.get_network_servers('dvportgroup-12133')
        self.logger.info(self.pp.pformat(servers))

    def test_create_network(self):
        name = 'network-test-01'
        desc = name
        vlan = 1567
        dvs = self.client.network.get_distributed_virtual_switch('dvs-21')
        numports = 24
        res = self.client.network.create_distributed_port_group(name, desc, vlan, dvs, numports)
        self.logger.info(res)

    def test_delete_network(self):
        res = self.client.network.list_networks()
        net = [n for n in res if n['name'] == 'network-test-01']
        oid = net[0]['obj']._moId
        network = self.client.network.get_network(oid)
        res = self.client.network.remove_network(network)
        self.logger.info(res)

    #
    # network nsx logical switch
    #    
    def test_nsx_list_logical_switches(self):
        res = self.client.network.nsx.lg.list()
        self.logger.info(res)

    def test_nsx_list_logical_switch(self):
        res = self.client.network.nsx.lg.get('virtualwire-1')
        self.logger.info(res)

    def test_nsx_create_logical_switch(self):
        scope_id = 'vdnscope-1'
        name = 'prova_net-intermedia_by_API'
        desc = name
        res = self.client.network.nsx.lg.create(scope_id, name, desc)
        self.logger.info(res)

    def test_nsx_delete_logical_switch(self):
        lgs = [lg for lg in self.client.network.nsx.lg.list() if lg['description'] == 'prova_net-intermedia_by_API']
        oid = lgs[0]['objectId']
        res = self.client.network.nsx.lg.delete(oid)
        self.logger.info(res)

        #

    # network nsx security group
    #        
    def test_nsx_list_security_group(self):
        res = self.client.network.nsx.sg.list()
        self.logger.info(res)

    def test_nsx_list_security_group_by_server(self):
        res = self.client.network.nsx.sg.list_by_server('vm-150')
        self.logger.info(res)

    def test_nsx_security_group_create(self):
        global oid
        res = self.client.network.nsx.sg.create('prova123')
        self.logger.info(res)
        oid = res

    def test_nsx_security_group_delete(self):
        global oid
        res = self.client.network.nsx.sg.delete(oid)
        self.logger.info(res)

    def test_nsx_get_security_group(self):
        global oid
        res = self.client.network.nsx.sg.get(oid)
        self.logger.info(res)

    def test_nsx_get_allowed_member_type(self):
        global oid
        res = self.client.network.nsx.sg.get_allowed_member_type(oid)
        self.logger.info(res)

    def test_nsx_update_security_group(self):
        global oid
        res = self.client.network.nsx.sg.update(oid)
        self.logger.info(res)

    def test_nsx_security_group_add_member(self):
        global oid
        res = self.client.network.nsx.sg.add_member(oid, 'ipset-1')
        self.logger.info(res)

    def test_nsx_security_group_delete_member(self):
        global oid
        res = self.client.network.nsx.sg.delete_member(oid, 'ipset-1')
        self.logger.info(res)

    #
    # network nsx ippool
    #
    def test_nsx_list_ippool(self):
        res = self.client.network.nsx.ippool.list()
        self.logger.info(res)
        global oid
        oid = res[0]['objectId']

    def test_nsx_get_ippool(self):
        global oid
        res = self.client.network.nsx.ippool.get(oid)
        self.logger.info(res)

    def test_nsx_create_ippool(self):
        global oid
        res = self.client.network.nsx.ippool.create('prova-ippool', prefix=24, dnssuffix='tstsddc.csi.it',
                                                    dns1='10.102.184.2', dns2='10.102.184.3', startip='10.102.185.50',
                                                    stopip='10.102.185.60', gateway='10.102.185.1')
        self.logger.info(res)
        oid = res

    def test_nsx_update_ippool(self):
        global oid
        res = self.client.network.nsx.ippool.update(oid, gateway='10.102.185.254')
        self.logger.info(res)

    def test_nsx_delete_ippool(self):
        global oid
        res = self.client.network.nsx.ippool.delete(oid)
        self.logger.info(res)

    def test_nsx_ippool_allocate_ip(self):
        global oid
        res = self.client.network.nsx.ippool.allocate(oid)
        self.logger.info(res)

    def test_nsx_ippool_release_ip(self):
        global oid
        res = self.client.network.nsx.ippool.release(oid, "10.102.185.50")
        self.logger.info(res)

    def test_nsx_ippool_allocations(self):
        global oid
        res = self.client.network.nsx.ippool.allocations(oid)
        self.logger.info(res)

    #
    # network nsx ipset
    #        
    def test_nsx_list_ipset(self):
        res = self.client.network.nsx.ipset.list()
        self.logger.info(res)

    def test_nsx_get_ipset(self):
        global oid
        res = self.client.network.nsx.ipset.get(oid)
        self.logger.info(res)

    def test_nsx_create_ipset(self):
        global oid
        res = self.client.network.nsx.ipset.create('prova_ipset', 'prova_ipset', '158.102.160.50/32,158.102.160.215/32')
        self.logger.info(res)
        oid = res

    def test_nsx_update_ipset(self):
        global oid
        res = self.client.network.nsx.ipset.update(oid, None, None, '158.102.160.0/24')
        self.logger.info(res)

    def test_nsx_delete_ipset(self):
        global oid
        res = self.client.network.nsx.ipset.delete(oid)
        self.logger.info(res)

    #
    # network nsx service
    #        
    def test_nsx_list_service(self):
        res = self.client.network.nsx.service.list()
        self.logger.info(res)

    def test_nsx_get_service(self):
        res = self.client.network.nsx.service.get('TCP', '8080')
        self.logger.info(res)

    def test_nsx_create_service(self):
        global oid
        protocol = 'TCP'
        ports = '4000-4001'
        name = 'tcp-4000'
        desc = 'tcp 4000-4001'
        res = self.client.network.nsx.service.create(protocol, ports, name, desc)
        self.logger.info(res)
        oid = res

    def test_nsx_delete_service(self):
        global oid
        res = self.client.network.nsx.service.delete(oid)
        self.logger.info(res)

    #
    # network nsx dlr
    #    
    def test_nsx_list_all_dlr(self):
        res = self.client.network.nsx.dlr.list()
        self.logger.info(res)

    def test_nsx_get_dlr(self):
        res = self.client.network.nsx.dlr.get('edge-10')
        self.logger.info(res)

    #
    # network nsx edge
    #
    def __wait_from_edge_job(self, nsx_jobid, edge, operation):
        res = self.client.network.nsx.edge.get_job(nsx_jobid)
        status = res['status']
        elapsed = 0
        while status not in ['COMPLETED', 'FAILED', 'ROLLBACK', 'TIMEOUT']:
            self.logger.info('wait for edge job: %s' % nsx_jobid)
            sleep(5)
            res = self.client.network.nsx.edge.get_job(nsx_jobid)
            status = res['status']
            elapsed += 5
            if elapsed > 600:
                status = 'TIMEOUT'
        self.logger.info('%s edge %s %s' % (operation, edge, status))

    def test_nsx_list_all_edge(self):
        global oid
        res = self.client.network.nsx.edge.list()
        self.logger.info(res)
        oid = res[0]['objectId']

    def test_nsx_get_edge(self):
        global oid
        res = self.client.network.nsx.edge.get(oid)
        self.logger.info(res)

    def test_nsx_add_edge(self):
        global edgeid
        kvargs = {
            'datacenterMoid': 'datacenter-2',
            'name': 'edge-prova-01',
            'tenant': 'tenant',
            'fqdn': 'edge-prova-01.tstsddc.csi.it',
            'appliances': [{
                'resourcePoolId': 'resgroup-130',
                'datastoreId': 'datastore-31',
            }],
            'vnics': [{
                'type': 'Uplink',
                'portgroupId': 'dvportgroup-1386',
                'addressGroups': [{
                    'primaryAddress': '192.168.3.2',
                    'subnetPrefixLength': 24
                }],
            }],
            'password': 'di12hEr8$DRtkc89eks0',
            'primaryDns': '10.101.0.10',
            'domainName': 'tstsddc.csi.it'
        }
        res = self.client.network.nsx.edge.add(kvargs)
        job = self.client.network.nsx.edge.get_job(res)
        edgeid = job['result'][0]['value']
        self.logger.info(edgeid)
        self.__wait_from_edge_job(res, edgeid, 'create')

    def test_nsx_get_edge_detail(self):
        global edgeid
        res = self.client.network.nsx.edge.get(edgeid)
        res = self.client.network.nsx.edge.detail(res)
        self.logger.info(res)

    def test_nsx_get_edge_appliances(self):
        global edgeid
        res = self.client.network.nsx.edge.get(edgeid)
        res = self.client.network.nsx.edge.appliances(res)
        self.logger.info(res)

    def test_nsx_get_edge_reset_pwd(self):
        global edgeid
        res = self.client.network.nsx.edge.reset_password(edgeid, 'di12hEr8$DRtkc89eks0sd')
        self.logger.info(res)

    def test_nsx_get_edge_firewall_rules(self):
        global edgeid
        res = self.client.network.nsx.edge.get(edgeid)
        res = self.client.network.nsx.edge.firewall_rules(res)
        self.logger.info(res)

    def test_nsx_add_edge_firewall_rules(self):
        global edgeid
        source = ['ip:10.10.13.34']
        res = self.client.network.nsx.edge.firewall_rule_add(edgeid, 'rule01', 'accept', logged=True, desc=None,
                                                             enabled=True, source=source, dest=None, application=None,
                                                             direction=None)
        self.logger.info(res)

    def test_nsx_del_edge_firewall_rules(self):
        global edgeid, ruleid
        res = self.client.network.nsx.edge.firewall_rule_delete(edgeid, ruleid)
        self.logger.info(res)

    def test_nsx_get_edge_nat_rules(self):
        global edgeid
        res = self.client.network.nsx.edge.get(edgeid)
        res = self.client.network.nsx.edge.nat(res)
        self.logger.info(res)

    def test_nsx_add_edge_nat_rules(self):
        global edgeid
        desc = 'nat-prova-01'
        action = 'dnat'
        original_address = '10.10.13.34'
        translated_address = '10.101.13.34'
        res = self.client.network.nsx.edge.nat_rule_add(edgeid, desc, action, original_address, translated_address,
                                                        logged=True, enabled=True, protocol=None, vnic=0,
                                                        translated_port=None, original_port=None)
        self.logger.info(res)

    def test_nsx_del_edge_nat_rules(self):
        global edgeid, ruleid
        res = self.client.network.nsx.edge.nat_rule_delete(edgeid, ruleid)
        self.logger.info(res)

    def test_nsx_get_edge_routing(self):
        global edgeid
        res = self.client.network.nsx.edge.get(edgeid)
        res = self.client.network.nsx.edge.route(res)
        self.logger.info(res)
        res = self.client.network.nsx.edge.route_static_get(edgeid)
        self.logger.info(res)

    def test_nsx_add_edge_default_route(self):
        global edgeid
        res = self.client.network.nsx.edge.route_default_add(edgeid, '192.168.3.1')
        self.logger.info(res)

    def test_nsx_add_edge_static_route(self):
        global edgeid
        res = self.client.network.nsx.edge.route_static_add(edgeid, 'route-test-01', '10.10.13.0/24', '192.168.3.1')
        self.logger.info(res)

    def test_nsx_del_edge_static_route(self):
        global edgeid
        res = self.client.network.nsx.edge.route_static_del(edgeid, '10.10.13.0/24', '192.168.3.1')
        self.logger.info(res)

    def test_nsx_add_edge_vnic(self):
        global edgeid
        kvargs = {
            'index': 1,
            'type': 'Internal',
            'portgroupId': 'dvportgroup-2054',
            'addressGroups': [{
                'primaryAddress': '192.169.3.2',
                'subnetPrefixLength': 24
            }]
        }
        res = self.client.network.nsx.edge.vnic_add(edgeid, kvargs)
        self.logger.info(res)

    def test_nsx_delete_edge(self):
        global edgeid
        res = self.client.network.nsx.edge.delete(edgeid)
        self.logger.info(res)
        self.__wait_from_edge_job(res, edgeid, 'delete')

    #
    # network nsx edge load balancing
    #        
    def test_nsx_edge_lb_get_config(self):
        res = self.client.network.nsx.edge.lb.get_config('edge-57')
        self.logger.info(res)

    def test_nsx_edge_lb_enable_true(self):
        res = self.client.network.nsx.edge.lb.update_global_config('edge-57', edgeLogging='true',
                                                                   edgeLogLevel='warning',
                                                                   accelerationEnabled='true')
        self.logger.info(res)

    def test_nsx_edge_lb_enable_false(self):
        res = self.client.network.nsx.edge.lb.update_global_config('edge-57', enable='False')
        self.logger.info(res)

    def test_nsx_edge_lb_list_app_profile(self):
        res = self.client.network.nsx.edge.lb.list_app_profile('edge-57')
        self.logger.info(res)

    def test_nsx_edge_lb_get_app_profiles(self):
        res = self.client.network.nsx.edge.lb.get_app_profile('edge-57', 'applicationProfile-19')
        self.logger.info(res)

    def test_nsx_edge_lb_add_app_profile(self):
        res = self.client.network.nsx.edge.lb.add_app_profile('edge-57', 'TCP', 'msrdp_by_api', persistence='msrdp',
                                                              expire=120)
        self.logger.info(res)

    def test_nsx_edge_lb_update_app_profile(self):
        res = self.client.network.nsx.edge.lb.update_app_profile('edge-57', 'applicationProfile-42',
                                                                 name="pluto e minnie", persistence='sourceip',
                                                                 expire='2010')
        self.logger.info(res)

    def test_nsx_edge_lb_del_app_profile(self):
        res = self.client.network.nsx.edge.lb.del_app_profile('edge-57', 'applicationProfile-39')
        self.logger.info(res)

    def test_nsx_edge_lb_del_all_app_profiles(self):
        res = self.client.network.nsx.edge.lb.del_all_app_profiles('edge-57')
        self.logger.info(res)

    def test_nsx_edge_lb_list_pools(self):
        res = self.client.network.nsx.edge.lb.list_pools('edge-57')
        self.logger.info(res)

    def test_nsx_edge_lb_get_pool(self):
        res = self.client.network.nsx.edge.lb.get_pool('edge-57', 'pool-2')
        self.logger.info(res)

    def test_nsx_edge_lb_add_pool(self):
        res = self.client.network.nsx.edge.lb.add_pool('edge-57', 'prova_by_api4', 'URl',
                                                       algorithmParameters='urlParam=http://pippo.com')
        self.logger.info(res)

    def test_nsx_edge_lb_add_pool_member(self):
        res = self.client.network.nsx.edge.lb.add_pool_member('edge-57', 'pool-2', ipAddress='10.102.189.17',
                                                              monitorPort='80', name='server3')
        self.logger.info(res)

    def test_nsx_edge_lb_delete_pool(self):
        res = self.client.network.nsx.edge.lb.del_pool('edge-57', 'pool-26')
        self.logger.info(res)

    def test_nsx_edge_lb_delete_all_pools(self):
        res = self.client.network.nsx.edge.lb.del_all_pools('edge-57')
        self.logger.info(res)

    def test_nsx_edge_lb_list_virtual_servers(self):
        res = self.client.network.nsx.edge.lb.list_virt_servers('edge-57')
        self.logger.info(res)

    def test_nsx_edge_lb_get_virtual_server(self):
        res = self.client.network.nsx.edge.lb.get_virt_server('edge-57', 'virtualServer-4')
        self.logger.info(res)

    def test_nsx_edge_lb_delete(self):
        res = self.client.network.nsx.edge.lb.delete('edge-57')
        self.logger.info(res)

    #
    # network nsx dfw
    #
    def test_nsx_list_all_dfw_rules(self):
        res = self.client.network.nsx.dfw.get_config()
        self.logger.info(res)

    def test_nsx_get_sections(self):
        global oid
        res = self.client.network.nsx.dfw.get_sections(rule_type='LAYER3')
        self.logger.info(res)
        res = dict_get(res, 'layer3Sections.section')
        oid = res[0]['id']

    def test_nsx_get_dfw_section(self):
        global oid, rid
        res = self.client.network.nsx.dfw.get_layer3_section(oid)
        # self.client.network.nsx.dfw.print_section(res, table=False)
        self.logger.info(res)
        rid = res['rule'][0]['id']

    def test_nsx_get_dfw_rule(self):
        global oid, rid
        res = self.client.network.nsx.dfw.get_rule(oid, rid)
        # self.client.network.nsx.dfw.print_rule(res)
        self.logger.info(res)

    def test_nsx_filter_dfw_rules(self):
        res = self.client.network.nsx.dfw.filter_rules(security_groups=['securitygroup-23'])
        # self.client.network.nsx.dfw.print_rule(res)
        self.logger.info(res)

    def test_nsx_create_dfw_section(self):
        global oid
        self.client.network.nsx.dfw.query_status()  # get etag
        res = self.client.network.nsx.dfw.create_section('prova', action='allow', logged=False)
        self.logger.info(res)
        oid = res['id']

    def test_nsx_delete_dfw_section(self):
        global oid
        res = self.client.network.nsx.dfw.delete_section(oid)
        self.logger.info(res)

    def test_nsx_create_dfw_rule(self):
        global oid, rid
        source = None
        destination = None
        # service = [{'port':'*', 'protocol':'*'}] # -> *:*
        # service = [{'port':'*', 'protocol':6}] # -> tcp:*
        # service = [{'port':80, 'protocol':6}] # -> tcp:80
        # service = [{'port':80, 'protocol':17}] # -> udp:80
        service = [{'protocol': 1, 'subprotocol': 8}]  # -> icmp:echo request
        appliedto = None
        res = self.client.network.nsx.dfw.create_rule(oid, 'prova', 'allow', 'out', False, source, destination,
                                                      service, appliedto)
        self.logger.info(res)
        rid = res['id']

    def test_nsx_create_dfw_rule_deny_isolotti(self):
        source = [{'name': None, 'value': 'securitygroup-1120', 'type': 'SecurityGroup'}]
        destination = [{'name': None, 'value': 'securitygroup-1120', 'type': 'SecurityGroup'}]
        appliedto = [{'name': None, 'value': 'securitygroup-1120', 'type': 'SecurityGroup'}]
        service = None
        res = self.client.network.nsx.dfw.create_rule('1028', 'deny_csi', 'deny', 'in', False, source, destination,
                                                      service, appliedto)
        self.logger.info(res)

    def test_nsx_create_dfw_rule_158(self):
        source = [{'name': None, 'value': '158.102.160.0/24', 'type': 'Ipv4Address'}]
        destination = [{'name': 'ISOLOTTI', 'value': 'securitygroup-29', 'type': 'SecurityGroup'}]
        appliedto = [{'name': 'ISOLOTTI', 'value': 'securitygroup-29', 'type': 'SecurityGroup'}]
        service = None
        res = self.client.network.nsx.dfw.create_rule('1022', 'enable-158', 'allow', 'inout', False, source,
                                                      destination, service, appliedto)
        self.logger.info(res)

    def test_nsx_create_dfw_rule_allow_demo(self):
        source = [{'name': 'DEMO', 'value': 'securitygroup-30', 'type': 'SecurityGroup'}]
        destination = [{'name': 'DEMO', 'value': 'securitygroup-30', 'type': 'SecurityGroup'}]
        appliedto = [{'name': 'DEMO', 'value': 'securitygroup-30', 'type': 'SecurityGroup'}]
        service = None
        res = self.client.network.nsx.dfw.create_rule('1022', 'allow_demo', 'allow', 'inout', False, source,
                                                      destination, service, appliedto)
        self.logger.info(res)

    def test_nsx_update_dfw_rule(self):
        global oid, rid
        res = self.client.network.nsx.dfw.update_rule(oid, rid, new_name='prova1')
        self.logger.info(res)

    def test_nsx_move_dfw_rule(self):
        global oid, rid
        self.client.network.nsx.dfw.query_status()  # get etag
        res = self.client.network.nsx.dfw.move_rule('1022', '133065', ruleafter='133067')
        self.logger.info(res)

    def test_nsx_delete_dfw_rule(self):
        global oid, rid
        self.client.network.nsx.dfw.query_status()  # get etag
        res = self.client.network.nsx.dfw.delete_rule(oid, rid)
        self.logger.info(res)

    def test_nsx_get_exclusion_list(self):
        self.client.network.nsx.dfw.query_status()  # get etag
        res = self.client.network.nsx.dfw.get_exclusion_list()
        self.logger.info(res)

    #
    # vsphere manager
    #
    def test_ping(self):
        res = self.client.ping()
        self.assertEquals(res, True)

    def test_version(self):
        res = self.client.version()

    def test_ping_vsphere(self):
        res = self.client.system.ping_vsphere()
        self.assertEquals(res, True)

    def test_ping_nsx(self):
        res = self.client.system.ping_nsx()
        self.assertEquals(res, True)

    #
    # virtual app
    #  
    def test_list_virtualapp(self):
        apps = self.client.vapp.list()
        self.logger.info(apps)

    def test_get_virtualapp(self):
        app = self.client.vapp.get_by_morid('vapp-533')
        info = self.client.vapp.info(app)
        self.logger.info(self.pp.pformat(info))

        #

    # server
    #  
    def test_list_servers(self):
        vms = self.client.server.list(template=False)
        self.logger.info(self.pp.pformat(vms))
        for vm in vms:
            self.logger.info(self.pp.pformat(self.client.server.info(vm)))

    def test_get_server(self):
        server = self.client.server.get_by_morid('vm-84')
        info = self.client.server.detail(server)
        self.logger.info(self.pp.pformat(info))

    def test_get_server_hardware(self):
        server = self.client.server.get_by_morid('vm-84')
        info = self.client.server.hardware.info(server)
        self.logger.info(self.pp.pformat(info))

    def test_get_server_devices(self):
        server = self.client.server.get_by_morid('vm-84')
        info = self.client.server.hardware.get_devices(server, dev_type='vim.vm.device.VirtualVmxnet3')
        self.logger.info(self.pp.pformat(info))

    def test_get_server_guest_info(self):
        server = self.client.server.get_by_morid('vm-84')
        info = self.client.server.guest_info(server)
        self.logger.info(self.pp.pformat(info))

    def test_get_server_runtime(self):
        server = self.client.server.get_by_morid('vm-84')
        info = self.client.server.runtime(server)
        self.logger.info(self.pp.pformat(info))

    def test_get_server_usage(self):
        server = self.client.server.get_by_morid('vm-84')
        info = self.client.server.usage(server)
        self.logger.info(self.pp.pformat(info))

    # def test_assign_server_tag(self):
    #     server = self.client.server.get_by_morid('vm-84')
    #     info = self.client.server.assign_tag(server, 'tag1')
    #     self.logger.info(self.pp.pformat(info))
    #
    # def test_get_server_tags(self):
    #     server = self.client.server.get_by_morid('vm-84')
    #     info = self.client.server.get_tags(server)
    #     self.logger.info(self.pp.pformat(info))

    def test_get_server_permissions(self):
        server = self.client.server.get_by_morid('vm-84')
        info = self.client.server.permissions(server)
        self.logger.info(self.pp.pformat(info))

    def test_get_server_remote_console(self):
        server = self.client.server.get_by_morid('vm-84')
        info = self.client.server.remote_console(server)
        self.logger.info(self.pp.pformat(info))

    def test_get_server_security_groups(self):
        server = self.client.server.get_by_morid('vm-84')
        info = self.client.server.security_groups(server)
        self.logger.info(self.pp.pformat(info))

    def test_get_server_by_dnsname(self):
        name = 'nsx-controller'
        vm = self.client.server.get_by_dnsname(name)
        self.logger.info(vm._moId)

    def test_get_server_by_ip(self):
        name = '10.102.184.100'
        vm = self.client.server.get_by_ip(name)
        self.logger.info(vm._moId)

    def test_get_server_network(self):
        server = self.client.server.get_by_morid('vm-84')
        net = self.client.server.network(server)
        self.logger.info(net)

    #
    # server create, delete
    #
    def __get_server(self, name):
        return self.client.server.list(name=name)[0]

    def test_create_server(self):
        name = 'vm-prova-01'
        guest_id = 'windows9Server64Guest'
        folder = self.client.folder.get('group-v3')
        datastore = self.client.datastore.get('datastore-31').name
        cluster = self.client.cluster.get('domain-c129')
        network = self.client.network.get_network('dvportgroup-2054')
        task = self.client.server.create(name, guest_id, datastore, folder, network, memory_mb=2048, cpu=2,
                                         core_x_socket=1, disk_size_gb=40, version='vmx-13', cluster=cluster)
        self.wait_task(task)

    # def test_create_linked_clone(self):
    #     server = self.__get_server('vm-prova-01')
    #     name = 'vm-prova-02'
    #     folder = self.client.folder.get('group-v3')
    #     datastore = self.client.datastore.get('datastore-10')
    #     resource_pool = self.client.cluster.resource_pool.get('resgroup-45')
    #     self.logger.info('Attempt to create vm %s' % name)
    #     task = self.client.server.create_linked_clone(server, name, folder, datastore, resource_pool, power_on=False)
    #     self.wait_task(task)

    def test_create_from_template(self):
        template = self.client.server.get_by_morid('vm-187')
        name = 'vm-prova-01'
        folder = self.client.folder.get('group-v3')
        datastore = self.client.datastore.get('datastore-31')
        cluster = self.client.cluster.get('domain-c129')
        task = self.client.server.create_from_template(template, name, folder, datastore, cluster=cluster)
        self.wait_task(task)

    def test_update_server(self):
        server = self.__get_server('vm-prova-01')
        task = self.client.server.update(server, name='vm-prova-01', notes='notes')
        self.wait_task(task)

    def test_remove_server(self):
        server = self.__get_server('vm-prova-01')
        task = self.client.server.remove(server)
        self.wait_task(task)

    def test_start_server(self):
        server = self.__get_server('vm-prova-01')
        task = self.client.server.start(server)
        self.wait_task(task)

    def test_stop_server(self):
        server = self.__get_server('vm-prova-01')
        task = self.client.server.stop(server)
        self.wait_task(task)

    #
    # server guest
    #
    def test_server_guest_info(self):
        server = self.__get_server('vm-prova-01')
        res = self.client.server.guest_info(server)
        self.logger.info(res)

    def test_server_guest_list_process(self):
        server = self.__get_server('vm-prova-01')
        pwd = self.params.get('server_pwd')
        res = self.client.server.guest_list_process(server, 'root', pwd)
        self.logger.info(res)

    def test_server_guest_execute_command(self):
        ip = '172.25.5.154'
        nm = '255.255.255.0'
        gw = '172.25.5.18'
        cmd = '-e "TYPE=Ethernet\n' \
              'BOOTPROTO=static\n' \
              'IPV6INIT=no\n' \
              'DEVICE=eth0\n' \
              'ONBOOT=yes\n' \
              'IPADDR=%s\n' \
              'NETMASK=%s\n' \
              'GATEWAY=%s" > /tmp/ifcfg-eth0' % (ip, nm, gw)
        server = self.__get_server('vm-prova-01')
        pwd = self.params.get('server_pwd')
        proc = self.client.server.guest_execute_command(server, 'root', pwd, path_to_program='/bin/echo',
                                                        program_arguments=cmd)
        res = self.client.server.guest_list_process(server, 'root', pwd, pids=[int(proc)])
        self.logger.info(res)

    def test_server_guest_read_environment_variable(self):
        server = self.__get_server('vm-prova-01')
        pwd = self.params.get('server_pwd')
        res = self.client.server.guest_read_environment_variable(server, 'root', pwd)
        self.logger.info(res)

    def test_server_guest_setup_network(self):
        ip = '172.25.5.154'
        macaddr = ''
        gw = '172.25.5.18'
        dns = '10.101.0.10'
        dns_search = 'csi.it'
        hostname = 'prova1'
        server = self.__get_server('vm-prova-01')
        pwd = self.params.get('server_pwd')
        res = self.client.server.guest_setup_network(server, 'root', pwd, ip, macaddr, gw, hostname, dns, dns_search)
        self.logger.info(res)

    #
    # server hw
    #
    def test_add_server_disk(self):
        server = self.__get_server('vm-prova-01')
        disk_size = 10
        datastore = self.client.datastore.get('datastore-31')
        disk_unit_number = self.client.server.hardware.get_available_hard_disk_unit_number(server)
        task = self.client.server.hardware.add_hard_disk(server, disk_size, datastore, disk_type='thin',
                                                         disk_unit_number=disk_unit_number)
        self.wait_task(task)

    def test_remove_server_disk(self):
        server = self.__get_server('vm-prova-01')
        task = self.client.server.hardware.delete_hard_disk(server, 1)
        self.wait_task(task)

    def test_add_server_network(self):
        server = self.__get_server('vm-prova-01')
        network = self.client.network.get_network('dvportgroup-2054')
        task = self.client.server.hardware.add_network(server, network)
        self.wait_task(task)

    def test_update_server_network(self):
        server = self.__get_server('vm-prova-01')
        network = self.client.network.get_network('dvportgroup-2054')
        net_number = 1
        task = self.client.server.hardware.update_network(server, net_number, nic_connected=True, network=None)
        self.wait_task(task)

    def test_remove_server_network(self):
        server = self.__get_server('vm-prova-01')
        task = self.client.server.hardware.delete_network(server, 1)
        self.wait_task(task)

    def test_update_server_cdrom(self):
        server = self.__get_server('vm-prova-01')
        full_path_to_iso = "[DatastoreNFS-ISO] virtio-win-0.1.102.iso"
        full_path_to_iso = ""
        cdrom_number = 1
        task = self.client.server.hardware.update_cdrom(server, cdrom_number, full_path_to_iso)
        self.wait_task(task)

        #

    # server snapshot
    #
    def test_list_server_snapshot(self):
        server = self.__get_server('vm-prova-01')
        res = self.client.server.snapshot.list(server)
        self.logger.info(self.pp.pformat(res))

    def test_get_current_server_snapshot(self):
        server = self.__get_server('vm-prova-01')
        res = self.client.server.snapshot.get_current(server)
        self.logger.info(self.pp.pformat(res))

    def test_get_server_snapshot(self):
        server = self.__get_server('vm-prova-01')
        res = self.client.server.snapshot.get(server, 'snapshot-26729')
        self.logger.info(self.pp.pformat(res))

    def test_take_server_snapshot(self):
        server = self.__get_server('vm-prova-01')
        name = 'for_linked_clone'
        desc = 'for_linked_clone'
        memory = False
        quiesce = False
        task = self.client.server.snapshot.create(server, name, desc, memory, quiesce)
        self.wait_task(task)

    # def test_rename_server_snapshot(self):
    #     server = self.__get_server('vm-prova-01')
    #     self.client.server.snapshot.rename(server, 'snapshot-26729', 'snap-0000')

    def test_revert_server_snapshot(self):
        server = self.__get_server('vm-prova-01')
        task = self.client.server.snapshot.revert(server, 'snapshot-26729')
        self.wait_task(task)

    def test_delete_server_snapshot(self):
        server = self.__get_server('vm-prova-01')
        task = self.client.server.snapshot.remove(server, 'snapshot-26729')
        self.wait_task(task)

        #

    # datacenter
    #  
    def test_list_datacenters(self):
        dcs = self.client.datacenter.list()
        for dc in dcs:
            self.logger.info(dc)

    def test_get_datacenter(self):
        dc = self.client.datacenter.get('datacenter-2')
        info = self.client.datacenter.detail(dc)
        self.logger.info(self.pp.pformat(info))

    #
    # folder
    #  
    def test_list_folders(self):
        folders = self.client.folder.list()
        for folder in folders:
            self.logger.info(folder)

    def test_get_folder(self):
        global folder_id
        folder = self.client.folder.get(folder_id)
        info = self.client.folder.detail(folder)
        self.logger.info(self.pp.pformat(info))

    def test_create_folder(self):
        datacenter = self.client.datacenter.get('datacenter-2')
        folder = self.client.folder.create('prova', datacenter=datacenter, host=True)
        self.logger.info(folder._moId)
        global folder_id
        folder_id = folder._moId

    def test_update_folder(self):
        global folder_id
        folder = self.client.folder.get(folder_id)
        task = self.client.folder.update(folder, 'prova1')
        self.wait_task(task)

    def test_remove_folder(self):
        global folder_id
        folder = self.client.folder.get(folder_id)
        task = self.client.folder.remove(folder)
        self.wait_task(task)

    #
    # datastore
    #  
    def test_list_datastores(self):
        ds = self.client.datastore.list()
        self.logger.info(ds)

    def test_get_datastore(self):
        ds = self.client.datastore.get('datastore-22350')
        info = self.client.datastore.detail(ds)
        self.logger.info(self.pp.pformat(info))

    def test_get_datastore_hosts(self):
        ds = self.client.datastore.get('datastore-22350')
        info = self.client.datastore.get_hosts(ds)
        self.logger.info(self.pp.pformat(info))

    #
    # cluster
    #  
    def test_list_clusters(self):
        clus = self.client.cluster.list()
        for clu in clus:
            self.logger.info(clu)

    def test_get_cluster(self):
        clu = self.client.cluster.get('domain-c7')
        self.logger.info(clu._moId)
        self.logger.info(clu.resourcePool.resourcePool)

    def test_list_hosts(self):
        hs = self.client.cluster.host.list()
        for h in hs:
            self.logger.info(h)

    def test_get_host(self):
        h = self.client.cluster.host.get('host-131')
        self.logger.info(h)

    def test_list_resource_pools(self):
        rps = self.client.cluster.resource_pool.list()
        for rp in rps:
            self.logger.info(rp)

    def test_get_resource_pool(self):
        rp = self.client.cluster.resource_pool.get('resgroup-130')
        self.logger.info(self.client.cluster.resource_pool.detail(rp))

    def test_get_resource_pool_servers(self):
        servers = self.client.cluster.resource_pool.get_servers('resgroup-130')
        self.logger.info(servers)

    def test_create_resource_pool(self):
        cluster = self.client.cluster.get('domain-c7')
        name = 'prova-respool-01'
        cpu = 4000
        memory = 10240
        shares = 'normal'
        res = self.client.cluster.resource_pool.create(cluster, name, cpu, memory, shares)
        self.logger.info(res)
        global respool_id
        respool_id = res._moId

    def test_update_resource_pool(self):
        global respool_id
        respool = self.client.cluster.resource_pool.get(respool_id)
        name = 'prova-respool-02'
        cpu = 4000
        memory = 10240
        shares = 'normal'
        res = self.client.cluster.resource_pool.update(respool, name, cpu, memory, shares)
        self.logger.info(res)

    def test_delete_resource_pool(self):
        global respool_id
        respool = self.client.cluster.resource_pool.get(respool_id)
        res = self.client.cluster.resource_pool.remove(respool)
        self.logger.info(res)

    def test_list_cluster_servers(self):
        servers = self.client.cluster.get_servers('domain-c7')
        for server in servers:
            self.logger.info(server)


if __name__ == '__main__':
    runtest(VsphereClientTestCase, tests)
