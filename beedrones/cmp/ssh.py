# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.types.type_string import truncate
from beedrones.cmp.client import CmpBaseService


class CmpResourceAbstractService(CmpBaseService):
    """Cmp ssh service"""

    SUBSYSTEM = "ssh"
    PREFIX = "gas"
    VERSION = "v1.0"

    def get_uri(self, uri):
        return "/%s/%s/%s" % (self.VERSION, self.PREFIX, uri)


class CmpSshService(CmpResourceAbstractService):
    """Cmp ssh service"""

    def __init__(self, manager):
        CmpResourceAbstractService.__init__(self, manager)

        self.group = CmpSshGroupService(self.manager)
        self.node = CmpSshNodeService(self.manager)
        self.user = CmpSshUserService(self.manager)
        self.key = CmpSshKeyService(self.manager)
        self.ansible = CmpSshAnsibleService(self.manager)


class CmpSshGroupService(CmpResourceAbstractService):
    """Cmp ssh group service"""

    def __init__(self, manager):
        super().__init__(manager)

        self.auth = CmpSshGroupAuthService(self.manager)

    def list(self, *args, **kwargs):
        """get groups

        :param name: ssh group name
        :param desc: ssh group description
        :param objid: ssh group authorization id
        :param page: query page
        :param size: query page size
        :param field: query sort field
        :param order: query sort order
        :return: list of groups
        :raise CmpApiClientError:
        """
        params = ["name", "desc", "objid"]
        mappings = {"name": lambda n: "%" + n + "%"}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri("groups")
        res = self.api_get(uri, data=data)
        self.logger.debug("get groups: %s" % truncate(res))
        return res

    def get(self, oid):
        """get ssh group

        :param oid: ssh group id or uuid
        :return: ssh group
        :raise CmpApiClientError:
        """
        uri = self.get_uri("groups/%s" % oid)
        res = self.api_get(uri).get("group")
        self.logger.debug("get ssh group %s: %s" % (oid, truncate(res)))
        return res

    def exist(self, oid):
        """verify if ssh group already exists

        :param oid: ssh group id or uuid
        :return: ssh group
        :raise CmpApiClientError:
        """
        try:
            self.get(oid)
            return True
        except:
            self.logger.debug("Ssh group %s does not exist" % oid)
            return False

    def add(self, name, desc, attribute, **kwargs):
        """add ssh group

        :param name: ssh group name
        :param desc: resource ssh group description
        :param attribute: ssh group attribute
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {"name": name, "desc": desc, "attribute": attribute}
        data.update(self.format_request_data(kwargs, []))
        uri = self.get_uri("groups")
        res = self.api_post(uri, data={"group": data})
        self.logger.debug("Create ssh group %s" % name)
        return res

    def update(self, oid, **kwargs):
        """update ssh group

        :param oid: id of the ssh group
        :param kwargs.name: ssh group name [optional]
        :param kwargs.desc: resource ssh group description [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ["name", "desc"])
        uri = self.get_uri("groups/%s" % oid)
        res = self.api_put(uri, data={"group": data})
        self.logger.debug("update ssh group %s" % oid)
        return res

    def delete(self, oid):
        """delete ssh group

        :param oid: id of the ssh group
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri("groups/%s" % oid)
        data = ""
        self.api_delete(uri, data=data)
        self.logger.debug("delete ssh group %s" % oid)

    def add_node(self, oid, node_id):
        """add ssh node

        :param oid: id of the ssh group
        :param node_id: ssh node id
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {"node": node_id}
        uri = self.get_uri("groups/%s/node" % oid)
        res = self.api_put(uri, data={"group": data})
        self.logger.debug("update ssh group %s" % oid)
        return res

    def del_node(self, oid, node_id):
        """delete ssh node

        :param oid: ssh node id, uuid or name
        :param node_id: ssh node id
        :return: True
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {"node": node_id}
        uri = self.get_uri("groups/%s/node" % oid)
        self.api_delete(uri, data=data)
        self.logger.debug("delete ssh group %s" % oid)
        return True


class CmpSshNodeService(CmpResourceAbstractService):
    """Cmp ssh node service"""

    def __init__(self, manager):
        super().__init__(manager)

        self.auth = CmpSshNodeAuthService(self.manager)

    def list(self, *args, **kwargs):
        """get nodes

        :param kwargs.group_id: ssh group id
        :param kwargs.names: ssh node name like
        :param kwargs.ip_address: ssh node ip address
        :param kwargs.key_id: ssh key id
        :param kwargs.page: query page
        :param kwargs.size: query page size
        :param kwargs.field: query sort field
        :param kwargs.order: query sort order
        :return: list of nodes
        :raise CmpApiClientError:
        """
        params = ["group_id", "names", "ip_address", "key_id"]
        data = self.format_paginated_query(kwargs, params, mappings={})
        uri = self.get_uri("nodes")
        res = self.api_get(uri, data=data)
        self.logger.debug("get nodes: %s" % truncate(res))
        return res

    def get(self, oid):
        """get ssh node

        :param oid: ssh node id or uuid
        :return: ssh node
        :raise CmpApiClientError:
        """
        uri = self.get_uri("nodes/%s" % oid)
        res = self.api_get(uri).get("node")
        self.logger.debug("get ssh node %s: %s" % (oid, truncate(res)))
        return res

    def exist(self, oid):
        """verify if ssh node already exists

        :param oid: ssh node id or uuid
        :return: ssh node
        :raise CmpApiClientError:
        """
        try:
            self.get(oid)
            return True
        except:
            self.logger.debug("Ssh node %s does not exist" % oid)
            return False

    def add(self, name, ip_address, node_type, group_id, **kwargs):
        """add ssh node

        :param name: ssh node name
        :param ip_address: ssh node ip address
        :param node_type: ssh node type
        :param group_id: group id
        :param kwargs.desc: ssh node description [optional]
        :param kwargs.attribute: ssh node attribute [optional]
        :param kwargs.active: ssh node active [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            "name": name,
            "node_type": node_type,
            "group_id": group_id,
            "ip_address": ip_address,
        }
        data.update(self.format_request_data(kwargs, []))
        uri = self.get_uri("nodes")
        res = self.api_post(uri, data={"node": data})
        self.logger.debug("Create ssh node %s" % name)
        return res

    def update(self, oid, **kwargs):
        """update ssh node

        :param oid: id of the ssh node
        :param kwargs.name: ssh node name [optional]
        :param kwargs.desc: ssh node description [optional]
        :param kwargs.ip_address: ssh node ip address [optional]
        :param kwargs.node_type: ssh node type [optional]
        :param kwargs.attribute: ssh node attribute [optional]
        :param kwargs.active: ssh node active [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ["name", "desc", "active", "ip_address", "attribute", "node_type"])
        uri = self.get_uri("nodes/%s" % oid)
        res = self.api_put(uri, data={"node": data})
        self.logger.debug("update ssh node %s" % oid)
        return res

    def delete(self, oid):
        """delete ssh node

        :param oid: id of the ssh node
        :param force: if True force delete
        :param deep: if True delete all the resource tree
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri("nodes/%s" % oid)
        data = ""
        self.api_delete(uri, data=data)
        self.logger.debug("delete ssh node %s" % oid)

    def get_actions(self, oid, *args, **kwargs):
        """get ssh node actions

        :param oid: id of the ssh node
        :param date: query date [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        params = ["date"]
        data = self.format_paginated_query(kwargs, params, mappings={})
        uri = self.get_uri("nodes/%s/actions" % oid)
        res = self.api_get(uri, data=data)
        self.logger.debug("get ssh node %s actions: %s" % (oid, truncate(res)))
        return res

    def add_action(self, oid, **kwargs):
        """add ssh node action

        :param oid: id of the ssh node
        :param kwargs.action: ssh node action
        :param kwargs.action_id: ssh node action id [optional]
        :param kwargs.status: ssh node action status [optional]
        :param dict kwargs.params: ssh node params
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ["action", "action_id", "status", "params"])
        uri = self.get_uri("nodes/%s/action" % oid)
        res = self.api_put(uri, data=data)
        self.logger.debug("add ssh node %s action" % oid)
        return res


