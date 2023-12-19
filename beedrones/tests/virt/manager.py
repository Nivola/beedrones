# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beedrones.tests.test_util import BeedronesTestCase, runtest
from beedrones.virt.manager import VirtManager

tests = [
    "test_is_alive",
    "test_ping",
    "test_info",
    "test_get_last_error",
    "test_stats",
    "test_ext_info",
    "test_get_network_conf",
    "test_get_datastores",
    "test_get_domains",
    "test_get_devices",
    "test_get_domains",
    "test_get_domain",
    "test_get_domain_info",
    "test_get_domain_ext_info",
    "test_get_domain_job",
    "test_get_domain_qemu_guest_ping",
    "test_get_domain_qemu_guest_info",
    "test_get_domain_qemu_guest_exec",
]


class VirtManagerTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()
        self = cls

        env = "test"
        params = self.platform.get("virt").get(env)
        host = params.get("host", None)
        user = params.get("user", None)
        keyfile = params.get("keyfile", None)
        self.client = VirtManager("virt1", host, user=user, key=keyfile)
        self.server = self.client.connect()

        self.domain = "instance-000002a6"

    @classmethod
    def tearDownClass(cls):
        cls.server.close()
        BeedronesTestCase.tearDownClass()

    # hypervisor
    def test_is_alive(self):
        res = self.server.is_alive()
        self.logger.debug(res)

    def test_ping(self):
        res = self.server.ping()
        self.logger.debug(res)

    def test_info(self):
        res = self.server.info()
        self.logger.debug(self.pp.pformat(res))

    def test_get_last_error(self):
        res = self.server.get_last_error()
        self.logger.debug(self.pp.pformat(res))

    def test_tree(self):
        res = self.server.tree()
        self.logger.debug(self.pp.pformat(res))

    def test_stats(self):
        res = self.server.stats()
        self.logger.debug(self.pp.pformat(res))

    def test_nw_filters_list(self):
        res = self.server.nw_filters_list()
        self.logger.debug(res)

    def test_ext_info(self):
        res = self.server.ext_info()
        self.logger.debug(self.pp.pformat(res))

    def test_get_network_conf(self):
        res = self.server.get_network_conf()
        self.logger.debug(self.pp.pformat(res))

    def test_get_datastores(self):
        res = self.server.get_datastores()
        self.logger.debug(self.pp.pformat(res))

    def test_get_datastore_info(self):
        res = self.server.get_datastore_info(self.ds_id)
        self.logger.debug(self.pp.pformat(res))

    def test_get_datastore_tree(self):
        res = self.server.gte_datastore_tree(id=self.ds_id)
        self.logger.debug(self.pp.pformat(res))

    def test_get_devices(self):
        res = self.server.get_devices()
        self.logger.debug(self.pp.pformat(res))

    def test_get_domains(self):
        status = 1
        res = self.server.get_domains(status=status)
        self.logger.debug(self.pp.pformat(res))

    def test_get_domain(self):
        res = self.server.get_domain(name=self.domain)
        self.logger.debug(self.pp.pformat(res))

    def test_get_domain_info(self):
        res = self.server.get_domain(name=self.domain)
        self.logger.debug(self.pp.pformat(res.info()))

    def test_get_domain_ext_info(self):
        res = self.server.get_domain(name=self.domain)
        self.logger.debug(self.pp.pformat(res.ext_info()))

    def test_get_domain_job(self):
        dom = self.server.get_domain(name=self.domain)
        res = dom.get_job()
        self.logger.debug(self.pp.pformat(res))

    def test_get_domain_qemu_guest_ping(self):
        dom = self.server.get_domain(name=self.domain)
        res = dom.qemu_guest_ping()
        self.logger.debug(self.pp.pformat(res))

    def test_get_domain_qemu_guest_info(self):
        dom = self.server.get_domain(name=self.domain)
        res = dom.qemu_guest_info()
        self.logger.debug(self.pp.pformat(res))

    def test_get_domain_qemu_guest_exec(self):
        dom = self.server.get_domain(name=self.domain)
        res = dom.qemu_guest_exec("ls", ["-la"])
        self.logger.debug(self.pp.pformat(res))


if __name__ == "__main__":
    runtest(VirtManagerTestCase, tests)
