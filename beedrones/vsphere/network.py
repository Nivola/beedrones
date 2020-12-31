# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

import traceback
from pyVmomi import vmodl
from pyVmomi import vim
from beecell.simple import get_attrib, str2uni
from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereNetwork(VsphereObject):
    """
    """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

        self._nsx = VsphereNetworkNsx(manager)

    @property
    def nsx(self):
        if self.manager.nsx is None:
            raise VsphereError('Nsx is not configured')
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
        props = ['name', 'parent', 'overallStatus']
        view = self.manager.get_container_view(obj_type=[vim.dvs.VmwareDistributedVirtualSwitch])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.dvs.VmwareDistributedVirtualSwitch,
                                               path_set=props,
                                               include_mors=True)
        return data

    def get_distributed_virtual_switch(self, morid):
        """Get distributed virtual switch by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        # container = self.si.content.rootFolder
        container = None
        dvs = self.manager.get_object(morid,
                                      [vim.dvs.VmwareDistributedVirtualSwitch],
                                      container=container)
        return dvs

    #
    # network and DistributedVirtualPortgroup
    #

    def list_networks(self):
        """Get networks with some properties:
            ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']

        return: list of vim.Network, vim.dvs.DistributedVirtualPortgroup
        """
        props = ['name', 'parent', 'overallStatus', 'summary.ipPoolId',
                 'summary.ipPoolName']
        view = self.manager.get_container_view(obj_type=[vim.Network])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.Network,
                                               path_set=props,
                                               include_mors=True)
        return data

    def get_network(self, morid):
        """Get network by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        # container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.Network],
                                      container=container)
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
                name=name, description=desc, autoExpand=True,
                defaultPortConfig=port_config, type='earlyBinding',
                numPorts=numports)

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
            'id': obj.get('obj')._moId,
            'parent': obj.get('parent')._moId,
            'name': obj.get('name'),
            'overallStatus': obj.get('overallStatus'),
        }
        return info

    def detail_distributed_virtual_switch(self, obj):
        """
        """
        creation_date = obj.config.createTime.strftime('%d-%m-%y %H:%M:%S')
        res = {
            'id': obj._moId,
            'parent': obj.parent._moId,
            'name': obj.name,
            'overallStatus': obj.overallStatus,
            'uuid': obj.uuid,
            'configVersion': obj.config.configVersion,
            'date': {'created': creation_date},
            'desc': obj.config.description,
            'extensionKey': obj.config.extensionKey,
            'networkResourceManagementEnabled': obj.config.networkResourceManagementEnabled,
            'numPorts': obj.config.numPorts,
            'maxPorts': obj.config.maxPorts,
            'numStandalonePorts': obj.config.numStandalonePorts,
            'switchIpAddress': obj.config.switchIpAddress,
            'targetInfo': obj.config.targetInfo,
            'uplinkPortgroup': [u._moId for u in obj.config.uplinkPortgroup]
        }
        return res

    def info_network(self, obj):
        """
        :param obj: instance. Get with get_by_****
        """
        try:
            info = {
                'id': obj.get('obj')._moId,
                'parent': obj.get('parent')._moId,
                'name': obj.get('name'),
                'overallStatus': obj.get('overallStatus'),
            }
        except Exception as error:
            self.logger.error(error, exc_info=False)
            info = {}
        return info

    def detail_network(self, obj):
        """
        """
        cfg = obj.config.defaultPortConfig
        res = {
            'id': obj._moId,
            'parent': obj.parent._moId,
            'name': obj.name,
            'overallStatus': obj.overallStatus,
            'desc': obj.config.description,
            # 'portKeys': [p for p in obj.portKeys],
            'autoExpand': obj.config.autoExpand,
            'configVersion': obj.config.configVersion,
            'description': obj.config.description,
            'numPorts': obj.config.numPorts,
            'type': obj.config.type,
            'dvs': obj.config.distributedVirtualSwitch._moId,
            'vlan': cfg.vlan.vlanId,
            'lacp': {'enable': cfg.lacpPolicy.enable.value, 'mode': cfg.lacpPolicy.mode.value},
            'config': {'in': {'ShapingPolicy': cfg.inShapingPolicy.enabled.value,
                              'averageBandwidth': cfg.inShapingPolicy.averageBandwidth.value,
                              'peakBandwidth': cfg.inShapingPolicy.averageBandwidth.value,
                              'burstSize': cfg.inShapingPolicy.averageBandwidth.value},
                       'out': {'ShapingPolicy': cfg.outShapingPolicy.enabled.value,
                               'averageBandwidth': cfg.outShapingPolicy.averageBandwidth.value,
                               'peakBandwidth': cfg.outShapingPolicy.averageBandwidth.value,
                               'burstSize': cfg.outShapingPolicy.averageBandwidth.value}}
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
        """
        """
        container = None
        obj = self.manager.get_object(morid, [vim.dvs.DistributedVirtualPortgroup], container=container)

        vm_data = []
        for o in obj.vm:
            vm_data.append(o)
            # vm_data.append({'_moId':o._moId,
            #                 'config.guestId':o.config.guestId,
            #                 'config.guestFullName':o.config.guestFullName,
            #                 'config.hardware.memoryMB':o.config.hardware.memoryMB,
            #                 'config.hardware.numCPU':o.config.hardware.numCPU,
            #                 'config.version':o.config.version,
            #                 'runtime.powerState':o.runtime.powerState,
            #                 'config.template':o.config.template,
            #                 'guest.hostName':o.guest.hostName,
            #                 'guest.ipAddress':o.guest.ipAddress})

        return vm_data


class VsphereNetworkNsx(VsphereObject):
    """
    """

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

    # #
    # # logical_switches
    # #
    # def list_transport_zones(self):
    #     """ """
    #     res = self.call('/api/2.0/vdn/scopes', 'GET', '')
    #     res = res['vdnScopes']['vdnScope']
    #     self.logger.debug('Get transport zones: %s' % res)
    #     return res
    #
    # #
    # # logical_switches
    # #
    # def list_logical_switches(self):
    #     """ """
    #     res = self.call('/api/2.0/vdn/virtualwires', 'GET', '')
    #     res = res.get('virtualWires', {}).get('dataPage', {}).get('virtualWire', [])
    #     if not isinstance(res, list):
    #         res = [res]
    #     return res
    #
    # def get_logical_switch(self, oid):
    #     """
    #     :param oid: logical switch id
    #     """
    #     res = self.call('/api/2.0/vdn/virtualwires/%s' % oid, 'GET', '')
    #     return res.get('virtualWire', [])
    #
    # def create_logical_switch(self, scope_id, name, desc, tenant="virtual wire tenant", guest_allowed='true'):
    #     """Create logical switch
    #
    #     :param scope_id: transport zone id
    #     :param name: logical switch name
    #     :param desc: logical switch desc
    #     :param tenant: tenant id [default="virtual wire tenant"]
    #     :param guest_allowed: [default='true']
    #     """
    #     data = ['<virtualWireCreateSpec>',
    #             '<name>%s</name>' % name,
    #             '<description>%s</description>' % desc,
    #             '<tenantId>%s</tenantId>' % tenant,
    #             '<controlPlaneMode>UNICAST_MODE</controlPlaneMode>',
    #             '<guestVlanAllowed>%s</guestVlanAllowed>' % guest_allowed,
    #             '</virtualWireCreateSpec>']
    #     data = ''.join(data)
    #     res = self.call('/api/2.0/vdn/scopes/%s/virtualwires' % scope_id,
    #                     'POST', data, headers={'Content-Type': 'text/xml'},
    #                     timeout=600)
    #     return res
    #
    # def delete_logical_switch(self, oid):
    #     """
    #     :param oid: logical switch id
    #     """
    #     res = self.call('/api/2.0/vdn/virtualwires/%s' % oid, 'DELETE', '',
    #                     timeout=600)
    #     return res
    #
    # def info_logical_switch(self, sw):
    #     """Format logical switch main info"""
    #     res = {
    #         "objectId": sw['objectId'],
    #         "objectTypeName": sw['objectTypeName'],
    #         "vsmUuid": sw['vsmUuid'],
    #         "nodeId": sw['nodeId'],
    #         "revision": sw['revision'],
    #         "description": sw['description'],
    #         "clientHandle": sw['clientHandle'],
    #         "extendedAttributes": sw['extendedAttributes'],
    #         "isUniversal": sw['isUniversal'],
    #         "universalRevision": sw['universalRevision'],
    #         "tenantId": sw['tenantId'],
    #         "vdnScopeId": sw['vdnScopeId'],
    #         "switch": [],
    #         "vdnId": sw['vdnId'],
    #         "guestVlanAllowed": sw['guestVlanAllowed'],
    #         "controlPlaneMode": sw['controlPlaneMode'],
    #         "ctrlLsUuid": sw['ctrlLsUuid'],
    #         "macLearningEnabled": sw['macLearningEnabled'],
    #     }
    #
    #     for item in sw['vdsContextWithBacking']:
    #         switch = item["switch"]
    #         data = {"switch": {"objectId": switch["objectId"],
    #                            "name": switch["name"]},
    #                 "mtu": item["mtu"],
    #                 "promiscuousMode": item["promiscuousMode"],
    #                 "portgroup": {"objectId": item["backingValue"]}}
    #         res['switch'].append(data)
    #
    #     return res
    #
    # def print_logicalswitch(self, data):
    #     """Format logical switch main info"""
    #     res = []
    #     row_tmpl = '%-40s%-20s%-20s%-7s%-10s'
    #     row_tmpl2 = '%-90s%-20s%-6s%-25s%-30s'
    #     legend = ('name',
    #               'transport',
    #               'tenant',
    #               'vlanid',
    #               'switch')
    #     res.append(row_tmpl % legend)
    #     for item in data:
    #
    #         row = (item['name'],
    #                item['controlPlaneMode'],
    #                item['tenantId'],
    #                item['vdnId'],
    #                '')
    #
    #         '''
    #         ]'''
    #         res.append(row_tmpl % row)
    #         for switch in item['vdsContextWithBacking']:
    #             try:
    #                 backingvalue = switch['backingValue']
    #             except:
    #                 backingvalue = None
    #             try:
    #                 mtu = switch['mt']
    #             except:
    #                 mtu = None
    #             try:
    #                 name = switch['switch']['name']
    #             except:
    #                 name = None
    #             try:
    #                 scope = switch['switch']['scope']['name']
    #             except:
    #                 scope = None
    #             row = ('',
    #                    backingvalue,
    #                    mtu,
    #                    name,
    #                    scope)
    #             res.append(row_tmpl2 % row)
    #     return res
