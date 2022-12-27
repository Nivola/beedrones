# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from urllib.parse import urlencode, quote

from beedrones.datadomain.client import DataDomainEntity
from beecell.simple import truncate


class DataDomainMtree(DataDomainEntity):
    """DataDomainMtree
    """
    def list(self, system_id, **filters):
        """List mtrees

        :param system_id: system id
        :param filters.page: page number, starting from 0 [default=0]
        :param filters.size: paging size [default=20]
        :param filters.sort: sort="name". For descending order, prefix the key with a dash (-). [default=name]
        :return: list of mtree info
        :raise ZabbixError:
        """
        query = ''
        if filters:
            query = urlencode(filters)
        uri = self.get_system_uri(system_id) + '/mtrees?' + query
        res = self.http_get(uri)
        self.logger.debug('get mtrees information: %s' % truncate(res))
        return res

    def get(self, system_id, oid):
        """Get mtree

        :param system_id: system id
        :param oid: mtree id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + '/mtrees/' + oid
        res = self.http_get(uri)
        self.logger.debug('get mtree %s: %s' % (oid, truncate(res)))
        return res

    def add(self, system_id, name):
        """add mtree

        :param system_id: system id
        :param name: mtree name
        :return:
        :raise ZabbixError:
        """
        data = {
            'name': '/data/col1/{}'.format(name)
        }
        uri = self.get_system_uri(system_id) + '/mtrees'
        res = self.http_post(uri, data={'mtree_create': data})
        self.logger.debug('add mtree %s: %s' % (name, truncate(res)))
        return res

    def update(self, system_id, oid):
        """update mtree

        :param system_id: system id
        :param oid: mtree id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + '/mtrees/' + oid
        res = self.http_put(uri)
        self.logger.debug('update mtree %s: %s' % (oid, truncate(res)))
        return res

    def delete(self, system_id, oid):
        """delete mtree

        :param system_id: system id
        :param oid: mtree id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + '/mtrees/' + oid
        res = self.http_delete(uri)
        self.logger.debug('delete mtree %s: %s' % (oid, truncate(res)))
        return res
