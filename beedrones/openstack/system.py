# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

from beecell.simple import truncate
from beedrones.openstack.client import OpenstackClient, OpenstackObject, setup_client


VERSION_MAPPING = {
    '2.3': 'Kilo',
    '2.12': 'Liberty',
    '2.25': 'Mitaka',
    '2.38': 'Newton',
    '2.42': 'Ocata',
    '2.53': 'Pike',
    '2.60': 'Queens',
    '2.65': 'Rocky',
    '2.72': 'Stein',
    '2.79': 'Train',
}


class OpenstackSystemObject(OpenstackObject):
    def setup(self):
        self.compute = OpenstackClient(self.manager.endpoint('nova'), self.manager.proxy, timeout=self.manager.timeout)
        self.blockstore = OpenstackClient(self.manager.endpoint('cinderv2'), self.manager.proxy,
                                          timeout=self.manager.timeout)
        self.network = OpenstackClient(self.manager.endpoint('neutron'), self.manager.proxy,
                                       timeout=self.manager.timeout)
        self.heat = OpenstackClient(self.manager.endpoint('heat'), self.manager.proxy, timeout=self.manager.timeout)
        self.swift = OpenstackClient(self.manager.endpoint('swift'), self.manager.proxy, timeout=self.manager.timeout)
        self.manila = OpenstackClient(self.manager.endpoint('manilav2'), self.manager.proxy,
                                      timeout=self.manager.timeout)


