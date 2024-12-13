# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from urllib.parse import urlencode, quote

from beedrones.datadomain.client import DataDomainEntity
from beecell.simple import truncate


class DataDomainTrust(DataDomainEntity):
    """DataDomainTrust"""

    def get(self, system_id):
        """Get trust

        :param system_id: system id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = "/trust"
        res = self.http_get(uri)
        self.logger.debug("get trust: %s" % truncate(res))
        return res

    def add(self, system_id, name):
        """add trust

        :param system_id: system id
        :param name: trust name
        :return:
        :raise ZabbixError:
        """
        data = {"name": "/data/col1/{}".format(name)}
        uri = "/trust"
        res = self.http_post(uri, data={"trust_create": data})
        self.logger.debug("add trust %s: %s" % (name, truncate(res)))
        return res

    def update(self, system_id, oid):
        """update trust

        :param system_id: system id
        :param oid: trust id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = "/trust"
        res = self.http_put(uri)
        self.logger.debug("update trust %s: %s" % (oid, truncate(res)))
        return res

    def delete(self, system_id, oid):
        """delete trust

        :param system_id: system id
        :param oid: trust id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = "/trust"
        res = self.http_delete(uri)
        self.logger.debug("delete trust %s: %s" % (oid, truncate(res)))
        return res
