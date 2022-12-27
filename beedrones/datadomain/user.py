# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from urllib.parse import urlencode, quote

from beedrones.datadomain.client import DataDomainEntity
from beecell.simple import truncate


class DataDomainUser(DataDomainEntity):
    """DataDomainUser
    """
    def list(self, system_id, **filters):
        """List users

        :param system_id: system id
        :param filters.page: page number, starting from 0 [default=0]
        :param filters.size: paging size [default=20]
        :param filters.sort: sort="name". For descending order, prefix the key with a dash (-). [default=name]
        :return: list of user info
        :raise ZabbixError:
        """
        query = ''
        if filters:
            query = urlencode(filters)
        uri = self.get_system_uri(system_id) + '/users?' + query
        res = self.http_get(uri)
        self.logger.debug('get users information: %s' % truncate(res))
        return res

    def get(self, system_id, oid):
        """Get user

        :param system_id: system id
        :param oid: user id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + '/users/' + oid
        res = self.http_get(uri)
        self.logger.debug('get user %s: %s' % (oid, truncate(res)))
        return res

    def add(self, system_id, name):
        """add user

        :param system_id: system id
        :param name: user name
        :return:
        :raise ZabbixError:
        """
        data = {
            'name': '/data/col1/{}'.format(name)
        }
        uri = self.get_system_uri(system_id) + '/users'
        res = self.http_post(uri, data={'user_create': data})
        self.logger.debug('add user %s: %s' % (name, truncate(res)))
        return res

    def update(self, system_id, oid):
        """update user

        :param system_id: system id
        :param oid: user id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + '/users/' + oid
        res = self.http_put(uri)
        self.logger.debug('update user %s: %s' % (oid, truncate(res)))
        return res

    def delete(self, system_id, oid):
        """delete user

        :param system_id: system id
        :param oid: user id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + '/users/' + oid
        res = self.http_delete(uri)
        self.logger.debug('delete user %s: %s' % (oid, truncate(res)))
        return res
