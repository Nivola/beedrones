# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

from datetime import datetime, timedelta
from time import mktime
from beedrones.zabbix.client import ZabbixManager
from beedrones.tests.test_util import BeedronesTestCase, runtest


host = None
template = None

tests = [
    'test_ping',
    'test_version',
    'test_authorize',

    'test_host_list',
    'test_host_get',
    'test_host_groups',
    ## 'test_host_link_template',
    ## 'test_host_unlink_template',
    'test_host_items',
    'test_host_triggers',

    'test_template_list',
    'test_template_get',
    ## 'test_template_export',
    ## 'test_template_load',
    ## 'test_template_delete',

    'test_group_list',
    'test_group_get',
    'test_group_get_by_name',
    'test_group_get_items',
    'test_group_get_triggers',
    'test_group_add',
    'test_group_delete',

    ## 'test_alert_list',
    ## 'test_alert_get',

    'test_action_list',
    'test_action_get',
    ## 'test_action_enable',
    ## 'test_action_disable',
    ## 'test_action_create_autoregistration',

    'test_logout'
]


class ZabbixClientTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()

        env = 'test'
        params = cls.platform.get('zabbix').get(env)
        cls.client = ZabbixManager(uri=params.get('uri', None))
        cls.user = params.get('user', None)
        cls.pwd = params.get('pwd', None)

    def test_ping(self):
        self.client.ping()

    def test_version(self):
        self.client.version()

    def test_authorize(self):
        self.client.authorize(self.user, self.pwd)

    def test_logout(self):
        self.client.logout(self.client.token)

    # host
    def test_host_list(self):
        global host
        res = self.client.host.list()
        host = res[-1]['hostid']

    def test_host_get(self):
        global host
        self.client.host.get(host)

    def test_host_groups(self):
        global host
        self.client.host.groups(host)

    def test_host_link_template(self):
        global host
        templates = []
        self.client.host.link_template(host, templates)

    def test_host_unlink_template(self):
        global host
        templates = []
        self.client.host.unlink_template(host, templates)

    def test_host_items(self):
        global host
        res = self.client.host.get_items(host)
        keys = ['itemid', 'type', 'name', 'delay', 'units', 'state', 'lastvalue', 'prevvalue', 'lastclock']
        for i in res:
            values = []
            for k in keys:
                values.append(i[k])
            self.logger.debug(values)

    def test_host_triggers(self):
        global host
        res = self.client.host.get_triggers(host)
        keys = ['triggerid', 'expression', 'description', 'state', 'value']
        for i in res:
            values = []
            for k in keys:
                values.append(i[k])
            self.logger.debug(values)

    # template
    def test_template_list(self):
        global template
        res = self.client.template.list()
        template = res[-1]['templateid']

    def test_template_get(self):
        global template
        self.client.template.get(template)

    def test_template_export(self):
        global template
        self.client.template.export(template)

    def test_template_load(self):
        global template
        source = ''
        self.client.template.load(source)

    def test_template_delete(self):
        global template
        self.client.template.delete(template)

    # group
    def test_group_list(self):
        global group
        res = self.client.group.list()
        group = res[-1]['groupid']

    def test_group_get(self):
        global group
        self.client.group.get(group)

    def test_group_get_by_name(self):
        global group
        self.client.group.list(name='awx_group_prova1')

    def test_group_get_items(self):
        global group
        self.client.group.get_items(group)

    def test_group_get_triggers(self):
        global group
        self.client.group.get_triggers(group)

    def test_group_add(self):
        global group
        res = self.client.group.add('group_prova')
        group = res['groupids'][0]

    def test_group_delete(self):
        global group
        self.client.group.delete(group)

    # alert
    def test_alert_list(self):
        global alert
        d = datetime.strptime('21/09/2019', '%d/%m/%Y')
        time_from = mktime(d.timetuple())
        res = self.client.alert.list(time_from=time_from)
        alert = res[-1]['alertid']

    def test_alert_get(self):
        global alert
        self.client.alert.get(alert)

    # action
    def test_action_list(self):
        global action
        res = self.client.action.list()
        action = res[-1]['actionid']

    def test_action_get(self):
        global action
        self.client.action.get(action)

    def test_action_enable(self):
        global action
        self.client.action.enable(action)

    def test_action_disable(self):
        global action
        self.client.action.disable(action)

    def test_action_create_autoregistration(self):
        groupid, groupname, templateid, operatingsystem = None
        self.client.action.create_autoregistration(groupid, groupname, templateid, operatingsystem)


if __name__ == '__main__':
    runtest(ZabbixClientTestCase, tests)
