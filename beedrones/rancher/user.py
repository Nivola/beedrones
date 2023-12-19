# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beedrones.rancher.client import RancherObject, RancherError
from beecell.simple import truncate


class RancherUser(RancherObject):
    """RancherUser"""

    def __init__(self, manager):
        super().__init__(manager)

        self.global_role_bind = RancherUserGlobalRoleBinding(manager)
        self.cluster_role_bind = RancherUserClusterRoleBinding(manager)
        self.project_role_bind = RancherUserProjectRoleBinding(manager)

    def list(self, **filters):
        """List users

        :param filters: custom filters
        :return: list of users
        """
        res = self.http_list("/users", **filters)
        self.logger.debug("list users: %s" % truncate(res))
        return res

    def get(self, user_id):
        """Get user info

        :param user_id: user id
        :return: user info
        """
        res = self.http_get("/users/%s" % user_id)
        self.logger.debug("get user: %s" % truncate(res))
        return res

    def add(self, name, pwd, enabled=True, change_pwd=False, **kwargs):
        """Create user

        :param name: user name
        :param pwd: user password
        :param enabled: user enabled [default=True]
        :param change_pwd: user change_pwd [default=False]
        :param kwargs: custom user params
        :param kwargs.description: user params
        :return: user id
        """
        data = {
            "type": "user",
            "enabled": enabled,
            "mustChangePassword": change_pwd,
            "name": name,
            "username": name,
            "password": pwd,
        }
        data.update(self.format_request_data(kwargs, []))
        res = self.http_post("/users", **data)
        self.logger.debug("add user: %s" % res.get("id"))
        return res

    def delete(self, user_id):
        """Delete user

        :param user_id: user id
        :return: True
        """
        self.http_delete("/users/%s" % user_id)
        self.logger.debug("delete user: %s" % user_id)
        return True

    def generate_kubeconfig(self, user_id, cluster_id):
        """generate user kubeconfig

        :param cluster_id: cluster id
        :param user_id: user id
        :return: True
        """
        self.base_uri = "/v3/clusters/%s?action=generateKubeconfig" % cluster_id
        res = self.http_post("").get("config", "")
        self.logger.debug("generate user %s kubeconfig for cluster %s: %s" % (user_id, cluster_id, res))
        return res

    def get_roles(self, user_id):
        """get user roles

        :param user_id: user id
        :return: user roles
        """
        roles = []

        # global role bindings
        role_bindings = self.global_role_bind.list(user_id=user_id)
        for rb in role_bindings:
            role = self.manager.role_global.get(rb.get("globalRoleName"))
            role["role_bind_id"] = rb["id"]
            roles.append(role)

        # cluster role bindings
        role_bindings = self.cluster_role_bind.list(user_id=user_id)
        for rb in role_bindings:
            role = self.manager.role_template.get(rb.get("roleTemplateName"))
            role["role_bind_id"] = rb["id"]
            role["context:entity"] = rb.get("clusterName", None)
            roles.append(role)

        # project role bindings
        role_bindings = self.project_role_bind.list(user_id=user_id)
        for rb in role_bindings:
            role = self.manager.role_template.get(rb.get("roleTemplateName"))
            role["context:entity"] = rb.get("projectName", None)
            roles.append(role)
        return roles

    def get_role_binds(self, role_type="global"):
        """get user role binds

        :param role_type: role type. Can be global, cluster, project or all
        :return: user roles
        """
        res = []

        if role_type == "all" or role_type == "global":
            # global role bindings
            role_bindings = self.global_role_bind.list()
            for rb in role_bindings:
                rb["role"] = self.manager.role_global.get(rb.get("globalRoleName"))
            res.extend(role_bindings)

        if role_type == "all" or role_type == "cluster":
            # cluster role bindings
            role_bindings = self.cluster_role_bind.list()
            for rb in role_bindings:
                rb["role"] = self.manager.role_template.get(rb.get("roleTemplateName"))
            res.extend(role_bindings)

        if role_type == "all" or role_type == "project":
            # project role bindings
            role_bindings = self.project_role_bind.list()
            for rb in role_bindings:
                rb["role"] = self.manager.role_template.get(rb.get("roleTemplateName"))
            res.extend(role_bindings)

        self.logger.debug("get users role bindings: %s" % truncate(res))
        return res

    def get_role_bind(self, user_id, role_id, role_type="global", cluster_id=None):
        """get user role bind

        :param user_id: user id
        :param role_id: role id
        :param role_type: role type. Can be global, cluster, project
        :return: user roles
        """
        res = None

        if role_type == "global":
            # global role bindings
            role_bindings = [
                rb["id"]
                for rb in self.global_role_bind.list()
                if rb.get("globalRoleName") == role_id and rb.get("userName") == user_id
            ]
            if 0 < len(role_bindings) < 2:
                res = role_bindings[0]

        elif role_type == "cluster":
            # cluster role bindings
            role_bindings = [
                rb["id"]
                for rb in self.cluster_role_bind.list()
                if rb.get("roleTemplateName") == role_id
                and rb.get("userName") == user_id
                and rb.get("clusterName") == cluster_id
            ]
            if 0 < len(role_bindings) < 2:
                res = role_bindings[0]

        elif role_type == "project":
            # project role bindings
            role_bindings = self.project_role_bind.list()
            for rb in role_bindings:
                rb["role"] = self.manager.role_template.get(rb.get("roleTemplateName"))
            res.extend(role_bindings)
        self.logger.debug("get user %s role %s binding: %s" % (user_id, role_id, truncate(res)))
        return res


