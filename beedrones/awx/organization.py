# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte


from beecell.simple import truncate
from beedrones.awx.client import AwxEntity


class AwxOrganization(AwxEntity):
    """ """

    def list(self, **params):
        """Get awx organizations

        :return: list of organizations
        :raise AwxError:
        """
        res = self.http_list("organizations/", **params)
        self.logger.debug("list organizations: %s" % truncate(res))
        return res

    def get(self, organization):
        """Get awx organization

        :param organization: organization id
        :return: organization
        :raise AwxError:
        """
        res = self.http_get("organizations/%s/" % organization)
        self.logger.debug("get organization: %s" % truncate(res))
        return res

    def get_users(self, orgid):
        """get awx users in organization id

        :param orgid: organization id
        :return: list of organization's users
        :raise AwxError:
        """
        res = self.http_list("organizations/%s/users/" % orgid)
        self.logger.debug("get organization %s users" % orgid)
        return res
