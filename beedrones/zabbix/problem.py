# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixProblem(ZabbixEntity):
    """ZabbixProblem
    """
    def list(self, **filter):
        """Get awx problems

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
        """Get awx problem

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
