# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2026 CSI-Piemonte

from typing import Dict
from netapp_ontap.resources.cifs_share import CifsShare
from netapp_ontap.resources.export_policy import ExportPolicy
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapProtocol(OntapEntity):
    """OntapProtocol"""

    resclass = CifsShare

    def get_nfs_export_policy(self, policy_id) -> Dict:
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
        fields = "svm.uuid,svm.name,volume.uuid,volume.name,name,path"
        return self.list_entities(OntapProtocol.resclass, fields, **kwargs)

    def get_cifs_share(self, svm_uuid, share_name):
        """get cifs share

        :param svm_uuid: svm uuid
        :param share_name: share name
        :return:
        """

        fields = ("name,path,comment,svm.name,svm.uuid,volume.name,volume.uuid,"
                  "acls.permission,acls.user_or_group,acls.type,encryption")
        kwargs = {}
        share = CifsShare(svm={"uuid": svm_uuid}, name=share_name)
        share.set_connection(self.client)
        share.get(fields=fields, **kwargs)
        resp = share.to_dict()
        self.logger.debug("get cifs share: %s" % truncate(resp))
        return resp
