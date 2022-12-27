# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from pyVmomi import vim
from beedrones.vsphere.client import VsphereObject, VsphereError
from beedrones.vsphere.host import VsphereHost
from beedrones.vsphere.resource_pool import VsphereResourcePool


class VsphereCluster(VsphereObject):
    """
    """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

        self.host = VsphereHost(self.manager)
        self.resource_pool = VsphereResourcePool(self.manager)

    def list(self):
        """Get clusters with some properties: ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']

        return: list of vim.Cluster
        """
        props = ['name', 'parent', 'overallStatus', 'resourcePool', 'host', 'summary.totalMemory',
                 'summary.numCpuThreads']
        view = self.manager.get_container_view(obj_type=[vim.ClusterComputeResource])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.ClusterComputeResource,
                                               path_set=props,
                                               include_mors=True)
        return data

    def get(self, morid):
        """Get cluster by managed object reference id. Some important properties: name, parent._moId, _moId
        """
        container = None
        obj = self.manager.get_object(morid, [vim.ClusterComputeResource], container=container)
        return obj

    #
    # summary
    #
    def info(self, obj):
        """Get info

        :param obj: obj morid
        :return: dict like {'id':.., 'name':..}
        """
        data = {
            'id': obj.get('obj')._moId,
            'parent': obj.get('parent')._moId,
            'name': obj.get('name'),
            'overallStatus': obj.get('overallStatus'),
            'numCpuThreads': obj.get('summary.numCpuThreads'),
            'totalMemory': round(obj.get('summary.totalMemory')/1024/1024/1024),
            'host': len(obj.get('host'))
        }

        return data

    def detail(self, obj):
        """
        """
        data = {
            'id': obj._moId,
            'parent': obj.parent._moId,
            'name': obj.name,
            'overallStatus': obj.overallStatus,
            'effectiveCpu': obj.summary.effectiveCpu,
            'effectiveMemory': obj.summary.effectiveMemory,
            'effectiveCpu': obj.summary.effectiveCpu,
            'numCpuCores': obj.summary.numCpuCores,
            'numCpuThreads': obj.summary.numCpuThreads,
            'numEffectiveHosts': obj.summary.numEffectiveHosts,
            'numHosts': obj.summary.numHosts,
            'totalCpu': obj.summary.totalCpu,
            'totalMemory': round(obj.summary.totalMemory/1024/1024/1024),
        }
        return data

    def usage(self):
        """Cpu, memory, storage usage
        """
        pass

    def ha_status(self):
        """
        """
        pass

    def drs_status(self):
        """
        """
        pass

    def related_objects(self):
        """datcenter
        """
        pass

    def consumers(self):
        """Resource pools, vApps, Virual machines
        """
        pass

    #
    # monitor
    #

    #
    # manage
    #

    #
    # related object
    #
    def get_servers(self, morid):
        """
        """
        container = None
        obj = self.manager.get_object(morid, [vim.ClusterComputeResource], container=container)
        view = self.manager.get_container_view(obj_type=[vim.VirtualMachine], container=obj)
        vm_data = self.manager.collect_properties(view_ref=view,
                                                  obj_type=vim.VirtualMachine,
                                                  path_set=self.manager.server_props,
                                                  include_mors=True)
        return vm_data
