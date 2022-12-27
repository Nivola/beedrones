# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import truncate
from beedrones.cmp.business import CmpBusinessAbstractService
from beedrones.cmp.business_common import CmpBusinessAuthService
from beedrones.cmp.client import CmpBaseService


class CmpBusinessDivisionService(CmpBusinessAbstractService):
    """Cmp business div
    """
    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)
        
        self.auth = CmpBusinessDivisionAuthService(self.manager)

    def list(self, *args, **kwargs):
        """get divisions

        :param id: division id
        :param page: query page
        :param size: query page size
        :param field: query sort field
        :param order: query sort order        
        :param objid: authorization id
        :param name: division name
        :param organization_id: organization id
        :param contact: division contact
        :param email: division email
        :param postaladdress: division legal email
        :param creation_date_start: creation date start
        :param creation_date_stop: creation date stop
        :return: list of divisions
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
        uri = self.get_uri('divisions')
        res = self.api_get(uri, data=data)
        self.logger.debug('get divisions: %s' % truncate(res))
        return res

    def get(self, oid):
        """get division

        :param oid: division id or uuid
        :return: div
        :raise CmpApiClientError:
        """
        uri = self.get_uri('divisions/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get division %s: %s' % (oid, truncate(res)))
        return res

    def add(self, name, organization, **kwargs):
        """Add division

        :param name: division name
        :param organization: division uuid
        :param kwargs.desc: division description [optional]
        :param kwargs.contact: division contact [optional]
        :param kwargs.email: division email [optional]
        :param kwargs.postaladdress: division postal address [optional]
        :param kwargs.price_list: division price list id [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'name': name,
            'organization': organization,
        }
        data.update(self.format_request_data(kwargs, ['desc', 'contact', 'email', 'postaladdress', 'price_list']))
        uri = self.get_uri('divisions')
        res = self.api_post(uri, data={'division': data})
        self.logger.debug('Create division %s' % name)
        return res

    def update(self, oid, **kwargs):
        """Update division

        :param oid: id of the div
        :param kwargs.name: division name [optional]
        :param kwargs.division: division uuid [optional]
        :param kwargs.desc: division description [optional]
        :param kwargs.contact: division contact [optional]
        :param kwargs.email: division email [optional]
        :param kwargs.postaladdress: division postal address [optional]
        :param kwargs.price_list: division price list id [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ['name',  'desc', 'contact', 'email', 'postaladdress', 'price_list'])
        uri = self.get_uri('divisions/%s' % oid)
        res = self.api_put(uri, data={'division': data})
        self.logger.debug('Update division %s' % oid)
        return res

    def patch(self, oid):
        """Patch division

        :param oid: id of the div
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('divisions/%s' % oid)
        self.api_patch(uri, data={'division': {}})
        self.logger.debug('patch division %s' % oid)

    def delete(self, oid):
        """Delete division

        :param oid: id of the div
        :param delete_services: if True delete chiild services
        :param delete_tags: if True delete child tags
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('divisions/%s' % oid)
        data = ''
        self.api_delete(uri, data=data)
        self.logger.debug('delete division %s' % oid)


class CmpBusinessDivisionAuthService(CmpBusinessAuthService):
    """Cmp business division authorization
    """
    common_name = 'divisions'
