# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import jsonDumps

import ujson as json
from six.moves.urllib.parse import urlencode
from beecell.simple import truncate
from beedrones.openstack.client import OpenstackClient, OpenstackObject, setup_client


class OpenstackFlavorObject(OpenstackObject):
    def setup(self):
        self.uri = self.manager.endpoint('nova')
        # change version from 2 to 2.1
        # self.uri = self.uri.replace('v2/', 'v2.1/')
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)


class OpenstackFlavor(OpenstackFlavorObject):
    """
    """
    def __init__(self, manager):
        OpenstackFlavorObject.__init__(self, manager)

    @setup_client
    def list(self, detail=False, tenant=None, limit=1000, marker=None):
        """List flavors

        :param tenant: tenant id
        :param limit: Requests a page size of items. Returns a number of items up to a limit value. Use the limit
            parameter to make an initial limited request and use the ID of the last-seen item from the response as the
            marker parameter value in a subsequent limited request.
        :param marker: The ID of the last-seen item. Use the limit parameter to make an initial limited request and use
            the ID of the last-seen item from the response as the marker parameter value in a subsequent limited
            request.
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors'
        if detail is True:
            path = '/flavors/detail'

        query = {'limit': limit}
        if tenant is not None:
            query['tenant_id'] = tenant
        if marker is not None:
            query['marker'] = marker
        path = '%s?%s' % (path, urlencode(query))

        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        resp = res[0]['flavors']
        self.logger.debug('Get openstack flavors: %s' % truncate(resp))
        return resp

    @setup_client
    def get(self, oid):
        """Get flavor

        :param oid: flavor id
        :param name: flavor name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack flavor: %s' % truncate(res[0]))
        if oid is not None:
            flavor = res[0]['flavor']

        return flavor

    @setup_client
    def create(self, name, vcpu, ram, disk, desc=None):
        """Create new openstack flavor

        :param name:
        :param vcpu:
        :param ram:
        :param disk:
        :param desc:
        :return:
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            'flavor': {
                'name': name,
                'ram': ram,
                'vcpus': vcpu,
                'disk': disk
            }
        }
        # if desc is not None:
        #     data['flavor']['description'] = desc

        path = '/flavors'
        res = self.client.call(path, 'POST', data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug('Create openstack flavor: %s' % truncate(res[0]))
        return res[0]['flavor']

    @setup_client
    def update(self, oid):
        """Update flavor

        :param oid: flavor id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s' % oid
        res = self.client.call(path, 'PUT', data='', token=self.manager.identity.token)
        self.logger.debug('Update openstack flavor: %s' % truncate(res[0]))
        return res[0]['flavor']

    @setup_client
    def delete(self, oid):
        """Delete flavor

        :param oid: flavor id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s' % oid
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack flavor: %s' % truncate(res[0]))
        return True

    #
    # extra specs
    #
    @setup_client
    def extra_spec_list(self, oid):
        """List Extra Specs For A Flavor

        :param oid: flavor id
        :return: flavor extra specs
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s/os-extra_specs' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        resp = res[0]['extra_specs']
        self.logger.debug('Get openstack flavor extra specs: %s' % truncate(resp))
        return resp

    @setup_client
    def extra_spec_get(self, oid, spec_id):
        """Show An Extra Spec For A Flavor

        :param oid: flavor id
        :param spec_id: extra spec key
        :return: flavor extra spec
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s/os-extra_specs/%s' % (oid, spec_id)
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack flavor extra spec: %s' % truncate(res[0]))
        resp = res[0]['extra_spec']
        return resp

    @setup_client
    def extra_spec_create(self, oid, extra_specs):
        """Create Extra Specs For A Flavor

        :param oid: flavor id
        :param extra_specs: extra specs dictionary
        :return: flavor extra spec
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = extra_specs
        path = '/flavors/%s/os-extra_specs' % oid
        res = self.client.call(path, 'POST', data={'extra_specs': data}, token=self.manager.identity.token)
        self.logger.debug('Create openstack flavor extra spec: %s' % truncate(res[0]))
        return res[0]['extra_specs']

    @setup_client
    def extra_spec_update(self, oid, spec_id, spec_value):
        """Update An Extra Spec For A Flavor

        :param oid: flavor id
        :param spec_id: extra spec key
        :param spec_value: new extra spec value
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s/os-extra_specs/%s' % (oid, spec_id)
        data = {spec_id: spec_value}
        res = self.client.call(path, 'PUT', data=data, token=self.manager.identity.token)
        self.logger.debug('Update openstack flavor extra spec: %s' % truncate(res[0]))
        return True

    @setup_client
    def extra_spec_delete(self, oid, spec_id):
        """Delete An Extra Spec For A Flavor

        :param oid: flavor id
        :param spec_id: extra spec key
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s/os-extra_specs/%s' % (oid, spec_id)
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack flavor extra spec: %s' % truncate(res[0]))
        return True
