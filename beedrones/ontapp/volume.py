# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2026 CSI-Piemonte

from netapp_ontap.resources import Volume, Snapshot
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request
from typing import Dict

class OntapVolume(OntapEntity):
    """OntapVolume"""
    resclass = Volume

    @staticmethod
    def is_snaplock(remote_volume: Dict):
        snaplock = remote_volume.get("snaplock")
        if not snaplock or not isinstance(snaplock, dict):
            return False
        snaplock_type = snaplock.get("type")
        if snaplock_type=="compliance":
            return True
        return False

    @make_request
    def list(self, **kwargs):
        """list volumes

        :param kwargs:
        :return:
        """
        kwargs["is_svm_root"] = False
        fields = "state,type,create_time,space,nas,svm,snapmirror.is_protected"
        if kwargs.pop("filter_snaplock",False):
            fields+=',snaplock'
        return self.list_entities(OntapVolume.resclass, fields, **kwargs)

    @make_request
    def get_by_svm_name(self, svm_name: str):
        """get for several volumes in the same svm

        :param svm_name: name of the svm
        :type svm_name: str
        :return: a List of Dict like in get
        :rtype: List[Dict]
        """
        fields = "svm,state,size,type,nas,snapmirror,encryption,snaplock,snapshot_policy"
        params = {
            "svm.name": svm_name
        }
        res = Volume.get_collection(connection=self.client, max_records=20, fields=fields, **params)
        resp = [volume.to_dict() for volume in res]

        self.logger.debug("parallel get volumes: %s", truncate(resp))
        return resp

    @make_request
    def get(self, volume_id, short_info=False):
        """get volume

        :param volume_id: volume uuid
        :return:
        """
        if short_info:
            fields = "svm,state,size,type,nas,snapmirror,encryption,snaplock,snapshot_policy,aggregates"
        else:
            fields = (
                "svm,state,size,type,create_time,space,nas,quota,qos,statistics,snapmirror,style,aggregates,"
                "encryption,files,metric,qos,snaplock,snapshot_policy"
            )
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

    @make_request
    def get_snaplock_info(self, volume_id):
        """
        given a volume uuid, fetch snaplock information.
        if volume is a snaplock volume snaplock type will be "compliance",
        otherwise "non-snaplock"
        """
        volume = Volume(uuid=volume_id)
        volume.set_connection(self.client)
        volume.get(fields="snaplock")
        resp = volume.to_dict()
        self.logger.debug("get snaplock info for volume %s: %s", volume_id, truncate(resp))
        return resp

    @make_request
    def delete(self, volume_id):
        volume = Volume(uuid=volume_id)
        volume.set_connection(self.client)
        resp = volume.delete()
        try:
            self.handle_response(resp)
        except Exception as ex:
            error_message = f"Volume {volume_id} deletion failed: {ex}"
            self.logger.debug(error_message, exc_info=True)
            raise Exception(error_message) from ex

        self.logger.debug("Volume %s deleted successfully", volume_id)
        return
