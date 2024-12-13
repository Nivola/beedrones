# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from itertools import islice
from netapp_ontap.resources import Qtree
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapQtree(OntapEntity):
    """
    OntapQtree
    """

    @make_request
    def list(self, **kwargs):
        """list qTree

        :param kwargs:
        :return:
        """
        # NB: max_records doesn't work as ontap says. it has no effect on the result, which is a generator.
        # so we get the right number of records ourselves
        # max_records left as parameter get_collection in hope they eventually fix it
        max_records = kwargs.pop("max_records", None)

        resp = []
        # expensive = statistics. ...
        # inutili? qos_policy. ...
        # forse servono solo: "id", "name", NO"path", "security_style", "unix_permissions"
        # path deprecated -> use nas.path
        fields = (
            "svm.uuid,svm.name,unix_permissions,user.id,user.name,"
            "nas.path,export_policy.name,export_policy.id,id,volume.name,volume.uuid,"
            "security_style,name,group.id,group.name"
        )

        res = Qtree.get_collection(connection=self.client, max_records=20, fields=fields, **kwargs)

        if max_records:
            res = islice(res, max_records)

        resp = [qTree.to_dict() for qTree in res]
        self.logger.debug("list qTree: %s" % truncate(resp))
        return resp

    @make_request
    def get(self, volume_id, qtree_id: int):
        """get qtree

        :param volume_id: volume uuid
        :param id: qtree id on that volume
        :return:
        """
        fields = (
            # "TODO"
        )
        kwargs = {}
        qtree = Qtree(volume={"uuid": volume_id}, id=qtree_id)
        qtree.set_connection(self.client)
        response = qtree.get(fields=fields, **kwargs)
        # resp = qtree.to_dict()
        # self.logger.debug("get volume: %s" % truncate(resp))
        self.logger.debug("get volume: %s" % truncate(response))
        return response.http_response.json()
