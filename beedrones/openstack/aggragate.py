# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import jsonDumps

import ujson as json
from six.moves.urllib.parse import urlencode
from beecell.simple import truncate
from beedrones.openstack.client import OpenstackClient, OpenstackObject, setup_client


class OpenstackAggregateObject(OpenstackObject):
    def setup(self):
        self.uri = self.manager.endpoint("nova")
        # change version from 2 to 2.1
        # self.uri = self.uri.replace('v2/', 'v2.1/')
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)


class OpenstackAggregate(OpenstackAggregateObject):
    """ """

    def __init__(self, manager):
        OpenstackAggregateObject.__init__(self, manager)

    @setup_client
    def list(self):
        """List aggregates

        :return: aggragate list
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/os-aggregates"
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        resp = res[0]["aggregates"]
        self.logger.debug("Get openstack aggregates: %s" % truncate(resp))
        return resp

    @setup_client
    def get(self, oid):
        """Get aggregate

        :param oid: aggregate id
        :param name: aggregate name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/os-aggregates/%s" % oid
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack aggregate: %s" % truncate(res[0]))
        if oid is not None:
            aggregate = res[0]["aggregate"]

        return aggregate

    @setup_client
    def create(self, name, availability_zone):
        """Create new openstack aggregate

        :param name: the name of the host aggregate.
        :param availability_zone: he availability zone of the host aggregate. You should use a custom availability zone
            rather than the default returned by the os-availability-zone API. The availability zone must not include
            ':' in its name.
        :return: aggregate
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "aggregate": {
                "name": name,
                "availability_zone": availability_zone,
            }
        }
        path = "/os-aggregates"
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Create openstack aggregate: %s" % truncate(res[0]))
        return res[0]["aggregate"]

    @setup_client
    def update(self, oid, name=None, availability_zone=None):
        """Updates either or both the name and availability zone for an aggregate

        :param oid: aggregate id
        :param name: the name of the host aggregate.
        :param availability_zone: he availability zone of the host aggregate.
        :return: aggregate
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/os-aggregates/%s" % oid
        data = {}
        if name is not None:
            data["name"] = name
        if availability_zone is not None:
            data["availability_zone"] = availability_zone
        res = self.client.call(path, "PUT", data={"aggregate": data}, token=self.manager.identity.token)
        self.logger.debug("Update openstack aggregate: %s" % truncate(res[0]))
        return res[0]["aggregate"]

    @setup_client
    def delete(self, oid):
        """Deletes an aggregate

        :param oid: aggregate id
        :return: aggregate
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/os-aggregates/%s" % oid
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack aggregate: %s" % truncate(res[0]))
        return True

    @setup_client
    def add_host(self, oid, host_id):
        """Adds a host to an aggregate

        :param oid: aggregate id
        :param host_id: host id
        :param availability_zone: he availability zone of the host aggregate.
        :return: aggregate
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/os-aggregates/%s/action" % oid
        data = {"add_host": {"host": host_id}}
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Adds a host to an openstack aggregate: %s" % truncate(res[0]))
        return res[0]["aggregate"]

    @setup_client
    def del_host(self, oid, host_id):
        """Adds a host to an aggregate

        :param oid: aggregate id
        :param host_id: host id
        :param availability_zone: he availability zone of the host aggregate.
        :return: aggregate
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/os-aggregates/%s/action" % oid
        data = {"remove_host": {"host": host_id}}
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Remove an host from an openstack aggregate: %s" % truncate(res[0]))
        return res[0]["aggregate"]

    @setup_client
    def update_metatdata(self, oid, metadata):
        """Creates or replaces metadata for an aggregate

        :param metadata: dict like {'key1': 'value1'}
        :return: aggregate
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"set_metadata": {"metadata": metadata}}
        path = "/os-aggregates/%s/action" % oid
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Creates or replaces metadata for an penstack aggregate: %s" % truncate(res[0]))
        return res[0]["aggregate"]

    def pre_cache_image(self, oid, host_id):
        """Requests that a set of images be pre-cached on compute nodes within the referenced aggregate"""
        pass
