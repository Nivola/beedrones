# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.types.type_string import truncate
from beedrones.cmp.client import CmpBaseService
from beedrones.cmp.resource import CmpResourceAbstractService


class CmpResourceOntapService(CmpResourceAbstractService):
    """Cmp resource ontap service"""

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        self.volume = CmpResourceOntapVolumeService(self.manager)


class CmpResourceOntapAbstractService(CmpResourceAbstractService):
    """Cmp resource ontap service"""

    pass


class CmpResourceOntapVolumeService(CmpResourceOntapAbstractService):
    """Cmp resource ontap volume service"""

    def list(self, *args, **kwargs):
        """get volumes

        :param container: container id or uuid
        :param name: entity name
        :param desc: entity description
        :param objid: entity authorization id
        :param ext_id: entity ext_id
        :param state: entity state
        :param attributes: entity attributes
        :param tags: comma separated list of tags
        :param page: query page
        :param size: query page size
        :param field: query sort field
        :param order: query sort order
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = [
            "container",
            "name",
            "desc",
            "objid",
            "ext_id",
            "state",
            "tags",
            "attributes",
        ]
        mappings = {"name": lambda n: "%" + n + "%"}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri("ontap/volumes", preferred_version=self.VERSION, **kwargs)
        res = self.api_get(uri, data=data)
        self.logger.debug("get volumes: %s" % truncate(res))
        return res

    def get(self, oid, **kwargs):
        """get volume

        :param oid: volume id or uuid
        :return: instance
        :raise CmpApiClientError:
        """
        uri = self.get_uri("ontap/volumes/%s" % oid, preferred_version=self.VERSION, **kwargs)
        res = self.api_get(uri)
        self.logger.debug("get volume %s: %s" % (oid, truncate(res)))
        return res

    def add(self, container, name, ontap_volume_id, desc=None, **kwargs):
        """add volume

        :param container: container id
        :param name: volume name
        :param desc: volume description
        :param ontap_volume_id: physical id of volume in ontap netapp platform
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        if desc is None:
            desc = name
        data = {
            "container": container,
            "name": name,
            "desc": desc,
            "ontap_volume_id": ontap_volume_id,
        }
        uri = self.get_uri("ontap/volumes", preferred_version=self.VERSION, **kwargs)
        res = self.api_post(uri, data={"volume": data})
        self.logger.debug("Create volume %s" % name)
        return res

    def delete(self, oid, force=True, deep=True, **kwargs):
        """delete volume

        :param oid: id of the container
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri("ontap/volumes/%s" % oid, preferred_version=self.VERSION, **kwargs)
        self.api_delete(uri, data="")
        self.logger.debug("delete volume %s" % oid)
