# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2026 CSI-Piemonte

from typing import List, Dict
from netapp_ontap.resources import SnapmirrorPolicy
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request

class OntapSnapmirrorPolicy(OntapEntity):
    """OntapSnapmirrorPolicy"""

    DR_POLICY_PREFIX = "staas_mirror_"
    SNAPLOCK_POLICY_PREFIX = "staas_vault_"

    @make_request
    def list(self, **kwargs: Dict) -> List[Dict]:
        """list snapmirror policies

        :param kwargs:
        :return: list of snapmirror policy items
        """
        show_all = kwargs.pop("show_all", False)
        resp = []
        res = SnapmirrorPolicy.get_collection(connection=self.client, **kwargs)
        for item in res:
            snapmirror_policy = item.to_dict()
            # filter policy by name
            policy_name: str = snapmirror_policy.get("name","")
            if policy_name.startswith(OntapSnapmirrorPolicy.DR_POLICY_PREFIX):
                snapmirror_policy["cmp_policy_type"] = "DR"
                resp.append(snapmirror_policy)
            elif policy_name.startswith(OntapSnapmirrorPolicy.SNAPLOCK_POLICY_PREFIX):
                snapmirror_policy["cmp_policy_type"] = "SNAPLOCK"
                resp.append(snapmirror_policy)
            else:
                snapmirror_policy["cmp_policy_type"] = "-> INVALID FOR CMP <-"
                if show_all:
                    resp.append(snapmirror_policy)
        self.logger.debug("list snapmirror policies: %s", truncate(resp))
        return resp

    @make_request
    def get(self, snapmirror_policy_id):
        """get snapmirror policy

        :param snapmirror_policy_id: snapmirror policy id
        :return:
        """
        fields=""
        kwargs = {}
        snapmirror_policy = SnapmirrorPolicy(uuid=snapmirror_policy_id)
        snapmirror_policy.set_connection(self.client)
        snapmirror_policy.get(fields=fields, **kwargs)
        resp = snapmirror_policy.to_dict()
        self.logger.debug("get snapmirror policy: %s" % truncate(resp))
        return resp
