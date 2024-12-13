# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte
from elasticsearch import NotFoundError

from beecell.simple import truncate
from beedrones.elk.client_elastic import ElasticEntity
from beecell.simple import jsonDumps


class ElasticRoleMapping(ElasticEntity):
    """ """

    def list(self, **params):
        """Get kibana role_mapping

        :return: list of role_mapping
        :raise KibanaError:
        """
        try:
            res = self.manager.es.security.get_role_mapping(**params)
        except NotFoundError:
            res = {}
        self.logger.debug("ElasticRoleMapping -list role mappings: %s" % truncate(res))
        return res

    def get(self, role_mapping_name=None):
        """Get elastic role_mapping

        :param role_mapping_name: role_mapping_name
        :return: role_mapping
        :raise ElasticError:
        """
        self.logger.debug("ElasticRoleMapping - get")
        res = self.manager.es.security.get_role_mapping(name=role_mapping_name)
        self.logger.debug("ElasticRoleMapping -get role_mapping: %s" % truncate(res))
        return res

    def add(self, role_mapping_name, role_name, users_email=None, realm_name=None, **params):
        """Add elastic role mapping

        :param str role_mapping_name: Name of this role mapping.
        :param str role_name: role_name.
        :param str user_email: (field, default=None)
        :param str realm_name: (field, default=None)
        :return: role_mapping
        :raise ElasticError:
        """
        # params.update(
        #     {
        #         'metadata': {
        #             'version': 1
        #         },
        #         'roles': [role_name],
        #         'enabled': 'true'
        #     }
        # )

        rules = {}
        if users_email is not None:
            rules = {
                "all": [
                    {"any": [{"field": {"username": [x for x in users_email]}}]},
                    {"field": {"realm.name": realm_name}},
                ]
            }

        self.logger.debug("ElasticRoleMapping -add role mapping params: %s" % params)

        res = self.manager.es.security.put_role_mapping(
            name=role_mapping_name, roles=[role_name], enabled=True, rules=rules
        )
        self.logger.debug("ElasticRoleMapping -add role mapping res: %s" % truncate(res))

        role_mapping = res["role_mapping"]
        created = role_mapping["created"]
        self.logger.debug("ElasticRoleMapping - add - created: %s" % created)
        return role_mapping

    def delete(self, role_mapping_name):
        """Delete elastic role mapping

        :param role_mapping_name: elastic role mapping name
        :return: True
        :raise ElasticError:
        """
        self.logger.debug("ElasticRoleMapping - delete - role_mapping_name: %s" % role_mapping_name)
        res = self.manager.es.security.delete_role_mapping(name=role_mapping_name)
        self.logger.debug("ElasticRoleMapping - delete - res: %s" % res)
        return res["found"]
