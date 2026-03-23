# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2026 CSI-Piemonte

from netapp_ontap.resources.qtree import Qtree
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapQtree(OntapEntity):
    """OntapQtree"""

    resclass = Qtree

    def list(self, **kwargs):
        """list qTree

        :param kwargs:
        :return:
        """
        fields = ("svm.uuid,svm.name,unix_permissions,user.id,user.name,nas.path,export_policy.name,"
                  "export_policy.id,id,volume.name,volume.uuid,security_style,name,group.id,group.name")
        return self.list_entities(OntapQtree.resclass, fields, **kwargs)

    @make_request
    def get(self, volume, qtree: int):
        """get qtree

        :param volume: volume uuid
        :param qtree: qtree id on that volume
        :return:
        """
        fields = (
            # TODO in case specific fields are needed
        )
        kwargs = {}
        qtree = Qtree(volume={"uuid": volume}, id=qtree)
        qtree.set_connection(self.client)
        response = qtree.get(fields=fields, **kwargs)
        self.logger.debug("get qtree: %s" % truncate(response))
        return response.http_response.json()
