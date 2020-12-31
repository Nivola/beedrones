# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte
from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixHostInterface(ZabbixEntity):
    """ZabbixHostInterface
    """
    def list(self, **filter):
        """Get interfaces

        :return: list of interfaces
        :raise ZabbixError:
        """
        params = {
            'output': 'extend',
            'filter': filter
        }
        res = self.call('hostinterface.get', params=params)
        self.logger.debug('list interfaces: %s' % truncate(res))
        return res

    def get(self, interface):
        """Get interfaces used by host

        :param interface: interface id
        :return: interface
        :raise ZabbixError:
        """
        params = {
            'output': 'extend',
            'interfaceids': interface
        }
        res = self.call('hostinterface.get', params=params)
        if len(res) == 0:
            raise ZabbixError('interface %s not found' % interface)
        res = res[0]
        self.logger.debug('get interface %s: %s' % (interface, truncate(res)))
        return res

    def hosts(self, interface):
        """Get hosts that use the interface

        :param interface: interface id
        :return: list of hosts
        :raise ZabbixError:
        """
        params = {
            'output': ['hosts'],
            'selectHosts': 'extend',
            'interfaceids': interface
        }
        res = self.call('hostinterface.get', params=params)
        if len(res) == 0:
            raise ZabbixError('interface %s not found' % interface)
        res = res[0]
        self.logger.debug('get hosts for interface %s: %s' % (interface, truncate(res)))
        return res

    def delete(self, interface):
        """delete interface

        :param interface: interface id
        :return: interface id
        :raise ZabbixError:
        """
        params = [interface]
        res = self.call('hostinterface.delete', params=params)
        self.logger.debug('delete interface %s: %s' % (interface, truncate(res)))
        return res
