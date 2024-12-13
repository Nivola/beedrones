# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.types.type_dict import dict_get
from bee_client import CmpApiManager
from beedrones.tests.test_util import BeedronesTestCase, runtest


tests = [
    "test_create_token",
    # 'test_list_resource_entity',
    # 'test_get_resource_entity',
    #
    # 'test_list_service_instance',
    # 'test_list_service_instance_by_tag',
    # 'test_list_service_instance_by_plugintype',
    # 'test_get_service_instance',
    "test_list_service_instance_by_plugintype_and_tag",
    "test_add_service_instance_tag",
    "test_list_service_instance_by_tag",
    "test_del_service_instance_tag",
    "test_list_service_instance_by_tag2",
    "test_list_security_group",
    "test_get_security_group",
    "test_add_security_group_rule",
    "test_del_security_group_rule",
]


class CmpClientTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()
        env = "test"
        # endpoints = {
        #     'auth': 'https://podto2-cmp.site02.nivolapiemonte.it:9443/stage1',
        #     'event': 'https://podto2-cmp.site02.nivolapiemonte.it:9443/stage1',
        #     'ssh': 'https://podto2-cmp.site02.nivolapiemonte.it:9443/stage1',
        #     'resource': 'https://podto2-cmp.site02.nivolapiemonte.it:9443/stage1',
        #     'service': 'https://podto2-cmp.site02.nivolapiemonte.it:9443/stage1',
        # }
        # authparams = {'type': 'keyauth', 'user': 'matricola@domnt.csi.it', 'pwd': ''}
        endpoints = {
            "auth": "https://tst-fe01.tstsddc.csi.it:443",
            "event": "https://tst-fe01.tstsddc.csi.it:443",
            "ssh": "https://tst-fe01.tstsddc.csi.it:443",
            "resource": "https://tst-fe01.tstsddc.csi.it:443",
            "service": "https://tst-fe01.tstsddc.csi.it:443",
        }
        authparams = {"type": "keyauth", "user": "admin@local", "pwd": "beehive_test"}
        cls.client = CmpApiManager(endpoints, authparams, key=None)

    def tearDown(self):
        BeedronesTestCase.tearDown(self)

    #
    # token
    #
    def test_create_token(self):
        self.client.create_token()

    #
    # resource entity
    #
    def test_list_resource_entity(self):
        r = self.client.resource.entity.list()

    def test_get_resource_entity(self):
        r = self.client.resource.entity.get(1)

    #
    # service instance
    #
    def test_list_service_instance(self):
        r = self.client.business.service.instance.list()
        res = dict_get(r, "serviceinsts.0.__meta__.definition")
        self.assertEqual(res, "Organization.Division.Account.ServiceInstance")

    def test_list_service_instance_by_plugintype(self):
        r = self.client.business.service.instance.list(plugintype="ComputeSecurityGroup")
        res = dict_get(r, "serviceinsts.0.__meta__.definition")
        self.assertEqual(res, "Organization.Division.Account.ServiceInstance")

    def test_get_service_instance(self):
        r = self.client.business.service.instance.get(1)
        res = dict_get(r, "serviceinst.id")
        self.assertEqual(res, 1)

    #
    # service instance tag
    #
    def test_list_service_instance_by_plugintype_and_tag(self):
        r = self.client.business.service.instance.list(plugintype="ComputeSecurityGroup", tags="rundeck")
        res = dict_get(r, "serviceinsts.0.__meta__.definition")
        self.assertEqual(res, "Organization.Division.Account.ServiceInstance")

    def test_add_service_instance_tag(self):
        r = self.client.business.service.instance.add_tag("ab04e63a-2f20-4ae9-a9e8-d5097378b762", tags=["prova123"])

    def test_list_service_instance_by_tag(self):
        r = self.client.business.service.instance.list(tags="prova123")
        res = dict_get(r, "serviceinsts")
        self.assertEqual(len(res), 1)

    def test_del_service_instance_tag(self):
        r = self.client.business.service.instance.del_tag("ab04e63a-2f20-4ae9-a9e8-d5097378b762", tags=["prova123"])

    def test_list_service_instance_by_tag2(self):
        r = self.client.business.service.instance.list(tags="prova123")
        res = dict_get(r, "serviceinsts")
        self.assertEqual(len(res), 0)

    #
    # security group
    #
    def test_list_security_group(self):
        r = self.client.business.netaas.sg.list()
        self.assertGreaterEqual(len(r.get("security_groups")), 1)

    def test_get_security_group(self):
        oid = "57246bc3-9fb1-4428-abad-b7211f1e66a2"
        r = self.client.business.netaas.sg.get(oid)
        self.assertEqual(r.get("groupId"), oid)

    def test_add_security_group_rule(self):
        oid = "57246bc3-9fb1-4428-abad-b7211f1e66a2"
        self.client.business.netaas.sg.add_rule(oid, "ingress", source="CIDR:10.10.10.10/32", proto="tcp", port=9000)

    def test_del_security_group_rule(self):
        oid = "57246bc3-9fb1-4428-abad-b7211f1e66a2"
        self.client.business.netaas.sg.del_rule(oid, "ingress", source="CIDR:10.10.10.10/32", proto="tcp", port=9000)


if __name__ == "__main__":
    runtest(CmpClientTestCase, tests)
