# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixAlert(ZabbixEntity):
    """ZabbixAlert
    """
    def list(self, **filter):
        """Get awx alerts

        :param filter: custom filter
        :return: list of alerts
        :raise ZabbixError:
        """
        params = {
            'output': 'extend'
        }
        params.update(filter)
        res = self.call('alert.get', params=params)
        self.logger.debug('list alerts: %s' % truncate(res))
        return res

    def get(self, alert):
        """Get awx alert

        :param alert: alert id
        :return: alert
        :raise ZabbixError:
        """
        params = {
            'output': 'extend',
            'alertids': alert
        }
        res = self.call('alert.get', params=params)
        if len(res) == 0:
            raise ZabbixError('alert %s not found' % alert)
        res = res[0]
        self.logger.debug('get alert: %s' % truncate(res))
        return res
