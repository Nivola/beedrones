# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixProxy(ZabbixEntity):
    """ZabbixProxy
    """
    def list(self, **filter):
        """Get proxies

        :return: list of proxies
        :raise ZabbixError:
        """
        params = {
            'output': 'extend',
        }
        params.update(filter)
        res = self.call('proxy.get', params=params)
        self.logger.debug('list proxies: %s' % truncate(res))
        return res

    def get(self, proxy):
        """Get proxy

        :param proxy: proxy id
        :return: proxy
        :raise ZabbixError:
        """
        params = {
            'output': 'extend',
            'proxyids': proxy,
            'selectInterface': 'extend',
            'selectHosts': 'extend',
        }
        res = self.call('proxy.get', params=params)
        if len(res) == 0:
            raise ZabbixError('proxy %s not found' % proxy)
        res = res[0]
        self.logger.debug('get proxy: %s' % truncate(res))
        return res

    def create(self, name):
        """Create proxy

        :param name: proxy name
        :return: proxy id
        :raise ZabbixError:
        """
        params = {
            'host': name,
            'description':  name,
            'status': '5',
            'interfaces': {
            #    "port": "10051"
            },
            'hosts': []
        }

        res = self.call('proxy.create', params=params)
        self.logger.debug('create proxy: %s' % truncate(res))
        return res

    def delete(self, proxy):
        """Delete proxy

        :param proxy: proxy id
        :return: proxy
        :raise ZabbixError:
        """
        params = [proxy]
        res = self.call('proxy.delete', params=params)
        self.logger.debug('delete proxy: %s' % truncate(res))
        return res

    def update(self, proxy, **props):
        """Update property of the proxy

        :param proxy: proxy id
        :return: proxy
        :raise ZabbixError:
        """
        params = {
            'output': 'extend',
            'proxyid': proxy,
        }
        for k, v in props.items():
            params[k] = v
        res = self.call('proxy.update', params=params)
        self.logger.debug('update proxy: %s' % truncate(res))
        return res
