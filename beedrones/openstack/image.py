# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

import ujson as json
from beecell.simple import truncate
from six.moves.urllib.parse import urlencode
from beedrones.openstack.client import OpenstackClient, OpenstackError, OpenstackObject, setup_client


class OpenstackImageObject(OpenstackObject):
    def setup(self):
        self.uri = self.manager.endpoint('nova')
        # change version from 2 to 2.1
        # self.uri = self.uri.replace('v2/', 'v2.1/')
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)


class OpenstackImage(OpenstackImageObject):
    """
    """
    def __init__(self, manager):
        OpenstackImageObject.__init__(self, manager)

    @setup_client
    def list(self, detail=False, tenant=None, status=None, mindisk=None, minram=None, itype=None, limit=None,
             marker=None):
        """
        :param tenant: tenant id
        :param status: Filters the response by an image status, as a string.
                       For example, ACTIVE.
        :param mindisk: Filters the response by a minimum disk size.
                        For example, 100.
        :param minram: Filters the response by a minimum RAM size.
                       For example, 512.
        :param itype: Filters the response by an image type. For example,
                      snapshot or backup.
        :param limit:  Requests a page size of items. Returns a number of items
                       up to a limit value. Use the limit parameter to make an
                       initial limited request and use the ID of the last-seen
                       item from the response as the marker parameter value in
                       a subsequent limited request.
        :param marker: The ID of the last-seen item. Use the limit parameter
                       to make an initial limited request and use the ID of the
                       last-seen item from the response as the marker parameter
                       value in a subsequent limited request.
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/images'
        if detail is True:
            path = '/images/detail'

        query = {}
        if tenant is not None:
            query['tenant_id'] = tenant
        if status is not None:
            query['status'] = status
        if mindisk is not None:
            query['mindisk'] = mindisk
        if minram is not None:
            query['minram'] = minram
        if itype is not None:
            query['itype'] = itype
        if limit is not None:
            query['limit'] = limit
        if marker is not None:
            query['marker'] = marker
        path = '%s?%s' % (path, urlencode(query))

        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack images: %s' % truncate(res[0]))
        return res[0]['images']

    @setup_client
    def get(self, oid=None, name=None):
        """
        :param oid: image id
        :param name: image name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = '/images/%s' % oid
        elif name is not None:
            path = '/images/detail?name=%s' % name
        else:
            raise OpenstackError('Specify at least project id or name')
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack image: %s' % truncate(res[0]))
        if oid is not None:
            image = res[0]['image']
        elif name is not None:
            image = res[0]['images'][0]

        return image

    @setup_client
    def create(self, tenant, name, image, flavor, security_groups=["default"], networks=[]):
        """Create new openstack image

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
        }

        path = '/images'
        res = self.client.call(path, 'POST', data=json.dumps(data), token=self.manager.identity.token)
        self.logger.debug('Create openstack image: %s' % truncate(res[0]))
        return res[0]['image']

    @setup_client
    def update(self, oid):
        """TODO
        :param oid: image id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/images/%s' % oid
        res = self.client.call(path, 'PUT', data='', token=self.manager.identity.token)
        self.logger.debug('Update openstack image: %s' % truncate(res[0]))
        return res[0]['image']

    @setup_client
    def delete(self, oid):
        """TODO
        :param oid: image id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/images/%s' % oid
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack image: %s' % truncate(res[0]))
        return res[0]['image']

    #
    # actions
    #
    @setup_client
    def get_metadata(self, image_id, key=None):
        """Shows metadata for an image.

        :param image_id: The UUID of the image.
        :return: list of metadata
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/images/%s/metadata' % image_id
        if key is not None:
            path += '/' + key

        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack image metadata: %s' % truncate(res[0]))
        return res[0]['metadata']