class OpenstackSystem(OpenstackSystemObject):
    """
    """
    def __init__(self, manager):
        OpenstackSystemObject.__init__(self, manager)

    @setup_client
    def compute_api(self):
        """Get compute api versions.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = self.compute.path = '/'
        res = self.compute.call('', 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get compute api: %s' % truncate(res[0]))
        self.compute.path = path
        return res[0]

    def version(self):
        """Get openstack version.

        :return: openstack version
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        api_vers = self.compute_api().get('versions')
        current_api_ver = [ver['version'] for ver in api_vers if ver['status'] == 'CURRENT'][0]
        current_version = VERSION_MAPPING.get(current_api_ver, None)
        self.logger.debug('openstack version: %s' % current_version)
        return current_version

    @setup_client
    def storage_api(self):
        """Get storage api versions.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = self.blockstore.path = '/'
        res = self.blockstore.call('', 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get block storage api: %s' % truncate(res[0]))
        self.blockstore.path = path
        return res[0]

    @setup_client
    def object_storage_api(self):
        """Get storage api versions.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = self.swift.path = '/info'
        res = self.swift.call('', 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get object storage api: %s' % truncate(res[0]))
        self.swift.path = path
        return res[0]

    @setup_client
    def network_api(self):
        """Get network api versions.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = self.network.path = '/'
        res = self.network.call('', 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get network api: %s' % truncate(res[0]))
        self.network.path = path
        return res[0]

    @setup_client
    def network_api_extension(self):
        """Get network api extensions.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = self.network.path = '/v2.0/extensions'
        res = self.network.call('', 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get network api extensions: %s' % truncate(res[0]))
        self.network.path = path
        return res[0]

    @setup_client
    def orchestrator_api(self):
        """Get heat api versions.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = self.heat.path = '/'
        res = self.heat.call('', 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get orchestrator api: %s' % truncate(res[0]))
        self.heat.path = path
        return res[0]

    def manila_api(self):
        """Get manila api versions.

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = self.manila.path = '/'
        res = self.manila.call('', 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get manila api: %s' % truncate(res[0]))
        self.manila.path = path
        return res[0]

    @setup_client
    def compute_services(self):
        """Get compute service.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-services'
        res = self.compute.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack compute services: %s' % truncate(res[0]))
        return res[0]['services']

    @setup_client
    def compute_zones(self):
        """Get compute availability zones.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-availability-zone/detail'
        res = self.compute.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack availability zone: %s' % truncate(res[0]))
        return res[0]['availabilityZoneInfo']

    @setup_client
    def compute_hosts(self):
        """Get physical hosts.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-hosts'
        res = self.compute.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack hosts: %s' % truncate(res[0]))
        return res[0]['hosts']

    @setup_client
    def compute_host_status(self, host):
        """Set physical host status.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-hosts/%s' % host
        data = {
            "status": "enable",
            "maintenance_mode": "disable"
        }
        res = self.compute.call(path, 'PUT', data=data, token=self.manager.identity.token, timeout=300)
        self.logger.debug('Set openstack host status: %s' % truncate(res[0]))
        return res[0]['hosts']

    @setup_client
    def compute_host_aggregates(self):
        """Get compute host aggregates.
        An aggregate assigns metadata to groups of compute nodes. Aggregates 
        are only visible to the cloud provider.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-aggregates'
        res = self.compute.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack host aggregates: %s' % truncate(res[0]))
        return res[0]['aggregates']

    @setup_client
    def compute_server_groups(self):
        """Get compute server groups.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-server-groups'
        res = self.compute.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack server groups: %s' % truncate(res[0]))
        return res[0]['server_groups']

    @setup_client
    def compute_hypervisors(self):
        """Displays extra statistical information from the machine that hosts 
        the hypervisor through the API for the hypervisor (XenAPI or KVM/libvirt).

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-hypervisors/detail'
        res = self.compute.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack hypervisors: %s' % truncate(res[0]))
        return res[0]['hypervisors']

    @setup_client
    def compute_hypervisors_statistics(self):
        """Get compute hypervisors statistics.

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-hypervisors/statistics'
        res = self.compute.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack hypervisors statistics: %s' % truncate(res[0]))
        return res[0]['hypervisor_statistics']

    @setup_client
    def compute_agents(self):
        """Get compute agents.
        Use guest agents to access files on the disk, configure networking, and 
        run other applications and scripts in the guest while it runs. This 
        hypervisor-specific extension is not currently enabled for KVM. Use of 
        guest agents is possible only if the underlying service provider uses 
        the Xen driver.  

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-agents'
        res = self.compute.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack compute agents: %s' % truncate(res[0]))
        return res[0]['agents']

    @setup_client
    def storage_services(self):
        """Get storage service.  

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-services'
        res = self.blockstore.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack storage services: %s' % truncate(res[0]))
        return res[0]['services']

    @setup_client
    def network_agents(self):
        """Get network agents.

        :return:
           [...,
            {'admin_state_up': True,
              'agent_type': 'Metadata agent',
              'alive': True,
              'binary': 'neutron-metadata-agent',
              'configurations': {'log_agent_heartbeats': False,
                                  'metadata_proxy_socket': '/var/lib/neutron/metadata_proxy',
                                  'nova_metadata_ip': 'ctrl-liberty.nuvolacsi.it',
                                  'nova_metadata_port': 8775},
              'created_at': '2015-12-22 14:33:59',
              'description': None,
              'heartbeat_timestamp': '2016-05-08 16:21:55',
              'host': 'ctrl-liberty2.nuvolacsi.it',
              'id': 'e6c1e736-d25c-45e8-a475-126a13a07332',
              'started_at': '2016-04-29 21:31:22',
              'topic': 'N/A'},
             {'admin_state_up': True,
              'agent_type': 'Linux bridge agent',
              'alive': True,
              'binary': 'neutron-linuxbridge-agent',
              'configurations': {'bridge_mappings': {},
                                  'devices': 21,
                                  'interface_mappings': {'netall': 'enp10s0f1', 'public': 'enp10s0f1.62'},
                                  'l2_population': True,
                                  'tunnel_types': ['vxlan'],
                                  'tunneling_ip': '192.168.205.69'},
              'created_at': '2015-12-22 14:33:59',
              'description': None,
              'heartbeat_timestamp': '2016-05-08 16:21:55',
              'host': 'ctrl-liberty2.nuvolacsi.it',
              'id': 'eb1010c4-ad95-4d8c-b377-6fce6a78141e',
              'started_at': '2016-04-29 21:31:22',
              'topic': 'N/A'}]
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/v2.0/agents'
        res = self.network.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack network agents: %s' % truncate(res[0]))
        return res[0]['agents']

    @setup_client
    def network_service_providers(self):
        """Get network service providers.

        :return: [{'default': True, 
                   'name': 'haproxy', 
                   'service_type': 'LOADBALANCER'}]
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/v2.0/service-providers'
        res = self.network.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack network service providers: %s' % truncate(res[0]))
        return res[0]['service_providers']

    @setup_client
    def orchestrator_services(self):
        """Get heat services.

        :return: Ex.
              [{'binary': 'heat-engine',
                'created_at': '2016-04-29T20:52:52.000000',
                'deleted_at': None,
                'engine_id': 'c1942356-3cf2-4e45-af5e-75334d7e6263',
                'host': 'ctrl-liberty2.nuvolacsi.it',
                'hostname': 'ctrl-liberty2.nuvolacsi.it',
                'id': '07cf7fbc-22c3-4091-823c-12e297a0cc51',
                'report_interval': 60,
                'status': 'up',
                'topic': 'engine',
                'updated_at': '2016-05-09T12:19:55.000000'},
               {'binary': 'heat-engine',
                'created_at': '2016-04-29T20:52:52.000000',
                'deleted_at': None,
                'engine_id': 'd7316fa6-2e82-4fe0-94d2-09cbb5ad1bc6',
                'host': 'ctrl-liberty2.nuvolacsi.it',
                'hostname': 'ctrl-liberty2.nuvolacsi.it',
                'id': '0a40b1ef-91e8-4f63-8c0b-861dbbfdcf31',
                'report_interval': 60,
                'status': 'up',
                'topic': 'engine',
                'updated_at': '2016-05-09T12:19:58.000000'},..,]        
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/services"
        res = self.heat.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack orchestrator services: %s' % truncate(res[0]))
        return res[0]['services']
