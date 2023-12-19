# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import jsonDumps

import ujson as json
from beecell.simple import truncate
from six.moves.urllib.parse import urlencode
from beedrones.openstack.client import (
    OpenstackClient,
    OpenstackError,
    OpenstackObject,
    setup_client,
)


class OpenstackImageObject(OpenstackObject):
    def setup(self):
        self.uri = self.manager.endpoint("glance")
        self.ver = "/v2"
        self.uri = "%s%s" % (self.uri, self.ver)
        # change version from 2 to 2.1
        # self.uri = self.uri.replace('v2/', 'v2.1/')
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)


class OpenstackImage(OpenstackImageObject):
    """Openstack image manager.

    The possible status values for images are presented in the following table:
        queued - The Image service reserved an image ID for the image in the catalog but did not yet upload any image
                 data.
        saving - The Image service is in the process of saving the raw data for the image into the backing store.
        active - The image is active and ready for consumption in the Image service.
        killed - An image data upload error occurred.
        deleted - The Image service retains information about the image but the image is no longer available for use.
        pending_delete - Similar to the deleted status. An image in this state is not recoverable.
        deactivated - The image data is not available for use.
        uploading - Data has been staged as part of the interoperable image import process. It is not yet available for
                    use. (Since Image API 2.6)
        importing - The image data is being processed as part of the interoperable image import process, but is not yet
                    available for use. (Since Image API 2.6)
    """

    def __init__(self, manager):
        OpenstackImageObject.__init__(self, manager)

    @setup_client
    def list(self, *args, **kwargs):
        """List images

        :param limit: Requests a page size of items. Returns a number of items up to a limit value. Use the limit
            parameter to make an initial limited request and use the ID of the last-seen item from the response as the
            marker parameter value in a subsequent limited request.
        :param marker: The ID of the last-seen item. Use the limit parameter to make an initial limited request and use
            the ID of the last-seen item from the response as the marker parameter value in a subsequent limited
            request.
        :param name: Filters the response by a name, as a string. A valid value is the name of an image.
        :param owner: Filters the response by a project (also called a “tenant”) ID. Shows only images that are shared
            with you by the specified owner.
        :param protected: Filters the response by the ‘protected' image property. A valid value is one of ‘true',
            ‘false' (must be all lowercase). Any other value will result in a 400 response.
        :param status: Filters the response by an image status.
        :param tag: Filters the response by the specified tag value. May be repeated, but keep in mind that you're
            making a conjunctive query, so only images containing all the tags specified will appear in the response.
        :param visibility: Filters the response by an image visibility value. A valid value is public, private,
            community, shared, or all. (Note that if you filter on shared, the images included in the response will
            only be those where your member status is accepted unless you explicitly include a member_status filter
            in the request.) If you omit this parameter, the response shows public, private, and those shared images
            with a member status of accepted.
        :param os_hidden: When true, filters the response to display only “hidden” images. By default, “hidden” images
            are not included in the image-list response. (Since Image API v2.7)
        :param member_status: Filters the response by a member status. A valid value is accepted, pending, rejected,
            or all. Default is accepted.
        :param size_max: Filters the response by a maximum image size, in bytes.
        :param size_min: Filters the response by a minimum image size, in bytes.
        :param created_at: Specify a comparison filter based on the date and time when the resource was created. The
            date and time stamp format is ISO 8601: CCYY-MM-DDThh:mm:ss±hh:mm
        :param updated_at: Specify a comparison filter based on the date and time when the resource was most recently
            modified. The date and time stamp format is ISO 8601: CCYY-MM-DDThh:mm:ss±hh:mm
        :param sort_dir: Sorts the response by a set of one or more sort direction and attribute (sort_key)
            combinations. A valid value for the sort direction is asc (ascending) or desc (descending). If you omit the
            sort direction in a set, the default is desc.
        :param sort_key: Sorts the response by an attribute, such as name, id, or updated_at. Default is created_at.
            The API uses the natural sorting direction of the sort_key image attribute.
        :param sort: Sorts the response by one or more attribute and sort direction combinations. You can also set
            multiple sort keys and directions. Default direction is desc. Use the comma (,) character to separate
            multiple values.
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/images"
        query = kwargs
        limit = kwargs.get("limit", 500)
        kwargs["limit"] = limit
        path = "%s?%s" % (path, urlencode(query))

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack images: %s" % truncate(res[0]))
        return res[0]["images"]

    @setup_client
    def get(self, oid=None, name=None, owner=None, visibility="public"):
        """Get image

        :param oid: image id
        :param name: image name
        :param owner: limit image of the owner.
        :param visibility: Visibility of images: public, private, community, shared, or all.
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = "/images/%s" % oid
        elif name is not None:
            path = "/images?name=%s" % name
        else:
            raise OpenstackError("Specify at least project id or name")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack image: %s" % truncate(res[0]))
        if oid is not None:
            image = res[0]
        elif name is not None:
            image = res[0]["images"][0]

        return image

    @setup_client
    def create(
        self,
        name,
        disk_format="qcow2",
        min_disk=None,
        min_ram=None,
        container_format="ami",
        visibility="public",
    ):
        """Create new openstack image

        :param name: image name
        :param disk_format: The format of the disk. Values may vary based on the configuration available in a
            particular OpenStack cloud. See the Image Schema response from the cloud itself for the valid values
            available. Example formats are: ami, ari, aki, vhd, vhdx, vmdk, raw, qcow2, vdi, ploop or iso.
        :param container_format: container format [default=ami]
        :param min_disk: Amount of disk space in GB that is required to boot the image.
        :param min_ram: Amount of RAM in MB that is required to boot the image.
        :param visibility: Visibility of images: public, private, community, shared, or all.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dict
        """
        data = {
            "name": name,
            "container_format": container_format,
            "disk_format": disk_format,
            "visibility": visibility,
        }
        if min_ram is not None:
            data["min_ram"] = min_ram
        if min_disk is not None:
            data["min_disk"] = min_disk
        path = "/images"
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Create openstack image: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def update(self, oid):
        """Update image

        TODO

        :param oid: image id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/images/%s" % oid
        res = self.client.call(path, "PUT", data="", token=self.manager.identity.token)
        self.logger.debug("Update openstack image: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def delete(self, oid):
        """TODO
        :param oid: image id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/images/%s" % oid
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack image: %s" % truncate(res[0]))
        return res[0]

    # #
    # # actions
    # #
    # @setup_client
    # def get_metadata(self, image_id, key=None):
    #     """Shows metadata for an image.
    #
    #     :param image_id: The UUID of the image.
    #     :return: list of metadata
    #     :raises OpenstackError: raise :class:`.OpenstackError`
    #     """
    #     path = '/images/%s/metadata' % image_id
    #     if key is not None:
    #         path += '/' + key
    #
    #     res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
    #     self.logger.debug('Get openstack image metadata: %s' % truncate(res[0]))
    #     return res[0]['metadata']

    #
    # image data
    #
    @setup_client
    def upload(self, image_id, qcow2_data):
        """Uploads binary image data

        :param image_id: image id
        :param qcow2_data: qcow2_data data
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dict
        """
        path = "/images/%s/file" % image_id
        res = self.client.call(
            path,
            "PUT",
            data=qcow2_data,
            token=self.manager.identity.token,
            content_type="application/octet-stream",
            timeout=1200,
        )
        self.logger.debug("upload data to openstack image %s" % image_id)
        return res[0]

    @setup_client
    def download(self, image_id):
        """Download binary image data

        :param image_id: image id
        :param qcow2_data: qcow2_data data
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return: dict
        """
        path = "/images/%s/file" % image_id
        res = self.client.call(
            path,
            "GET",
            token=self.manager.identity.token,
            content_type="application/octet-stream",
            timeout=1200,
        )
        self.logger.debug("download data from openstack image %s" % image_id)
        return res[0]

    #
    # schemas
    #
    @setup_client
    def list_schemas(self, *args, **kwargs):
        """Lists image schemas.

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/schemas/images"
        query = kwargs
        path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack image schemas: %s" % truncate(res[0]))
        return res[0]

    #
    # Sharing: todo
    #

    #
    # tasks
    #
    @setup_client
    def list_tasks(self, *args, **kwargs):
        """Lists tasks.

        :param limit: Requests a page size of items. Returns a number of items up to a limit value. Use the limit
            parameter to make an initial limited request and use the ID of the last-seen item from the response as the
            marker parameter value in a subsequent limited request
        :param marker: The ID of the last-seen item. Use the limit parameter to make an initial limited request and use
            the ID of the last-seen item from the response as the marker parameter value in a subsequent limited
            request.
        :param sort_dir: Sorts the response by a set of one or more sort direction and attribute (sort_key)
            combinations. A valid value for the sort direction is asc (ascending) or desc (descending). If you omit the
            sort direction in a set, the default is desc.
        :param sort_key: Sorts the response by one of the following attributes: created_at, expires_at, status, type,
            updated_at. Default is created_at.
        :param status: Filters the response by a task status. A valid value is pending, processing, success, or failure.
        :param type: Filters the response by a task type. A valid value is import.
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/tasks"
        query = kwargs
        path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack image tasks: %s" % truncate(res[0]))
        return res[0]["tasks"]

    @setup_client
    def get_task(self, oid):
        """Shows details for a task.

        :param oid: image id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/tasks/%s" % oid
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack image task: %s" % truncate(res[0]))
        task = res[0]
        return task
