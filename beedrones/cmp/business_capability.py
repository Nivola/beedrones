# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import truncate
from beecell.types.type_dict import dict_get
from beedrones.cmp.business import CmpBusinessAbstractService
from beedrones.cmp.business_common import CmpBusinessAuthService
from beedrones.cmp.client import CmpBaseService, CmpApiManagerError


class CmpBusinessCapabilityService(CmpBusinessAbstractService):
    """Cmp business capability"""

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

    def list(self, *args, **kwargs):
        """get capabilities

        :param id: capability id
        :param objid: capability objid
        :param page: query page
        :param size: query page size
        :param field: query sort field
        :param order: query sort order
        :param objid: authorization id
        :return: list of capabilities
        :raise CmpApiClientError:
        """
        params = ["id", "objid"]
        aliases = {}
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri("capabilities")
        res = self.api_get(uri, data=data)
        self.logger.debug("get capabilities: %s" % truncate(res))
        return res

    def get(self, oid):
        """get capability

        :param oid: capability id or uuid
        :return: capability
        :raise CmpApiClientError:
        """
        uri = self.get_uri("capabilities/%s" % oid)
        res = self.api_get(uri).get("capability")
        self.logger.debug("get capability %s: %s" % (oid, truncate(res)))
        return res

    # def add(self, name, division, **kwargs):
    #     """Add capability
    #
    #     :param name: capability name
    #     :param division: division uuid
    #     :param kwargs.desc: capability description [optional]
    #     :param kwargs.contact: capability contact [optional]
    #     :param kwargs.email: capability email [optional]
    #     :param kwargs.email_support: capability email support [optional]
    #     :param kwargs.email_support_link: capability email support link [optional]
    #     :param kwargs.note: capability note [optional]
    #     :param kwargs.acronym: capability acronym [optional]
    #     :param kwargs.managed: if true set capability as managed [optional]
    #     :return:
    #     :raises CmpApiClientError: raise :class:`CmpApiClientError`
    #     """
    #     data = {
    #         'name': name,
    #         'division': division,
    #     }
    #     data.update(self.format_request_data(kwargs, ['desc', 'contact', 'email', 'email_support', 'email_support_link',
    #                                                   'note', 'acronym', 'managed']))
    #     uri = self.get_uri('capabilities')
    #     res = self.api_post(uri, data={'capability': data})
    #     self.logger.debug('Create capability %s' % name)
    #     return res
    #
    # def update(self, oid, **kwargs):
    #     """Update capability
    #
    #     :param oid: id of the capability
    #     :param name: capability name [optional]
    #     :param division: division uuid [optional]
    #     :param kwargs.desc: capability description [optional]
    #     :param kwargs.contact: capability contact [optional]
    #     :param kwargs.email: capability email [optional]
    #     :param kwargs.email_support: capability email support [optional]
    #     :param kwargs.email_support_link: capability email support link [optional]
    #     :param kwargs.note: capability note [optional]
    #     :param kwargs.acronym: capability acronym [optional]
    #     :param kwargs.managed: if true set capability as managed [optional]
    #     :return:
    #     :raises CmpApiClientError: raise :class:`CmpApiClientError`
    #     """
    #     data = self.format_request_data(kwargs, ['name',  'desc', 'ext_id', 'active', 'attribute', 'tags'])
    #     uri = self.get_uri('capabilities/%s' % oid)
    #     res = self.api_put(uri, data={'capability': data})
    #     self.logger.debug('Update capability %s' % oid)
    #     return res
    #
    # def patch(self, oid):
    #     """Patch capability
    #
    #     :param oid: id of the capability
    #     :return:
    #     :raises CmpApiClientError: raise :class:`CmpApiClientError`
    #     """
    #     uri = self.get_uri('capabilities/%s' % oid)
    #     self.api_patch(uri, data={'capability': {}})
    #     self.logger.debug('patch capability %s' % oid)

    def delete(self, oid):
        """Delete capability

        :param oid: id of the capability
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri("capabilities/%s" % oid)
        data = ""
        self.api_delete(uri, data=data)
        self.logger.debug("delete capability %s" % oid)
