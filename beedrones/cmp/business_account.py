# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import truncate
from beecell.types.type_dict import dict_get
from beedrones.cmp.business import CmpBusinessAbstractService
from beedrones.cmp.business_common import CmpBusinessAuthService
from beedrones.cmp.client import CmpBaseService, CmpApiManagerError


class CmpBusinessAccountService(CmpBusinessAbstractService):
    """Cmp business account
    """
    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        self.auth = CmpBusinessAccountAuthService(self.manager)

    def list(self, *args, **kwargs):
        """get accounts

        :param id: account id
        :param page: query page
        :param size: query page size
        :param field: query sort field
        :param order: query sort order        
        :param objid: authorization id
        :param name: account name
        :param division_id: division uuid
        :param contact: account contact
        :param email: account email
        :param email_support: account email support
        :param creation_date_start: creation date start
        :param creation_date_stop: creation date stop
        :return: list of accounts
        :raise CmpApiClientError:
        """
        params = ['name', 'objid', 'division_id', 'contact', 'email', 'email_support', 'creation_date_start',
                  'creation_date_stop']
        aliases = {
            'creation_date_start': 'filter_creation_date_start',
            'creation_date_stop': 'filter_creation_date_stop'
        }
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri('accounts')
        res = self.api_get(uri, data=data)
        self.logger.debug('get accounts: %s' % truncate(res))
        return res

    def get(self, oid):
        """get account

        :param oid: account id or uuid
        :return: account
        :raise CmpApiClientError:
        """
        uri = self.get_uri('accounts/%s' % oid)
        res = self.api_get(uri).get('account', {})
        self.logger.debug('get account %s: %s' % (oid, truncate(res)))
        return res

    def add(self, name, division, acronym='', **kwargs):
        """Add account

        :param name: account name
        :param division: division uuid
        :param acronym: account acronym [default='']
        :param kwargs.desc: account description [optional]
        :param kwargs.contact: account contact [optional]
        :param kwargs.email: account email [optional]
        :param kwargs.email_support: account email support [optional]
        :param kwargs.email_support_link: account email support link [optional]
        :param kwargs.note: account note [optional]
        :param kwargs.managed: if true set account as managed [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'name': name,
            'division_id': division,
            'acronym': acronym
        }
        data.update(self.format_request_data(kwargs, ['desc', 'contact', 'email', 'email_support', 'email_support_link',
                                                      'note', 'managed']))
        uri = self.get_uri('accounts')
        res = self.api_post(uri, data={'account': data}).get('uuid')
        self.logger.debug('Create account %s' % name)
        return res

    def update(self, oid, **kwargs):
        """Update account

        :param oid: id of the account
        :param name: account name [optional]
        :param division: division uuid [optional]
        :param kwargs.desc: account description [optional]
        :param kwargs.contact: account contact [optional]
        :param kwargs.email: account email [optional]
        :param kwargs.email_support: account email support [optional]
        :param kwargs.email_support_link: account email support link [optional]
        :param kwargs.note: account note [optional]
        :param kwargs.acronym: account acronym [optional]
        :param kwargs.managed: if true set account as managed [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ['name',  'desc', 'ext_id', 'active', 'attribute', 'tags'])
        uri = self.get_uri('accounts/%s' % oid)
        res = self.api_put(uri, data={'account': data})
        self.logger.debug('Update account %s' % oid)
        return res

    def patch(self, oid):
        """Patch account

        :param oid: id of the account
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('accounts/%s' % oid)
        self.api_patch(uri, data={'account': {}})
        self.logger.debug('patch account %s' % oid)

    def delete(self, oid, delete_services=True, delete_tags=True):
        """Delete account

        :param oid: id of the account
        :param delete_services: if True delete chiild services
        :param delete_tags: if True delete child tags
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('accounts/%s' % oid)
        data = {'delete_services': delete_services, 'delete_tags': delete_tags}
        self.api_delete(uri, data=data)
        self.logger.debug('delete account %s' % oid)

    def get_tags(self, oid, *args, **kwargs):
        """get account tags

        :param oid: account id or uuid
        :param page: query page
        :param size: query page size
        :param field: query sort field
        :param order: query sort order
        :return: account
        :raise CmpApiClientError:
        """
        params = []
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('accounts/%s/tags' % oid)
        res = self.api_get(uri, data=data)
        self.logger.debug('get account %s tags: %s' % (oid, truncate(res)))
        return res

    def get_definitions(self, oid, *args, **kwargs):
        """get account definitions

        :param oid: account id or uuid
        :param page: query page
        :param size: query page size
        :param field: query sort field
        :param order: query sort order
        :param plugintype: filter by definition plugin
        :param category: filter by category
        :param container: get only containers definitions
        :return: account
        :raise CmpApiClientError:
        """
        params = ['plugintype', 'category', 'container']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('accounts/%s/definitions' % oid, version='v2.0')
        res = self.api_get(uri, data=data)
        self.logger.debug('get account %s definitions: %s' % (oid, truncate(res)))
        return res

    def add_definitions(self, oid, definitions, *args, **kwargs):
        """add account definitions

        :param oid: account id or uuid
        :param definitions: list of definition uuid or name
        :return: account
        :raise CmpApiClientError:
        """
        data = definitions
        uri = self.get_uri('accounts/%s/definitions' % oid, version='v2.0')
        res = self.api_post(uri, data={'definitions': data})
        self.logger.debug('add account %s definitions %s: %s' % (oid, definitions, truncate(res)))
        return res

    def get_active_services(self, oid):
        """get account active services info

        :param oid: account id or uuid
        :return: active services
        :raise CmpApiClientError:
        """
        data = ''
        uri = self.get_uri('accounts/%s/activeservices' % oid)
        res = self.api_get(uri, data=data)
        self.logger.debug('get account %s active services: %s' % (oid, truncate(res)))
        return res

    # def get_consumes(self, oid):
    #     """get account consumes
    #
    #     :param oid: account id or uuid
    #     :return: active services
    #     :raise CmpApiClientError:
    #     """
    #     data = ''
    #     uri = self.get_uri('accounts/%s/costs' % oid)
    #     res = self.api_get(uri, data=data)
    #     self.logger.debug('get account %s consumes: %s' % (oid, truncate(res)))
    #     return res

    def get_capabilities(self, oid, *args, **kwargs):
        """get account capabilities

        :param oid: account id or uuid
        :return: active services
        :raise CmpApiClientError:
        """
        params = []
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('accounts/%s/capabilities' % oid)
        res = self.api_get(uri, data=data)
        self.logger.debug('get account %s capabilities: %s' % (oid, truncate(res)))
        return res

    def add_capabilities(self, oid, capabilities, *args, **kwargs):
        """get account capabilities

        :param oid: account id or uuid
        :param capabilities: capability list
        :return: {'taskid':..}
        :raise CmpApiClientError:
        """
        data = capabilities
        uri = self.get_uri('accounts/%s/capabilities' % oid)
        res = self.api_post(uri, data={'capabilities': data})
        self.logger.debug('add account %s capabilities %s: %s' % (oid, capabilities, truncate(res)))
        return res

    def tree(self, oid, *args, **kwargs):
        """get account tree. It describe the deep tree from service to resource

        :param oid: account id or uuid
        :return: active services
        :raise CmpApiClientError:
        """
        account = self.get(oid)

        res = self.manager.business.service.instance.list(account_id=oid, plugintype='ComputeService')\
            .get('serviceinsts', [])
        if len(res) > 0:
            compute_zone = dict_get(res, '0.resource_uuid')
        else:
            raise CmpApiManagerError('account %s tree can not be evaluated' % oid)

        tree = self.manager.resource.entity.tree(compute_zone).get('resourcetree', {})
        account['type'] = dict_get(account, '__meta__.definition')
        account['state'] = account['status']
        account['children'] = [tree]
        self.logger.debug('get account %s tree: %s' % (oid, truncate(account)))
        return account


class CmpBusinessAccountAuthService(CmpBusinessAuthService):
    """Cmp business account authorization
    """
    common_name = 'accounts'
