# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import truncate
from beedrones.grafana.client_grafana import GrafanaEntity


class GrafanaUser(GrafanaEntity):
    def get(self, user_id=None):
        """Get grafana user

        :param user_id: user_id
        :return: user
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.users.get_user(user_id)
        self.logger.debug("get user: %s" % truncate(res))
        return res

    def get_by_login_or_email(self, login_or_email):
        """Get grafana user

        :param login_or_email: login or email
        :return: user
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.users.find_user(login_or_email)
        self.logger.debug("get user by login_or_email: %s" % truncate(res))
        return res

    def update(self, user_id, name=None, email=None, login=None):
        """Get grafana user

        :param user_id
        :param user
        :return: user
        :raise GrafanaError:
        """
        data_user = {}
        if name is not None:
            data_user.update({"name": name})
        if email is not None:
            data_user.update({"email": email})
        if login is not None:
            data_user.update({"login": login})

        self.logger.debug("update user - data_user: %s" % truncate(data_user))
        res = self.manager.grafanaFace.users.update_user(user_id, data_user)
        self.logger.debug("update user: %s" % truncate(res))
        return res

    def list(self, query=None, page=None, size=None):
        """List grafana users

        :return: users
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.users.search_users(query=query, page=page, perpage=size)
        self.logger.debug("get users: %s" % truncate(res))
        return res

    def add(self, name=None, email=None, login=None, password=None, **params):
        """Add grafana user

        :param str email: login or email of this user.
        :return: user
        :raise GrafanaError:
        """
        data_user = {"email": email}
        if name is not None:
            data_user.update({"name": name})
        if login is not None:
            data_user.update({"login": login})
        if password is not None:
            data_user.update({"password": password})

        self.logger.debug("add user - data_user: %s" % truncate(data_user))
        res = self.manager.grafanaFace.admin.create_user(user=data_user)
        self.logger.debug("add user - res: %s" % truncate(res))

        message = res["message"]
        self.logger.debug("email: %s - message: %s" % (email, message))
        return res

    def delete(self, user_id):
        """Delete grafana user

        :param user_id: grafana user_id
        :return: True
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.organization.delete_user_current_organization(user_id=user_id)
        return True
