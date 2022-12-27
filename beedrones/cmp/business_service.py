# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import truncate
from beecell.types.type_dict import dict_get
from beedrones.cmp.business import CmpBusinessAbstractService
from beedrones.cmp.client import CmpBaseService


class CmpBusinessServiceService(CmpBusinessAbstractService):
    """Cmp business service service
    """

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        self.definition = CmpBusinessServiceDefinitionService(self.manager)
        self.instance = CmpBusinessServiceInstanceService(self.manager)


class CmpBusinessServiceDefinitionService(CmpBusinessAbstractService):
    """Cmp business service definition service
    """
    VERSION = 'v1.0'

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

    def list(self, *args, **kwargs):
        """get service definitions

        :param id: service definition id
        :param page: query page
        :param size: query page size
        :param field: query sort field
        :param order: query sort order
        :param objid: authorization id
        :param name: service definition name
        :param version: definition version
        :param status: type status
        :param account_id: account id
        :param resource: resource uuid
        :param parent: parent service definition
        :param plugintype: service plugintype
        :param tags: comma separated tag list
        :param iscontainer: if True show only container service definition
        :param creation_date_start: creation date start
        :param creation_date_stop: creation date stop
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ['name', 'objid', 'version', 'status', 'account_id', 'resource', 'parent', 'plugintype',
                  'tags', 'iscontainer', 'creation_date_start', 'creation_date_stop']
        aliases = {
            'account': 'account_id',
            'resource': 'resource_uuid',
            'parent': 'parent_id',
            'iscontainer': 'flag_container',
            'creation_date_start': 'filter_creation_date_start',
            'creation_date_stop': 'filter_creation_date_stop'
        }
        mappings = {'name': lambda n: '%' + n + '%'}
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri('servicedefs')
        res = self.api_get(uri, data=data)
        self.logger.debug('get service definitions: %s' % truncate(res))
        return res

    def get(self, oid):
        """get service definition

        :param oid: service definition id or uuid
        :return: servicedef
        :raise CmpApiClientError:
        """
        uri = self.get_uri('servicedefs/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get servicedef %s: %s' % (oid, truncate(res)))
        return res

    def add(self, name, division, **kwargs):
        """Add service definition

        :param name: service definition name
        :param division: division uuid
        :param kwargs.desc: servicedef description [optional]
        :param kwargs.contact: servicedef contact [optional]
        :param kwargs.email: servicedef email [optional]
        :param kwargs.email_support: servicedef email support [optional]
        :param kwargs.email_support_link: servicedef email support link [optional]
        :param kwargs.note: servicedef note [optional]
        :param kwargs.acronym: servicedef acronym [optional]
        :param kwargs.managed: if true set servicedef as managed [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'name': name,
            'division': division,
        }
        data.update(self.format_request_data(kwargs, ['desc', 'contact', 'email', 'email_support', 'email_support_link',
                                                      'note', 'acronym', 'managed']))
        uri = self.get_uri('servicedefs')
        res = self.api_post(uri, data={'resource': data})
        self.logger.debug('Create servicedef %s' % name)
        return res

    def update(self, oid, **kwargs):
        """Update service definition

        :param oid: id of the service definition
        :param -resource_uuid: resource uuid
        :param -parent: parent service definition
        :param -name: service definition name
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ['name', 'parent', 'resource_uuid'])
        uri = self.get_uri('servicedefs/%s' % oid)
        res = self.api_put(uri, data={'servicedef': data})
        self.logger.debug('Update service definition %s' % oid)
        return res

    def delete(self, oid):
        """Delete service definition

        :param oid: id of the service definition
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('servicedefs/%s' % oid, version='v2.0')
        data = ''
        self.api_delete(uri, data=data)
        self.logger.debug('delete service definition %s' % oid)

    def set_config(self, oid, key, value=None):
        """Update service definition config

        :param oid: id of the service definition
        :param key: config key like config.key
        :param value: config value
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('servicedefs/%s/config' % oid)
        self.api_put(uri, data={'config': {'key': key, 'value': value}})
        self.logger.debug('update service entity %s config' % oid)


class CmpBusinessServiceInstanceService(CmpBusinessAbstractService):
    """Cmp business service instance service
    """
    VERSION = 'v2.0'

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

    def list(self, *args, **kwargs):
        """get service instances

        :param id: service instance id
        :param page: query page
        :param size: query page size
        :param field: query sort field
        :param order: query sort order
        :param objid: authorization id
        :param name: service instance name
        :param names: service instance name like filter
        :param version: definition version
        :param status: type status
        :param account_id: account id
        :param resource: resource uuid
        :param parent: parent service instance
        :param plugintype: service plugintype
        :param tags: comma separated tag list
        :param iscontainer: if True show only container service instance
        :param creation_date_start: creation date start
        :param creation_date_stop: creation date stop
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ['name', 'names', 'objid', 'version', 'status', 'account_id', 'resource', 'parent', 'plugintype',
                  'tags', 'iscontainer', 'creation_date_start', 'creation_date_stop']
        aliases = {
            'account': 'account_id',
            'resource': 'resource_uuid',
            'parent': 'parent_id',
            'iscontainer': 'flag_container',
            'creation_date_start': 'filter_creation_date_start',
            'creation_date_stop': 'filter_creation_date_stop'
        }
        mappings = {'names': lambda n: '%' + n + '%'}
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri('serviceinsts')
        res = self.api_get(uri, data=data)
        self.logger.debug('get service instances: %s' % truncate(res))
        return res

    def get(self, oid):
        """get service instance

        :param oid: service instance id or uuid
        :return: serviceinst
        :raise CmpApiClientError:
        """
        uri = self.get_uri('serviceinsts/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get serviceinst %s: %s' % (oid, truncate(res)))
        return res

    def tree(self, oid, *args, **kwargs):
        """get account tree. It describe the deep tree from service to resource

        :param oid: account id or uuid
        :return: active services
        :raise CmpApiClientError:
        """
        serviceinst = self.get(oid).get('serviceinst')
        resource = dict_get(serviceinst, 'resource_uuid')
        tree = self.manager.resource.entity.tree(resource).get('resourcetree', {})
        serviceinst['type'] = dict_get(serviceinst, '__meta__.definition')
        serviceinst['state'] = serviceinst['status']
        serviceinst['children'] = [tree]
        self.logger.debug('get serviceinst %s tree: %s' % (oid, truncate(serviceinst)))
        return serviceinst

    def add(self, name, division, **kwargs):
        """Add service instance

        :param name: service instance name
        :param division: division uuid
        :param kwargs.desc: serviceinst description [optional]
        :param kwargs.contact: serviceinst contact [optional]
        :param kwargs.email: serviceinst email [optional]
        :param kwargs.email_support: serviceinst email support [optional]
        :param kwargs.email_support_link: serviceinst email support link [optional]
        :param kwargs.note: serviceinst note [optional]
        :param kwargs.acronym: serviceinst acronym [optional]
        :param kwargs.managed: if true set serviceinst as managed [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'name': name,
            'division': division,
        }
        data.update(self.format_request_data(kwargs, ['desc', 'contact', 'email', 'email_support', 'email_support_link',
                                                      'note', 'acronym', 'managed']))
        uri = self.get_uri('serviceinsts')
        res = self.api_post(uri, data={'resource': data})
        self.logger.debug('Create serviceinst %s' % name)
        return res

    def load(self, name, account, plugintype, container_plugintype, resource, *args, **kwargs):
        """import service instance from resource

        :param name: service instance name', 'action': 'store', 'type': str}),
        :param account: account id', 'action': 'store', 'type': str}),
        :param plugintype: plugin type of the service instance', 'action': 'store', 'type': str}),
        :param container_plugintype: plugin type of the container', 'action': 'store', 'type': str}),
        :param resource: resource id
        :param desc: description [optional]
        :param service_definition_id: service definition id [optional]
        :param parent: parent id [optional]
        :return:
        """
        
        data = {
            'name': name,
            'account_id': account,
            'plugintype': plugintype,
            'container_plugintype': container_plugintype,
            'resource_id': resource,
        }
        data.update(self.format_request_data(kwargs, ['desc', 'service_definition_id', 'parent']))
        uri = self.get_uri('serviceinsts/import')
        res = self.api_post(uri, data={'serviceinst': data}).get('uuid', None)
        self.logger.debug('import service instance: %s' % res)
        return res

    def update(self, oid, **kwargs):
        """Update service instance

        :param oid: id of the service instance
        :param -resource_uuid: resource uuid
        :param -parent: parent service instance
        :param -name: service instance name
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ['name',  'parent', 'resource_uuid'])
        uri = self.get_uri('serviceinsts/%s' % oid)
        res = self.api_put(uri, data={'serviceinst': data})
        self.logger.debug('Update service instance %s' % oid)
        return res

    def check(self, oid):
        """check service instance

        :param oid: id of the service instance
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('serviceinsts/%s/check' % oid)
        self.api_get(uri, data={'serviceinst': {}})
        self.logger.debug('patch service instance %s' % oid)

    def patch(self, oid):
        """Patch service instance

        :param oid: id of the service instance
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('serviceinsts/%s' % oid)
        self.api_patch(uri, data={'serviceinst': {}})
        self.logger.debug('patch service instance %s' % oid)

    def delete(self, oid, propagate=False, force=False):
        """Delete service instance

        :param oid: id of the service instance     
        :param propagate: if True propagate delete to all cmp modules [default=False]
        :param force: if True force delete [default=False]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('serviceinsts/%s' % oid, version='v2.0')
        data = {'propagate': propagate, 'force': force}
        self.api_delete(uri, data=data)
        self.logger.debug('delete service instance %s' % oid)

    def set_status(self, oid, status):
        """Set service instance status

        :param oid: id of the service instance
        :param status: service instance status
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('serviceinsts/%s/status' % oid)
        self.api_put(uri, data={'serviceinst': {'status': status.upper()}})
        self.logger.debug('set service instance %s status' % oid)

    def add_tag(self, oid, tags):
        """Add tags to service instance

        :param oid: id of the service instance
        :param tags: list of tags
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('serviceinsts/%s' % oid)
        self.api_put(uri, data={'serviceinst': {'tags': {'cmd': 'add', 'values': tags}}})
        self.logger.debug('add tags %s to service instance %s' % (tags, oid))

    def del_tag(self, oid, tags):
        """Delete tags from service instance

        :param oid: id of the service instance
        :param tags: list of tags
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('serviceinsts/%s' % oid)
        self.api_put(uri, data={'serviceinst': {'tags': {'cmd': 'delete', 'values': tags}}})
        self.logger.debug('delet tags %s from service instance %s' % (tags, oid))

    def set_config(self, oid, key, value=None):
        """Update service instance config

        :param oid: id of the service instance
        :param key: config key like config.key
        :param value: config value
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('serviceinsts/%s/config' % oid)
        self.api_put(uri, data={'config': {'key': key, 'value': value}})
        self.logger.debug('update service entity %s config' % oid)
