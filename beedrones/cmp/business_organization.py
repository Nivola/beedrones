# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import truncate
from beedrones.cmp.business import CmpBusinessAbstractService
from beedrones.cmp.business_common import CmpBusinessAuthService
from beedrones.cmp.client import CmpBaseService


class CmpBusinessOrganizationService(CmpBusinessAbstractService):
    """Cmp business div
    """
    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)
        
        self.auth = CmpBusinessOrganizationAuthService(self.manager)

    def list(self, *args, **kwargs):
        """get organizations

        :param id: organization id
        :param page: query page
        :param size: query page size
        :param field: query sort field
        :param order: query sort order        
        :param objid: authorization id
        :param name: organization name
        :param organization_id: organization id
        :param contact: organization contact
        :param email: organization email
        :param postaladdress: organization legal email
        :param creation_date_start: creation date start
        :param creation_date_stop: creation date stop
        :return: list of organizations
        :raise CmpApiClientError:
        """
        params = ['name', 'objid', 'organization_id', 'contact', 'email', 'postaladdress', 'creation_date_start',
                  'creation_date_stop']
        aliases = {
            'creation_date_start': 'filter_creation_date_start',
            'creation_date_stop': 'filter_creation_date_stop'
        }
        mappings = {'name': lambda n: '%' + n + '%'}
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri('organizations')
        res = self.api_get(uri, data=data)
        self.logger.debug('get organizations: %s' % truncate(res))
        return res

    def get(self, oid):
        """get organization

        :param oid: organization id or uuid
        :return: div
        :raise CmpApiClientError:
        """
        uri = self.get_uri('organizations/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get organization %s: %s' % (oid, truncate(res)))
        return res

    def add(self, name, organization, **kwargs):
        """Add organization

        :param name: organization name
        :param organization: organization uuid
        :param kwargs.desc: organization description [optional]
        :param kwargs.contact: organization contact [optional]
        :param kwargs.email: organization email [optional]
        :param kwargs.postaladdress: organization postal address [optional]
        :param kwargs.price_list: organization price list id [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'name': name,
            'organization': organization,
        }
        data.update(self.format_request_data(kwargs, ['desc', 'contact', 'email', 'postaladdress', 'price_list']))
        uri = self.get_uri('organizations')
        res = self.api_post(uri, data={'organization': data})
        self.logger.debug('Create organization %s' % name)
        return res

    def update(self, oid, **kwargs):
        """Update organization

        :param oid: id of the div
        :param kwargs.name: organization name [optional]
        :param kwargs.organization: organization uuid [optional]
        :param kwargs.desc: organization description [optional]
        :param kwargs.contact: organization contact [optional]
        :param kwargs.email: organization email [optional]
        :param kwargs.postaladdress: organization postal address [optional]
        :param kwargs.price_list: organization price list id [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ['name',  'desc', 'contact', 'email', 'postaladdress', 'price_list'])
        uri = self.get_uri('organizations/%s' % oid)
        res = self.api_put(uri, data={'organization': data})
        self.logger.debug('Update organization %s' % oid)
        return res

    def patch(self, oid):
        """Patch organization

        :param oid: id of the div
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('organizations/%s' % oid)
        self.api_patch(uri, data={'organization': {}})
        self.logger.debug('patch organization %s' % oid)

    def delete(self, oid):
        """Delete organization

        :param oid: id of the div
        :param delete_services: if True delete chiild services
        :param delete_tags: if True delete child tags
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('organizations/%s' % oid)
        data = ''
        self.api_delete(uri, data=data)
        self.logger.debug('delete organization %s' % oid)


class CmpBusinessOrganizationAuthService(CmpBusinessAuthService):
    """Cmp business organization authorization
    """
    common_name = 'organizations'
