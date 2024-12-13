# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import truncate
from beedrones.openstack.client import OpenstackClient, OpenstackObject, setup_client


class OpenstackGlanceObject(OpenstackObject):
    def setup(self):
        self.uri = self.manager.endpoint("glance")
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)


class OpenstackGlance(OpenstackGlanceObject):
    """Openstack glance client"""

    def __init__(self, manager):
        OpenstackGlanceObject.__init__(self, manager)

    @setup_client
    def api(self):
        """Get glance api versions.

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        redux_uri = self.uri.split("/")[0] + "//" + self.uri.split("/")[2]
        client = OpenstackClient(redux_uri, self.manager.proxy)
        path = "/"
        self.logger.debug("Path to check: %s%s" % (client.path, path))
        res = client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack glance api: %s" % truncate(res[0]))
        return res[0]["versions"]
