# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from netapp_ontap.resources import SnapmirrorRelationship
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapSnapMirror(OntapEntity):
    """OntapSnapMirror"""

    @make_request
    def list(self, **kwargs):
        """list snapmirrors

        :param kwargs:
        :return:
        """
        resp = []
        filter = False
        base_fields = "uuid,policy.type,destination.path,destination.cluster.name,source.path"

        # no filter
        if len(list(kwargs.keys())) == 0:
            fields = base_fields
        else:
            filter = True
            fields = "uuid"

        kwargs["list_destinations_only"] = True
        res = SnapmirrorRelationship.get_collection(connection=self.client, max_records=100, fields=fields, **kwargs)
        for snapmirror in res:
            if filter:
                snapmirror.get(list_destinations_only=True)
            resp.append(snapmirror.to_dict())

        self.logger.debug("list snapmirrors: %s" % truncate(resp))
        return resp

    @make_request
    def get(self, snapmirror_id):
        """get snapmirror

        :param snapmirror: snapmirror uuid
        :return:
        """
        kwargs = {"list_destinations_only": True}
        fields = "uuid,policy,destination,source,state,restore,healthy"
        snapmirror = SnapmirrorRelationship(uuid=snapmirror_id)
        snapmirror.set_connection(self.client)
        snapmirror.get(fields=fields, **kwargs)
        resp = snapmirror.to_dict()
        self.logger.debug("get snapmirror: %s" % truncate(resp))
        return resp
