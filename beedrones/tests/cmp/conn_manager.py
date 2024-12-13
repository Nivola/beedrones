# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from bee_client.conn_manager import CmpApiConnectionManager
from beedrones.tests.test_util import BeedronesTestCase, runtest


tests = [
    "test_ping",
    "test_db_mysql_ping",
    # 'test_db_mysql_add_schema',
    # 'test_db_mysql_get_schemas',
    # 'test_db_mysql_del_schema',
    # 'test_db_mysql_get_tables',
    # 'test_db_mysql_add_user',
    # 'test_db_mysql_get_users',
    # 'test_db_mysql_del_user',
    #
    # 'test_db_postgres_ping',
    # 'test_db_postgres_add_schema',
    # 'test_db_postgres_get_schemas',
    # 'test_db_postgres_del_schema',
    # 'test_db_postgres_get_tables',
    # 'test_db_postgres_add_user',
    # 'test_db_postgres_get_users',
    # 'test_db_postgres_del_user',
]


class CmpApiConnectionManagerTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()
        env = "test"
        endpoint = "https://dev-node01.tstsddc.csi.it"
        token = "token1"
        key = (
            "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUFzK01ZUl"
            "RnRzhhUjNxa01OUmkyUApxbm9wdktYMUprTU5QSWNUcFJNbjgxQndOditzaU1BMjVoZ3R1VWduajNNTnVVT3A4bS83UUxrbFRWMFhl"
            "L01jCkZ2UXM1V0dtTkFFTWRXOG93czlsTmd6TTN1VnlUNWkyb1BZbFhxd1pIaU8xQ3dtSStSNlE5Yy9qcDdtVU9XTTAKMERLRnM3YV"
            "BYVXlNMHd4djk5M1cwemdZQUUxUTh0VWlndGhhbGhyamp6R0tuRnQydm1jZGZkSTQ5bjdZUXRhMQpiVXlKQ21HNitkRnZPNEJHMEtS"
            "bVVlL3hCUWYyTmwvWmQrV2F2R0p1TkJzYy9sV3A1dDdNNi9lK3MwT1lldlRSCmdTYkN6b3lJL1dNaXFHRmM4YVZOL2UrOUNvZE5ta1"
            "kwUlhFSHk5WDlndVpiaDdpVklVY2J5cnAyOGRmR2hiY1EKVVFJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=="
        )
        cls.client = CmpApiConnectionManager(endpoint, token, key=key, timeout=30.0)

        # db mysql
        cls.mysql_config = ["mysql", "10.102.185.227", "LGi(N4t37wgfofbei."]
        cls.mysql_schema_name = "prova"
        cls.mysql_user_name = "prova@%"
        cls.mysql_user_pwd = "dhy76e-y3Er"

        # db postgres
        cls.postgres_config = ["postgres", "10.102.185.232", "QFr8On)BNxcAyj(7)m"]
        cls.postgres_schema_name = "prova"
        cls.postgres_user_name = "prova"
        cls.postgres_user_pwd = "dhy76e-y3Er"

    def tearDown(self):
        BeedronesTestCase.tearDown(self)

    #
    # token
    #
    def test_ping(self):
        res = self.client.sys.ping()
        self.assertTrue(res)
        self.assertEqual(res, {"ping": True})

    #
    # db mysql
    #
    def test_db_mysql_ping(self):
        self.client.db.setup(*self.mysql_config)
        res = self.client.db.ping()
        self.assertEqual(res, {"ping": True})

    def test_db_mysql_add_schema(self):
        self.client.db.setup(*self.mysql_config)
        res = self.client.db.add_schema(self.mysql_schema_name)
        self.assertEqual(res, {"schemas": {"name": self.mysql_schema_name}})

    def test_db_mysql_get_schemas(self):
        self.client.db.setup(*self.mysql_config)
        res = self.client.db.get_schemas()
        # self.assertEqual(res, {'schema': self.mysql_schema_name})

    def test_db_mysql_del_schema(self):
        self.client.db.setup(*self.mysql_config)
        res = self.client.db.del_schema(self.mysql_schema_name)
        self.assertEqual(res, {"schemas": {"name": self.mysql_schema_name}})

    def test_db_mysql_get_tables(self):
        self.client.db.setup(*self.mysql_config)
        res = self.client.db.get_tables("mysql")
        # self.assertEqual(res, {'schema': self.mysql_schema_name})

    def test_db_mysql_add_user(self):
        self.client.db.setup(*self.mysql_config)
        res = self.client.db.add_user(self.mysql_user_name, self.mysql_user_pwd)
        self.assertEqual(res, {"users": {"name": self.mysql_user_name}})

    def test_db_mysql_get_users(self):
        self.client.db.setup(*self.mysql_config)
        res = self.client.db.get_users()
        # self.assertEqual(res, {'user': self.mysql_user_name})

    def test_db_mysql_del_user(self):
        self.client.db.setup(*self.mysql_config)
        res = self.client.db.del_user(self.mysql_user_name)
        self.assertEqual(res, {"users": {"name": self.mysql_user_name}})

    #
    # db postgres
    #
    def test_db_postgres_ping(self):
        self.client.db.setup(*self.postgres_config)
        res = self.client.db.ping()
        self.assertEqual(res, {"ping": True})

    def test_db_postgres_add_schema(self):
        self.client.db.setup(*self.postgres_config)
        res = self.client.db.add_schema(self.postgres_schema_name)
        self.assertEqual(res, {"schemas": {"name": self.postgres_schema_name}})

    def test_db_postgres_get_schemas(self):
        self.client.db.setup(*self.postgres_config)
        res = self.client.db.get_schemas()
        # self.assertEqual(res, {'schema': self.postgres_schema_name})

    def test_db_postgres_del_schema(self):
        self.client.db.setup(*self.postgres_config)
        res = self.client.db.del_schema(self.postgres_schema_name)
        self.assertEqual(res, {"schemas": {"name": self.postgres_schema_name}})

    def test_db_postgres_get_tables(self):
        self.client.db.setup(*self.postgres_config)
        res = self.client.db.get_tables("oracle")
        # self.assertEqual(res, {'schema': self.mysql_schema_name})

    def test_db_postgres_add_user(self):
        self.client.db.setup(*self.postgres_config)
        res = self.client.db.add_user(self.postgres_user_name, self.postgres_user_pwd)
        self.assertEqual(res, {"users": {"name": self.postgres_user_name}})

    def test_db_postgres_get_users(self):
        self.client.db.setup(*self.postgres_config)
        res = self.client.db.get_users()
        # self.assertEqual(res, {'user': self.postgres_user_name})

    def test_db_postgres_del_user(self):
        self.client.db.setup(*self.postgres_config)
        res = self.client.db.del_user(self.postgres_user_name)
        self.assertEqual(res, {"users": {"name": self.postgres_user_name}})


if __name__ == "__main__":
    runtest(CmpApiConnectionManagerTestCase, tests)
