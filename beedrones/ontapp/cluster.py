# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from netapp_ontap.resources import Cluster, ClusterPeer
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapCluster(OntapEntity):
    """OntapCluster
    """
    @make_request
    def get(self):
        """get cluster info

        :return:
        """
        # Create new cluster object
        clus = Cluster()
        clus.set_connection(self.client)
        # Issue REST API call
        clus.get()
        resp = clus.to_dict()
        self.logger.debug('get cluster info: %s' % truncate(resp))
        return resp

    @make_request
    def list_peers(self, **kwargs):
        """get cluster peers

        :return:
        """
        resp = []
        # fields = 'uuid'
        res = ClusterPeer.get_collection(connection=self.client, max_records=100, **kwargs)
        for item in res:
            # snapmirror.get()
            resp.append(item.to_dict())
        self.logger.debug('list cluster peers: %s' % truncate(resp))
        return resp
