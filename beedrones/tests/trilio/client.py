# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

import datetime
from time import sleep
from beecell.simple import id_gen
from beedrones.trilio.client import TrilioManager
from beedrones.tests.test_util import BeedronesTestCase, runtest
from beedrones.openstack.client import OpenstackManager


tests = [
    "test_authorize",
    "test_get_global_job_scheduler",
    "test_workloads_types",
    "test_workloads_create",
    "test_workloads_list",
    "test_workloads_list_by_project",
    "test_workloads_get",
    "test_workloads_delete",
    "test_snapshots_list",
    "test_snapshots_list_by_project",
    "test_snapshots_list_by_workload",
    "test_snapshots_get",
]

workload = "be21c891-16f7-494a-9a7b-bd1c1c2f8ebc"
snapshot = None
instance = "383fb185-5966-4852-a6b1-e6a1816fcc20"
project_id = "302bee047df44ef5ae56589de5719631"


class TrilioManagerTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()

        env = "test"
        params = cls.platform.get("openstack").get(env)
        cls.oclient = OpenstackManager(uri=params.get("uri", None), default_region=params.get("region", None))
        cls.client = TrilioManager(cls.oclient)

        cls.user = params.get("user", None)
        cls.pwd = params.get("pwd", None)
        cls.region = params.get("region", None)
        cls.project = params.get("project", None)
        cls.domain = params.get("domain", None)

    def test_ping(self):
        res = self.client.ping()

    def test_authorize(self):
        res = self.oclient.authorize(self.user, self.pwd, project=self.project, domain=self.domain)

    def test_get_global_job_scheduler(self):
        res = self.client.job_scheduler.get_global_job_scheduler()

    def test_workloads_types(self):
        res = self.client.workload.types()

    def test_workloads_create(self):
        global instance, project_id
        name = "test-workload-%s" % id_gen()
        workload_type_id = [t["id"] for t in self.client.workload.types() if t["name"] == "Parallel"][0]
        instances = [instance]
        now = datetime.datetime.today()
        start_date = "%s/%s/%s" % (now.day, now.month, now.year)
        self.oclient.authorize(self.user, self.pwd, project=None, domain=self.domain, project_id=project_id)
        res = self.client.workload.add(
            name,
            workload_type_id,
            instances,
            interval="1hr",
            fullbackup_interval=2,
            snapshots_to_retain=4,
            start_date=start_date,
        )
        workload = res["id"]
        status = res["status"]
        while status not in ["available", "error"]:
            res = self.client.workload.get(workload)
            status = res["status"]
            sleep(2)

    def test_workloads_list(self):
        global workload
        res = self.client.workload.list()
        workload = res[0]

    def test_workloads_list_by_project(self):
        global workload
        project = self.oclient.project.get(oid=workload["project_id"])
        self.oclient.authorize(self.user, self.pwd, project=project["name"], domain=self.domain)
        res = self.client.workload.list()
        workload = res[0]

    def test_workloads_get(self):
        global workload
        res = self.client.workload.get(workload)

    def test_workloads_delete(self):
        global workload
        res = self.client.workload.delete(workload)

    def test_snapshots_list(self):
        res = self.client.snapshot.list(all=True)

    def test_snapshots_list_by_project(self):
        global workload
        global snapshot
        project = self.oclient.project.get(oid=workload["project_id"])
        self.oclient.authorize(self.user, self.pwd, project=project["name"], domain=self.domain)
        res = self.client.snapshot.list()
        snapshot = res[0]

    def test_snapshots_list_by_workload(self):
        global workload
        global snapshot
        project = self.oclient.project.get(oid=workload["project_id"])
        self.oclient.authorize(self.user, self.pwd, project=project["name"], domain=self.domain)
        res = self.client.snapshot.list(workload_id=workload["id"])
        snapshot = res[0]

    def test_snapshots_get(self):
        global workload
        global snapshot
        project = self.oclient.project.get(oid=workload["project_id"])
        self.oclient.authorize(self.user, self.pwd, project=project["name"], domain=self.domain)
        res = self.client.snapshot.get(workload["project_id"], snapshot["id"])


if __name__ == "__main__":
    runtest(TrilioManagerTestCase, tests)
