# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte

from beecell.simple import truncate
from beedrones.elk.client_elastic import ElasticEntity


class ElasticUser(ElasticEntity):
    def get(self, user_name=None):
        """Get elastic user

        :param user_name: user_name
        :return: user
        :raise ElasticError:
        """
        res = self.manager.es.security.get_user(username=user_name)
        self.logger.debug('get user: %s' % truncate(res))
        return res

    def add(self, user_name, password, role, full_name=None, email=None, **params):
        """Add elastic user

        :param str user_name: Name of this user.
        :param str password: role name.
        :param str role: user role
        :param str full_name: (field, default=None)
        :param str email: (field, default=None)
        :return: user
        :raise ElasticError:
        """
        params.update(
            {
                'password': password,
                'roles': [role]
            }           
        )

        if full_name is not None:
            params.update({'full_name': full_name})

        if email is not None:
            params.update({'email': email})

        res = self.manager.es.security.put_user(user_name, params)
        self.logger.debug('add user: %s' % truncate(res))

        created = res['created']
        self.logger.debug('created: %s' % created)
        return created

    def delete(self, user_name):
        """Delete elastic user

        :param user_name: elastic user name
        :return: True
        :raise ElasticError:
        """
        res = self.manager.es.security.delete_user(username=user_name)
        return True