class CmpSshKeyService(CmpResourceAbstractService):
    """Cmp ssh key service"""

    def __init__(self, manager):
        super().__init__(manager)

        self.auth = CmpSshKeyAuthService(self.manager)

    def list(self, *args, **kwargs):
        """get keys

        :param kwargs.user_id: ssh user id
        :param kwargs.page: query page
        :param kwargs.size: query page size
        :param kwargs.field: query sort field
        :param kwargs.order: query sort order
        :return: list of keys
        :raise CmpApiClientError:
        """
        params = ["user_id"]
        data = self.format_paginated_query(kwargs, params, mappings={})
        uri = self.get_uri("keys")
        res = self.api_get(uri, data=data)
        self.logger.debug("get keys: %s" % truncate(res))
        return res

    def get(self, oid):
        """get ssh key

        :param oid: ssh key id or uuid
        :return: ssh key
        :raise CmpApiClientError:
        """
        uri = self.get_uri("keys/%s" % oid)
        res = self.api_get(uri).get("key")
        self.logger.debug("get ssh key %s: %s" % (oid, truncate(res)))
        return res

    def exist(self, oid):
        """verify if ssh key already exists

        :param oid: ssh key id or uuid
        :return: ssh key
        :raise CmpApiClientError:
        """
        try:
            self.get(oid)
            return True
        except:
            self.logger.debug("Ssh key %s does not exist" % oid)
            return False

    def add(self, name, **kwargs):
        """add ssh key

        :param name: ssh key name
        :param kwargs.priv_key: private key. Use for existing key [optional]
        :param kwargs.pub_key: public key. Use with priv_key for existing key [optional]
        :param kwargs.type: specify type like rsa, dsa. Use for new key when priv_key is null [default=rsa]
        :param int kwargs.bits: for new key specify bits like 2096. Use with type [default=2048]
        :param kwargs.desc: ssh key description [optional]
        :param kwargs.attribute: ssh key attribute [optional]
        :param kwargs.active: ssh key active [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            "name": name,
        }
        data.update(self.format_request_data(kwargs, []))
        uri = self.get_uri("keys")
        res = self.api_post(uri, data={"key": data})
        self.logger.debug("create ssh key %s" % name)
        return res

    def update(self, oid, **kwargs):
        """update ssh key

        :param oid: id of the ssh key
        :param kwargs.name: ssh key name [optional]
        :param kwargs.desc: ssh key description [optional]
        :param kwargs.priv_key: ssh key private key [optional]
        :param kwargs.pub_key: ssh key public key [optional]
        :param kwargs.active: ssh key active [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ["name", "desc", "active", "priv_key", "pub_key"])
        uri = self.get_uri("keys/%s" % oid)
        res = self.api_put(uri, data={"key": data})
        self.logger.debug("update ssh key %s" % oid)
        return res

    def delete(self, oid):
        """delete ssh key

        :param oid: id of the ssh key
        :param force: if True force delete
        :param deep: if True delete all the resource tree
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri("keys/%s" % oid)
        data = ""
        self.api_delete(uri, data=data)
        self.logger.debug("delete ssh key %s" % oid)


class CmpSshUserService(CmpResourceAbstractService):
    """Cmp ssh user service"""

    def __init__(self, manager):
        super().__init__(manager)

    def list(self, *args, **kwargs):
        """get node users

        :param kwargs.node_id: ssh node id
        :param kwargs.username: ssh user name in the server
        :param kwargs.page: query page
        :param kwargs.size: query page size
        :param kwargs.field: query sort field
        :param kwargs.order: query sort order
        :return: list of users
        :raise CmpApiClientError:
        """
        params = ["username", "node_id"]
        data = self.format_paginated_query(kwargs, params, mappings={})
        uri = self.get_uri("users")
        res = self.api_get(uri, data=data)
        self.logger.debug("get users: %s" % truncate(res))
        return res

    def get(self, oid):
        """get ssh user

        :param oid: ssh user id or uuid
        :return: ssh user
        :raise CmpApiClientError:
        """
        uri = self.get_uri("users/%s" % oid)
        res = self.api_get(uri).get("user")
        self.logger.debug("get ssh user %s: %s" % (oid, truncate(res)))
        return res

    def exist(self, oid):
        """verify if ssh user already exists

        :param oid: ssh user id or uuid
        :return: ssh user
        :raise CmpApiClientError:
        """
        try:
            self.get(oid)
            return True
        except:
            self.logger.debug("Ssh user %s does not exist" % oid)
            return False

    def add(self, name, username, node_id, **kwargs):
        """add ssh user

        :param name: ssh user name
        :param username: ssh user name in the server
        :param kwargs.password: ssh user password [optional]
        :param node_id: ssh node id
        :param kwargs.key_id: ssh key id [optional]
        :param kwargs.desc: ssh user description [optional]
        :param kwargs.attribute: ssh user attribute [optional]
        :param kwargs.active: ssh user active [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            "name": name,
            "username": username,
            "node_id": node_id,
        }
        data.update(self.format_request_data(kwargs, []))
        uri = self.get_uri("users")
        res = self.api_post(uri, data={"user": data})
        self.logger.debug("create ssh user %s" % name)
        return res

    def update(self, oid, **kwargs):
        """update ssh user

        :param oid: id of the ssh user
        :param kwargs.name: ssh user name [optional]
        :param kwargs.desc: ssh user description [optional]
        :param kwargs.active: ssh user active [optional]
        :param kwargs.username: ssh user name in the server [optional]
        :param kwargs.password: ssh user public user [optional
        :param kwargs.node_id: ssh node id [optional]
        :param kwargs.key_id: ssh key id [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(
            kwargs,
            ["name", "desc", "active", "username", "password", "node_id", "key_id"],
        )
        uri = self.get_uri("users/%s" % oid)
        res = self.api_put(uri, data={"user": data})
        self.logger.debug("update ssh user %s" % oid)
        return res

    def delete(self, oid):
        """delete ssh user

        :param oid: id of the ssh user
        :param force: if True force delete
        :param deep: if True delete all the resource tree
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri("users/%s" % oid)
        data = ""
        self.api_delete(uri, data=data)
        self.logger.debug("delete ssh user %s" % oid)

    def get_password(self, oid):
        """get ssh user password

        :param oid: ssh user id or uuid
        :return: ssh user password
        :raise CmpApiClientError:
        """
        uri = self.get_uri("users/%s/password" % oid)
        res = self.api_get(uri).get("password")
        self.logger.debug("get ssh user %s password" % oid)
        return res

    def set_password(self, oid, pwd):
        """set ssh user password

        :param oid: ssh user id or uuid
        :param pwd: ssh user password
        :return: ssh user password
        :raise CmpApiClientError:
        """
        uri = self.get_uri("users/%s" % oid)
        res = self.api_put(uri, data={"user": {"password": pwd}})
        self.logger.debug("set ssh user %s password" % oid)
        return res


