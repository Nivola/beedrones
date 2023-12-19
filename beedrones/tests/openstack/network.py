# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

import gevent

from beecell.simple import id_gen
from beedrones.tests.openstack.client import OpenstackClientTestCase
from beedrones.vsphere.client import VsphereManager
import json
import random
import os
from beedrones.tests.test_util import BeedronesTestCase, runtest
from beedrones.openstack.client import OpenstackManager

network_id = None
subnet_id = None
port_id = None
sg_id = None
router_id = None
rule_id = None
floating_ip = None

tests = [
    "test_authorize",
    # ----- network -------
    "test_network_list",
    "test_network_get",
    "test_create_network",
    "test_network_get_by_name",
    "test_update_network",
    # ----- subnet -------
    "test_network_subnet_list",
    "test_network_subnet_get",
    "test_create_subnet",
    "test_update_subnet",
    # ----- port -------
    "test_network_port_list",
    "test_network_port_get",
    "test_create_port",
    "test_update_port",
    # ----- router -------
    "test_network_router_list",
    "test_network_router_get",
    "test_network_router_create",
    "test_network_router_update",
    "test_network_router_add_interface",
    "test_network_router_remove_interface",
    "test_network_router_remove",
    # ----- security group -------
    "test_security_group_list",
    "test_security_group_get",
    "test_security_group_get_by_tenant",
    "test_security_group_create",
    "test_security_group_update",
    "test_security_group_rule_create",
    "test_security_group_rule_delete",
    "test_security_group_delete",
    # ----- ip -------
    "test_list_floating_ips",
    "test_get_floating_ip",
    ## 'test_floating_ip_create',
    ## 'test_floating_ip_update',
    ## 'test_floating_ip_remove',
    "test_delete_port",
    "test_delete_subnet",
    "test_delete_network",
]


