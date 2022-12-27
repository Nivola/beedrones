# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import truncate
from beedrones.cmp.client import CmpBaseService


class CmpResourceAbstractService(CmpBaseService):
    """Cmp resource service
    """
    SUBSYSTEM = 'resource'
    PREFIX = 'nrs'
    VERSION = 'v1.0'

    def get_uri(self, uri):
        return '/%s/%s/%s' % (self.VERSION, self.PREFIX, uri)


class CmpResourceService(CmpResourceAbstractService):
    """Cmp resource service
    """
    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        self.entity = CmpResourceEntityService(self.manager)
        self.tag = CmpResourceTagService(self.manager)
        self.link = CmpResourceLinkService(self.manager)
        self.container = CmpResourceContainerService(self.manager)

        from .resource_provider import CmpResourceProviderService
        from .resource_ontap import CmpResourceOntapService

        self.provider = CmpResourceProviderService(self.manager)
        self.ontap = CmpResourceOntapService(self.manager)


class CmpResourceContainerService(CmpResourceAbstractService):
    """Cmp resource container service
    """
    def list(self, *args, **kwargs):
        """get containers

        :param type: container type
        :param name: container name
        :param objid: container authorization id
        :param attributes: container attributes
        :param state: container state
        :param tags: comma separated list of tags
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ['type', 'name', 'objid', 'attributes', 'state', 'tags']
        mappings = {'name': lambda n: '%' + n + '%'}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('containers')
        res = self.api_get(uri, data=data)
        self.logger.debug('get containers: %s' % truncate(res))
        return res

    def get(self, oid):
        """get container

        :param oid: container id or uuid
        :return: container
        :raise CmpApiClientError:
        """
        uri = self.get_uri('containers/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get container %s: %s' % (oid, truncate(res)))
        return res

    def list_types(self, *args, **kwargs):
        """get container types

        :param category: container category
        :param type: container type
        :return: list of container types
        :raise CmpApiClientError:
        """
        params = ['category', 'type']
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri('containers/types')
        res = self.api_get(uri, data=data)
        self.logger.debug('get container types: %s' % truncate(res))
        return res

    def add(self, name, type, desc, conn, **kwargs):
        """Add container

        :param name: container name
        :param type: resource container type
        :param desc: resource container description
        :param dict conn: resource container connection
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'name': name,
            'type': type,
            'desc': desc,
            'conn': conn
        }
        uri = self.get_uri('containers')
        res = self.api_post(uri, data={'resourcecontainer': data})
        self.logger.debug('Create container %s' % name)
        return res

    def update(self, oid, **kwargs):
        """Update container

        :param oid: id of the container
        :param kwargs.name: container name
        :param kwargs.desc: resource container description
        :param dict kwargs.conn: resource container connection
        :param kwargs.active: resource container active status [optional]
        :param kwargs.tags: resource container tags [optional]
        :param kwargs.state: container state
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ['name',  'desc', 'conn', 'active', 'tags', 'state'])
        uri = self.get_uri('containers/%s' % oid)
        res = self.api_put(uri, data={'resourcecontainer': data})
        self.logger.debug('Update container %s' % oid)
        return res

    def delete(self, oid, force=True, deep=True):
        """Delete container

        :param oid: id of the container
        :param force: if True force delete
        :param deep: if True delete all the resource tree
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('containers/%s?force=%s&deep=%s' % (oid, force, deep))
        self.api_delete(uri, data='')
        self.logger.debug('delete container %s' % oid)

    def ping(self, oid):
        """Ping container

        :param oid: id of the container
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('containers/%s/ping' % oid)
        res = self.api_get(uri, data='')
        self.logger.debug('ping container %s: %s' % (oid, res))
        return res

    def discover_types(self, oid):
        """discover container <class> resources

        :param oid: container id or uuid
        :return: list of <class> resources
        :raise CmpApiClientError:
        """
        uri = self.get_uri('containers/%s/discover/types' % oid)
        res = self.api_get(uri, data='')
        self.logger.debug('get container %s <class> resources: %s' % (oid, truncate(res)))
        return res

    def discover(self, oid, resclass):
        """discover container

        :param oid: container id or uuid
        :param resclass: class resource to discover
        :return: list of discovered resources
        :raise CmpApiClientError:
        """
        uri = self.get_uri('containers/%s/discover' % oid)
        res = self.api_get(uri, data='type=%s' % resclass)
        self.logger.debug('get container %s discovered resources: %s' % (oid, truncate(res)))
        return res

    def synchronize(self, oid, resclass, new=True, died=True, changed=True, **kwargs):
        """synchronize container <class> resources

        :param oid: container id or uuid
        :param resclass: class resource to discover
        :param new: add new physical entities [default=True]
        :param died: delete not alive physical entities [default=True]
        :param changed: update physical entities [default=True]
        :param kwargs.ext_id: physical entity id [optional]
        :return:
        :raise CmpApiClientError:
        """
        data = {
            'types': resclass,
            'new': new,
            'died': died,
            'changed': changed
        }
        data.update(self.format_request_data(kwargs, ['ext_id']))
        uri = self.get_uri('containers/%s/discover' % oid)
        res = self.api_put(uri, data={'synchronize': data})
        self.logger.debug('synchronize container %s %s resources: %s' % (oid, resclass, truncate(res)))
        return res


class CmpResourceEntityService(CmpResourceAbstractService):
    """Cmp resource entity service
    """
    def list(self, *args, **kwargs):
        """get entities

        :param container: container id or uuid
        :param type: entity type
        :param name: entity name
        :param desc: entity description
        :param objid: entity authorization id
        :param ext_id: entity ext_id
        :param parent: parent id or uuid
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
        params = ['container', 'type', 'name', 'desc', 'objid', 'ext_id', 'parent', 'state', 'tags', 'attributes']
        mappings = {'name': lambda n: '%' + n + '%'}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('entities')
        res = self.api_get(uri, data=data)
        self.logger.debug('get entities: %s' % truncate(res))
        return res

    def get(self, oid):
        """get entity

        :param oid: entity id or uuid
        :return: entity
        :raise CmpApiClientError:
        """
        uri = self.get_uri('entities/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get entity %s: %s' % (oid, truncate(res)))
        return res

    def list_types(self, *args, **kwargs):
        """get entity types

        :param resclass: entity type resclass
        :param type: entity type
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ['resclass', 'type']
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri('entities/types')
        res = self.api_get(uri, data=data)
        self.logger.debug('get entity types: %s' % truncate(res))
        return res

    def list_errors(self, oid):
        """get the last resource error from a task

        :param oid: entity id
        :return: list of entity errors
        :raise CmpApiClientError:
        """
        uri = self.get_uri('entities/%s/errors' % oid)
        res = self.api_get(uri, data='')
        self.logger.debug('get entity last errors: %s' % truncate(res))
        return res

    def add(self, name, container, resclass, desc, **kwargs):
        """Add entity

        :param name: entity name
        :param container: resource container uuid
        :param resclass: resource entity class
        :param desc: resource entity description
        :param kwargs.ext_id: resource entity physical id [optional]
        :param kwargs.parent: resource entity parent uuid [optional]
        :param kwargs.attribute: resource entity attributes [optional]
        :param kwargs.tags: resource entity tags [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'name': name,
            'container': container,
            'resclass': resclass,
            'desc': desc
        }
        data.update(self.format_request_data(kwargs, ['ext_id', 'parent', 'attribute', 'tags']))
        uri = self.get_uri('entities')
        res = self.api_post(uri, data={'resource': data})
        self.logger.debug('Create entity %s' % name)
        return res

    def update(self, oid, **kwargs):
        """Update entity

        :param oid: id of the entity
        :param kwargs.name: entity name
        :param kwargs.desc: resource entity description [optional]
        :param kwargs.active: resource entity active status [optional]
        :param kwargs.ext_id: resource entity physical id [optional]
        :param kwargs.attribute: resource entity attributes [optional]
        :param kwargs.tags: resource entity tags [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ['name',  'desc', 'ext_id', 'active', 'attribute', 'tags'])
        uri = self.get_uri('entities/%s' % oid)
        res = self.api_put(uri, data={'resource': data})
        self.logger.debug('Update entity %s' % oid)
        return res

    def patch(self, oid):
        """Patch entity

        :param oid: id of the entity
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s' % oid)
        self.api_patch(uri, data={'resource': {}})
        self.logger.debug('patch entity %s' % oid)

    def delete(self, oid, force=True, deep=True):
        """Delete entity

        :param oid: id of the entity
        :param force: if True force delete
        :param deep: if True delete all the resource tree
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s' % oid)
        # data = {'is_force': force, 'is_deep': deep}
        data = ''
        self.api_delete(uri, data=data)
        self.logger.debug('delete entity %s' % oid)

    def tree(self, oid, *args, **kwargs):
        """get entity tree

        :param oid: entity id or uuid
        :return: entity tree
        :raise CmpApiClientError:
        """
        params = ['parent', 'link']
        data = self.format_query(kwargs, params)
        uri = self.get_uri('entities/%s/tree' % oid)
        res = self.api_get(uri, data=data)
        self.logger.debug('get entity %s tree: %s' % (oid, truncate(res)))
        return res

    def check(self, oid, **kwargs):
        """check entity

        :param oid: id of the entity
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s/check' % oid)
        res = self.api_get(uri, data='')
        self.logger.debug('Check entity %s' % oid)
        return res

    def get_cache(self, oid):
        """Get entity cache

        :param oid: id of the entity
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s/cache' % oid)
        res = self.api_get(uri, data='')
        self.logger.debug('get entity %s cache' % oid)
        return res

    def del_cache(self, oid):
        """Delete entity cache

        :param oid: id of the entity
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s/cache' % oid)
        self.api_put(uri, data='')
        self.logger.debug('delete entity %s cache' % oid)

    def get_config(self, oid):
        """Get entity config

        :param oid: id of the entity
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s/config' % oid)
        res = self.api_get(uri, data='')
        self.logger.debug('get entity %s config: %s' % (oid, truncate(res)))
        return res

    def set_config(self, oid, key, value=None):
        """Delete entity config

        :param oid: id of the entity
        :param key: config key
        :param value: config value [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s/config' % oid)
        data = {'config': {'key': key, 'value': value}}
        self.api_put(uri, data=data)
        self.logger.debug('set entity %s config' % oid)

    def enable_quota(self, oid):
        """Enable entity quota

        :param oid: id of the entity
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s' % oid)
        self.api_put(uri, data={'resource': {'enable_quotas': True}})
        self.logger.debug('enable entity %s quota' % oid)

    def disable_quota(self, oid):
        """Disable entity quota

        :param oid: id of the entity
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s' % oid)
        self.api_put(uri, data={'resource': {'disable_quotas': True}})
        self.logger.debug('disable entity %s quota' % oid)

    def get_linked_entities(self, oid):
        """Get linked entities

        :param oid: id of the entity
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s/linked' % oid)
        res = self.api_get(uri, data='')
        self.logger.debug('get entity %s linked entities: %s' % (oid, truncate(res)))
        return res

    def get_metrics(self, oid):
        """Get entity metrics

        :param oid: id of the entity
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s/metrics' % oid)
        res = self.api_get(uri, data='')
        self.logger.debug('get entity %s metrics: %s' % (oid, truncate(res)))
        return res

    def set_state(self, oid, state):
        """Set entity state

        :param oid: id of the entity
        :param state: entity state
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('entities/%s/state' % oid)
        self.api_put(uri, data={'state': state})
        self.logger.debug('set entity %s state to %s' % (oid, state))

    def add_tag(self, oid, tag):
        """add tag to entity

        :param oid: id of the entity
        :param tag: tag name
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'tags': {
                    'cmd': 'add',
                    'values': [tag]
                }
        }
        uri = self.get_uri('entities/%s' % oid)
        self.api_put(uri, data={'resource': data})
        self.logger.debug('add tag %s to resource %s' % (tag, oid))

    def del_tag(self, oid, tag):
        """add tag to entity

        :param oid: id of the entity
        :param tag: tag name
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'tags': {
                    'cmd': 'remove',
                    'values': [tag]
                }
        }
        uri = self.get_uri('entities/%s' % oid)
        self.api_put(uri, data={'resource': data})
        self.logger.debug('remove tag %s from resource %s' % (tag, oid))


class CmpResourceLinkService(CmpResourceAbstractService):
    """Cmp resource link service
    """
    def list(self, *args, **kwargs):
        """get links

        :param type: link type
        :param name: link name
        :param objid: link authorization id
        :param resource: start or end resource id
        :param tags: comma separated list of tags
        :return: list of links
        :raise CmpApiClientError:
        """
        params = ['type', 'name', 'objid', 'resource', 'tags']
        mappings = {'name': lambda n: '%' + n + '%'}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('links')
        res = self.api_get(uri, data=data)
        self.logger.debug('get links: %s' % truncate(res))
        return res

    def get(self, oid):
        """get link

        :param oid: link id or uuid
        :return: link
        :raise CmpApiClientError:
        """
        uri = self.get_uri('links/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get link %s: %s' % (oid, truncate(res)))
        return res

    def add(self, name, type, start_resource, end_resource, **kwargs):
        """Add link

        :param name: link name
        :param type: link type
        :param start_resource: start resource id
        :param end_resource: end resource id
        :param kwargs.attributes: link attributes [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'name': name,
            'type': type,
            'start_resource': start_resource,
            'end_resource': end_resource
        }
        data.update(self.format_request_data(kwargs, ['attributes']))
        if 'attributes' not in data:
            data['attributes'] = {}
        uri = self.get_uri('links')
        res = self.api_post(uri, data={'resourcelink': data})
        self.logger.debug('Create link %s' % name)
        return res

    def update(self, oid, **kwargs):
        """Update link

        :param oid: id of the link
        :param kwargs.name: link name
        :param kwargs.type: link type
        :param kwargs.start_resource: start resource id
        :param kwargs.end_resource: end resource id
        :param kwargs.attributes: link attributes [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ['name',  'type', 'start_resource', 'end_resource', 'attributes'])
        uri = self.get_uri('links/%s' % oid)
        res = self.api_put(uri, data={'resourcelink': data})
        self.logger.debug('Update link %s' % oid)
        return res

    def patch(self, oid):
        """Patch link

        :param oid: id of the link
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('links/%s' % oid)
        self.api_patch(uri, data={'resourcelink': {}})
        self.logger.debug('patch link %s' % oid)

    def delete(self, oid):
        """Delete link

        :param oid: id of the link
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('links/%s' % oid)
        self.api_delete(uri, data='')
        self.logger.debug('delete link %s' % oid)


class CmpResourceTagService(CmpResourceAbstractService):
    """Cmp resource tag service
    """
    def list(self, *args, **kwargs):
        """get tags

        :param value: tag value
        :param container: resource container id
        :param resource: resource id
        :param link: link id
        :return: list of tags
        :raise CmpApiClientError:
        """
        params = ['value', 'container', 'resource', 'link']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('tags')
        res = self.api_get(uri, data=data)
        self.logger.debug('get tags: %s' % truncate(res))
        return res

    def get(self, oid):
        """get tag

        :param oid: tag id or uuid
        :return: tag
        :raise CmpApiClientError:
        """
        uri = self.get_uri('tags/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get tag %s: %s' % (oid, truncate(res)))
        return res

    def add(self, value, **kwargs):
        """Add tag

        :param value: tag value
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'value': value
        }
        uri = self.get_uri('tags')
        res = self.api_post(uri, data={'resourcetag': data})
        self.logger.debug('Create tag %s' % value)
        return res

    def update(self, oid, **kwargs):
        """Update tag

        :param oid: id of the tag
        :param kwargs.value: tag value
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ['value'])
        uri = self.get_uri('tags/%s' % oid)
        res = self.api_put(uri, data={'resourcetag': data})
        self.logger.debug('Update tag %s' % oid)
        return res

    def delete(self, oid):
        """Delete tag

        :param oid: id of the tag
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('tags/%s' % oid)
        self.api_delete(uri, data='')
        self.logger.debug('delete tag %s' % oid)
