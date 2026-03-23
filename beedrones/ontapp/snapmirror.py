# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2026 CSI-Piemonte

from typing import List
from netapp_ontap.resources import SnapmirrorRelationship, Cluster #, SnapmirrorPolicy
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapSnapMirror(OntapEntity):
    """
    OntapSnapMirror

    list is used to list snapmirror relationships whose source is on the current container
    get is used to get details about snapmirror relationship on the destination container only
    """

    @make_request
    def list(self, search_remote=True, search_local=False, **kwargs):
        """list snapmirrors

        :param kwargs:
        :return:
        """
        # fields = "**" -> request all available fields
        # filter by source: e.g. kwargs["source.path"] = "svmp2-cmpstaas-test:svmp2_cmpstaas_test_TODEL_ALE_19_C_72b9dc"

        # get current cluster name
        if search_local:
            current_cluster = Cluster()
            current_cluster.set_connection(self.client)
            current_cluster.get(fields="name")
            current_cluster_name = current_cluster.name

        # there is no way to determine which relationships are on which cluster,
        # based on the source path or source svm.
        # either search twice, once for either case, or specify which case with the
        # given search_remote and search_local flags.

        resp = []
        fields = "uuid,policy.type,policy.name,destination.path,destination.cluster.name,source.path"
        if search_remote:
            # first time assume relationships are on destination cluster:
            # - search on source cluster for relationships that are actually defined on other destination clusters
            kwargs["list_destinations_only"] = True
            # TODO adapt res = self.list_entities(OntapSnapMirror.resclass, fields, **kwargs)
            res: List[SnapmirrorRelationship] = SnapmirrorRelationship.get_collection(connection=self.client, max_records=100, fields=fields, **kwargs)
            for snapmirror in res:
                snapmirror.get(list_destinations_only=True)
                snapmirror_dict = snapmirror.to_dict()
                snapmirror_dict["local_remote"] = "remote"
                resp.append(snapmirror_dict)

        if search_local:
            fields = f"{fields},state,healthy" # extend with additional properties
            # second time assume relationships are on current cluster
            # - search on destination cluster for relationships that are defined on this cluster.
            # - this works if this cluster is a destination cluster of some snapmirror relationships
            kwargs.pop("list_destinations_only", None)
            res: List[SnapmirrorRelationship] = SnapmirrorRelationship.get_collection(connection=self.client, max_records=100, fields=fields, **kwargs)
            for snapmirror in res:
                #SnapmirrorRelationship.find(connection=self.client, uuid=snapmirror.uuid)
                #snapmirror.get()
                snapmirror_dict = snapmirror.to_dict()
                # destination cluster is not set if it's the current cluster. set it manually
                snapmirror_dict["destination"]["cluster"]= {
                    "name": current_cluster_name
                }
                snapmirror_dict["local_remote"] = "local"
                resp.append(snapmirror_dict)

        self.logger.debug("list snapmirrors: %s", truncate(resp))
        return resp

    @make_request
    def get(self, relationship_id, get_policy_detail=False):
        """get snapmirror
        NB: works on destination only
        :param relationship_id: snapmirror relationship uuid
        :param get_policy_detail:
        :return:
        """
        fields = "uuid,policy,destination,source,state,restore,healthy"
        snapmirror = SnapmirrorRelationship(uuid=relationship_id)
        snapmirror.set_connection(self.client)
        snapmirror.get(fields=fields)
        resp = snapmirror.to_dict()
        if get_policy_detail:
            # add detail
            resp["policy"] = self.policy_get(snapmirror.policy.uuid)

        self.logger.debug("get snapmirror: %s", truncate(resp))
        return resp

    @make_request
    def delete(self, relationship_id):
        # TODO handle all cases
        relationship = SnapmirrorRelationship(uuid=relationship_id)
        relationship.set_connection(self.client)
        resp = relationship.delete() # deletes both from source and from destination
        try:
            self.handle_response(resp)
        except Exception as ex:
            error_message = f"Relationship {relationship_id} deletion failed: {ex}"
            self.logger.debug(error_message, exc_info=True)
            raise Exception(error_message) from ex

        self.logger.debug("Relationship %s deleted successfully", relationship_id)
        return

    @make_request
    def policy_get(self, policy_id):
        from .snapmirror_policy import OntapSnapmirrorPolicy
        snapmirror_policy = OntapSnapmirrorPolicy(self.manager)
        return snapmirror_policy.get(policy_id)
