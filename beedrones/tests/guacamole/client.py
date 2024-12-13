# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte

import gevent
from pyVmomi import vim
from beedrones.tests.test_util import BeedronesTestCase, runtest

# test
from beedrones.guacamole.client import GuacamoleClient
from beedrones.guacamole.templates import *


contid = 14
component = "NSX"


tests = [
    # 'prova',
    # 'test_get_connections',
    "test_get_connections_groups",
    # 'test_get_users',
    # 'test_get_connection_by_name',
    # 'test_add_connection_group',
    # 'test_get_connection_group'
    # 'test_add_connection'
    # 'test_create_from_template_with_win_cust',
    # system
    # #'test_ping_vsphere',
    # 'test_ping_nsx',
]


class GuacamoleClientTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()
        cls.guacamole = GuacamoleClient("84.1.2.3", username="xxx", password="", url_path="/guacamole", verify=False)

    def tearDown(self):
        BeedronesTestCase.tearDown(self)

    def wait_task(self, task):
        while task.info.state not in [
            vim.TaskInfo.State.success,
            vim.TaskInfo.State.error,
        ]:
            self.logger.info(task.info.state)
            gevent.sleep(1)

        if task.info.state in [vim.TaskInfo.State.error]:
            self.logger.info("Error: %s" % task.info.error.msg)
        if task.info.state in [vim.TaskInfo.State.success]:
            self.logger.info("Completed")

    #
    # system connections
    #
    def test_get_connections(self):
        res = self.guacamole.get_connections()
        self.logger.info(self.pp.pformat(res))

    def test_get_connections_groups(self):
        res = self.guacamole.get_connections_groups()
        self.logger.info(self.pp.pformat(res))
        self.logger.info(res)

    def test_get_connection_by_name(self):
        res = self.guacamole.get_connection_by_name(name="inst-vspher")
        self.logger.info(self.pp.pformat(res))

    def test_add_connection(self):
        payload = {
            "parentIdentifier": "2",
            "protocol": "rdp",
            "name": "inst-vsphere02-by-api",
            "parameters": {
                "username": "administrator",
                "ignore-cert": "true",
                "enable-wallpaper": "true",
                "hostname": "192.168.216.100",
                "security": "nla",
                "password": "ccc",
                "port": "3389",
            },
            "activeConnections": 0,
            "attributes": {
                "guacd-hostname": "",
                "weight": "None",
                "max-connections-per-user": "2",
                "guacd-port": "",
                "failover-only": "",
                "max-connections": "10",
                "guacd-encryption": "",
            },
        }
        res = self.guacamole.add_connection(payload=payload)
        self.logger.info(self.pp.pformat(res))

    #
    # system users
    #
    def test_get_users(self):
        res = self.guacamole.get_users()
        self.logger.info(self.pp.pformat(res))

    def test_get_connection_group(self):
        res = self.guacamole.get_connection_group_by_name("Site 03 - Vercelli 22")
        print("get-group: %s" % res)
        self.logger.info(res)

    def test_add_connection_group(self):
        payload = {
            "parentIdentifier": "ROOT",
            "name": "Site 03 - Vercelli 2",
            "type": "ORGANIZATIONAL",
            "attributes": {"max-connections": "10", "max-connections-per-user": "10"},
        }
        res = self.guacamole.add_connection_group(payload=payload)
        self.logger.info(res)

    """{"parentIdentifier":"ROOT",
        "name":"iaas-099 (Test)",
        "type":"ORGANIZATIONAL",
        "attributes":{"max-connections":"","max-connections-per-user":""}}
        '''"""

    #
    # vsphere manager
    #
    def test_ping_vsphere(self):
        res = self.util.system.ping_vsphere()
        self.logger.info(res)

    def test_ping_nsx(self):
        res = self.util.system.ping_nsx()
        self.logger.info(res)

    def test_delete_resource_pool(self):
        respool = self.util.cluster.resource_pool.get("resgroup-711")
        res = self.util.cluster.resource_pool.remove(respool)
        self.logger.info(res)


if __name__ == "__main__":
    runtest(GuacamoleClientTestCase, tests)
