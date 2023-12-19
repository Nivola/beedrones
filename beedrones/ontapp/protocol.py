# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from netapp_ontap.resources import ExportPolicy, CifsShare
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapProtocol(OntapEntity):
    """OntapProtocol"""

    def get_nfs_export_policy(self, policy_id):
        """get nfs export policy

        :param policy_id: policy uuid
        :return:
        """
        fields = "id,name,rules"
        kwargs = {}
        policy = ExportPolicy(id=policy_id)
        policy.set_connection(self.client)
        policy.get(fields=fields, **kwargs)
        resp = policy.to_dict()
        self.logger.debug("get export policy: %s" % truncate(resp))
        return resp

    def list_cifs_shares(self, **kwargs):
        """list cifs shares

        :param kwargs:
        :return:
        """
        resp = []
        fields = ""
        res = CifsShare.get_collection(connection=self.client, max_records=20, fields=fields, **kwargs)
        for share in res:
            share.get()
            resp.append(share.to_dict())
        self.logger.debug("list cifs shares: %s" % truncate(resp))
        return resp

    def get_cifs_share(self, svm_id, share_name):
        """get cifs share

        :param policy_id: policy uuid
        :return:
        """
        fields = "id,name,rules"
        kwargs = {}
        share = CifsShare(svm_id, share_name)
        share.set_connection(self.client)
        share.get(fields=fields, **kwargs)
        resp = share.to_dict()
        self.logger.debug("get cifs share: %s" % truncate(resp))
        return resp
