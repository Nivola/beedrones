# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte
from urllib.parse import urlencode, quote

from beedrones.datadomain.client import DataDomainEntity
from beecell.simple import truncate


class DataDomainNetwork(DataDomainEntity):
    """DataDomainNetwork
    """
    def list(self, system_id, **filters):
        """List networks

        :param system_id: system id
        :param filters.page: page number, starting from 0 [default=0]
        :param filters.size: paging size [default=20]
        :param filters.sort: sort="name". For descending order, prefix the key with a dash (-). [default=name]
        :return: list of network info
        :raise ZabbixError:
        """
        query = ''
        if filters:
            query = urlencode(filters)
        uri = self.get_system_uri(system_id) + '/networks?' + query
        res = self.http_get(uri)
        self.logger.debug('get networks information: %s' % truncate(res))
        return res

    def get(self, system_id, oid):
        """Get network

        :param system_id: system id
        :param oid: network id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + '/networks/' + oid
        res = self.http_get(uri)
        self.logger.debug('get network %s: %s' % (oid, truncate(res)))
        return res
