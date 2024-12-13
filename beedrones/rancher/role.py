# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beedrones.rancher.client import RancherObject, RancherError
from beecell.simple import truncate


class RancherGlobalRole(RancherObject):
    """RancherGlobalRole"""

    def __init__(self, manager):
        super().__init__(manager)
        self.base_uri = "/v1/management.cattle.io.globalroles"

    def list(self, **filters):
        """List global roles

        :return: list of global roles
        """
        res = self.http_list("/", **filters)
        self.logger.debug("list global roles: %s" % truncate(res))
        return res

    def get(self, role_id):
        """Get global role info

        :param role_id: global role id
        :return: global role info
        """
        res = self.http_get("/%s" % role_id)
        self.logger.debug("get global role: %s" % truncate(res))
        return res

    def add(self, **kvargs):
        """Create global role

        :param kvargs: global role params
        :return: global role id
        """
        res = self.http_post("/", **kvargs)
        self.logger.debug("add global role: %s" % res.get("id"))
        return res

    def delete(self, role_id):
        """Delete global role

        :param role_id: role global id
        :return: True
        """
        self.http_delete("/%s" % role_id)
        self.logger.debug("delete global role: %s" % role_id)
        return True


class RancherTemplateRole(RancherObject):
    """RancherTemplateRole"""

    def __init__(self, manager):
        super().__init__(manager)
        self.base_uri = "/v1/management.cattle.io.roletemplates"

    def list(self, **filters):
        """List role templates

        :return: list of role templates
        """
        res = self.http_list("/", **filters)
        self.logger.debug("list role templates: %s" % truncate(res))
        return res

    def get(self, role_id):
        """Get role template info

        :param role_id: role template id
        :return: role template info
        """
        res = self.http_get("/%s" % role_id)
        self.logger.debug("get role template: %s" % truncate(res))
        return res

    def add(self, **kvargs):
        """Create role template

        :param kvargs: role template params
        :return: role id
        """
        res = self.http_post("/", **kvargs)
        self.logger.debug("add role template: %s" % res.get("id"))
        return res

    def delete(self, role_id):
        """Delete role template

        :param role_id: role template id
        :return: True
        """
        self.http_delete("/%s" % role_id)
        self.logger.debug("delete role template: %s" % role_id)
        return True
