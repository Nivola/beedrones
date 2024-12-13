# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte
from beecell.types.type_dict import dict_get
from beedrones.vsphere.client import VsphereObject


class VsphereNetworkLogicalSwitch(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list_transport_zones(self):
        """ """
        res = self.call("/api/2.0/vdn/scopes", "GET", "")
        res = res["vdnScopes"]["vdnScope"]
        self.logger.debug("Get transport zones: %s" % res)
        return res

    def get_transport_zone(self, oid):
        """ """
        res = self.call("/api/2.0/vdn/scopes/%s" % oid, "GET", "")
        res = res["vdnScope"]
        self.logger.debug("Get transport zone: %s" % res)
        return res

    def list(self):
        """get logical switches

        :return:
        """
        res = self.call("/api/2.0/vdn/virtualwires?pagesize=1024", "GET", "")
        return res["virtualWires"]["dataPage"]["virtualWire"]

    def get(self, oid):
        """get logical switch by id

        :param oid: logical switch id
        """
        res = self.call("/api/2.0/vdn/virtualwires/%s" % oid, "GET", "")
        return res["virtualWire"]

    def get_by_dvpg(self, dvpg):
        """get logical switch by dvpg mor_id

        :param dvpg: dvpg mor_id
        """
        virtualwires = self.list()
        idx = {}
        for item in virtualwires:
            switches = item.get("vdsContextWithBacking", [])
            if isinstance(switches, list):
                for switch in switches:
                    dvpg_id = dict_get(switch, "backingValue")
                    if dvpg_id is not None:
                        idx[dvpg_id] = item
            elif isinstance(switches, dict):
                dvpg_id = dict_get(switches, "backingValue")
                if dvpg_id is not None:
                    idx[dvpg_id] = item

        res = idx.get(dvpg, None)
        return res

    def create(self, scope_id, name, desc, tenant="virtual wire tenant", guest_allowed="true"):
        """Create logical switch

        :param scope_id: transport zone id
        :param name: logical switch name
        :param desc: logical switch desc
        :param tenant: tenant id [default="virtual wire tenant"]
        :param guest_allowed: [default='true']
        """
        data = [
            "<virtualWireCreateSpec>",
            "<name>%s</name>" % name,
            "<description>%s</description>" % desc,
            "<tenantId>%s</tenantId>" % tenant,
            "<controlPlaneMode>UNICAST_MODE</controlPlaneMode>",
            "<guestVlanAllowed>%s</guestVlanAllowed>" % guest_allowed,
            "</virtualWireCreateSpec>",
        ]
        data = "".join(data)
        res = self.call(
            "/api/2.0/vdn/scopes/%s/virtualwires" % scope_id,
            "POST",
            data,
            headers={"Content-Type": "text/xml"},
            timeout=600,
        )
        return res

    def delete(self, oid):
        """
        :param oid: logical switch id
        """
        res = self.call("/api/2.0/vdn/virtualwires/%s" % oid, "DELETE", "", timeout=600)
        return res

    def info(self, sw):
        """Format logical switch main info"""
        res = {
            "objectId": sw["objectId"],
            "objectTypeName": sw["objectTypeName"],
            "vsmUuid": sw["vsmUuid"],
            "nodeId": sw["nodeId"],
            "revision": sw["revision"],
            "description": sw["description"],
            "clientHandle": sw["clientHandle"],
            "extendedAttributes": sw["extendedAttributes"],
            "isUniversal": sw["isUniversal"],
            "universalRevision": sw["universalRevision"],
            "tenantId": sw["tenantId"],
            "vdnScopeId": sw["vdnScopeId"],
            "switch": [],
            "vdnId": sw["vdnId"],
            "guestVlanAllowed": sw["guestVlanAllowed"],
            "controlPlaneMode": sw["controlPlaneMode"],
            "ctrlLsUuid": sw["ctrlLsUuid"],
            "macLearningEnabled": sw["macLearningEnabled"],
        }

        data = sw["vdsContextWithBacking"]
        if not isinstance(data, list):
            data = [data]

        for item in data:
            switch = item["switch"]
            data = {
                "switch": {"objectId": switch["objectId"], "name": switch["name"]},
                "mtu": item["mtu"],
                "promiscuousMode": item["promiscuousMode"],
                "portgroup": {"objectId": item["backingValue"]},
            }
            res["switch"].append(data)

        return res

    def detail(self, sw):
        """Format logical switch main info"""
        res = self.info(sw)

        return res

    def info_print(self, data):
        """Format logical switch main info"""
        res = []
        row_tmpl = "%-40s%-20s%-20s%-7s%-10s"
        row_tmpl2 = "%-90s%-20s%-6s%-25s%-30s"
        legend = ("name", "transport", "tenant", "vlanid", "switch")
        res.append(row_tmpl % legend)
        for item in data:
            row = (
                item["name"],
                item["controlPlaneMode"],
                item["tenantId"],
                item["vdnId"],
                "",
            )
            res.append(row_tmpl % row)
            for switch in item["vdsContextWithBacking"]:
                backingvalue = switch.get("backingValue")
                mtu = switch.get("mt")
                switch_elem = switch.get("switch", {})
                name = switch_elem.get("name")
                scope = switch_elem.get("scope", {}).get("name")
                row = ("", backingvalue, mtu, name, scope)
                res.append(row_tmpl2 % row)
        return res
