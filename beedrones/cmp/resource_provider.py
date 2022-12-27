# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.types.type_string import truncate
from beedrones.cmp.client import CmpBaseService
from beedrones.cmp.resource import CmpResourceAbstractService


class CmpResourceProviderService(CmpResourceAbstractService):
    """Cmp resource provider service
    """
    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        self.instance = CmpResourceProviderInstanceService(self.manager)


class CmpResourceProviderInstanceService(CmpResourceAbstractService):
    """Cmp resource provider instance service
    """
    def get(self, oid):
        """get instance

        :param oid: instance id or uuid
        :return: instance
        :raise CmpApiClientError:
        """
        uri = self.get_uri('provider/instances/%s' % oid)
        res = self.api_get(uri).get('instance', {})
        self.logger.debug('get instance %s: %s' % (oid, truncate(res)))
        return res

    def load(self, container, name, physical_resource, pwd, image, **kwargs):
        """import provider instance from physical server

        :param container: provider container id
        :param name: instance name
        :param physical_resource: physical server resource id
        :param pwd: instance password
        :param image: instance image
        :param kwargs: additional key value params
        :param kwargs.hotsname: hostname
        :return:
        """
        data = {
            'container': container,
            'name': name,
            'desc': name,
            'physical_id': physical_resource,
            'attribute': {},
            'resclass': 'beehive_resource.plugins.provider.entity.instance.ComputeInstance',
            'configs': {
                'multi_avz': True,
                'admin_pass': pwd,
                'image': image
            }
        }
        data['configs'].update(kwargs)
        uri = self.get_uri('entities/import')
        res = self.api_post(uri, data={'resource': data}).get('uuid', None)
        self.logger.debug('import entity: %s' % res)

    def del_cache(self, oid):
        """Delete resource provider instance cache

        :return:
        """
        uri = self.get_uri('entities/%s/cache' % oid)
        res = self.api_put(uri)
        self.logger.debug('delete cache for provider instance: %s' % res.get('uuid'))
