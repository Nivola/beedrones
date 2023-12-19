# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import truncate
from beedrones.cmp.business import CmpBusinessAbstractService
from beedrones.cmp.client import CmpBaseService


class CmpBusinessAuthService(CmpBusinessAbstractService):
    """Cmp business authorization"""

    common_name = ""

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

    def get_roles(self, oid):
        """get roles

        :param oid: id or uuid
        :return: roles
        :raise CmpApiClientError:
        """
        uri = self.get_uri("%s/%s/roles" % (self.common_name, oid))
        res = self.api_get(uri)
        self.logger.debug("get %s %s roles: %s" % (self.common_name, oid, truncate(res)))
        return res

    def get_users(self, oid):
        """get users

        :param oid: id or uuid
        :return: users
        :raise CmpApiClientError:
        """
        uri = self.get_uri("%s/%s/users" % (self.common_name, oid))
        res = self.api_get(uri)
        self.logger.debug("get %s %s users: %s" % (self.common_name, oid, truncate(res)))
        return res

    def add_user(self, oid, role, user):
        """Add role to user

        :param oid: id or uuid
        :param roles: business role
        :param user: auth user
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            "user_id": user,
            "role": role,
        }
        uri = self.get_uri("%s/%s/users" % (self.common_name, oid))
        res = self.api_post(uri, data={"user": data})
        self.logger.debug("Add %s %s role %s to user %s" % (self.common_name, oid, role, user))
        return res

    def del_user(self, oid, role, user):
        """Remove role from user

        :param oid: id or uuid
        :param roles: business role
        :param user: auth user
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri("%s/%s/users" % (self.common_name, oid))
        data = {
            "user_id": user,
            "role": role,
        }
        res = self.api_delete(uri, data={"user": data})
        self.logger.debug("Remove %s %s role %s from user %s" % (self.common_name, oid, role, user))
        return res

    def get_groups(self, oid):
        """get groups

        :param oid: id or uuid
        :return: groups
        :raise CmpApiClientError:
        """
        uri = self.get_uri("%s/%s/groups" % (self.common_name, oid))
        res = self.api_get(uri)
        self.logger.debug("get %s %s groups: %s" % (self.common_name, oid, truncate(res)))
        return res

    def add_group(self, oid, role, group):
        """Add role to group

        :param oid: id or uuid
        :param roles: business role
        :param group: auth group
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            "group_id": group,
            "role": role,
        }
        uri = self.get_uri("%s/%s/groups" % (self.common_name, oid))
        res = self.api_post(uri, data={"group": data})
        self.logger.debug("Add %s %s role %s to group %s" % (self.common_name, oid, role, group))
        return res

    def del_group(self, oid, role, group):
        """Remove role from group

        :param oid: id or uuid
        :param roles: business role
        :param group: auth group
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri("%s/%s/groups" % (self.common_name, oid))
        data = {
            "group_id": group,
            "role": role,
        }
        res = self.api_delete(uri, data={"group": data})
        self.logger.debug("Remove %s %s role %s from group %s" % (self.common_name, oid, role, group))
        return res