class CmpSshAnsibleService(CmpResourceAbstractService):
    """Cmp ssh ansible node service"""

    def __init__(self, manager):
        super().__init__(manager)

    def get_inventory(self, *args, **kwargs):
        """Create an ansible inventory

        :param kwargs.group: group id
        :param kwargs.node: node id
        :param kwargs.node_name: node name
        """
        data = self.format_request_data(kwargs, ["group", "node", "node_name"])
        uri = self.get_uri("ansible")
        res = self.api_get(uri, data=data)
        inventory_dict = res.get("ansible")
        return inventory_dict


class CmpSshAuthService(CmpResourceAbstractService):
    """Cmp ssh authorization"""

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
        """add role to user

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
        self.logger.debug("add %s %s role %s to user %s" % (self.common_name, oid, role, user))
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
        """add role to group

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
        self.logger.debug("add %s %s role %s to group %s" % (self.common_name, oid, role, group))
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


class CmpSshGroupAuthService(CmpSshAuthService):
    """Cmp ssh group authorization"""

    common_name = "groups"


class CmpSshNodeAuthService(CmpSshAuthService):
    """Cmp ssh node authorization"""

    common_name = "nodes"


class CmpSshKeyAuthService(CmpSshAuthService):
    """Cmp ssh key authorization"""

    common_name = "keys"
