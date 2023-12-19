# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import jsonDumps

import re
from copy import deepcopy

import ujson as json
from beecell.simple import truncate, set_request_params
from six.moves.urllib.parse import urlencode
from beedrones.openstack.client import (
    OpenstackClient,
    OpenstackError,
    OpenstackObject,
    setup_client,
)


class OpenstackNetworkObject(OpenstackObject):
    def setup(self):
        self.uri = self.manager.endpoint("neutron")
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)


class OpenstackNetwork(OpenstackNetworkObject):
    """ """

    def __init__(self, manager):
        OpenstackNetworkObject.__init__(self, manager)

        self.ver = "/v2.0"

        self.floatingip = OpenstackFloatingIp(self)
        self.subnet = OpenstackSubnet(self)
        self.port = OpenstackPort(self)
        self.router = OpenstackRouter(self)
        self.security_group = OpenstackSecurityGroup(self)
        self.fwaas = OpenstackFwaas2(self)

    @setup_client
    def list(
        self,
        tenant=None,
        limit=None,
        marker=None,
        shared=None,
        segmentation_id=None,
        network_type=None,
        external=None,
        physical_network=None,
    ):
        """list network

        :param tenant: tenant id
        :param limit:  Requests a page size of items. Returns a number of items
                       up to a limit value. Use the limit parameter to make an
                       initial limited request and use the ID of the last-seen
                       item from the response as the marker parameter value in
                       a subsequent limited request.
        :param marker: The ID of the last-seen item. Use the limit parameter
                       to make an initial limited request and use the ID of the
                       last-seen item from the response as the marker parameter
                       value in a subsequent limited request.
        :param segmentation_id: An isolated segment on the physical network.
                                The network_type attribute defines the
                                segmentation model. For example, if the
                                network_type value is vlan, this ID is a vlan
                                identifier. If the network_type value is gre,
                                this ID is a gre key. [optional]
        :param network_type: The type of physical network that maps to this
                             network resource. For example, flat, vlan, vxlan,
                             or gre. [optional]
        :param external: Indicates whether this network can provide floating IPs
                         via a router. [optional]
        :param shared: Indicates whether this network is shared
                       across all projects. [optional]
        :param physical_network: The physical network where this network object
                                 is implemented. The Networking API v2.0 does
                                 not provide a way to list available physical
                                 networks. For example, the Open vSwitch plug-in
                                 configuration file defines a symbolic name
                                 that maps to specific bridges on each Compute host.
        :return: Ex.

            [{'admin_state_up': True,
              'id': '622a06be-4f21-47fc-9df0-06c9c82fbc02',
              'mt': 0,
              'name': 'public',
              'port_security_enabled': True,
              'provider:network_type': 'flat',
              'provider:physical_network': 'public',
              'provider:segmentation_id': None,
              'router:external': True,
              'shared': True,
              'status': 'ACTIVE',
              'subnets': ['46620b60-76f6-4f1e-a754-dccfc50880c4'],
              'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}]

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/networks" % self.ver
        query = {}
        if tenant is not None:
            query["tenant_id"] = tenant
        if limit is not None:
            query["limit"] = limit
        if marker is not None:
            query["marker"] = marker
        if segmentation_id is not None:
            query["provider:segmentation_id"] = segmentation_id
        if network_type is not None:
            query["provider:network_type"] = network_type
        if external is not None:
            query["router:external"] = external
        if shared is not None:
            query["shared"] = shared
        if physical_network is not None:
            query["provider:physical_network"] = physical_network

        path = "%s?%s" % (path, urlencode(query))

        # get tenant network
        net = self.client.call(path, "GET", data="", token=self.manager.identity.token)

        res = net[0]["networks"]
        if tenant is not None:
            # get shared network
            path = "%s/networks?%s" % (self.ver, urlencode({"shared": True}))
            shared = self.client.call(path, "GET", data="", token=self.manager.identity.token)
            if len(shared) > 0:
                res.extend(shared[0]["networks"])
        self.logger.debug("Get openstack networks: %s" % truncate(res))
        return res

    @setup_client
    def get(self, oid=None, name=None):
        """
        :param oid: network id
        :param name: network name
        :return: Ex.

             {'admin_state_up': True,
              'id': '622a06be-4f21-47fc-9df0-06c9c82fbc02',
              'mt': 0,
              'name': 'public',
              'port_security_enabled': True,
              'provider:network_type': 'flat',
              'provider:physical_network': 'public',
              'provider:segmentation_id': None,
              'router:external': True,
              'shared': True,
              'status': 'ACTIVE',
              'subnets': ['46620b60-76f6-4f1e-a754-dccfc50880c4'],
              'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = "%s/networks/%s" % (self.ver, oid)
        elif name is not None:
            path = "%s/networks?name=%s" % (self.ver, name)
        else:
            raise OpenstackError("Specify at least network id or name")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack network: %s" % truncate(res[0]))
        if oid is not None:
            server = res[0]["network"]
        elif name is not None:
            server = res[0]["networks"][0]

        return server

    @setup_client
    def create(
        self,
        name,
        tenant_id,
        physical_network,
        shared=False,
        qos_policy_id=None,
        external=False,
        segments=None,
        network_type="vlan",
        segmentation_id=None,
        mtu=1450,
    ):
        """Creates a network.

        :param name str: The network name.
        :param shared bool: [default=false] Indicates whether this network is shared across all tenants. By default,
            only administrative users can change this value.
        :param tenant_id id: The UUID of the tenant that owns the network. This tenant can be different from the tenant
            that makes the create network request. However, only administrative users can specify a tenant UUID other
            than their own. You cannot change this value through authorization policies.
        :param qos_policy_id id: [optional] Admin-only. The UUID of the QoS policy associated with this network. The
            policy will need to have been created before the network to associate it with.
        :param external bool: [optional] Indicates whether this network is externally accessible.
        :param segments list: [optional] A list of provider segment objects.
        :param physical_network str: [optional] The physical network where this network object is implemented. The
            Networking API v2.0 does not provide a way to list available physical networks. For example, the Open
            vSwitch plug-in configuration file defines a symbolic name that maps to specific bridges on each Compute
            host.
        :param network_type str: [default=vlan] The type of physical network that maps to this network
            resource. For example, flat, vlan, vxlan, or gre.
        :param segmentation_id str: [optional] An isolated segment on the physical network. The network_type
            attribute defines the segmentation model. For example, if the network_type value is vlan, this ID is a vlan
            identifier. If the network_type value is gre, this ID is a gre key.
        :param mtu: the maximum transmission unit MTU [default=1450]
        :return: new network
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "network": {
                "name": name,
                "tenant_id": tenant_id,
                "admin_state_up": True,
                "port_security_enabled": True,
                "shared": shared,
                "router:external": external,
                "provider:network_type": network_type,
                "mtu": mtu,
            }
        }

        if physical_network is not None:
            data["network"]["provider:physical_network"] = physical_network
        if qos_policy_id is not None:
            data["network"]["qos_policy_id"] = qos_policy_id
        if segments is not None:
            data["network"]["segments"] = segments
        if segmentation_id is not None:
            data["network"]["provider:segmentation_id"] = segmentation_id

        path = "%s/networks" % self.ver
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Create openstack network: %s" % truncate(res[0]))
        return res[0]["network"]

    @setup_client
    def update(self, oid, name=None, shared=None, qos_policy_id=None, external=None, mtu=None):
        """Updates a network.

        :param name str: [optional] The network name.
        :param shared bool: [optional] Indicates whether this network is shared across all tenants. By default, only
            administrative users can change this value.
        :param qos_policy_id id: [optional] Admin-only. The UUID of the QoS policy associated with this network. The
            policy will need to have been created before the network to associate it with.
        :param external bool: [optional] Indicates whether this network is externally accessible.
        :param mtu: The maximum transmission unit (MTU) value to address fragmentation. Minimum value is 68 for IPv4,
            and 1280 for IPv6.
        :return: Ex.
            {'admin_state_up': True,
             'id': 'e96c7e29-2190-4fa0-8b8b-885a9dae6915',
             'mt': 0,
             'name': 'prova-net-02',
             'port_security_enabled': True,
             'provider:network_type': 'vlan',
             'provider:physical_network': 'netall',
             'provider:segmentation_id': 1900,
             'router:external': False,
             'shared': False,
             'status': 'ACTIVE',
             'subnets': [],
             'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"network": {"admin_state_up": True, "port_security_enabled": True}}

        if name is not None:
            data["network"]["name"] = name
        if shared is not None:
            data["network"]["shared"] = shared
        if external is not None:
            data["network"]["router:external"] = external
        # if physical_network is not None:
        #    data['network']['provider:physical_network'] = physical_network
        # if network_type is not None:
        #    data['network']['provider:network_type'] = network_type
        if qos_policy_id is not None:
            data["network"]["qos_policy_id"] = qos_policy_id
        if mtu is not None:
            data["network"]["mtu"] = mtu
        # if segmentation_id is not None:
        #    data['network']['provider:segmentation_id'] = segmentation_id

        path = "%s/networks/%s" % (self.ver, oid)
        res = self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Update openstack network: %s" % truncate(res[0]))
        return res[0]["network"]

    @setup_client
    def delete(self, oid):
        """Deletes a network and its associated resources.

        :param oid: network id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/networks/%s" % (self.ver, oid)
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack network: %s" % truncate(res[0]))
        return res[0]

    #
    # log
    #
    @setup_client
    def get_loggable_resources(self):
        """Lists all resource log types are supporting

        :return: Ex.

            [
                {
                    "type": "security_group"
                }
            ]

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/log/loggable-resources" % self.ver

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Lists all resource log types are supporting: %s" % truncate(res[0]))
        return res[0]["loggable_resources"]

    @setup_client
    def get_log_resources(self):
        """Lists all log resources associated with the projects

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/log/logs" % self.ver

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Lists all log resources associated with the projects: %s" % truncate(res[0]))
        return res[0]["logs"]

    #
    # actions
    #


class OpenstackSubnet(OpenstackNetworkObject):
    """ """

    def __init__(self, network):
        OpenstackNetworkObject.__init__(self, network.manager)

        self.ver = network.ver

    @setup_client
    def list(self, tenant=None, network=None, gateway_ip=None, cidr=None):
        """Lists subnets to which the tenant has access.

        :param tenant: tenant id
        :param network: The ID of the attached network.
        :param gateway_ip : The gateway IP address.
        :param cidr: The CIDR.
        :return: Ex.
            [{'allocation_pools': [{'end': '172.25.4.250', 'start': '172.25.4.201'}],
              'cidr': '172.25.4.0/24',
              'dns_nameservers': ['172.25.5.100'],
              'enable_dhcp': True,
              'gateway_ip': '172.25.4.2',
              'host_routes': [{'destination': '10.102.160.0/24', 'nexthop': '172.25.4.1'},
                               {'destination': '158.102.160.0/24', 'nexthop': '172.25.4.1'}],
              'id': 'f375e490-1103-4c00-9803-2703e3165271',
              'ip_version': 4,
              'ipv6_address_mode': None,
              'ipv6_ra_mode': None,
              'name': 'sub306',
              'network_id': '40803c62-f4b1-4afb-bd94-f773a5c70f7b',
              'subnetpool_id': None,
              'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'},...,
             ]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/subnets" % self.ver

        query = {}
        if tenant is not None:
            query["tenant_id"] = tenant
        if network is not None:
            query["network_id"] = network
        if gateway_ip is not None:
            query["gateway_ip"] = gateway_ip
        if cidr is not None:
            query["cidr"] = cidr
        path = "%s?%s" % (path, urlencode(query))

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack subnets: %s" % truncate(res[0]))
        return res[0]["subnets"]

    @setup_client
    def get(self, oid=None, name=None):
        """Shows details for a subnet.

        :param oid: network id
        :param name: network name
        :return: Ex.
             {'allocation_pools': [{'end': '172.25.4.250', 'start': '172.25.4.201'}],
              'cidr': '172.25.4.0/24',
              'dns_nameservers': ['172.25.5.100'],
              'enable_dhcp': True,
              'gateway_ip': '172.25.4.2',
              'host_routes': [{'destination': '10.102.160.0/24', 'nexthop': '172.25.4.1'},
                               {'destination': '158.102.160.0/24', 'nexthop': '172.25.4.1'}],
              'id': 'f375e490-1103-4c00-9803-2703e3165271',
              'ip_version': 4,
              'ipv6_address_mode': None,
              'ipv6_ra_mode': None,
              'name': 'sub306',
              'network_id': '40803c62-f4b1-4afb-bd94-f773a5c70f7b',
              'subnetpool_id': None,
              'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = "%s/subnets/%s" % (self.ver, oid)
        elif name is not None:
            path = "%s/subnets?display_name=%s" % (self.ver, name)
        else:
            raise OpenstackError("Specify at least subnet id or name")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack subnets: %s" % truncate(res[0]))
        if oid is not None:
            server = res[0]["subnet"]
        elif name is not None:
            server = res[0]["subnets"][0]

        return server

    @setup_client
    def create(
        self,
        name,
        network_id,
        tenant_id,
        gateway_ip,
        cidr,
        allocation_pools=None,
        enable_dhcp=True,
        host_routes=None,
        dns_nameservers=["8.8.8.7", "8.8.8.8"],
        service_types=None,
    ):
        """Creates a subnet on a network.

        :param name str: The subnet name.
        :param network_id id: The UUID of the attached network.
        :param tenant_id id: The UUID of the tenant who owns the network.
        :param gateway_ip: The gateway IP address.
        :param cidr:  The CIDR.
        :param allocation_pools: dict like
            {"allocation_pools":{"start":<start ip>,
                                 "end":<end ip>,}}
        :param enable_dhcp: [default=True] Set to true if DHCP is enabled and
            false if DHCP is disabled.
        :param dns_nameservers: [default=['8.8.8.7', '8.8.8.8'] A list of DNS
            name servers for the subnet. Specify each name server as an IP
            address and separate multiple entries with a space.
        :param host_routes:  A list of host route dictionaries for the subnet.
            For example:
            [
                {
                  "destination":"0.0.0.0/0",
                  "nexthop":"123.45.67.89"
                },
                {
                  "destination":"192.168.0.0/24",
                  "nexthop":"192.168.0.1"
                }
            ]
        :param service_types: The service types associated with the subnet. Ex. ['compute:nova'], ['compute:foo']
        :return: Ex.
            {'allocation_pools': [{'end': '10.108.1.254',
                                    'start': '10.108.1.2'}],
             'cidr': '10.108.1.0/24',
             'dns_nameservers': [],
             'enable_dhcp': True,
             'gateway_ip': '10.108.1.1',
             'host_routes': [{'destination': '0.0.0.0/0',
                               'nexthop': '123.45.67.89'},
                              {'destination': '192.168.0.0/24',
                               'nexthop': '192.168.0.1'}],
             'id': '340de24a-7ca9-42b1-bfec-699110485235',
             'ip_version': 4,
             'ipv6_address_mode': None,
             'ipv6_ra_mode': None,
             'name': 'prova-net-01-subnet',
             'network_id': 'e96c7e29-2190-4fa0-8b8b-885a9dae6915',
             'subnetpool_id': None,
             'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "subnet": {
                "name": name,
                "network_id": network_id,
                "tenant_id": tenant_id,
                "ip_version": 4,
                "cidr": cidr,
                "gateway_ip": gateway_ip,
            }
        }
        if allocation_pools is not None:
            data["subnet"]["allocation_pools"] = allocation_pools
        if host_routes is not None:
            data["subnet"]["host_routes"] = host_routes
        if enable_dhcp is not None:
            data["subnet"]["enable_dhcp"] = enable_dhcp
        if dns_nameservers is not None:
            data["subnet"]["dns_nameservers"] = dns_nameservers
        if service_types is not None:
            data["subnet"]["service_types"] = service_types

        path = "%s/subnets" % self.ver
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Create openstack subnet: %s" % truncate(res[0]))
        return res[0]["subnet"]

    @setup_client
    def update(
        self,
        oid,
        name=None,
        network_id=None,
        tenant_id=None,
        gateway_ip=None,
        cidr=None,
        allocation_pools=None,
        enable_dhcp=None,
        host_routes=None,
        dns_nameservers=None,
    ):
        """Update a subnet on a network.

        :param oid: id of the subnet
        :param name str: [optional] The subnet name.
        :param network_id id: [optional] The UUID of the attached network.
        :param tenant_id id: [optional] The UUID of the tenant who owns the network.
        :param gateway_ip: [optional] The gateway IP address.
        :param cidr: [optional] The CIDR.
        :param allocation_pools: [optional]  dict like
            {"allocation_pools":{"start":<start ip>,
                                 "end":<end ip>,}}
        :param enable_dhcp: [optional]  Set to true if DHCP is enabled and
            false if DHCP is disabled.
        :param dns_nameservers: [optional] A list of DNS
            name servers for the subnet. Specify each name server as an IP
            address and separate multiple entries with a space.
        :param host_routes:[optional] A list of host route dictionaries for the subnet.
            For example:
            [
                {
                  "destination":"0.0.0.0/0",
                  "nexthop":"123.45.67.89"
                },
                {
                  "destination":"192.168.0.0/24",
                  "nexthop":"192.168.0.1"
                }
            ]
        :return: Ex.
           [{'end': '10.108.1.254', 'start': '10.108.1.2'}],
             'cidr': '10.108.1.0/24',
             'dns_nameservers': [],
             'enable_dhcp': True,
             'gateway_ip': '10.108.1.1',
             'host_routes': [{'destination': '0.0.0.0/0', 'nexthop': '123.45.67.89'},
                              {'destination': '192.168.0.0/24', 'nexthop': '192.168.0.1'}],
             'id': '340de24a-7ca9-42b1-bfec-699110485235',
             'ip_version': 4,
             'ipv6_address_mode': None,
             'ipv6_ra_mode': None,
             'name': 'prova-net-02-subnet',
             'network_id': 'e96c7e29-2190-4fa0-8b8b-885a9dae6915',
             'subnetpool_id': None,
             'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"subnet": {}}

        if network_id is not None:
            data["subnet"]["network_id"] = network_id
        if tenant_id is not None:
            data["subnet"]["tenant_id"] = tenant_id
        if cidr is not None:
            data["subnet"]["cidr"] = cidr
        if gateway_ip is not None:
            data["subnet"]["gateway_ip"] = gateway_ip
        if name is not None:
            data["subnet"]["name"] = name
        if allocation_pools is not None:
            data["subnet"]["allocation_pools"] = allocation_pools
        if host_routes is not None:
            data["subnet"]["host_routes"] = host_routes
        if enable_dhcp is not None:
            data["subnet"]["enable_dhcp"] = enable_dhcp
        if dns_nameservers is not None:
            data["subnet"]["dns_nameservers"] = dns_nameservers

        path = "%s/subnets/%s" % (self.ver, oid)
        res = self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Update openstack subnet: %s" % truncate(res[0]))
        return res[0]["subnet"]

    @setup_client
    def delete(self, oid):
        """Deletes a subnet.

        :param oid: subnet id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/subnets/%s" % (self.ver, oid)
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack subnet: %s" % truncate(res[0]))
        return res[0]


class OpenstackPort(OpenstackNetworkObject):
    """ """

    def __init__(self, network):
        OpenstackNetworkObject.__init__(self, network.manager)

        self.ver = network.ver

    @setup_client
    def list(
        self,
        tenant=None,
        network=None,
        status=None,
        device_id=None,
        device_owner=None,
        security_group=None,
        subnet_id=None,
        ip_address=None,
    ):
        """Lists ports to which the tenant has access.

        :param tenant: tenant id
        :param network: The ID of the attached network.
        :param status : The port status. Value is ACTIVE or DOWN.
        :param device_id: The UUID of the device that uses this port. For example, a virtual server.
        :param device_owner: The entity type that uses this port. For example,
            compute:nova (server instance), network:dhcp (DHCP agent) or
            network:router_interface (router interface).
        :param security_groups: The UUIDs of any attached security groups.
        :param ip_address: port ip address
        :param subnet_id: port subnet id
        :return: Ex.
            [{'admin_state_up': True,
              'allowed_address_pairs': [],
              'binding:host_id': 'comp-liberty2-kvm.nuvolacsi.it',
              'binding:profile': {},
              'binding:vif_details': {'port_filter': True},
              'binding:vif_type': 'bridge',
              'binding:vnic_type': 'normal',
              'device_id': 'af0064bb-5c1b-44cb-9cd4-52ac210aa091',
              'device_owner': 'compute:nova',
              'dns_assignment': [{'fqdn': 'host-172-25-4-210.openstacklocal.', 'hostname': 'host-172-25-4-210',
                                   'ip_address': '172.25.4.210'}],
              'dns_name': '',
              'extra_dhcp_opts': [],
              'fixed_ips': [{'ip_address': '172.25.4.210', 'subnet_id': 'f375e490-1103-4c00-9803-2703e3165271'}],
              'id': '070ef967-02b8-4c67-9840-cee1cedd5850',
              'mac_address': 'fa:16:3e:07:ae:72',
              'name': '',
              'network_id': '40803c62-f4b1-4afb-bd94-f773a5c70f7b',
              'port_security_enabled': True,
              'security_groups': ['25fce921-3d6f-42a9-bcf2-8ab66e564951'],
              'status': 'ACTIVE',
              'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'},..,
            ]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/ports" % self.ver

        query = {}
        if tenant is not None:
            query["tenant_id"] = tenant
        if network is not None:
            query["network_id"] = network
        if status is not None:
            query["status"] = status
        if device_id is not None:
            query["device_id"] = device_id
        if ip_address is not None:
            query["fixed_ips"] = "ip_address_substr=%s" % ip_address
        if subnet_id is not None:
            query["fixed_ips"] = "subnet_id=%s" % subnet_id
        path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)

        resp = []
        if security_group is not None:
            for item in res[0]["ports"]:
                if security_group in item.get("security_groups", []):
                    resp.append(item)
        else:
            resp = res[0]["ports"]

        self.logger.debug("Get openstack ports: %s" % truncate(resp))
        return resp

    @setup_client
    def get(self, oid=None, name=None, mac_address=None):
        """Shows details for a port.

        :param oid: port id
        :param name: port name
        :param mac_address: The MAC address of the port.
        :return: Ex.
             {'admin_state_up': True,
              'allowed_address_pairs': [],
              'binding:host_id': 'comp-liberty2-kvm.nuvolacsi.it',
              'binding:profile': {},
              'binding:vif_details': {'port_filter': True},
              'binding:vif_type': 'bridge',
              'binding:vnic_type': 'normal',
              'device_id': 'af0064bb-5c1b-44cb-9cd4-52ac210aa091',
              'device_owner': 'compute:nova',
              'dns_assignment': [{'fqdn': 'host-172-25-4-210.openstacklocal.', 'hostname': 'host-172-25-4-210',
                                   'ip_address': '172.25.4.210'}],
              'dns_name': '',
              'extra_dhcp_opts': [],
              'fixed_ips': [{'ip_address': '172.25.4.210', 'subnet_id': 'f375e490-1103-4c00-9803-2703e3165271'}],
              'id': '070ef967-02b8-4c67-9840-cee1cedd5850',
              'mac_address': 'fa:16:3e:07:ae:72',
              'name': '',
              'network_id': '40803c62-f4b1-4afb-bd94-f773a5c70f7b',
              'port_security_enabled': True,
              'security_groups': ['25fce921-3d6f-42a9-bcf2-8ab66e564951'],
              'status': 'ACTIVE',
              'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = "%s/ports/%s" % (self.ver, oid)
        elif name is not None:
            path = "%s/ports?display_name=%s" % (self.ver, name)
        elif mac_address is not None:
            path = "%s/ports?mac_address=%s" % (self.ver, mac_address)
        else:
            raise OpenstackError("Specify at least port id or name")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack port: %s" % truncate(res[0]))
        if oid is not None:
            server = res[0]["port"]
        elif name is not None:
            server = res[0]["ports"][0]

        return server

    @setup_client
    def create(
        self,
        name,
        network_id,
        fixed_ips,
        host_id=None,
        profile=None,
        vnic_type=None,
        device_owner=None,
        device_id=None,
        security_groups=None,
        mac_address=None,
        tenant_id=None,
        allowed_address_pairs=None,
    ):
        """Creates a port on a network.

        :param name str: A symbolic name for the port.
        :param network_id id: The UUID of the network.
        :param fixed_ips list: specify the subnet. Ex.
            without ip:
            [{
                "subnet_id": "a0304c3a-4f08-4c43-88af-d796509c97d2",
            },..]

            with fixed ip:
            [{
                "subnet_id": "a0304c3a-4f08-4c43-88af-d796509c97d2",
                "ip_address": "10.0.0.2"
            },..]
        :param security_groups: [optional] One or more security group UUIDs.
        :param host_id: [optional] The ID of the host where the port is
            allocated. In some cases, different implementations can run on
            different hosts.
        :param profile: [optional] A dictionary that enables the application
            running on the host to pass and receive virtual network interface
            (VIF) port-specific information to the plug-in.
        :param vnic_type: [optional] The virtual network interface card (vNIC)
            type that is bound to the neutron port. A valid value is normal,
            direct, or macvtap.
        :param device_owner str: [optional] The UUID of the entity that uses
                                 this port. For example, a DHCP agent.
        :param device_id id: [optional] The UUID of the device that uses this
                             port. For example, a virtual server.
        :param mac_address: The MAC address of an allowed address pair. [optional]
        :param allowed_address_pairs: A set of zero or more allowed address pairs. An address pair contains an IP
            address and MAC address. Ex. [{'mac_address': .., 'ip_address': ..}] [optional]
        :param tenant_id: The ID of the tenant who owns the resource.
        :return: port data
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"port": {"network_id": network_id, "name": name, "admin_state_up": True}}
        if fixed_ips is not None:
            data["port"]["fixed_ips"] = fixed_ips
        if tenant_id is not None:
            data["port"]["tenant_id"] = tenant_id
        if host_id is not None:
            data["port"]["binding:host_id"] = host_id
        if profile is not None:
            data["port"]["binding:profile"] = profile
        if host_id is not None:
            data["port"]["binding:vnic_type"] = vnic_type
        if device_owner is not None:
            data["port"]["device_owner"] = device_owner
        if device_id is not None:
            data["port"]["device_id"] = device_id
        if security_groups is not None:
            data["port"]["security_groups"] = security_groups
        if allowed_address_pairs is not None:
            data["port"]["allowed_address_pairs"] = allowed_address_pairs

        path = "%s/ports" % self.ver
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Create openstack port: %s" % truncate(res[0]))
        return res[0]["port"]

    @setup_client
    def update(
        self,
        oid,
        name,
        network_id,
        fixed_ips=None,
        host_id=None,
        profile=None,
        vnic_type=None,
        device_owner=None,
        device_id=None,
        security_groups=None,
        port_security_enabled=None,
        allowed_address_pairs=None,
    ):
        """Update a port on a network.

        :param name: A symbolic name for the port.
        :param network_id: The UUID of the network.
        :param fixed_ips: specify the subnet. Ex.
            without ip:
            [{
                "subnet_id": "a0304c3a-4f08-4c43-88af-d796509c97d2",
            },..]

            with fixed ip:
            [{
                "subnet_id": "a0304c3a-4f08-4c43-88af-d796509c97d2",
                "ip_address": "10.0.0.2"
            },..]
        :param allowed_address_pairs: A set of zero or more allowed address pair objects each where address pair object
            contains an ip_address and mac_address. While the ip_address is required, the mac_address will be taken
            from the port if not specified. The value of ip_address can be an IP Address or a CIDR (if supported by
            the underlying extension plugin). A server connected to the port can send a packet with source address
            which matches one of the specified allowed address pairs.
        :param security_groups: [optional] One or more security group UUIDs.
        :param host_id: [optional] The ID of the host where the port is allocated. In some cases, different
            implementations can run on different hosts.
        :param profile: [optional] A dictionary that enables the application running on the host to pass and receive
            virtual network interface (VIF) port-specific information to the plug-in.
        :param vnic_type: [optional] The virtual network interface card (vNIC) type that is bound to the neutron port.
            A valid value is normal, direct, or macvtap.
        :param device_owner: [optional] The UUID of the entity that uses this port. For example, a DHCP agent.
        :param device_id: [optional] The UUID of the device that uses this port. For example, a virtual server.
        :param port_security_enabled: port_security_enabled
        :return: Ex.
            {'admin_state_up': True,
             'allowed_address_pairs': [],
             'binding:host_id': '',
             'binding:profile': {},
             'binding:vif_details': {},
             'binding:vif_type': 'unbound',
             'binding:vnic_type': 'normal',
             'device_id': '',
             'device_owner': '',
             'dns_assignment': [{'fqdn': 'host-10-108-1-5.openstacklocal.',
                                  'hostname': 'host-10-108-1-5',
                                  'ip_address': '10.108.1.5'}],
             'dns_name': '',
             'fixed_ips': [{'ip_address': '10.108.1.5',
                             'subnet_id': '340de24a-7ca9-42b1-bfec-699110485235'}],
             'id': 'a6899bb8-b654-4246-a0f8-5a4abe79cf4d',
             'mac_address': 'fa:16:3e:2e:d7:7b',
             'name': 'prova-net-01-port',
             'network_id': 'e96c7e29-2190-4fa0-8b8b-885a9dae6915',
             'port_security_enabled': True,
             'security_groups': ['25fce921-3d6f-42a9-bcf2-8ab66e564951'],
             'status': 'DOWN',
             'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"port": {}}
        if network_id is not None:
            data["port"]["network_id"] = network_id
        if name is not None:
            data["port"]["name"] = name
        if fixed_ips is not None:
            data["port"]["fixed_ips"] = fixed_ips
        if host_id is not None:
            data["port"]["binding:host_id"] = host_id
        if profile is not None:
            data["port"]["binding:profile"] = profile
        if host_id is not None:
            data["port"]["binding:vnic_type"] = vnic_type
        if device_owner is not None:
            data["port"]["device_owner"] = device_owner
        if device_id is not None:
            data["port"]["device_id"] = device_id
        if security_groups is not None:
            data["port"]["security_groups"] = security_groups
        if port_security_enabled is not None:
            data["port"]["port_security_enabled"] = port_security_enabled
        if allowed_address_pairs is not None:
            data["port"]["allowed_address_pairs"] = allowed_address_pairs

        path = "%s/ports/%s" % (self.ver, oid)
        res = self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Update openstack port: %s" % truncate(res[0]))
        return res[0]["port"]

    @setup_client
    def delete(self, oid):
        """Deletes a port.

        :param oid: subnet id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/ports/%s" % (self.ver, oid)
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack port: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def add_security_group(self, oid, security_group):
        """Add security group

        :param oid: port id
        :param security_group: security_group id
        :return: True or False
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        # get port
        path = "%s/ports/%s" % (self.ver, oid)
        port = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        port = port[0].get("port")
        security_groups = port["security_groups"]

        # add security group if it not already attached
        if security_group not in security_groups:
            security_groups.append(security_group)

            data = {"security_groups": security_groups}
            path = "%s/ports/%s" % (self.ver, oid)
            res = self.client.call(path, "PUT", data={"port": data}, token=self.manager.identity.token)
            self.logger.debug(
                "Add security group %s to openstack port %s: %s" % (security_group, oid, truncate(res[0]))
            )
            return True
        return False

    @setup_client
    def remove_security_group(self, oid, security_group):
        """Remove security group

        :param oid: port id
        :param security_group: security_group id
        :return: True or False
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        # get port
        path = "%s/ports/%s" % (self.ver, oid)
        port = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        port = port[0].get("port")
        security_groups = port["security_groups"]

        # add security group if it not already attached
        if security_group in security_groups:
            security_groups.remove(security_group)

            data = {"security_groups": security_groups}
            path = "%s/ports/%s" % (self.ver, oid)
            res = self.client.call(path, "PUT", data={"port": data}, token=self.manager.identity.token)
            self.logger.debug(
                "Remove security group %s to openstack port %s: %s" % (security_group, oid, truncate(res[0]))
            )
            return True
        return False


class OpenstackFloatingIp(OpenstackNetworkObject):
    """Manage openstack floating ip"""

    def __init__(self, network):
        OpenstackNetworkObject.__init__(self, network.manager)

        self.ver = network.ver

    '''
    def get_fixed_ip(self, ip):
        """Shows details for a fixed IP address.

        :param ip: The fixed IP of interest to you. 
        :return: Ex: 
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-fixed-ips/%s' % ip
        res = self.nova.call(path, 'GET', data='', 
                             token=self.manager.identity.token)
        self.logger.debug('Get openstack fixed ip %s: %s' % (ip, truncate(res[0])))
        return res[0]['fixed_ip']'''

    @setup_client
    def list(self):
        """Lists floating IP addresses associated with the tenant.

        :return: Ex:
            [{'fixed_ip_address': '192.168.90.175',
              'floating_ip_address': '194.116.110.171',
              'floating_network_id': '622a06be-4f21-47fc-9df0-06c9c82fbc02',
              'id': '00adbb47-8869-43fb-8054-f4ef4426421b',
              'port_id': 'ba315146-bc4f-4aba-89d5-695569133975',
              'router_id': 'd8a4b609-98bf-4acc-9b59-3588564eae23',
              'status': 'ACTIVE',
              'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'},...,
            ]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/floatingips" % self.ver
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("List openstack floating ips: %s" % (truncate(res[0])))
        return res[0]["floatingips"]

    @setup_client
    def get(self, oid):
        """Get floating IP addresses associated with the tenant.

        :param oid: id of the floating ip
        :return: Ex:
             {'fixed_ip_address': '192.168.90.175',
              'floating_ip_address': '194.116.110.171',
              'floating_network_id': '622a06be-4f21-47fc-9df0-06c9c82fbc02',
              'id': '00adbb47-8869-43fb-8054-f4ef4426421b',
              'port_id': 'ba315146-bc4f-4aba-89d5-695569133975',
              'router_id': 'd8a4b609-98bf-4acc-9b59-3588564eae23',
              'status': 'ACTIVE',
              'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/floatingips/%s" % (self.ver, oid)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack floating ip %s: %s" % (oid, truncate(res[0])))
        return res[0]["floatingip"]

    @setup_client
    def create(self, network_id, tenant_id, port_id):
        """Creates a floating IP, and, if you specify port information,
        associates the floating IP with an internal port.

        :param network_id: id of an external network
        :param tenant_id: id of the tenant owner of the ip
        :param port_id: id of the port to associate with ths floating ip
        :return: Ex:
            {'fixed_ip_address': '172.25.4.210',
             'floating_ip_address': '194.116.110.115',
             'floating_network_id': '622a06be-4f21-47fc-9df0-06c9c82fbc02',
             'id': '3f069a11-26bb-4e09-b929-1d6eaadc64bf',
             'port_id': '070ef967-02b8-4c67-9840-cee1cedd5850',
             'router_id': 'd8a4b609-98bf-4acc-9b59-3588564eae23',
             'status': 'DOWN',
             'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "floatingip": {
                "tenant_id": tenant_id,
                "floating_network_id": network_id,
                "port_id": port_id,
            }
        }

        path = "%s/floatingips" % (self.ver)
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Create openstack floating ip over port %s: %s" % (port_id, truncate(res[0])))
        return res[0]["floatingip"]

    @setup_client
    def update(self, floatingip_id, network_id=None, tenant_id=None, port_id=None):
        """Updates a floating IP and its association with an internal port.

        :param floatingip_id: floatingip id
        :param network_id: [optional] id of an external network
        :param tenant_id: [optional] id of the tenant owner of the ip
        :param port_id: [optional] id of the port to associate with ths floating ip
        :return: Ex:
             {'fixed_ip_address': '192.168.90.175',
              'floating_ip_address': '194.116.110.171',
              'floating_network_id': '622a06be-4f21-47fc-9df0-06c9c82fbc02',
              'id': '00adbb47-8869-43fb-8054-f4ef4426421b',
              'port_id': 'ba315146-bc4f-4aba-89d5-695569133975',
              'router_id': 'd8a4b609-98bf-4acc-9b59-3588564eae23',
              'status': 'ACTIVE',
              'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"floatingip": {}}

        if tenant_id is not None:
            data["floatingip"]["tenant_id"] = tenant_id
        if network_id is not None:
            data["floatingip"]["floating_network_id"] = network_id
        if port_id is not None:
            data["floatingip"]["port_id"] = port_id

        path = "%s/floatingips/%s" % (self.ver, floatingip_id)
        res = self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Update openstack floating ip %s: %s" % (floatingip_id, truncate(res[0])))
        return res[0]["floatingip"]

    @setup_client
    def delete(self, floatingip_id):
        """Deletes a floating IP and, if present, its associated port.

        :param floatingip_id: id of the floating ip
        :return: None
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/floatingips/%s" % (self.ver, floatingip_id)
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack floating ip %s: %s" % (floatingip_id, truncate(res[0])))
        return res[0]


class OpenstackRouter(OpenstackNetworkObject):
    """ """

    def __init__(self, network):
        OpenstackNetworkObject.__init__(self, network.manager)

        self.ver = network.ver

    @setup_client
    def list(self, tenant_id=None):
        """List routers.

        :return: Ex.
            [...,
             {'admin_state_up': True,
              'distributed': False,
              'external_gateway_info':
                  {'enable_snat': True,
                   'external_fixed_ips': [
                       {'ip_address': '194.116.110.161',
                        'subnet_id': '46620b60-76f6-4f1e-a754-dccfc50880c4'}],
                   'network_id': '622a06be-4f21-47fc-9df0-06c9c82fbc02'},
              'ha': True,
              'id': 'f49b48de-05de-4942-a21c-7e10ce024025',
              'name': 'cloudify-management-router',
              'routes': [],
              'status': 'ACTIVE',
              'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        query = {}
        if tenant_id is not None:
            query["tenant_id"] = tenant_id

        path = "%s/routers?%s" % (self.ver, urlencode(query))

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack routers: %s" % truncate(res[0]))
        return res[0]["routers"]

    @setup_client
    def get(self, oid=None):
        """Get router

        :param oid: router id
        :return: Ex.
            {'admin_state_up': True,
             'distributed': False,
             'external_gateway_info': None,
             'ha': True,
             'id': '39660b87-3319-43d3-9780-e60eb5c5079e',
             'name': 'router-306',
             'routes': [{'destination': '0.0.0.0/0', 'nexthop': '172.25.4.18'},
                         {'destination': '169.254.169.254/32', 'nexthop': '172.25.4.201'},
                         {'destination': '172.25.0.0/16', 'nexthop': '172.25.4.1'}],
             'status': 'ACTIVE',
             'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = "%s/routers/%s" % (self.ver, oid)
        else:
            raise OpenstackError("Specify at least router id")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack router: %s" % truncate(res[0]))
        if oid is not None:
            router = res[0]["router"]

        return router

    @setup_client
    def create(self, name, tenant_id, network, external_ips=None):
        """Create a router.

        :param name: router name
        :param tenant_id: router tenant id
        :param network: router external network id [optional]
        :param external_ips: [optional] router external_ips. Ex.

            [
                {
                    "subnet_id": "255.255.255.0",
                    "ip": "192.168.10.1"
                }
            ]

        :return: Ex.
            {'admin_state_up': True,
             'distributed': False,
             'external_gateway_info': {'enable_snat': True,
                                        'external_fixed_ips': [
                                        {'ip_address': '194.116.110.113', u
                                        'subnet_id': '46620b60-76f6-4f1e-a754-dccfc50880c4'}],
                                        'network_id': '622a06be-4f21-47fc-9df0-06c9c82fbc02'},
             'ha': True,
             'id': '22e71dd6-1c74-42c3-9898-cd627957208b',
             'name': 'prova-router-01',
             'routes': [],
             'status': 'ACTIVE',
             'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"router": {"name": name, "tenant_id": tenant_id, "admin_state_up": True}}
        if network is not None:
            data["router"]["external_gateway_info"] = {
                "network_id": network,
                "enable_snat": True,
            }
        if external_ips is not None:
            data["router"]["external_gateway_info"]["external_fixed_ips"] = external_ips
        # if routes is not None:
        #    data['router']['routes'] = routes

        path = "%s/routers" % self.ver
        res = self.client.call(
            path,
            "POST",
            data=jsonDumps(data),
            token=self.manager.identity.token,
            timeout=30,
        )
        self.logger.debug("Create openstack router: %s" % truncate(res[0]))
        return res[0]["router"]

    @setup_client
    def update(self, oid, name=None, network=None, external_ips=None, routes=None):
        """Updates a logical router.

        :param oid: [optional] network id
        :param name: [optional] router name
        :param network: [optional] router external network id
        :param external_ips: [optional] router external_ips. Ex.

            [
                {
                    "subnet_id": "255.255.255.0",
                    "ip": "192.168.10.1"
                }
            ]

        :param routes: [optional] A list of dictionary pairs in this format:

                [
                  {
                    "nexthop":"IPADDRESS",
                    "destination":"CIDR"
                  }
                ]

        :return: Ex.
            {'admin_state_up': True,
             'distributed': False,
             'external_gateway_info': {'enable_snat': True, 'external_fixed_ips': [
                                        {'ip_address': '194.116.110.113',
                                         'subnet_id': '46620b60-76f6-4f1e-a754-dccfc50880c4'}],
                                         'network_id': '622a06be-4f21-47fc-9df0-06c9c82fbc02'},
             'ha': True,
             'id': '22e71dd6-1c74-42c3-9898-cd627957208b',
             'name': 'prova-router-01',
             'routes': [],
             'status': 'ACTIVE',
             'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"router": {}}
        if name is not None:
            data["router"]["name"] = name
        if network is not None:
            data["router"]["external_gateway_info"] = {"network_id": network}
        if network is not None and external_ips is not None:
            data["router"]["external_gateway_info"]["external_fixed_ips"] = external_ips
        if routes is not None:
            data["router"]["routes"] = routes

        path = "%s/routers/%s" % (self.ver, oid)
        res = self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Update openstack router: %s" % truncate(res[0]))
        return res[0]["router"]

    @setup_client
    def delete(self, oid):
        """Deletes a logical router and, if present, its external gateway interface.

        :param oid: router id
        :return: None
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/routers/%s" % (self.ver, oid)
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack router: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def add_internal_interface(self, oid, subnet, port=None):
        """Adds an internal interface to a logical router.

        :param oid: router id
        :param subnet: subnet to add with an internal interface
        :param port: port to add as internal interface [optional]
        :return: Ex.
            {'id': '32332281-3ca0-434c-b63a-eb9886a32c20',
             'port_id': '1b5482d1-ad45-4efc-ba4a-9a767000fd46',
             'subnet_id': '340de24a-7ca9-42b1-bfec-699110485235',
             'subnet_ids': ['340de24a-7ca9-42b1-bfec-699110485235'],
             'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if subnet is not None:
            data = {"subnet_id": subnet}
        elif port is not None:
            data = {"port_id": port}
        path = "%s/routers/%s/add_router_interface" % (self.ver, oid)
        res = self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Adds an internal interface to openstack router %s: %s" % (oid, truncate(res[0])))
        return res[0]

    @setup_client
    def delete_internal_interface(self, oid, subnet):
        """Deletes an internal interface from a logical router.

        :param oid: router id
        :param subnet: subnet to remove from internal interfaces
        :return: Ex.
            {'id': '32332281-3ca0-434c-b63a-eb9886a32c20',
             'port_id': '1b5482d1-ad45-4efc-ba4a-9a767000fd46',
             'subnet_id': '340de24a-7ca9-42b1-bfec-699110485235',
             'subnet_ids': ['340de24a-7ca9-42b1-bfec-699110485235'],
             'tenant_id': 'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"subnet_id": subnet}
        path = "%s/routers/%s/remove_router_interface" % (self.ver, oid)
        res = self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Delete an internal interface from openstack router %s: %s" % (oid, truncate(res[0])))
        return res[0]

    @setup_client
    def add_routes(self, oid, routes):
        """Add extra routes to the router.

        :param oid: router id
        :param routes: list of dict { 'destination' : '10.0.1.0/24', 'nexthop' : '10.0.0.11' }
        :return: True
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"router": {"routes": routes}}
        path = "%s/routers/%s" % (self.ver, oid)
        self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Add openstack router %s routes %s" % (oid, routes))
        return True

    @setup_client
    def del_routes(self, oid, routes):
        """Delete extra routes from the router.

        :param oid: router id
        :param routes: list of dict { 'destination' : '10.0.1.0/24', 'nexthop' : '10.0.0.11' }
        :return: True
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"router": {"routes": routes}}
        path = "%s/routers/%s" % (self.ver, oid)
        self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Delete openstack router %s routes %s" % (oid, routes))
        return True

    @setup_client
    def add_route(self, oid, destination, nexthop):
        """Add an extra routes to the router’s already existing extra routes.

        :param oid: router id
        :param destination: destination cidr
        :param nexthop: next hop
        :return: Ex.
            {
               'router' : {
                  'id' : '64e339bb-1a6c-47bd-9ee7-a0cf81a35172',
                  'name' : 'router1',
                  'routes' : [
                     { 'destination' : '10.0.1.0/24', 'nexthop' : '10.0.0.11' },
                     { 'destination' : '10.0.2.0/24', 'nexthop' : '10.0.0.12' },
                     { 'destination' : '10.0.3.0/24', 'nexthop' : '10.0.0.13' },
                     { 'destination' : '10.0.4.0/24', 'nexthop' : '10.0.0.14' }
                  ]
               }
            }
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"router": {"routes": [{"destination": destination, "nexthop": nexthop}]}}
        path = "/%s/routers/%s/add_extraroutes" % (self.ver, oid)
        res = self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("add route to openstack router %s: %s" % (oid, truncate(res[0])))
        return res[0]

    @setup_client
    def del_route(self, oid, destination, nexthop):
        """Delete an extra routes from the router’s already existing extra routes.

        :param oid: router id
        :param destination: destination cidr
        :param nexthop: next hop
        :return: Ex.
            {
               'router' : {
                  'id' : '64e339bb-1a6c-47bd-9ee7-a0cf81a35172',
                  'name' : 'router1',
                  'routes' : [
                     { 'destination' : '10.0.1.0/24', 'nexthop' : '10.0.0.11' },
                     { 'destination' : '10.0.2.0/24', 'nexthop' : '10.0.0.12' },
                     { 'destination' : '10.0.3.0/24', 'nexthop' : '10.0.0.13' },
                     { 'destination' : '10.0.4.0/24', 'nexthop' : '10.0.0.14' }
                  ]
               }
            }
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"router": {"routes": [{"destination": destination, "nexthop": nexthop}]}}
        path = "/%s/routers/%s/remove_extraroutes" % (self.ver, oid)
        res = self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("remove route from openstack router %s: %s" % (oid, truncate(res[0])))
        return res[0]


class OpenstackSecurityGroup(OpenstackNetworkObject):
    """ """

    def __init__(self, network):
        OpenstackNetworkObject.__init__(self, network.manager)

        self.ver = network.ver

    @setup_client
    def list_logging(self, detail=False, tenant=None):
        """List flavors

        :param tenant: tenant id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/logging/logs" % self.ver

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack security groups log: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def list(self, detail=False, tenant=None):
        """List flavors

        :param tenant: tenant id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/security-groups" % self.ver

        query = {}
        if tenant is not None:
            query["tenant_id"] = tenant
        path = "%s?%s" % (path, urlencode(query))

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack security groups: %s" % truncate(res[0]))
        return res[0]["security_groups"]

    @setup_client
    def get(self, oid):
        """Get security group

        :param oid: flavor id
        :param name: flavor name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/security-groups/%s" % (self.ver, oid)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack security group: %s" % truncate(res[0]))
        if oid is not None:
            security_group = res[0]["security_group"]

        return security_group

    @setup_client
    def create(self, name, desc, tenant_id):
        """Create new security group

        :param name: name
        :param desc: description
        :param tenant_id: tenant_id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "security_group": {
                "name": name,
                "description": desc,
                "tenant_id": tenant_id,
            }
        }

        path = "%s/security-groups" % self.ver
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Create openstack security group: %s" % truncate(res[0]))
        return res[0]["security_group"]

    @setup_client
    def update(self, oid, name=None, desc=None):
        """TODO
        :param oid: security group id
        :param name: name [optional]
        :param desc: description  [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"security_group": {}}
        if name is not None:
            data["security_group"]["name"] = name
        if desc is not None:
            data["security_group"]["description"] = desc

        path = "%s/security-groups/%s" % (self.ver, oid)
        res = self.client.call(path, "PUT", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Update openstack security group: %s" % truncate(res[0]))
        return res[0]["security_group"]

    @setup_client
    def delete(self, oid):
        """Remove a security group

        :param oid: security group id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/security-groups/%s" % (self.ver, oid)
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack security group: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def get_rule(self, ruleid):
        """get a security group rule

        :param ruleid: rule id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/security-group-rules/%s" % (self.ver, ruleid)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("get openstack security group rule %s: %s" % (ruleid, truncate(res[0])))
        return res[0]

    @setup_client
    def create_rule(
        self,
        security_group,
        direction,
        ethertype=None,
        port_range_min=None,
        port_range_max=None,
        protocol=None,
        remote_group_id=None,
        remote_ip_prefix=None,
    ):
        """Create new security group rule

        :param security_group: security group id
        :param direction: ingress or egress: The direction in which the
                          security group rule is applied. For a compute
                          instance, an ingress security group rule is applied
                          to incoming (ingress) traffic for that instance.
                          An egress rule is applied to traffic leaving the
                          instance.
        :param ethertype: Must be IPv4 or IPv6, and addresses represented in
                          CIDR must match the ingress or egress rules. [optional]
        :param port_range_min: The minimum port number in the range that is
                               matched by the security group rule. If the
                               protocol is TCP or UDP, this value must be less
                               than or equal to the port_range_max attribute
                               value. If the protocol is ICMP, this value must
                               be an ICMP type. [optional]
        :param port_range_max: The maximum port number in the range that is
                               matched by the security group rule. The
                               port_range_min attribute constrains the
                               port_range_max attribute. If the protocol is
                               ICMP, this value must be an ICMP type. [optional]
        :param protocol: The protocol that is matched by the security group
                         rule. Valid values are null, tcp, udp, and icmp. [optional]
        :param remote_group_id: The remote group UUID to associate with this
                                security group rule. You can specify either the
                                remote_group_id or remote_ip_prefix attribute
                                in the request body. [optional]
        :param remote_ip_prefix:  The remote IP prefix to associate with this
                                  security group rule. You can specify either
                                  the remote_group_id or remote_ip_prefix
                                  attribute in the request body. This attribute
                                  matches the IP prefix as the source IP address
                                  of the IP packet. [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "security_group_rule": {
                "direction": direction,
                "protocol": protocol,
                "security_group_id": security_group,
            }
        }
        if remote_ip_prefix is not None:
            data["security_group_rule"].update(
                {
                    "port_range_min": port_range_min,
                    "port_range_max": port_range_max,
                    "ethertype": ethertype,
                    "remote_ip_prefix": remote_ip_prefix,
                }
            )
        elif remote_group_id is not None:
            data["security_group_rule"].update(
                {
                    "port_range_min": port_range_min,
                    "port_range_max": port_range_max,
                    "ethertype": ethertype,
                    "remote_group_id": remote_group_id,
                }
            )

        def resolve_conflicts(res):
            # NeutronError - Security group rule already exists. Rule id is 6ef5ab8c-f550-4b15-ac0c-4b99a7003280.
            if res.find("NeutronError - Security group rule already exists.") == 0:
                r = re.search("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", res)
                rule_id = r.group(0)
                self.delete_rule(rule_id)

                # recreate rule
                path = "%s/security-group-rules" % self.ver
                res = self.client.call(
                    path,
                    "POST",
                    data=jsonDumps(data),
                    token=self.manager.identity.token,
                )
                self.logger.debug(
                    "Resolve conflict for openstack security group %s rule: %s" % (security_group, truncate(res[0]))
                )
                return res

        path = "%s/security-group-rules" % self.ver
        res = self.client.call(
            path,
            "POST",
            data=jsonDumps(data),
            token=self.manager.identity.token,
            resolve_conflicts=resolve_conflicts,
        )
        self.logger.debug("Create openstack security group %s rule: %s" % (security_group, truncate(res[0])))
        return res[0]["security_group_rule"]

    @setup_client
    def delete_rule(self, ruleid):
        """Remove a security group rule

        :param ruleid: rule id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/security-group-rules/%s" % (self.ver, ruleid)
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack security group rule %s: %s" % (ruleid, truncate(res[0])))
        return res[0]

    #
    # actions
    #


class OpenstackFwaas2(OpenstackNetworkObject):
    """Manage openstack firewall as a service v2"""

    RULE_PARAMS = [
        "project_id",
        "description",
        "destination_firewall_group_id",
        "destination_ip_address",
        "destination_port",
        "ip_version",
        "protocol",
        "source_firewall_group_id",
        "source_firewall_group_id",
        "source_ip_address",
        "source_port",
    ]
    POLICY_PARAMS = ["project_id", "description", "firewall_rules", "audited", "shared"]
    GROUP_PARAMS = ["project_id", "description", "ports"]

    def __init__(self, network):
        OpenstackNetworkObject.__init__(self, network.manager)

        self.ver = network.ver
        self.fw2_path = "%s/fwaas" % self.ver

    @setup_client
    def list_rules(self, **kwargs):
        """List firewall rules

        :param tenant: tenant id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/firewall_rules" % self.fw2_path
        params = deepcopy(self.RULE_PARAMS)
        params.extend(["name", "action", "enabled", "shared"])
        query = set_request_params(kwargs, params)
        path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        if len(res) > 0:
            self.logger.debug("Get openstack firewall rules: %s" % truncate(res[0]))
            return res[0]["firewall_rules"]
        else:
            return []

    @setup_client
    def get_rule(self, oid):
        """Get firewall rule

        :param oid: rule id
        :param name: rule name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/firewall_rules/%s" % (self.fw2_path, oid)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack firewall rule: %s" % truncate(res[0]))
        if oid is not None:
            firewall_rule = res[0]["firewall_rule"]

        return firewall_rule

    @setup_client
    def create_rule(self, name, action, enabled=True, shared=False, **kwargs):
        """Create new firewall rule

        :param name: name
        :param desc: description [optional]
        :param project_id: project_id [optional]
        :param action: The action that the API performs on traffic that matches the firewall rule. Valid values are
            allow or deny. Default is deny.
        :param destination_firewall_group_id: The ID of the remote destination firewall group. [optional]
        :param destination_ip_address: The destination IPv4 or IPv6 address or CIDR for the firewall rule. No
            default. [optional]
        :param destination_port: The destination port or port range for the firewall rule. A valid value is a port
            number, as an integer, or a port range, in the format of a : separated range. For a port range, include
            both ends of the range. For example, 80:90.  [optional]
        :param bool enabled: Set to false to disable this rule in the firewall policy. Facilitates selectively turning
            off rules without having to disassociate the rule from the firewall policy. Valid values are true or false.
            Default is true. [default=True]
        :param int ip_version: The IP protocol version for the firewall rule. Valid values are 4 or 6. Default is
            4. [optional]
        :param protocol: The IP protocol for the firewall rule. Possible values are icmp, tcp, udp, or null. [optional]
        :param shared: Indicates whether this firewall rule is shared across all projects. [default=False]
        :param source_firewall_group_id: The ID of the remote source firewall group.  [optional]
        :param source_ip_address: The source IPv4 or IPv6 address or CIDR for the firewall rule. No default. [optional]
        :param source_port: The source port or port range for the firewall rule. A valid value is a port number, as
            an integer, or a port range, in the format of a : separated range. For a port range, include both ends of
            the range. For example, 80:90. [optional]
        :return: rule
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = set_request_params(kwargs, self.RULE_PARAMS)
        data.update({"name": name, "action": action, "enabled": enabled, "shared": shared})
        path = "%s/firewall_rules" % self.fw2_path
        res = self.client.call(
            path,
            "POST",
            data={"firewall_rule": data},
            token=self.manager.identity.token,
        )
        self.logger.debug("Create openstack firewall rule: %s" % truncate(res[0]))
        return res[0]["firewall_rule"]

    @setup_client
    def update_rule(self, oid, **kwargs):
        """Update a firewall rule

        :param oid: firewall rule id
        :param name: name [optional]
        :param desc: description [optional]
        :param project_id: project_id [optional]
        :param action: The action that the API performs on traffic that matches the firewall rule. Valid values are
            allow or deny. Default is deny. [optional]
        :param destination_firewall_group_id: The ID of the remote destination firewall group. [optional]
        :param destination_ip_address: The destination IPv4 or IPv6 address or CIDR for the firewall rule. No
            default. [optional]
        :param destination_port: The destination port or port range for the firewall rule. A valid value is a port
            number, as an integer, or a port range, in the format of a : separated range. For a port range, include
            both ends of the range. For example, 80:90. [optional]
        :param bool enabled: Set to false to disable this rule in the firewall policy. Facilitates selectively turning
            off rules without having to disassociate the rule from the firewall policy. Valid values are true or false.
            Default is true. [optional]
        :param int ip_version: The IP protocol version for the firewall rule. Valid values are 4 or 6. Default is
            4. [optional]
        :param protocol: The IP protocol for the firewall rule. Possible values are icmp, tcp, udp, or null. [optional]
        :param shared: Indicates whether this firewall rule is shared across all projects. [optional]
        :param source_firewall_group_id: The ID of the remote source firewall group.  [optional]
        :param source_ip_address: The source IPv4 or IPv6 address or CIDR for the firewall rule. No default. [optional]
        :param source_port: The source port or port range for the firewall rule. A valid value is a port number, as
            an integer, or a port range, in the format of a : separated range. For a port range, include both ends of
            the range. For example, 80:90. [optional]
        :return: rule
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        params = deepcopy(self.RULE_PARAMS)
        params.remove("project_id")
        params.extend(["name", "action", "enabled", "shared"])
        data = set_request_params(kwargs, params)

        path = "%s/firewall_rules/%s" % (self.fw2_path, oid)
        res = self.client.call(path, "PUT", data={"firewall_rule": data}, token=self.manager.identity.token)
        self.logger.debug("Update openstack firewall rule: %s" % truncate(res[0]))
        return res[0]["firewall_rule"]

    @setup_client
    def delete_rule(self, oid):
        """Remove a firewall rule

        :param oid: firewall rule id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/firewall_rules/%s" % (self.fw2_path, oid)
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack firewall rule: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def list_policies(self, **kwargs):
        """List firewall policies

        :param tenant: tenant id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/firewall_policies" % self.fw2_path
        params = deepcopy(self.POLICY_PARAMS)
        params.extend(["name"])
        query = set_request_params(kwargs, params)
        path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        if len(res) > 0:
            self.logger.debug("Get openstack firewall policies: %s" % truncate(res[0]))
            return res[0]["firewall_policies"]
        else:
            return []

    @setup_client
    def get_policy(self, oid):
        """Get firewall policy

        :param oid: policy id
        :param name: policy name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/firewall_policies/%s" % (self.fw2_path, oid)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack firewall policy: %s" % truncate(res[0]))
        if oid is not None:
            firewall_policy = res[0]["firewall_policy"]

        return firewall_policy

    @setup_client
    def create_policy(self, name, **kwargs):
        """Create new firewall policy

        :param name: name
        :param desc: description [optional]
        :param project_id: project_id [optional]
        :param bool audited: Each time that the firewall policy or its associated rules are changed, the API sets this
            attribute to false. To audit the policy, explicitly set this attribute to true. [optional]
        :param list firewall_rules: A list of the IDs of the firewall rules associated with the firewall policy.
            [optional]
        :param bool shared: Set to true to make this firewall policy visible to other projects. Default is false.
            [optional]
        :return: policy
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = set_request_params(kwargs, self.POLICY_PARAMS)
        data.update({"name": name})
        path = "%s/firewall_policies" % self.fw2_path
        res = self.client.call(
            path,
            "POST",
            data={"firewall_policy": data},
            token=self.manager.identity.token,
        )
        self.logger.debug("Create openstack firewall policy: %s" % truncate(res[0]))
        return res[0]["firewall_policy"]

    @setup_client
    def update_policy(self, oid, **kwargs):
        """Update a firewall policy

        :param oid: firewall policy id
        :param name: name [optional]
        :param desc: description [optional]
        :param project_id: project_id [optional]
        :param bool audited: Each time that the firewall policy or its associated rules are changed, the API sets this
            attribute to false. To audit the policy, explicitly set this attribute to true. [optional]
        :param list firewall_rules: A list of the IDs of the firewall rules associated with the firewall policy.
            [optional]
        :param bool shared: Set to true to make this firewall policy visible to other projects. Default is false.
            [optional]
        :return: policy
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        params = deepcopy(self.POLICY_PARAMS)
        params.remove("project_id")
        params.extend(["name"])
        data = set_request_params(kwargs, params)

        path = "%s/firewall_policies/%s" % (self.fw2_path, oid)
        res = self.client.call(
            path,
            "PUT",
            data={"firewall_policy": data},
            token=self.manager.identity.token,
        )
        self.logger.debug("Update openstack firewall policy: %s" % truncate(res[0]))
        return res[0]["firewall_policy"]

    @setup_client
    def delete_policy(self, oid):
        """Remove a firewall policy

        :param oid: firewall policy id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/firewall_policies/%s" % (self.fw2_path, oid)
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack firewall policy: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def insert_policy_rule(self, oid, firewall_rule_id, insert_after="", insert_before=""):
        """Insert firewall rule into a policy. A firewall_rule_id is inserted relative to the position of the
        firewall_rule_id set in insert_before or insert_after. If insert_before is set, insert_after is ignored. If
        both insert_before and insert_after are not set, the new firewall_rule_id is inserted as the first rule of the
        policy.

        :param oid: firewall policy id
        :param firewall_rule_id: The ID of the firewall rule.
        :param insert_after: The ID of the firewall_rule to insert the new rule after. The new rule will be inserted
            immediately after the specified firewall_rule. If both before and after values are supplied, the after
            value will be ignored. To insert a rule into a policy with no rules yet, the both the before and the after
            values must be "".
        :param insert_before: The ID of the firewall_rule to insert the new rule before. The new rule will be inserted
            immediately before the specified firewall_rule. If both before and after values are supplied, the after
            value will be ignored. To insert a rule into a policy with no rules yet, the both the before and the after
            values must be "".
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "firewall_rule_id": firewall_rule_id,
            "insert_after": insert_after,
            "insert_before": insert_before,
        }
        path = "%s/firewall_policies/%s/insert_rule" % (self.fw2_path, oid)
        res = self.client.call(path, "PUT", data=data, token=self.manager.identity.token)
        self.logger.debug("Insert openstack firewall rule into policy: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def remove_policy_rule(self, oid, firewall_rule_id):
        """Insert firewall rule into a policy. A firewall_rule_id is inserted relative to the position of the
        firewall_rule_id set in insert_before or insert_after. If insert_before is set, insert_after is ignored. If
        both insert_before and insert_after are not set, the new firewall_rule_id is inserted as the first rule of the
        policy.

        :param oid: firewall policy id
        :param firewall_rule_id: The ID of the firewall rule.
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "firewall_rule_id": firewall_rule_id,
        }
        path = "%s/firewall_policies/%s/remove_rule" % (self.fw2_path, oid)
        res = self.client.call(path, "PUT", data=data, token=self.manager.identity.token)
        self.logger.debug("Remove openstack firewall rule from policy: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def list_groups(self, **kwargs):
        """List firewall groups

        :param tenant: tenant id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/firewall_groups" % self.fw2_path
        params = deepcopy(self.GROUP_PARAMS)
        params.extend(
            [
                "name",
                "egress_firewall_policy_id",
                "ingress_firewall_policy_id",
                "shared",
            ]
        )
        query = set_request_params(kwargs, params)
        path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        if len(res) > 0:
            self.logger.debug("Get openstack firewall groups: %s" % truncate(res[0]))
            return res[0]["firewall_groups"]
        else:
            return []

    @setup_client
    def get_group(self, oid):
        """Get firewall group

        :param oid: group id
        :param name: group name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/firewall_groups/%s" % (self.fw2_path, oid)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack firewall group: %s" % truncate(res[0]))
        if oid is not None:
            firewall_group = res[0]["firewall_group"]

        return firewall_group

    @setup_client
    def create_group(
        self,
        name,
        egress_firewall_policy_id,
        ingress_firewall_policy_id,
        shared=False,
        **kwargs,
    ):
        """Create new firewall group

        :param name: name
        :param description: description [optional]
        :param project_id: project_id [optional]
        :param egress_firewall_policy_id : The ID of the egress firewall policy for the firewall group.
        :param ingress_firewall_policy_id: The ID of the ingress firewall policy for the firewall group.
        :param list ports: A list of the IDs of the ports associated with the firewall group. [optional]
        :param bool shared: Indicates whether this firewall group is shared across all projects. [default=False]
        :return: group
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = set_request_params(kwargs, self.GROUP_PARAMS)
        data.update(
            {
                "name": name,
                "admin_state_up": True,
                "egress_firewall_policy_id": egress_firewall_policy_id,
                "ingress_firewall_policy_id": ingress_firewall_policy_id,
                "shared": shared,
            }
        )
        path = "%s/firewall_groups" % self.fw2_path
        res = self.client.call(
            path,
            "POST",
            data={"firewall_group": data},
            token=self.manager.identity.token,
        )
        self.logger.debug("Create openstack firewall group: %s" % truncate(res[0]))
        return res[0]["firewall_group"]

    @setup_client
    def update_group(self, oid, **kwargs):
        """Update a firewall group

        :param oid: firewall group id
        :param name: name [optional]
        :param description: description [optional]
        :param project_id: project_id [optional]
        :param egress_firewall_policy_id : The ID of the egress firewall policy for the firewall group.
        :param ingress_firewall_policy_id: The ID of the ingress firewall policy for the firewall group.
        :param list ports: A list of the IDs of the ports associated with the firewall group.
        :param bool shared: Indicates whether this firewall group is shared across all projects.
        :return: group
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        params = deepcopy(self.GROUP_PARAMS)
        params.remove("project_id")
        params.extend(
            [
                "name",
                "egress_firewall_policy_id",
                "ingress_firewall_policy_id",
                "shared",
            ]
        )
        data = set_request_params(kwargs, params)

        path = "%s/firewall_groups/%s" % (self.fw2_path, oid)
        res = self.client.call(
            path,
            "PUT",
            data={"firewall_group": data},
            token=self.manager.identity.token,
        )
        self.logger.debug("Update openstack firewall group: %s" % truncate(res[0]))
        return res[0]["firewall_group"]

    @setup_client
    def delete_group(self, oid):
        """Remove a firewall group

        :param oid: firewall group id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "%s/firewall_groups/%s" % (self.fw2_path, oid)
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack firewall group: %s" % truncate(res[0]))
        return res[0]
