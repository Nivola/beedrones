# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte
from time import sleep

from beecell.file import read_file
from beecell.types.type_dict import dict_get
from beedrones.rancher.client import RancherManager
from beedrones.tests.test_util import BeedronesTestCase, runtest


tests = [
    "test_create_token",
    "test_ping",
    "test_version",
    "test_get_cluster",
    "test_create_cluster",
    #'test_get_registration_cmd',
    #'test_delete_cluster',
]

cluster_id = None


class RancherClientTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()

        cls.user = "admin"
        cls.password = "cs1rancher"
        uri = "https://tst-nivola-rancher-nginx.tstsddc.csi.it/v3"
        cls.client = RancherManager(uri)

    def tearDown(self):
        BeedronesTestCase.tearDown(self)

    #
    # token
    #
    def test_create_token(self):
        self.client.authorize(user=self.user, pwd=self.password, token=None, key=None)

    #
    # base
    #
    def test_ping(self):
        self.client.ping()

    def test_version(self):
        self.client.version()

    #
    # cluster
    #
    def test_get_cluster(self):
        self.client.cluster.list()

    def test_create_cluster(self):
        global cluster_id
        data = read_file("./_res/cluster.json")
        res = self.client.cluster.add(data)
        cluster_id = res.get("id")

    def test_get_registration_cmd(self):
        global cluster_id
        sleep(2)
        res = self.client.cluster.get_registration_cmd(cluster_id)
        self.logger.debug(res.get("token"))

    def test_delete_cluster(self):
        global cluster_id
        self.client.cluster.delete(cluster_id)


if __name__ == "__main__":
    runtest(RancherClientTestCase, tests)
