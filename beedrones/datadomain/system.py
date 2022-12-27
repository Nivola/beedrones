# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte
from urllib.parse import urlencode, quote

from beedrones.datadomain.client import DataDomainEntity
from beecell.simple import truncate


class DataDomainSystem(DataDomainEntity):
    """DataDomainSystem
    """
    def get(self, **filter):
        """Get system information.

        :param filter: custom filter
        :return: list of system info
        :raise ZabbixError:
        """
        res = self.http_get('/system')
        self.logger.debug('get system information: %s' % truncate(res))
        return res

    def get_settings(self, oid):
        """Get settings information.

        :param oid: system id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(oid) + '/settings'
        res = self.http_get(uri)
        self.logger.debug('get system %s settings: %s' % (oid, truncate(res)))
        return res

    def get_services(self, oid):
        """Get services.

        :param oid: system id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(oid) + '/services'
        res = self.http_get(uri)
        self.logger.debug('get system %s services: %s' % (oid, truncate(res)))
        return res
