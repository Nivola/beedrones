# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import jsonDumps

from beecell.simple import truncate
from beedrones.elk.client_kibana import KibanaEntity


class KibanaRole(KibanaEntity):
    """ """

    def list(self, **params):
        """Get kibana roles

        :return: list of roles
        :raise KibanaError:
        """
        res = self.http_list("api/security/role", **params)
        self.logger.debug("KibanaRole - list roles: %s" % truncate(res))
        return res

    def get(self, role_id):
        """Get kibana role

        :param role: role id
        :return: role
        :raise KibanaError:
        """
        res = self.http_get("api/security/role/%s" % role_id)
        self.logger.debug("KibanaRole - get role: %s" % truncate(res))
        return res

    def add(self, role_name, indice, space_id, **params):
        """Add kibana role

        :param str role_name: Name of this role.
        :param str indice: indice of this role.
        :param str space_id
        :return: role
        :raise KibanaError:
        """

        params.update(
            {
                "metadata": {"version": 1},
                "elasticsearch": {"indices": [{"names": [indice], "privileges": ["all"]}]},
                "kibana": [
                    {
                        "base": [],  # 'read', 'all'
                        "feature": {  # definition of [feature] isn't allowed when non-empty [base] is defined
                            "discover": ["all"],
                            "dashboard": ["all"],
                        },
                        "spaces": [space_id],
                    }
                ],
            }
        )
        res = self.http_put("api/security/role/%s" % role_name, data=params)
        self.logger.debug("KibanaRole - add role: %s" % truncate(res))
        return res

    def delete(self, role_name):
        """Delete kibana role

        :param role_id: kibana role id
        :return: True
        :raise KibanaError:
        """
        self.logger.debug("KibanaRole - delete - role_name: %s" % role_name)
        self.http_delete("api/security/role/%s" % role_name)
        return True
