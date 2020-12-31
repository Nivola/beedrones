# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

import ujson as json
from six.moves.urllib.parse import urlencode
from beecell.simple import truncate
from beedrones.openstack.client import OpenstackClient, OpenstackObject, setup_client


class OpenstackFlavorObject(OpenstackObject):
    def setup(self):
        self.uri = self.manager.endpoint(u'nova')
        # change version from 2 to 2.1
        # self.uri = self.uri.replace(u'v2/', u'v2.1/')
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)


class OpenstackFlavor(OpenstackFlavorObject):
    """
    """
    def __init__(self, manager):
        OpenstackFlavorObject.__init__(self, manager)

    @setup_client
    def list(self, detail=False, tenant=None):
        """List flavors

        :param tenant: tenant id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors'
        if detail is True:
            path = '/flavors/detail'

        query = {}
        if tenant is not None:
            query['tenant_id'] = tenant
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
            u'flavor': {
                u'name': name,
                u'ram': ram,
                u'vcpus': vcpu,
                u'disk': disk
            }
        }
        # if desc is not None:
        #     data[u'flavor'][u'description'] = desc

        path = u'/flavors'
        res = self.client.call(path, u'POST', data=json.dumps(data), token=self.manager.identity.token)
        self.logger.debug(u'Create openstack flavor: %s' % truncate(res[0]))
        return res[0][u'flavor']

    @setup_client
    def update(self, oid):
        """TODO
        :param oid: flavor id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s' % oid
        res = self.client.call(path, 'PUT', data='', token=self.manager.identity.token)
        self.logger.debug('Update openstack flavor: %s' % truncate(res[0]))
        return res[0]['flavor']

    @setup_client
    def delete(self, oid):
        """TODO
        :param oid: flavor id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s' % oid
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack flavor: %s' % truncate(res[0]))
        return True

    #
    # actions
    #