# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from netapp_ontap.resources import Svm, SvmPeer
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapSvm(OntapEntity):
    """OntapSvm"""

    @make_request
    def list(self, **kwargs):
        """list svms

        :param kwargs:
        :return:
        """
        resp = []
        fields = "state,nfs,cifs,ip_interfaces"
        res = Svm.get_collection(connection=self.client, max_records=20, fields=fields, **kwargs)
        for svm in res:
            svm.get()
            resp.append(svm.to_dict())
        self.logger.debug("list svms: %s" % truncate(resp))
        return resp

    @make_request
    def get(self, svm):
        """get svm

        :param svm: svm uuid
        :return:
        """
        # fields = 'state,ip_interfaces,nfs,cifs'
        fields = ""
        kwargs = {}
        svm = Svm(uuid=svm)
        svm.set_connection(self.client)
        svm.get(fields=fields, **kwargs)
        resp = svm.to_dict()
        self.logger.debug("get svm: %s" % truncate(resp))
        return resp

    @make_request
    def list_peers(self, **kwargs):
        """list svm peers

        :param kwargs:
        :return:
        """
        resp = []
        res = SvmPeer.get_collection(connection=self.client, max_records=20, **kwargs)
        for svm in res:
            svm.get()
            resp.append(svm.to_dict())
        self.logger.debug("list svm peers: %s" % truncate(resp))
        return resp

    @make_request
    def get_peer(self, svm):
        """get svm peer

        :param svm: svm uuid
        :return:
        """
        # fields = 'state,ip_interfaces,nfs,cifs'
        kwargs = {}
        svm = SvmPeer(uuid=svm)
        svm.set_connection(self.client)
        svm.get(**kwargs)
        resp = svm.to_dict()
        self.logger.debug("get svm peer: %s" % truncate(resp))
        return resp
