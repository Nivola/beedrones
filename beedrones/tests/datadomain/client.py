# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from time import sleep
from beedrones.datadomain.client import DataDomainManager
from beedrones.tests.test_util import BeedronesTestCase, runtest


tests = [
    #'test_ping',
    "test_authorize",
    "test_get_token",
    "test_get_system_info",
    "test_get_system_settings",
    "test_get_networks",
    "test_get_mtrees",
    "test_get_nfs_exports",
    "test_delete_token"
    #'test_version',
]


class DataDomainClientTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()

        env = "podvc"
        params = cls.platform.get("datadomain").get(env)
        cls.client = DataDomainManager(uri=params.get("uri", None))
        cls.user = params.get("user", None)
        cls.pwd = params.get("pwd", None)
        cls.system_id = "99f46d3e418630a1:7af526b9c148f32b"

    def __wait_for_job(self, job_query_func, job_id, maxtime=600, delta=1):
        job = job_query_func(job_id)
        status = job["status"]
        elapsed = 0
        while status not in ["successful", "failed", "error", "canceled"]:
            job = job_query_func(job_id)
            status = job["status"]
            sleep(delta)
            elapsed += delta
            if elapsed >= maxtime:
                raise TimeoutError("job %s query timeout" % job_id)
        if status in ["failed", "error"]:
            self.logger.error(job["result_traceback"])
            raise Exception("job %s error" % job_id)
        elif status == "cancelled":
            self.logger.error(job["job %s cancelled" % job_id])
            raise Exception("job %s cancelled" % job_id)
        else:
            self.logger.info("job %s successful" % job_id)

    def test_ping(self):
        self.client.ping()

    def test_version(self):
        self.client.version()

    def test_authorize(self):
        self.client.authorize(user=self.user, pwd=self.pwd)

    def test_get_token(self):
        self.client.get_token()

    def test_delete_token(self):
        self.client.delete_token()

    def test_get_system_info(self):
        res = self.client.system.get()
        print(res)

    def test_get_system_settings(self):
        res = self.client.system.get_settings(self.system_id)
        print(res)

    def test_get_networks(self):
        res = self.client.network.list(self.system_id)
        print(res)

    def test_get_mtrees(self):
        res = self.client.mtree.list(self.system_id)
        print(res)

    def test_get_nfs_exports(self):
        res = self.client.protocol.nfs.list(self.system_id)
        print(res)


if __name__ == "__main__":
    runtest(DataDomainClientTestCase, tests)
