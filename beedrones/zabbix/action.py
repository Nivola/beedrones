# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixAction(ZabbixEntity):
    """ZabbixAction
    """
    def list(self, **filter):
        """Get awx actions

        :return: list of actions
        :raise ZabbixError:
        """
        params = {
            'output': 'extend',
            'selectOperations': 'extend',
            'selectFilter': 'extend',
            'filter': filter
        }
        res = self.call('action.get', params=params)
        self.logger.debug('list actions: %s' % truncate(res))
        return res

    def get(self, action):
        """Get awx action

        :param action: action id
        :return: action
        :raise ZabbixError:
        """
        params = {
            'output': 'extend',
            'actionids': action
        }
        res = self.call('action.get', params=params)
        if len(res) == 0:
            raise ZabbixError('action %s not found' % action)
        res = res[0]
        self.logger.debug('get action: %s' % truncate(res))
        return res

    def enable(self, action):
        """enable zabbix action

        :param action: action id
        :return: action
        :raise ZabbixError:
        """
        params = {
            'actionid': action,
            'status': 0
        }
        res = self.call('action.update', params=params)
        self.logger.debug('enable action %s: %s' % (action, truncate(res)))
        return res

    def disable(self, action):
        """disable zabbix action

        :param action: action id
        :return: action
        :raise ZabbixError:
        """
        params = {
            'actionid': action,
            'status': 1
        }
        res = self.call('action.update', params=params)
        self.logger.debug('disable action %s: %s' % (action, truncate(res)))
        return res

    def create_autoregistration(self, groupid, groupname, templateid, operatingsystem):
        """create autoregistration action based on groups

        :param groupid: groupid (account groupid)
        :param groupname: groupname
        :param templateid: templateid (operating system templateid)
        :param operatingsystem: operatingsystem ("Linux or Windows")
        :return: True/False and True/False
        :raise ZabbixError:
        """
        action_name = groupname + '-' + operatingsystem
        params = {
            'name': action_name,
            'eventsource': 2,
            'status': 0,
            'esc_period': 0,
            'def_shortdata': 'Auto registration: {HOST.HOST}',
            'def_longdata': 'Host name: {HOST.HOST}\r\nHost IP: {HOST.IP}\r\nAgent port: {HOST.PORT}',
            'filter': {
                'evaltype': 1,
                'conditions': [
                    {
                        'conditiontype': 24,
                        'operator': 2,
                        'value': operatingsystem
                    },
                    {
                        'conditiontype': 24,
                        'operator': 2,
                        'value': groupname
                    }
                ]
            },
            'operations': [
                {
                    'operationtype': 4,
                    'opgroup': [
                        {
                            'groupid': groupid
                        }
                    ]},
                {
                    'operationtype': 6,
                    'optemplate': [
                        {
                            'templateid': templateid
                        }
                    ]

                }
            ]
        }
        res = self.call('action.create', params=params)
        self.logger.debug('disable action %s: %s' % (action, truncate(res)))
        return res
