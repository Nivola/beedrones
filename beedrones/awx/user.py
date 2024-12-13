# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import truncate
from beedrones.awx.client import AwxEntity


class AwxUser(AwxEntity):
    """ """

    def list(self, **params):
        """Get awx users

        :return: list of users
        :raise AwxError:
        """
        res = self.http_list("users/", **params)
        self.logger.debug("list users: %s" % truncate(res))
        return res

    def get(self, user):
        """Get awx user

        :param user: user id
        :return: user
        :raise AwxError:
        """
        res = self.http_get("users/%s/" % user)
        self.logger.debug("get user: %s" % truncate(res))
        return res

    def add(self, username, password, **params):
        """Add awx user

        :param str username: Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. (string, required)
        :param str first_name: (string, default="")
        :param str last_name: (string, default="")
        :param str email: (string, default="")
        :param bool is_superuser: Designates that this user has all permissions without explicitly assigning them.
            (boolean, default=False)
        :param bool is_system_auditor: (boolean, default=False)
        :param str password: Write-only field used to change the password.
        :param datetime last_login: (datetime, default=``)
        :return: user
        :raise AwxError:
        """
        params.update({"username": username, "password": password})
        res = self.http_post("users/", data=params)
        self.logger.debug("add user: %s" % truncate(res))
        return res

    def delete(self, user):
        """Delete awx user

        :param user: awx user id
        :return: True
        :raise AwxError:
        """
        self.http_delete("users/%s/" % user)
        self.logger.debug("delete user %s" % user)
        return True
