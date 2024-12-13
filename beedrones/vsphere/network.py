# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from pyVmomi import vmodl
from pyVmomi import vim
from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereNetwork(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

        self._nsx = VsphereNetworkNsx(manager)

    @property
    def nsx(self):
        if self.manager.nsx is None:
            raise VsphereError("Nsx is not configured")
        else:
            return self._nsx

    #
    # DistributedVirtualSwitch
    #

    def list_distributed_virtual_switches(self):
        """Get distributed virtual switch with some properties:
            ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']

        return: list of vim.dvs.VmwareDistributedVirtualSwitch
        """
        props = ["name", "parent", "overallStatus"]
        view = self.manager.get_container_view(obj_type=[vim.dvs.VmwareDistributedVirtualSwitch])
        data = self.manager.collect_properties(
            view_ref=view,
            obj_type=vim.dvs.VmwareDistributedVirtualSwitch,
            path_set=props,
            include_mors=True,
        )
        return data

    def get_distributed_virtual_switch(self, morid):
        """Get distributed virtual switch by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        container = None
        dvs = self.manager.get_object(morid, [vim.dvs.VmwareDistributedVirtualSwitch], container=container)
        return dvs

    #
    # network and DistributedVirtualPortgroup
    #

    def list_networks(self):
        """Get networks with some properties:
            ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']

        return: list of vim.Network, vim.dvs.DistributedVirtualPortgroup
        """
        props = [
            "name",
            "parent",
            "overallStatus",
            "summary.ipPoolId",
            "summary.ipPoolName",
        ]
        view = self.manager.get_container_view(obj_type=[vim.Network])
        data = self.manager.collect_properties(view_ref=view, obj_type=vim.Network, path_set=props, include_mors=True)
        return data

    def get_network(self, morid):
        """Get network by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        container = None
        obj = self.manager.get_object(morid, [vim.Network], container=container)
        return obj

    def create_distributed_port_group(self, name, desc, vlan, dvs, numports=24):
        """Creates a distributed virtual port group.

        :param name: String Name
        :param desc: String desc
        :param vlan: vlan id
        :param dvs: dvs object reference
        :param numports: number of ports in the portgroup [default=24]
        """
        try:
            vlan_config = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
            vlan_config.vlanId = vlan
            port_config = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
            port_config.vlan = vlan_config

            config = vim.dvs.DistributedVirtualPortgroup.ConfigSpec(
                name=name,
                description=desc,
                autoExpand=True,
                defaultPortConfig=port_config,
                type="earlyBinding",
                numPorts=numports,
            )

            task = dvs.CreateDVPortgroup_Task(spec=config)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def remove_network(self, network):
        """Remove a distributed virtual port group.

        :param morid:
        """
        try:
            task = network.Destroy_Task()
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    #
    # summary
    #
    def info_distributed_virtual_switch(self, obj):
        """
        :param obj: instance. Get with get_by_****
        """
        info = {
            "id": obj.get("obj")._moId,
            "parent": obj.get("parent")._moId,
            "name": obj.get("name"),
            "overallStatus": obj.get("overallStatus"),
        }
        return info

    def detail_distributed_virtual_switch(self, obj):
        """ """
        creation_date = obj.config.createTime.strftime("%d-%m-%y %H:%M:%S")
        res = {
            "id": obj._moId,
            "parent": obj.parent._moId,
            "name": obj.name,
            "overallStatus": obj.overallStatus,
            "uuid": obj.uuid,
            "configVersion": obj.config.configVersion,
            "date": {"created": creation_date},
            "desc": obj.config.description,
            "extensionKey": obj.config.extensionKey,
            "networkResourceManagementEnabled": obj.config.networkResourceManagementEnabled,
            "numPorts": obj.config.numPorts,
            "maxPorts": obj.config.maxPorts,
            "numStandalonePorts": obj.config.numStandalonePorts,
            "switchIpAddress": obj.config.switchIpAddress,
            "targetInfo": obj.config.targetInfo,
            "uplinkPortgroup": [u._moId for u in obj.config.uplinkPortgroup],
        }
        return res

    def info_network(self, obj):
        """
        :param obj: instance. Get with get_by_****
        """
        try:
            info = {
                "id": obj.get("obj")._moId,
                "parent": obj.get("parent")._moId,
                "name": obj.get("name"),
                "overallStatus": obj.get("overallStatus"),
            }
        except Exception as error:
            self.logger.error(error, exc_info=False)
            info = {}
        return info

    def detail_network(self, obj):
        """ """
        cfg = obj.config.defaultPortConfig
        res = {
            "id": obj._moId,
            "parent": obj.parent._moId,
            "name": obj.name,
            "overallStatus": obj.overallStatus,
            "desc": obj.config.description,
            # 'portKeys': [p for p in obj.portKeys],
            "autoExpand": obj.config.autoExpand,
            "configVersion": obj.config.configVersion,
            "description": obj.config.description,
            "numPorts": obj.config.numPorts,
            "type": obj.config.type,
            "dvs": obj.config.distributedVirtualSwitch._moId,
            "vlan": cfg.vlan.vlanId,
            "lacp": {
                "enable": cfg.lacpPolicy.enable.value,
                "mode": cfg.lacpPolicy.mode.value,
            },
            "config": {
                "in": {
                    "ShapingPolicy": cfg.inShapingPolicy.enabled.value,
                    "averageBandwidth": cfg.inShapingPolicy.averageBandwidth.value,
                    "peakBandwidth": cfg.inShapingPolicy.averageBandwidth.value,
                    "burstSize": cfg.inShapingPolicy.averageBandwidth.value,
                },
                "out": {
                    "ShapingPolicy": cfg.outShapingPolicy.enabled.value,
                    "averageBandwidth": cfg.outShapingPolicy.averageBandwidth.value,
                    "peakBandwidth": cfg.outShapingPolicy.averageBandwidth.value,
                    "burstSize": cfg.outShapingPolicy.averageBandwidth.value,
                },
            },
        }
        return res

    #
    # monitor
    #

    #
    # manage
    #

    #
    # related object
    #

    def get_network_servers(self, morid):
        """ """
        container = None
        obj = self.manager.get_object(morid, [vim.dvs.DistributedVirtualPortgroup], container=container)

        vm_data = []
        for o in obj.vm:
            vm_data.append(o)

        return vm_data


class VsphereNetworkNsx(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

        from .dfw import VsphereNetworkDfw
        from .dlr import VsphereNetworkDlr
        from .edge import VsphereNetworkEdge
        from .ip_pool import VsphereNetworkIpPool
        from .ip_set import VsphereNetworkIpSet
        from .logical_switch import VsphereNetworkLogicalSwitch
        from .security_group import VsphereNetworkSecurityGroup
        from .service import VsphereNetworkService

        self.dfw = VsphereNetworkDfw(self.manager)
        self.lg = VsphereNetworkLogicalSwitch(self.manager)
        self.sg = VsphereNetworkSecurityGroup(self.manager)
        self.dlr = VsphereNetworkDlr(self.manager)
        self.edge = VsphereNetworkEdge(self.manager)
        self.ippool = VsphereNetworkIpPool(self.manager)
        self.ipset = VsphereNetworkIpSet(self.manager)
        self.service = VsphereNetworkService(self.manager)
