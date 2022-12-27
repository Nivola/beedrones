# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from urllib.parse import urlencode, quote

from beedrones.datadomain.client import DataDomainEntity
from beecell.simple import truncate


class DataDomainTenant(DataDomainEntity):
    """DataDomainTenant
    """
    def list(self, system_id, **filters):
        """List tenants

        :param system_id: system id
        :param filters.page: page number, starting from 0 [default=0]
        :param filters.size: paging size [default=20]
        :param filters.sort: sort="name". For descending order, prefix the key with a dash (-). [default=name]
        :return: list of tenant info
        :raise ZabbixError:
        """
        query = ''
        if filters:
            query = urlencode(filters)
        uri = self.get_system_uri(system_id) + '/smt/tenants?' + query
        res = self.http_get(uri)
        self.logger.debug('get tenants information: %s' % truncate(res))
        return res

    def get(self, system_id, oid):
        """Get tenant

        :param system_id: system id
        :param oid: tenant id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + '/smt/tenants/' + oid
        res = self.http_get(uri)
        self.logger.debug('get tenant %s: %s' % (oid, truncate(res)))
        return res

    def add(self, system_id, name):
        """add tenant

        :param system_id: system id
        :param name: tenant name
        :return:
        :raise ZabbixError:
        """
        data = {
            'name': '/data/col1/{}'.format(name)
        }
        uri = self.get_system_uri(system_id) + '/smt/tenants'
        res = self.http_post(uri, data={'tenant_create': data})
        self.logger.debug('add tenant %s: %s' % (name, truncate(res)))
        return res

    def update(self, system_id, oid):
        """update tenant

        :param system_id: system id
        :param oid: tenant id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + '/smt/tenants/' + oid
        res = self.http_put(uri)
        self.logger.debug('update tenant %s: %s' % (oid, truncate(res)))
        return res

    def delete(self, system_id, oid):
        """delete tenant

        :param system_id: system id
        :param oid: tenant id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + '/smt/tenants/' + oid
        res = self.http_delete(uri)
        self.logger.debug('delete tenant %s: %s' % (oid, truncate(res)))
        return res