class OpenstackNetworkTestCase(OpenstackClientTestCase):
    @classmethod
    def setUpClass(cls):
        OpenstackClientTestCase.setUpClass()

    #
    # network
    #
    def test_network_list(self):
        global network_id
        res = self.client.network.list()
        self.logger.debug(self.pp.pformat(res))
        network_id = res[0]["id"]

    def test_network_get(self):
        global network_id
        res = self.client.network.get(oid=network_id)
        self.logger.debug(self.pp.pformat(res))

    def test_network_get_by_name(self):
        global network_id
        res = self.client.network.get(name="prova-net-01")
        self.logger.debug(self.pp.pformat(res))
        network_id = res["id"]

    def test_create_network(self):
        name = "prova-net-01"
        project = self.client.project.get(name="demo")["id"]
        physical_network = "datacentre"
        qos_policy_id = None
        external = False
        shared = False
        segments = None
        network_type = "vlan"
        segmentation_id = 1900
        res = self.client.network.create(
            name,
            project,
            physical_network,
            shared,
            qos_policy_id,
            external,
            segments,
            network_type,
            segmentation_id,
        )
        self.logger.debug(self.pp.pformat(res))

    def test_update_network(self):
        global network_id
        name = "prova-net-02"
        qos_policy_id = None
        external = None
        shared = None
        segments = None
        res = self.client.network.update(network_id, name, shared, qos_policy_id, external, segments)
        self.logger.debug(self.pp.pformat(res))

    def test_delete_network(self):
        global network_id
        res = self.client.network.delete(network_id)
        self.logger.debug(self.pp.pformat(res))

    #
    # network - subnet
    #
    def test_network_subnet_list(self):
        global subnet_id
        res = self.client.network.subnet.list()
        self.logger.debug(self.pp.pformat(res))
        subnet_id = res[0]["id"]

    def test_network_subnet_get(self):
        global subnet_id
        res = self.client.network.subnet.get(oid=subnet_id)
        self.logger.debug(self.pp.pformat(res))

    def test_create_subnet(self):
        global subnet_id, network_id
        name = "prova-subnet-01"
        project = self.client.project.get(name="demo")["id"]
        gateway_ip = "10.102.188.1"
        cidr = "10.102.188.0/24"
        allocation_pools = [{"start": "10.102.188.50", "end": "10.102.188.60"}]
        enable_dhcp = True
        host_routes = []
        dns_nameservers = ["10.102.184.2", "10.102.184.3"]
        res = self.client.network.subnet.create(
            name,
            network_id,
            project,
            gateway_ip,
            cidr,
            allocation_pools,
            enable_dhcp,
            host_routes,
            dns_nameservers,
        )
        self.logger.debug(self.pp.pformat(res))
        subnet_id = res["id"]

    def test_update_subnet(self):
        global subnet_id
        name = "prova-subnet-02"
        tenant_id = None
        network_id = None
        gateway_ip = None
        cidr = None
        allocation_pools = None
        enable_dhcp = None
        host_routes = None
        dns_nameservers = None
        res = self.client.network.subnet.update(
            subnet_id,
            name,
            network_id,
            tenant_id,
            gateway_ip,
            cidr,
            allocation_pools,
            enable_dhcp,
            host_routes,
            dns_nameservers,
        )
        self.logger.debug(self.pp.pformat(res))

    def test_delete_subnet(self):
        global subnet_id
        res = self.client.network.subnet.delete(subnet_id)
        self.logger.debug(self.pp.pformat(res))

    #
    # network - port
    #
    def test_network_port_list(self):
        global port_id
        res = self.client.network.port.list()
        self.logger.debug(self.pp.pformat(res))
        port_id = res[0]["id"]

    def test_network_port_get(self):
        global port_id
        res = self.client.network.port.get(port_id)
        self.logger.debug(self.pp.pformat(res))

    def test_create_port(self):
        global port_id, network_id, subnet_id
        name = "prova-port-01"
        fixed_ips = [
            {
                "subnet_id": subnet_id,
            }
        ]
        host_id = None
        profile = None
        vnic_type = None
        device_owner = None
        device_id = None
        security_groups = None
        res = self.client.network.port.create(
            name,
            network_id,
            fixed_ips,
            host_id,
            profile,
            vnic_type,
            device_owner,
            device_id,
            security_groups,
        )
        self.logger.debug(self.pp.pformat(res))
        port_id = res["id"]

    def test_update_port(self):
        global port_id
        name = "prova-port-02"
        network_id = None
        fixed_ips = None
        host_id = None
        profile = None
        vnic_type = None
        device_owner = None
        device_id = None
        security_groups = None
        port_security_enabled = True
        res = self.client.network.port.update(
            port_id,
            name,
            network_id,
            fixed_ips,
            host_id,
            profile,
            vnic_type,
            device_owner,
            device_id,
            security_groups,
            port_security_enabled,
        )
        self.logger.debug(self.pp.pformat(res))

    def test_delete_port(self):
        global port_id
        res = self.client.network.port.delete(port_id)
        self.logger.debug(self.pp.pformat(res))

    #
    # network - ip
    #
    def test_list_floating_ips(self):
        global floating_ip
        res = self.client.network.floatingip.list()
        self.logger.debug(self.pp.pformat(res))
        floating_ip = res[0]["id"]

    def test_get_floating_ip(self):
        global floating_ip
        res = self.client.network.floatingip.get(floating_ip)
        self.logger.debug(self.pp.pformat(res))

    #
    # network - router
    #
    def test_network_router_list(self):
        global router_id
        res = self.client.network.router.list()
        self.logger.debug(self.pp.pformat(res))
        router_id = res[0]["id"]

    def test_network_router_get(self):
        global router_id
        res = self.client.network.router.get(oid=router_id)
        self.logger.debug(self.pp.pformat(res))

    def test_network_router_create(self):
        global router_id
        name = "prova-router-01"
        project = self.client.project.get(name="demo")["id"]
        network = self.client.network.get(name="rupar")["id"]
        external_ips = None
        res = self.client.network.router.create(name, project, network, external_ips)
        self.logger.debug(self.pp.pformat(res))
        router_id = res["id"]

    def test_network_router_update(self):
        global router_id
        name = "prova-router-02"
        tenant_id = None
        network = None
        external_ips = None
        res = self.client.network.router.update(router_id, name, tenant_id, network, external_ips)
        self.logger.debug(self.pp.pformat(res))

    def test_network_router_add_interface(self):
        global router_id, subnet_id
        res = self.client.network.router.add_internal_interface(router_id, subnet_id)
        self.logger.debug(self.pp.pformat(res))

    def test_network_router_remove_interface(self):
        global router_id, subnet_id
        res = self.client.network.router.delete_internal_interface(router_id, subnet_id)
        self.logger.debug(self.pp.pformat(res))

    def test_network_router_remove(self):
        global router_id
        res = self.client.network.router.delete(router_id)
        self.logger.debug(self.pp.pformat(res))

    #
    # network - security group
    #
    def test_security_group_list(self):
        global sg_id
        res = self.client.network.security_group.list()
        self.logger.debug(self.pp.pformat(res))
        sg_id = res[0]["id"]

    def test_security_group_get(self):
        global sg_id
        res = self.client.network.security_group.get(sg_id)
        self.logger.debug(self.pp.pformat(res))

    def test_security_group_get_by_tenant(self):
        project = self.client.project.get(name="demo")["id"]
        res = self.client.network.security_group.list(tenant=project)
        self.logger.debug(self.pp.pformat(res))

    def test_security_group_create(self):
        global sg_id
        project = self.client.project.get(name="demo")["id"]
        res = self.client.network.security_group.create("prova-sg-01", "prova-sg-01", project)
        self.logger.debug(self.pp.pformat(res))
        sg_id = res["id"]

    def test_security_group_update(self):
        global sg_id
        res = self.client.network.security_group.update(sg_id, "prova-sg-02", "prova-sg-02")
        self.logger.debug(self.pp.pformat(res))

    def test_security_group_delete(self):
        global sg_id
        res = self.client.network.security_group.delete(sg_id)
        self.logger.debug(self.pp.pformat(res))

    def test_security_group_rule_create(self):
        global sg_id, rule_id
        direction = "ingress"
        res = self.client.network.security_group.create_rule(
            sg_id,
            direction,
            ethertype="IPv4",
            port_range_min=1000,
            port_range_max=1010,
            protocol="TCP",
            remote_group_id=None,
            remote_ip_prefix="10.100.2.0/24",
        )
        self.logger.debug(self.pp.pformat(res))
        rule_id = res["id"]

    def test_security_group_rule_delete(self):
        global rule_id
        res = self.client.network.security_group.delete_rule(rule_id)
        self.logger.debug(self.pp.pformat(res))


if __name__ == "__main__":
    runtest(OpenstackNetworkTestCase, tests)
