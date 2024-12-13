# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from urllib.parse import urlencode, quote

from beedrones.datadomain.client import DataDomainEntity
from beecell.simple import truncate


class DataDomainProtocol(DataDomainEntity):
    """DataDomainProtocol"""

    def __init__(self, manager):
        super(DataDomainProtocol, self).__init__(manager)

        self.cifs = DataDomainProtocolCifs(manager)
        self.ddboost = DataDomainDDBoost(manager)
        self.nfs = DataDomainProtocolNfs(manager)
        self.vdisk = DataDomainProtocolVdisk(manager)


class DataDomainProtocolVdisk(DataDomainEntity):
    """DataDomainProtocolVdisk"""

    pass


class DataDomainProtocolNfs(DataDomainEntity):
    """DataDomainProtocolNfs"""

    def get_system_uri(self, system_id):
        return super(DataDomainProtocolNfs, self).get_system_uri(system_id) + "/protocols/nfs/exports"

    def list(self, system_id, **filters):
        """List nfs export

        :param system_id: system id
        :param filters.page: page number, starting from 0 [default=0]
        :param filters.size: paging size [default=20]
        :param filters.sort: sort="name". For descending order, prefix the key with a dash (-). [default=name]
        :return: list of nfs export info
        :raise ZabbixError:
        """
        query = ""
        if filters:
            query = urlencode(filters)
        uri = self.get_system_uri(system_id) + "?" + query
        res = self.http_get(uri)
        self.logger.debug("get nfs export information: %s" % truncate(res))
        return res

    def get(self, system_id, oid):
        """Get nfs export

        :param system_id: system id
        :param oid: nfs export id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + "/" + oid
        res = self.http_get(uri)
        self.logger.debug("get nfs export %s: %s" % (oid, truncate(res)))
        return res

    def add(self, system_id, mtree, path):
        """add nfs export

        :param system_id: system id
        :param mtree: mtree name
        :param path: nfs export path
        :return:
        :raise ZabbixError:
        """
        data = {
            "path": "%s/%s" % (mtree, path),
        }
        uri = self.get_system_uri(system_id)
        res = self.http_post(uri, data={"export_create": data})
        self.logger.debug("add mtree %s nfs export %s: %s" % (mtree, path, truncate(res)))
        return res

    def add_client(self, system_id, oid, name, options=None):
        """add nfs export client

        :param system_id: system id
        :param oid: nfs export id
        :param name: nfs export client fqdn
        :param options: nfs export client options [default='sec=sys rw no_root_squash no_all_squash secure version=3']
        :return:
        :raise ZabbixError:
        """
        if options is None:
            options = "sec=sys rw no_root_squash no_all_squash secure version=3"
        data = {
            "clients": [{"name": name, "options": options}],
        }
        uri = self.get_system_uri(system_id) + "/" + oid + "?"
        res = self.http_put(uri, data={"export_modify": data})
        self.logger.debug("add nfs export %s client %s: %s" % (oid, name, truncate(res)))
        return res

    def del_client(self, system_id, oid, name, options=None):
        """add nfs export client

        :param system_id: system id
        :param oid: nfs export id
        :param name: nfs export client fqdn
        :param options: nfs export client options [default='sec=sys rw no_root_squash no_all_squash secure version=3']
        :return:
        :raise ZabbixError:
        """
        if options is None:
            options = "sec=sys rw no_root_squash no_all_squash secure version=3"
        data = {
            "clients": [{"name": name, "options": options, "delete": True}],
        }
        uri = self.get_system_uri(system_id) + "/" + oid
        res = self.http_put(uri, data={"export_modify": data})
        self.logger.debug("delete nfs export %s client %s: %s" % (oid, name, truncate(res)))
        return res

    def delete(self, system_id, oid):
        """delete nfs export

        :param system_id: system id
        :param oid: nfs export id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + "/" + oid
        res = self.http_delete(uri)
        self.logger.debug("delete nfs export %s: %s" % (oid, truncate(res)))
        return res


class DataDomainDDBoost(DataDomainEntity):
    """DataDomainDDBoost"""

    pass


class DataDomainProtocolCifs(DataDomainEntity):
    """DataDomainProtocolCifs"""

    def get_system_uri(self, system_id):
        return super(DataDomainProtocolCifs, self).get_system_uri(system_id) + "/protocols/cifs/shares"

    def list(self, system_id, **filters):
        """List nfs export

        :param system_id: system id
        :param filters.page: page number, starting from 0 [default=0]
        :param filters.size: paging size [default=20]
        :param filters.sort: sort="name". For descending order, prefix the key with a dash (-). [default=name]
        :return: list of cifs share info
        :raise ZabbixError:
        """
        query = ""
        if filters:
            query = urlencode(filters)
        uri = self.get_system_uri(system_id) + query
        res = self.http_get(uri)
        self.logger.debug("get cifs share information: %s" % truncate(res))
        return res

    def get(self, system_id, oid):
        """Get cifs share

        :param system_id: system id
        :param oid: cifs share id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + "/" + oid
        res = self.http_get(uri)
        self.logger.debug("get cifs share %s: %s" % (oid, truncate(res)))
        return res

    def add(self, system_id, name):
        """add cifs share

        :param system_id: system id
        :param name: cifs share name
        :return:
        :raise ZabbixError:
        """
        data = {
            "name": name,
            "path": "string",
            "max_connections": 0,
            "comment": "string",
            "clients": ["string"],
            "users": ["string"],
            "groups": ["string"],
        }
        uri = self.get_system_uri(system_id)
        res = self.http_post(uri, data={"share_create": data})
        self.logger.debug("add cifs share %s: %s" % (name, truncate(res)))
        return res

    def update(self, system_id, oid):
        """update cifs share

        :param system_id: system id
        :param oid: cifs share id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + "/" + oid
        res = self.http_put(uri)
        self.logger.debug("update cifs share %s: %s" % (oid, truncate(res)))
        return res

    def delete(self, system_id, oid):
        """delete cifs share

        :param system_id: system id
        :param oid: cifs share id
        :return: list of settings
        :raise ZabbixError:
        """
        uri = self.get_system_uri(system_id) + "/" + oid
        res = self.http_delete(uri)
        self.logger.debug("delete cifs share %s: %s" % (oid, truncate(res)))
        return res
