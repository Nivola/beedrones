# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beedrones.cmp.client import CmpBaseService
from beedrones.cmp.resource import CmpResourceAbstractService


class CmpResourceVsphereService(CmpResourceAbstractService):
    """Cmp resource vsphere service"""

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        self.nsx_edge = CmpResourceVsphereNsxEdgeService(self.manager)


class CmpResourceVsphereAbstractService(CmpResourceAbstractService):
    """Cmp resource vsphere service"""

    pass

    # vsphere/network")


class CmpResourceVsphereDvpgService(CmpResourceVsphereAbstractService):
    """Cmp resource vsphere distributed virtual portgroup service"""

    def get(self, oid, **kwargs):
        """Get dvpg details

        :param oid: dvpg id, uuid or name
        :return: dvpg details dictionary
        """
        uri = self.get_uri("vsphere/network/dvpgs/%s" % oid, preferred_version=self.VERSION, **kwargs)
        res = self.api_get(uri).get("dvpg", {})
        return res


class CmpResourceVsphereNsxEdgeService(CmpResourceVsphereAbstractService):
    """Cmp resource vsphere nsx edge service"""

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        self.dvpg = CmpResourceVsphereDvpgService(self.manager)

    def get(self, oid, **kwargs):
        """Get nsx edge details

        :param oid: plugin vsphere nsx edge id, uuid or name
        :return: nsx edge details dictionary
        """
        uri = self.get_uri("vsphere/network/nsx_edges/%s" % oid, preferred_version=self.VERSION, **kwargs)
        res = self.api_get(uri).get("nsx_edge", {})
        return res

    def get_vnics(self, edge, portgroup=None, index=None, vnic_type=None):
        """List vnics

        :param edge: nsx edge full configuration dictionary
        :param portgroup: portgroup id, uuid or name
        :param index: vnic index
        :param vnic_type: vnic type
        :return: list of dictionaries of vnic details
        """
        res = edge.get("details", {}).get("vnics", {}).get("vnic", [])
        resp = res
        if portgroup is not None:
            portgroup_ext_id = self.dvpg.get(portgroup).get("ext_id")
            resp = [r for r in res if r.get("portgroupId") == portgroup_ext_id]
        if index is not None:
            resp = [r for r in res if r.get("index") == index]
        if vnic_type is not None:
            resp = [r for r in res if r.get("type") == vnic_type]
        return resp
