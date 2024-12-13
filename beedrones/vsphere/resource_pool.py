# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from pyVmomi import vmodl
from pyVmomi import vim
from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereResourcePool(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self, cluster=None):
        """Get resource_polls with some properties: ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']

        :param cluster: cluster mor id
        :return: list of vim.ResourcePool
        """
        props = ["name", "parent", "overallStatus"]
        container = None
        obj = None
        if cluster is not None:
            obj = self.manager.get_object(cluster, [vim.ClusterComputeResource], container=container)

        view = self.manager.get_container_view(obj_type=[vim.ResourcePool], container=obj)
        data = self.manager.collect_properties(
            view_ref=view, obj_type=vim.ResourcePool, path_set=props, include_mors=True
        )
        return data

    def get(self, morid):
        """Get resource_poll by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        container = None
        obj = self.manager.get_object(morid, [vim.ResourcePool], container=container)
        return obj

    def create(self, cluster, name, cpu, memory, shares="normal"):
        """Creates a resource pool.

        :parma cluster: cluster instance
        :param name: String Name
        :param cpu: cpu limit in MHz
        :param memory: memory limit in MB
        :param shares: high
                         For CPU: Shares = 2000 * nmumber of virtual CPUs
                         For Memory: Shares = 20 * virtual machine memory size in megabytes
                         For Disk: Shares = 2000
                         For Network: Shares = networkResourcePoolHighShareValue
                       low
                         For CPU: Shares = 500 * number of virtual CPUs
                         For Memory: Shares = 5 * virtual machine memory size in megabytes
                         For Disk: Shares = 500
                         For Network: Shares = 0.25 * networkResourcePoolHighShareValue
                       normal
                         For CPU: Shares = 1000 * number of virtual CPUs
                         For Memory: Shares = 10 * virtual machine memory size in megabytes
                         For Disk: Shares = 1000
                         For Network: Shares = 0.5 * networkResourcePoolHighShareValue
                      [default=normal]
        :raise VsphereError:
        """
        try:
            config = vim.ResourceConfigSpec()
            config.cpuAllocation = vim.ResourceAllocationInfo()
            config.cpuAllocation.expandableReservation = False
            config.cpuAllocation.limit = cpu
            config.cpuAllocation.reservation = cpu
            config.cpuAllocation.shares = vim.SharesInfo()
            config.cpuAllocation.shares.level = shares
            config.memoryAllocation = vim.ResourceAllocationInfo()
            config.memoryAllocation.expandableReservation = False
            config.memoryAllocation.limit = memory
            config.memoryAllocation.reservation = memory
            config.memoryAllocation.shares = vim.SharesInfo()
            config.memoryAllocation.shares.level = shares

            res = cluster.resourcePool.CreateResourcePool(name, config)
            self.logger.debug("Create resource pool %s" % name)
            return res
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def update(self, respool, name, cpu, memory, shares="normal"):
        """Creates a resource pool.

        :parma cluster: cluster instance
        :param name: String Name
        :param cpu: cpu limit in MHz
        :param memory: memory limit in MB
        :param shares: high
                         For CPU: Shares = 2000 * nmumber of virtual CPUs
                         For Memory: Shares = 20 * virtual machine memory size in megabytes
                         For Disk: Shares = 2000
                         For Network: Shares = networkResourcePoolHighShareValue
                       low
                         For CPU: Shares = 500 * number of virtual CPUs
                         For Memory: Shares = 5 * virtual machine memory size in megabytes
                         For Disk: Shares = 500
                         For Network: Shares = 0.25 * networkResourcePoolHighShareValue
                       normal
                         For CPU: Shares = 1000 * number of virtual CPUs
                         For Memory: Shares = 10 * virtual machine memory size in megabytes
                         For Disk: Shares = 1000
                         For Network: Shares = 0.5 * networkResourcePoolHighShareValue
                      [default=normal]
        :raise VsphereError:
        """
        try:
            config = vim.ResourceConfigSpec()
            config.cpuAllocation = vim.ResourceAllocationInfo()
            config.cpuAllocation.expandableReservation = False
            config.cpuAllocation.limit = cpu
            config.cpuAllocation.reservation = cpu
            config.cpuAllocation.shares = vim.SharesInfo()
            config.cpuAllocation.shares.level = shares
            config.memoryAllocation = vim.ResourceAllocationInfo()
            config.memoryAllocation.expandableReservation = False
            config.memoryAllocation.limit = memory
            config.memoryAllocation.reservation = memory
            config.memoryAllocation.shares = vim.SharesInfo()
            config.memoryAllocation.shares.level = shares

            res = respool.UpdateConfig(name, config)
            self.logger.debug("Update resource pool %s" % name)
            return res
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def remove(self, respool):
        """Remove a resource pool.

        :param morid:
        """
        task = respool.Destroy_Task()
        return task

    #
    # summary
    #
    def detail(self, respool):
        """Get resource pool infos.

        shares mean:

        high
          For CPU: Shares = 2000 * nmumber of virtual CPUs
          For Memory: Shares = 20 * virtual machine memory size in megabytes
          For Disk: Shares = 2000
          For Network: Shares = networkResourcePoolHighShareValue
        low
          For CPU: Shares = 500 * number of virtual CPUs
          For Memory: Shares = 5 * virtual machine memory size in megabytes
          For Disk: Shares = 500
          For Network: Shares = 0.25 * networkResourcePoolHighShareValue
        normal
          For CPU: Shares = 1000 * number of virtual CPUs
          For Memory: Shares = 10 * virtual machine memory size in megabytes
          For Disk: Shares = 1000
          For Network: Shares = 0.5 * networkResourcePoolHighShareValue

        :param respool: resource pool instance
        """
        cpu = respool.config.cpuAllocation
        mem = respool.config.memoryAllocation
        data = {
            "config": {
                "version": respool.config.changeVersion,
                "cpu_allocation": {
                    "reservation": cpu.reservation,
                    "expandableReservation": cpu.expandableReservation,
                    "limit": cpu.limit,
                    "shares": {"level": cpu.shares.level, "shares": cpu.shares.shares},
                },
                "memory_allocation": {
                    "reservation": mem.reservation,
                    "expandableReservation": mem.expandableReservation,
                    "limit": mem.limit,
                    "shares": {"level": mem.shares.level, "shares": mem.shares.shares},
                },
            },
            "date": {"modified": respool.config.lastModified},
        }
        return data

    def runtime(self, respool):
        """ """
        return respool.runtime

    def usage(self, respool):
        """Cpu, memory, storage usage"""
        return respool.summary.quickStats

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
        """ """
        container = None
        obj = self.manager.get_object(morid, [vim.ResourcePool], container=container)

        view = self.manager.get_container_view(obj_type=[vim.VirtualMachine], container=obj)
        vm_data = self.manager.collect_properties(
            view_ref=view,
            obj_type=vim.VirtualMachine,
            path_set=self.manager.server_props,
            include_mors=True,
        )
        return vm_data