class RancherUserGlobalRoleBinding(RancherObject):
    """RancherUserGlobalRoleBinding"""

    def __init__(self, manager):
        super().__init__(manager)
        self.base_uri = "/v1/management.cattle.io.globalrolebindings"

    def list(self, user_id=None, **kwargs):
        """Get global role bindings by user

        :param user_id: user id
        :return:
        """
        data = ""
        res = self.http_get("?").get("data")
        if user_id is not None:
            res = [r for r in res if r.get("userName") == user_id]
        self.logger.debug("get global role binding: %s" % (truncate(res)))
        return res

    def add(self, user_id, role):
        """assign global role to user

        :param user_id: user id
        :param role: global role id
        :return:
        """
        data = {"type": "globalRoleBinding", "globalRoleId": role, "userId": user_id}
        self.base_uri = "/v3/globalrolebindings"
        res = self.http_post("", **data)
        self.logger.debug("assign global role %s to user %s" % (role, user_id))
        return res

    def delete(self, role_id):
        """deassign a global role binding

        :param role_id: role id
        :return:
        """
        self.base_uri = "/v3/globalrolebindings"
        res = self.http_delete("/%s" % role_id)
        self.logger.debug("deassign global role %s" % role_id)
        return res


class RancherUserClusterRoleBinding(RancherObject):
    """RancherUserClusterRoleBinding"""

    def __init__(self, manager):
        super().__init__(manager)
        self.base_uri = "/v1/management.cattle.io.clusterroletemplatebindings"

    def list(self, user_id=None, **kwargs):
        """Get cluster role bindings by user

        :param user_id: user id
        :return:
        """
        res = self.http_get("?").get("data")
        if user_id is not None:
            res = [r for r in res if r.get("userName") == user_id]
        self.logger.debug("get user %s cluster role binding: %s" % (user_id, truncate(res)))
        return res

    def add(self, user_id, role_id, cluster_id, user_type="local"):
        """assign cluster role to user

        :param user_id: user id
        :param role_id: cluster role id
        :param user_type: user type [default=local]
        :return:
        """
        data = {
            "type": "clusterRoleTemplateBinding",
            "clusterId": cluster_id,
            "roleTemplateId": role_id,
            "userPrincipalId": "%s://%s" % (user_type, user_id),
        }
        self.base_uri = "/v3/clusterroletemplatebindings"
        res = self.http_post("", **data)
        self.logger.debug("assign cluster %s role %s to user %s" % (cluster_id, role_id, user_id))
        return res

    def delete(self, role_id):
        """deassign a cluster role binding

        :param role_id: role id
        :return:
        """
        role_id = role_id.replace("/", ":")
        self.base_uri = "/v3/clusterroletemplatebindings"
        res = self.http_delete("/%s" % role_id)
        self.logger.debug("deassign cluster role %s" % role_id)
        return res


class RancherUserProjectRoleBinding(RancherObject):
    """RancherUserProjectRoleBinding"""

    def __init__(self, manager):
        super().__init__(manager)
        self.base_uri = "/v1/management.cattle.io.projectroletemplatebindings"

    def list(self, user_id=None, **kwargs):
        """Get cluster role bindings by user

        :param user_id: user id
        :return:
        """
        res = self.http_get("?").get("data")
        if user_id is not None:
            res = [r for r in res if r.get("userName") == user_id]
        self.logger.debug("get user %s project role binding: %s" % (user_id, truncate(res)))
        return res

    def add(self, user_id, role_id, project_id, user_type="local"):
        """assign project role to user

        :param user_id: user id
        :param role_id: project role id
        :param user_type: user type [default=local]
        :return:
        """
        data = {
            "type": "projectRoleTemplateBinding",
            "projectId": project_id,
            "roleTemplateId": role_id,
            "userPrincipalId": "%s://%s" % (user_type, user_id),
        }
        self.base_uri = "/v3/projectroletemplatebindings"
        res = self.http_post("", **data)
        self.logger.debug("assign project %s role %s to user %s" % (project_id, role_id, user_id))
        return res

    def delete(self, role_id):
        """deassign a project role binding

        :param role_id: role id
        :return:
        """
        role_id = role_id.replace("/", ":")
        self.base_uri = "/v3/projectroletemplatebindings"
        res = self.http_delete("/%s" % role_id)
        self.logger.debug("deassign project role %s" % role_id)
        return res
