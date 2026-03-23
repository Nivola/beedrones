# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2026 CSI-Piemonte

from typing import List, Dict
from beedrones.ontapp.client import OntapEntity, make_request
from netapp_ontap.resources import SnapshotPolicy
from beecell.types.type_string import truncate


class OntapSnapshotPolicy(OntapEntity):
    """OntapSnapshotPolicy"""

    @make_request
    def list(self, **kwargs: Dict) -> List[Dict]:
        """list snapshot policies

        :param kwargs:
        :return: list of snapshot policy items
        """
        resp = []
        res = SnapshotPolicy.get_collection(connection=self.client, **kwargs)
        for item in res:
            snapshot_policy = item.to_dict()
            # filter policy by name
            if "staas_snap_" in snapshot_policy.get("name"):
                resp.append(snapshot_policy)
        self.logger.debug("list snapshot policies: %s" % truncate(resp))
        return resp

    @make_request
    def get(self, snapshot_policy_id):
        """get snapshot policy

        :param snapshot_policy_id: snapshot policy id
        :return:
        """
        fields=""
        kwargs = {}
        snapshot_policy = SnapshotPolicy(uuid=snapshot_policy_id)
        snapshot_policy.set_connection(self.client)
        snapshot_policy.get(fields=fields, **kwargs)
        resp = snapshot_policy.to_dict()
        self.logger.debug("get snapshot policy: %s" % truncate(resp))
        return resp