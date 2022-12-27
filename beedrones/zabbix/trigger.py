# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixTrigger(ZabbixEntity):
    """ZabbixTrigger
    """
    def list(self, **filter):
        """Get zabbix triggers

        :param filter: custom filter
        :return: list of triggers
        :raise ZabbixError:
        """
        params = {
            'output': 'extend'
        }
        params.update(filter)
        res = self.call('trigger.get', params=params)
        self.logger.debug('list triggers: %s' % truncate(res))
        return res

    def get(self, trigger):
        """Get zabbix trigger

        :param trigger: trigger id
        :return: trigger
        :raise ZabbixError:
        """
        params = {
            'output': 'extend',
            'triggerids': trigger
        }
        res = self.call('trigger.get', params=params)
        if len(res) == 0:
            raise ZabbixError('trigger %s not found' % trigger)
        res = res[0]
        self.logger.debug('get trigger: %s' % truncate(res))
        return res

    def create(self, desc, comment, expression, priority):
        """create zabbix trigger

        :param desc: desc
        :param comment: comment
        :param expression: expression
        :param priority: priority type. Can be:
            - 0 (Default) not classified
            - 1 information
            - 2 warning
            - 3 average
            - 4 high
            - 5 disaster
        :return: trigger
        :raise ZabbixError:
        """
        params = {
            'description': desc,
            'comments': comment,
            'expression': expression,
            'priority': priority
        }
        res = self.call('trigger.create', params=params)
        self.logger.debug('create trigger: %s' % truncate(res))
        return res

    def delete(self, trigger):
        """Delete zabbix trigger

        :param trigger: trigger id
        :return: host
        :raise ZabbixError:
        """
        params = [trigger]
        res = self.call('trigger.delete', params=params)
        self.logger.debug('delete trigger: %s' % truncate(res))
        return res
