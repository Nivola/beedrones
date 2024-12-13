# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from time import sleep
from beedrones.awx.client import AwxManager
from beedrones.tests.test_util import BeedronesTestCase, runtest


inventory = None
inventory_source = None
inventory_script = None
inventory_group = None
inventory_host = None
organization = None
user = None
credential = None
project = None
job = None
project_job = None
job_template = None

tests = [
    "test_ping",
    "test_authorize",
    "test_version",
    "test_user_list",
    "test_user_add",
    "test_user_get",
    "test_user_delete",
    "test_organization_list",
    "test_organization_get",
    "test_organization_get_users",
    "test_inventory_add",
    "test_inventory_list",
    "test_inventory_get",
    "test_inventory_delete",
    "test_credential_list",
    "test_credential_type_list",
    "test_credential_get",
    "test_credential_add_ssh1",
    "test_credential_delete",
    "test_credential_add_ssh2",
    "test_credential_delete",
    "test_credential_add_git",
    "test_credential_delete",
    "test_project_add",
    "test_project_list",
    "test_project_get",
    "test_project_sync",
    "test_project_job_list",
    "test_project_job_get",
    "test_project_job_events",
    "test_project_job_stdout",
    "test_job_template_add",
    "test_job_template_list",
    "test_job_template_get",
    "test_job_template_launch",
    "test_job_template_delete",
    "test_job_list",
    "test_job_get",
    "test_job_stdout",
    "test_job_events",
    "test_project_delete",
]


class AwxClientTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()

        env = "test"
        params = cls.platform.get("awx").get(env)
        cls.client = AwxManager(uri=params.get("uri", None))
        cls.user = params.get("user", None)
        cls.pwd = params.get("pwd", None)

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

    # user
    def test_user_list(self):
        self.client.user.list()

    def test_user_add(self):
        global user
        res = self.client.user.add("prova_user", "prova")
        user = res["id"]

    def test_user_get(self):
        global user
        self.client.user.get(user)

    def test_user_delete(self):
        global user
        self.client.user.delete(user)

    def test_organization_list(self):
        res = self.client.organization.list()
        global organization
        organization = res[0]["id"]

    # organization
    def test_organization_get(self):
        global organization
        self.client.organization.get(organization)

    def test_organization_get_users(self):
        global organization
        self.client.organization.get_users(organization)

    # inventory
    def test_inventory_list(self):
        global organization, inventory
        res = self.client.inventory.list()
        inventory = res[0]["id"]

    def test_inventory_add(self):
        global organization, inventory
        res = self.client.inventory.add("prova_inventory", organization)
        inventory = res["id"]

    def test_inventory_get(self):
        global inventory
        self.client.inventory.get(inventory)

    def test_inventory_delete(self):
        global inventory
        self.client.inventory.delete(inventory)

    # inventory source
    def test_inventory_source_list(self):
        global inventory
        res = self.client.inventory.source_list(inventory)
        global inventory_source
        inventory_source = res[0]["id"]

    def test_inventory_source_get(self):
        global inventory_source
        self.client.inventory.source_get(inventory_source)

    def test_inventory_source_sync(self):
        global inventory_source
        self.client.inventory.source_sync(inventory_source)

    # inventory host
    def test_inventory_host_list(self):
        global inventory
        res = self.client.inventory.host_list(inventory)
        global inventory_host
        inventory_host = res[0]["id"]

    def test_inventory_host_get(self):
        global inventory_host
        self.client.inventory.host_get(inventory_host)

    # inventory group
    def test_inventory_group_list(self):
        global inventory
        res = self.client.inventory.group_list(inventory)
        global inventory_group
        inventory_group = res[0]["id"]

    def test_inventory_group_get(self):
        global inventory_group
        self.client.inventory.group_get(inventory_group)

    # inventory script
    def test_inventory_script_list(self):
        self.client.inventory_script.list()

    def test_inventory_script_add(self):
        global organization, inventory_script
        script = "#!/bin/bash\nsource /opt/beehive/bin/activate\n"
        res = self.client.inventory_script.add("prova_inventory_script", organization, script)
        inventory_script = res["id"]

    def test_inventory_script_get(self):
        global inventory_script
        self.client.inventory_script.get(inventory_script)

    def test_inventory_script_delete(self):
        global inventory_script
        self.client.inventory_script.delete(inventory_script)

    # inventory host
    def test_host_add(self):
        global inventory_host
        self.client.host.add("localhost", inventory_host)

    # job
    def test_job_list(self):
        global job
        res = self.client.job.list(page=1)
        job = res[2]["id"]

    def test_job_get(self):
        global job
        self.client.job.get(job)

    def test_job_stdout(self):
        global job
        self.client.job.stdout(job)

    def test_job_events(self):
        global job
        self.client.job.events(job)

    def test_job_delete(self):
        global job
        self.client.job.delete(job)

    def test_job_cancel(self):
        global job
        self.client.job.cancel(job)

    def test_job_relaunch(self):
        global job
        self.client.job.relaunch(job)

    # project
    def test_project_list(self):
        global project
        res = self.client.project.list(page=1)
        project = res[0]["id"]

    def test_project_add(self):
        global project, credential
        try:
            res = self.client.credential.add_git("gitlab.csi.it-cred", 1, "ansible", "xxx")
            credential = res["id"]
        except:
            res = self.client.credential.list(name="gitlab.csi.it-cred")
            credential = res[0]["id"]
        res = self.client.project.add(
            "prova_prj",
            scm_type="git",
            scm_url="https://gitlab.csi.it/nivola/ansible/zabbix-agent",
            scm_branch="master",
            credential=credential,
        )
        project = res["id"]

    def test_project_get(self):
        global project
        self.client.project.get(project)

    def test_project_sync(self):
        project = self.client.project.list(name="prova_prj")
        job = self.client.project.sync(project[0]["id"])
        self.__wait_for_job(self.client.project.job.get, job["id"], delta=2)

    def test_project_delete(self):
        global project, credential
        self.client.project.delete(project)
        self.client.credential.delete(credential)

    # project job
    def test_project_job_list(self):
        global project_job
        project = self.client.project.list(name="prova_prj")
        res = self.client.project.job.list(project=project[0]["id"])
        project_job = res[-1]["id"]

    def test_project_job_get(self):
        global project_job
        self.client.project.job.get(project_job)

    def test_project_job_events(self):
        global project_job
        self.client.project.job.events(project_job)

    def test_project_job_stdout(self):
        global project_job
        self.client.project.job.stdout(project_job)

    # credential
    def test_credential_list(self):
        global credential
        res = self.client.credential.list(page=1)
        credential = res[0]["id"]

    def test_credential_add(self):
        global credential
        res = self.client.credential.add("prova_cred")
        credential = res["id"]

    def test_credential_add_ssh1(self):
        global credential
        res = self.client.credential.add_ssh("prova_cred1", 1, "prova", password="prova")
        credential = res["id"]

    def test_credential_add_ssh2(self):
        # to generate a private key use
        # ssh-keygen -t rsa -b 1024 -C "your_email@example.com"
        global credential
        priv_key = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "Proc-Type: 4,ENCRYPTED\n"
            "DEK-Info: AES-128-CBC,0B009C3FAB0C2E22D07FE000BEC911EF\n\n"
            "b8grdAtM80jNgzEQAE2pxjeJQEZJQbJF9681z8f0+IkJA7IGogPypM/rUGtz2Tqb\n"
            "ank+VYP9oaRBmfcmhPiW2kshqLsfcLjLLxbSYsi0pj5U0tBUSWpm3jyNOEyVLW3F\n"
            "MQeO3M2iemOKvNDUqMAXRmFBlz7/Es7m6WThScE20XCgsIna7Q1xmDs0FLh8dwRB\n"
            "pNuPjm7MM1SzYhdMsiXu8bDaVdfMy4LX56+FwE0C43XnfjnBtu8Zdb9Jr22uYTYp\n"
            "zZQw+DJzgJUa0gYLhLnfCSJ5X125UFlHAPRrYCaTH4nlQU6rRNB5HFf9fSkp0wKF\n"
            "BHjlCbgFdLCt7KsZYRPYrcB4jA1or5wusNhOABTPfTt8ZfP3I603OTFNGHntf7yy\n"
            "aykUCWegt0nqqivuMQ7nXZQGNCOhmiXQKz3JmpbPL3VnsfIL0mzqNwO3L63KDqxU\n"
            "BW74X+Hn9x3U28OxtStYihD0fVU+CKdKncdiY4Sjn1z9ZtAccfbs8mh9/I2osZEm\n"
            "v6SYcKZEn0W+bIetZOEnTj01x1FHmkEfXIaOum++Xdq4hjEvQXqGovzkPsTNJgLl\n"
            "OaVsgcZxTrag8Kd5CsmKFi+8PJ48OI9DS78ZYzwaSk8cpbgdnbgpUfOhHoSiB9wW\n"
            "BU45iE1ESc2G5MS2EgTNbcff2rKdHLCD/RQkwHEjQGCb/VXYS7L937EDY2nBSGmZ\n"
            "6ZnEoXMfcVU26AB8gZmwAD3+oPzDQUvPbVzwXYZwyYgQ8dqWdDvkSM47ahmJIfnQ\n"
            "YZ2E9545BSNfT8dCpv4fj0jN/rje0HiCBH0OEQafCJWT5+86uUxGcR3QomUuvj1D\n"
            "-----END RSA PRIVATE KEY-----"
        )
        pass_phrase = "prova"
        res = self.client.credential.add_ssh(
            "prova_cred2", 1, "prova", ssh_key_data=priv_key, ssh_key_unlock=pass_phrase
        )
        credential = res["id"]

    def test_credential_add_git(self):
        global credential
        res = self.client.credential.add_git("prova_cred3", 1, "user", "password")
        credential = res["id"]

    def test_credential_get(self):
        global credential
        self.client.credential.get(credential)

    def test_credential_type_list(self):
        global credential
        self.client.credential.type_list()

    def test_credential_delete(self):
        global credential
        self.client.credential.delete(credential)

    # job_template
    def test_job_template_list(self):
        global job_template
        res = self.client.job_template.list(page=1)
        job_template = res[0]["id"]

    def test_job_template_add(self):
        global job_template, organization
        inventory = "nivola_cmp_stage_inventory"
        project = "prova_prj"
        playbook = "zabbix-agent.yml"
        project = self.client.project.list(name=project)[0]["id"]

        try:
            inventory = self.client.inventory.list(name=inventory)[0]["id"]
        except:
            inventory = self.client.inventory.add(inventory, organization)["id"]

        # create template
        res = self.client.job_template.add(
            "prova_template",
            "run",
            inventory,
            project,
            playbook,
            ask_credential_on_launch=True,
            ask_variables_on_launch=True,
            ask_limit_on_launch=True,
        )
        job_template = res["id"]

    def test_job_template_launch(self):
        job_template = self.client.job_template.list(name="prova_template")

        try:
            # create ssh key
            credential = self.client.credential.add_ssh("prova_template_cred", 1, "root", password="xxx")
        except:
            credential = self.client.credential.list(name="prova_template_cred")

        limit = "provola-dctest.site03.nivolapiemonte.it"
        extra_vars = {
            "host_groups": ["awx_group_prova", "awx_group_prova1"],
            "host_templates": ["Template OS Linux"],
            "zabbix_server_password": "xxx",
            "zabbix_server": "10.138.218.29",
            "zabbix_server_proxy": "10.138.200.15",
            "zabbix_server_proxy_name": "zabbixproxyweb",
        }
        params = {
            "credentials": [credential[0]["id"]],
            "extra_vars": extra_vars,
            "limit": limit,
        }
        job = self.client.job_template.launch(job_template[0]["id"], **params)
        self.__wait_for_job(self.client.job.get, job["id"], delta=2)

    def test_job_template_get(self):
        global job_template
        self.client.job_template.get(job_template)

    def test_job_template_delete(self):
        global job_template
        self.client.job_template.delete(job_template)


if __name__ == "__main__":
    runtest(AwxClientTestCase, tests)
