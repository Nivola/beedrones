# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

from beecell.simple import truncate
from beedrones.openstack.client import OpenstackClient, OpenstackObject


class OpenstackAodhObject(OpenstackObject):
    def setup(self):
        self.uri = self.manager.endpoint(u'aodh')
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)


class OpenstackAodh(OpenstackAodhObject):
    """Openstack aodh client
    """
    def __init__(self, manager):
        OpenstackAodhObject.__init__(self, manager)

    def api(self):
        """Get aodh api versions.

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        redux_uri = self.uri.split('/')[0] + "//" + self.uri.split('/')[2]
        client = OpenstackClient(redux_uri, self.manager.proxy)
        path = '/'
        self.logger.debug('Path to check: %s%s' % (client.path, path))
        res = client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack aodh api: %s' % truncate(res[0]))
        return res[0][u'versions']

