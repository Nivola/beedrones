# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beedrones.vsphere.client import VsphereObject, VsphereError
from six.moves.urllib.parse import urlencode


class VsphereNetworkDlr(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self, datacenter=None, portgroup=None):
        """
        :param datacenter: Retrieve Edges by datacenter
        :param portgroup: Retrieve Edges with one interface on specified port group
        """
        params = {}
        if datacenter is not None:
            params["datacenter"] = datacenter
        if portgroup is not None:
            params["portgroup"] = portgroup
        params = urlencode(params)
        items = self.call("/api/4.0/edges?%s" % params, "GET", "")
        items = items["pagedEdgeList"]["edgePage"]
        if "edgeSummary" in items.keys():
            items = items.get("edgeSummary")
            if isinstance(items, dict):
                items = [items]

            res = [i for i in items if i.get("edgeType", None) == "distributedRouter"]
        else:
            res = []

        return res

    def get(self, oid):
        """
        :param oid: dlr id
        """
        res = self.call("/api/4.0/edges/%s" % oid, "GET", "")
        return res["edge"]

    def info(self, dlr):
        """TODO
        :param dlr: dlr instance
        """
        dlr.pop("id")
        res = dlr
        return res

    def detail(self, dlr):
        """TODO
        :param dlr: dlr instance
        """
        dlr.pop("id")
        res = dlr
        return res

    def create(self, dictNewDlr):
        """
        Create a Distribuited Logical Router

           TO DO:   1) multiply address for each  interface
                    2) HA edge
                    3) async task


        :param dictNewDlr: a dictionary containing the value to create a new DLR

            Dictionary format example:

            dict = {'datacenterMoid':'datacenter-38',
                    'name':'NSX_Miko-APIDICT',
                    'staticRouting':{'enabled':'true',
                                     'vnic':'2',
                                     'mt':'1500',
                                     'description':'Miko Gateway',
                                     'gatewayAddress':'10.102.184.1'},
                    'appliances':{'deployAppliances':'true',
                                  'resourcePoolId':'domain-c54',
                                  'datastoreId':'datastore-93'},
                    'cliSettings':{'remoteAccess':'true',
                                   'userName':'admin',
                                   'password':'Applenumber@143'},
                    'mgmtInterface':{'connectedToId':'dvportgroup-82'},
                    'interfaces':{'interface':[
                                    {'name':'Uplink_miko_by_API',
                                    'mt':'1500','type':'uplink',
                                    'connectedToId':'dvportgroup-82',
                                    'primaryAddress':'10.102.184.40',
                                    'subnetMask':'255.255.255.0',
                                    'subnetPrefixLength':'24',
                                    'isConnected':'true'},
                                    {'name':'internal_miko_by_API',
                                    'mt':'1500',
                                    'type':'internal',
                                    'connectedToId':'virtualwire-7',
                                    'primaryAddress':'192.168.100.1',
                                    'subnetMask':'255.255.255.0',
                                    'subnetPrefixLength':'24',
                                    'isConnected':'true'}
                                    ]}
                    }
        """

        if dictNewDlr["appliances"]["deployAppliances"] == "false":
            #
            # NO Appliance to deploy: i have to create DLR WITHOUT static routing adminDistance
            #
            edge = [
                "<edge>",
                "<datacenterMoid>%s</datacenterMoid>",
                "<type>distributedRouter</type>",
                "<name>%s</name>",
                "<features>",
                "<routing>",
                "<enabled>%s</enabled>",
                "<staticRouting>",
                "<defaultRoute>",
                "<vnic>%s</vnic>",
                "<mtu>%s</mtu>",
                "<description>%s</description>",
                "<gatewayAddress>%s</gatewayAddress>",
                "</defaultRoute>",
                "<staticRoutes/>",
                "</staticRouting>",
                "</routing>",
                "</features>",
                "<appliances>",
                "<deployAppliances>%s</deployAppliances>",
                "</appliances>",
                "<cliSettings>",
                "<remoteAccess>%s</remoteAccess>",
                "<userName>%s</userName>",
                "<password>%s</password>",
                "</cliSettings>",
                "<mgmtInterface>",
                "<connectedToId>%s</connectedToId>",
                "</mgmtInterface>",
                "<interfaces>",
            ]

            edge = "".join(edge) % (
                dictNewDlr["datacenterMoid"],
                dictNewDlr["name"],
                dictNewDlr["staticRouting"]["enabled"],
                dictNewDlr["staticRouting"]["vnic"],
                dictNewDlr["staticRouting"]["mt"],
                dictNewDlr["staticRouting"]["description"],
                dictNewDlr["staticRouting"]["gatewayAddress"],
                dictNewDlr["appliances"]["deployAppliances"],
                dictNewDlr["cliSettings"]["remoteAccess"],
                dictNewDlr["cliSettings"]["userName"],
                dictNewDlr["cliSettings"]["password"],
                dictNewDlr["mgmtInterface"]["connectedToId"],
            )

        else:
            edge = [
                "<edge>",
                "<datacenterMoid>%s</datacenterMoid>",
                "<type>distributedRouter</type>",
                "<name>%s</name>",
                "<features>",
                "<routing>",
                "<enabled>%s</enabled>",
                "<staticRouting>",
                "<defaultRoute>",
                "<vnic>%s</vnic>",
                "<mtu>%s</mtu>",
                "<description>%s</description>",
                "<gatewayAddress>%s</gatewayAddress>",
                "<adminDistance>1</adminDistance>",
                "</defaultRoute>",
                "<staticRoutes/>",
                "</staticRouting>",
                "</routing>",
                "</features>",
                "<appliances>",
                "<deployAppliances>%s</deployAppliances>",
                "<appliance>",
                "<resourcePoolId>%s</resourcePoolId>",
                "<datastoreId>%s</datastoreId>",
                "</appliance>",
                "</appliances>",
                "<cliSettings>",
                "<remoteAccess>%s</remoteAccess>",
                "<userName>%s</userName>",
                "<password>%s</password>",
                "</cliSettings>",
                "<mgmtInterface>",
                "<connectedToId>%s</connectedToId>",
                "</mgmtInterface>",
                "<interfaces>",
            ]
            edge = "".join(edge) % (
                dictNewDlr["datacenterMoid"],
                dictNewDlr["name"],
                dictNewDlr["staticRouting"]["enabled"],
                dictNewDlr["staticRouting"]["vnic"],
                dictNewDlr["staticRouting"]["mt"],
                dictNewDlr["staticRouting"]["description"],
                dictNewDlr["staticRouting"]["gatewayAddress"],
                dictNewDlr["appliances"]["deployAppliances"],
                dictNewDlr["appliances"]["resourcePoolId"],
                dictNewDlr["appliances"]["datastoreId"],
                dictNewDlr["cliSettings"]["remoteAccess"],
                dictNewDlr["cliSettings"]["userName"],
                dictNewDlr["cliSettings"]["password"],
                dictNewDlr["mgmtInterface"]["connectedToId"],
            )

        # Costruisco parte del file XML per la sezione interfaces
        interfaces = ""
        for element in dictNewDlr["interfaces"]["interface"]:
            interface = [
                "<interface>",
                "<name>%s</name>",
                "<addressGroups>",
                "<addressGroup>",
                "<primaryAddress>%s</primaryAddress>",
                "<subnetMask>%s</subnetMask>",
                "<subnetPrefixLength>%s</subnetPrefixLength>",
                "</addressGroup>",
                "</addressGroups>",
                "<mtu>%s</mtu>",
                "<type>%s</type>",
                "<isConnected>%s</isConnected>",
                "<isSharedNetwork>false</isSharedNetwork>",
                "<connectedToId>%s</connectedToId>",
                "</interface>",
            ]
            interface = "".join(interface) % (
                element["name"],
                element["primaryAddress"],
                element["subnetMask"],
                element["subnetPrefixLength"],
                element["mt"],
                element["type"],
                element["isConnected"],
                element["connectedToId"],
            )
            interfaces = interfaces + interface

        XML = edge + interfaces + "</interfaces></edge>"

        res = self.call(
            "/api/4.0/edges",
            "POST",
            XML,
            headers={"Content-Type": "text/xml"},
            parse=False,
        )

        return res

    def delete(self, oid):
        """

        Modified by Miko( TO DO by Sergio )


        :param oid: edge id
        """

        res = self.call("/api/4.0/edges/%s" % oid, "DELETE", "", timeout=600)
        return True
