# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixProblem(ZabbixEntity):
    """ZabbixProblem
    """
    def list(self, **filter):
        """Get zabbix problems

        :param time_from: time from in unixtime format
        :return: list of problems
        :raise ZabbixError:
        """
        params = {
            'output': 'extend',
            'filter': filter
        }
        res = self.call('problem.get', params=params)
        self.logger.debug('list problems: %s' % truncate(res))
        return res

    def get(self, problem):
        """Get zabbix problem

        :param problem: problem id
        :return: problem
        :raise ZabbixError:
        """
        params = {
            'output': 'extend',
            'eventids': problem
        }
        res = self.call('problem.get', params=params)
        if len(res) == 0:
            raise ZabbixError('problem %s not found' % problem)
        res = res[0]
        self.logger.debug('get problem: %s' % truncate(res))
        return res
