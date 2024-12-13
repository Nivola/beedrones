# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte

from time import sleep
from beedrones.elk.client_elastic import ElasticManager
from beedrones.elk.client_kibana import KibanaManager
from beedrones.tests.test_util import BeedronesTestCase, runtest

space_id = None
role_name = None
dashboard_id = None
str_dashboard = None

tests = [
    "test_ping",
    "test_version",
    # 'test_space_list',
    # 'test_space_add',
    # 'test_space_get',
    # 'test_space_delete',
    # 'test_space_find_dashboard',
    # 'test_space_export_dashboard',
    # 'test_space_import_dashboard',
    "test_space_add_dashboard",
    #'test_role_list',
    #'test_role_add',
    #'test_role_get',
    #'test_role_mapping_add',
    #'test_role_mapping_get',
    #'test_role_mapping_del',
    #'test_role_delete',
    #'test_user_add',
    #'test_user_get',
    #'test_user_del',
]


class ElkClientTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()

        env = "test"
        kibana_params = cls.platform.get("kibana").get(env)
        kibana_uri = kibana_params.get("uri", None)
        kibana_user = kibana_params.get("user", None)
        kibana_pwd = kibana_params.get("pwd", None)

        elastic_params = cls.platform.get("elastic").get(env)
        elastic_host = elastic_params.get("host", None)
        elastic_user = elastic_params.get("user", None)
        elastic_pwd = elastic_params.get("pwd", None)

        cls.client_kibana = KibanaManager(uri=kibana_uri, user=kibana_user, passwd=kibana_pwd)
        cls.client_elastic = ElasticManager(host=elastic_host, user=elastic_user, pwd=elastic_pwd)

    def test_ping(self):
        self.client_kibana.ping()

    def test_version(self):
        self.client_kibana.version()

    # space
    def test_space_list(self):
        self.client_kibana.space.list()

    def test_space_add(self):
        global space_id
        space_id = "id_prova_space"
        res = self.client_kibana.space.add(space_id, "nome_prova", "desc prova", "#aabbcc", "PS")
        space_id = res["id"]

    def test_space_get(self):
        global space_id
        self.client_kibana.space.get(space_id)

    def test_space_find_dashboard(self):
        global dashboard_id
        # space_id = 'Default' # lo space di default non ha un path!
        space_id = None
        search = "Okta"
        dashboard_id = self.client_kibana.space.find_dashboard(space_id, search)

    def test_space_export_dashboard(self):
        global str_dashboard
        str_dashboard = self.client_kibana.space.export_dashboard(dashboard_id)

    def test_space_import_dashboard(self):
        space_id = "test_space_id_0001"
        self.client_kibana.space.import_dashboard(space_id, str_dashboard)

    def test_space_add_dashboard(self):
        space_id_from = None
        dashboard_to_search = "Okta"
        space_id_to = "test_space_id_0001"
        index_pattern = None
        self.client_kibana.space.add_dashboard(space_id_from, dashboard_to_search, space_id_to, index_pattern)

    def test_space_delete(self):
        global space_id
        self.client_kibana.space.delete(space_id)

    # role
    def test_role_list(self):
        self.client_kibana.role.list()

    def test_role_add(self):
        global role_name
        role_name = "name_prova_role_21072021"
        res = self.client_kibana.role.add(role_name, "*.alert-prova", "id_prova_space")

    def test_role_get(self):
        global role_id
        self.client_kibana.role.get(role_name)

    def test_role_delete(self):
        global role_id
        self.client_kibana.role.delete(role_name)

    # role mapping
    def test_role_mapping_add(self):
        global role_name
        role_mapping_name = "mapping_prova_21072021"
        role_name = "name_prova_role"
        users_email = ["xxx@csi.it", "aaa.bbb@csi.it", "ccc.ddd@csi.it"]
        realm_name = "ldap-internal"
        res = self.client_elastic.role_mapping.add(role_mapping_name, role_name, users_email, realm_name)

    def test_role_mapping_get(self):
        global role_id
        self.client_elastic.role_mapping.get()

    def test_role_mapping_del(self):
        global role_id
        self.client_elastic.role_mapping.delete("mapping_prova")

    # user
    def test_user_add(self):
        global user_name
        user_name = "test_user_elastic_21072021"
        password = "test12345"
        # role_name = 'admin'
        full_name = "utente test 01"
        email = "test_user_elastic_01@csi.it"
        res = self.client_elastic.user.add(user_name, password, role_name, full_name, email)

    def test_user_get(self):
        global user_name
        self.client_elastic.user.get(user_name)

    def test_user_del(self):
        global user_name
        self.client_elastic.user.delete(user_name)


if __name__ == "__main__":
    runtest(ElkClientTestCase, tests)
