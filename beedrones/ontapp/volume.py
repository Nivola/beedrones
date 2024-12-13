# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from netapp_ontap.resources import Volume, Snapshot
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapVolume(OntapEntity):
    """OntapVolume"""

    @make_request
    def list(self, **kwargs):
        """list volumes

        :param kwargs:
        :return:
        """
        resp = []
        kwargs["is_svm_root"] = False
        fields = "state,type,create_time,space,nas,svm,snapmirror.is_protected"
        # fields = 'uuid'
        res = Volume.get_collection(connection=self.client, max_records=20, fields=fields, **kwargs)
        for volume in res:
            # volume.get()
            resp.append(volume.to_dict())
        self.logger.debug("list volumes: %s" % truncate(resp))
        return resp

    @make_request
    def get(self, volume_id):
        """get volume

        :param volume_id: volume uuid
        :return:
        """
        fields = (
            "svm,state,size,type,create_time,space,nas,quota,qos,statistics,snapmirror,style,aggregates,"
            "encryption,files,metric,qos,snaplock"
        )
        # fields = None
        kwargs = {}
        volume = Volume(uuid=volume_id)
        volume.set_connection(self.client)
        volume.get(fields=fields, **kwargs)
        resp = volume.to_dict()
        self.logger.debug("get volume: %s" % truncate(resp))
        return resp

    @make_request
    def get_snapshots(self, volume_id):
        """get volume snapshots

        :param volume_id: volume uuid
        :return:
        """
        resp = []
        fields = "uuid,name,create_time,expiry_time,state"
        kwargs = {}
        res = Snapshot.get_collection(volume_id, connection=self.client, max_records=20, fields=fields, **kwargs)
        for item in res:
            resp.append(item.to_dict())
        self.logger.debug("get volume %s snapshots: %s" % (volume_id, truncate(resp)))
        return resp
