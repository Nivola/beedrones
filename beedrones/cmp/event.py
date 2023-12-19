# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.types.type_string import truncate
from beedrones.cmp.client import CmpBaseService


class CmpEventAbstractService(CmpBaseService):
    """Cmp resource event"""

    SUBSYSTEM = "event"
    PREFIX = "nes"
    VERSION = "v1.0"

    def get_uri(self, uri):
        return "/%s/%s/%s" % (self.VERSION, self.PREFIX, uri)


class CmpEventService(CmpEventAbstractService):
    """Cmp resource event"""

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

    def list(self, *args, **kwargs):
        """get events

        :param type: event type
        :param name: event name
        :param objid: event authorization id
        :param attributes: event attributes
        :param state: event state
        :param tags: comma separated list of tags
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ["type", "name", "objid", "attributes", "state", "tags"]
        mappings = {"name": lambda n: "%" + n + "%"}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri("events")
        res = self.api_get(uri, data=data)
        self.logger.debug("get events: %s" % truncate(res))
        return res

    def get(self, oid):
        """get event

        :param oid: event id or uuid
        :return: event
        :raise CmpApiClientError:
        """
        uri = self.get_uri("events/%s" % oid)
        res = self.api_get(uri)
        self.logger.debug("get event %s: %s" % (oid, truncate(res)))
        return res

    def list_api(self, *args, **kwargs):
        """get api events

        :param eventid: event id
        :param uri: api uri:method
        :param user: api source user
        :param ip: api source ip
        :param pod: api destination pod
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ["eventid", "uri", "user", "ip", "pod"]
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri("apis")
        res = self.api_get(uri, data=data)
        self.logger.debug("get api events: %s" % truncate(res))
        return res

    def get_api_log(self, oid, **kwargs):
        """get api event log

        :param oid: event id
        :param kwargs.size: number of lines to print
        :param kwargs.page: number of page of lines to print
        :return: task instance log
        :raise CmpApiClientError:
        """
        params = ["size", "page"]
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri("apis/%s/log" % oid)
        res = self.api_get(uri, data=data).get("api_log", {})
        self.logger.debug("get api event %s log: %s" % (oid, truncate(res)))
        return res
