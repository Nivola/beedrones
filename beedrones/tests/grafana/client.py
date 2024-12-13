# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte

import json
from time import sleep
from beecell.simple import jsonDumps
from beedrones.grafana.client_grafana import GrafanaManager
from beedrones.tests.test_util import BeedronesTestCase, runtest
from beedrones.tests.grafana.dashboard_resource import dash_resource
import logging

logger = logging.getLogger("beedrones.test")


folder_uid = None  # uuid
folder_id = None  # id numerico
folder_name = "prova-beedrones-folder"  # title

team_id = None
team_name = "team01"

user_id = None
user_email = "test_beedrones_01@test.it"

alert_uid = None
alert_name = "test.beedrones"
alert_email = "test@csi.it"

tests = [
    "test_ping",
    "test_version",
    "test_folder_list",
    "test_folder_add",
    "test_folder_get",
    "test_folder_search",
    "test_folder_list_dashboard",
    "test_team_add",
    "test_team_get",
    "test_folder_add_permission",
    "test_user_add",
    "test_user_get",
    "test_user_get_by_email",
    "test_team_user_add",
    "test_team_user_get",
    "test_team_user_delete",
    "test_user_delete",
    "test_team_delete",
    "test_dashboard_add",
    "test_dashboard_copy",
    "test_dashboard_get",
    "test_dashboard_delete",
    "test_folder_delete",
    "test_alert_notification_add",
    "test_alert_notification_get",
    "test_alert_notification_update",
    "test_alert_notification_get",
    "test_alert_notification_delete",
]


class GrafanaClientTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()

        env = "test"
        grafana_params = cls.platform.get("grafana").get(env)
        grafana_host = grafana_params.get("host", None)
        grafana_port = grafana_params.get("port", None)
        grafana_user = grafana_params.get("user", None)
        grafana_pwd = grafana_params.get("pwd", None)
        grafana_protocol = grafana_params.get("proto", "http")

        cls.client_grafana = GrafanaManager(
            host=grafana_host,
            port=grafana_port,
            protocol=grafana_protocol,
            username=grafana_user,
            pwd=grafana_pwd,
        )

    def test_ping(self):
        self.client_grafana.ping()

    def test_version(self):
        self.client_grafana.version()

    # folder
    def test_folder_list(self):
        self.client_grafana.folder.list()

    def test_folder_add(self):
        global folder_uid
        global folder_id
        res = self.client_grafana.folder.add(folder_name=folder_name)
        folder_uid = res["uid"]
        folder_id = res["id"]

    def test_folder_get(self):
        global folder_uid
        self.client_grafana.folder.get(folder_uid)

    def test_folder_search(self):
        global folder_name
        self.client_grafana.folder.search(folder_name)

    def test_folder_delete(self):
        global folder_uid
        self.client_grafana.folder.delete(folder_uid)

    def test_folder_list_dashboard(self):
        global folder_id
        self.client_grafana.dashboard.list(folder_id)

    def test_folder_add_permission(self):
        global folder_uid
        global team_id
        self.client_grafana.folder.add_permission(folder_uid, team_id_viewer=team_id)

    # team
    def test_team_add(self):
        global team_id
        res = self.client_grafana.team.add(team_name=team_name)
        team_id = res["teamId"]

    def test_team_get(self):
        global team_id
        self.client_grafana.team.get(team_id)

    def test_team_delete(self):
        global team_id
        self.client_grafana.team.delete(team_id)

    def test_team_user_add(self):
        global team_id
        global user_id
        self.client_grafana.team.add_user(team_id, user_id)

    def test_team_user_get(self):
        global team_id
        self.client_grafana.team.get_users(team_id)

    def test_team_user_delete(self):
        global team_id
        self.client_grafana.team.del_user(team_id, user_id)

    # user
    def test_user_add(self):
        global user_id
        res = self.client_grafana.user.add(email=user_email, password="test12345")
        user_id = res["id"]

    def test_user_get(self):
        global user_id
        self.client_grafana.user.get(user_id)

    def test_user_get_by_email(self):
        self.client_grafana.user.get_by_login_or_email(user_email)

    def test_user_delete(self):
        global user_id
        self.client_grafana.user.delete(user_id)

    # alert notification
    def test_alert_notification_add(self):
        global alert_uid
        res = self.client_grafana.alert_notification.add(alert_name, alert_email)
        alert_uid = res["uid"]

    def test_alert_notification_get(self):
        global alert_uid
        self.client_grafana.alert_notification.get(alert_uid)

    def test_alert_notification_update(self):
        global alert_uid
        res = self.client_grafana.alert_notification.update(alert_uid, alert_name, "upd_" + alert_email)
        alert_uid = res["uid"]

    def test_alert_notification_delete(self):
        global alert_uid
        self.client_grafana.alert_notification.delete(alert_uid)

    # dashboard
    def test_dashboard_add(self):
        global dashboard_uid
        dash = dash_resource.replace("9999999999", str(folder_id))
        json_dashboard = json.loads(dash)
        res = self.client_grafana.dashboard.add(data_dashboard=json_dashboard)
        dashboard_uid = res["uid"]

    def test_dashboard_copy(self):
        global dashboard_uid
        dashboard_to_search = "dash01"
        folder_id_to = folder_id
        organization = "org01"
        division = "div01"
        account = "acc01"
        res = self.client_grafana.dashboard.add_dashboard(
            dashboard_to_search, folder_id_to, organization, division, account
        )

    def test_dashboard_get(self):
        global dashboard_uid
        self.client_grafana.dashboard.get(dashboard_uid)

    def test_dashboard_delete(self):
        global dashboard_uid
        self.client_grafana.dashboard.delete(dashboard_uid)


if __name__ == "__main__":
    runtest(GrafanaClientTestCase, tests)
