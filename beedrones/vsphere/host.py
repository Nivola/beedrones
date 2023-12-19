# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from pyVmomi import vim
from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereHost(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self, cluster=None):
        """Get hosts with some properties: ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']

        :param cluster: cluster mor id
        :return: list of vim.Cluster
        """
        props = [
            "name",
            "parent",
            "overallStatus",
            "hardware.cpuInfo.numCpuThreads",
            "config.network.vnic",
            "summary.hardware.cpuModel",
            "summary.quickStats.overallMemoryUsage",
            "runtime.bootTime",
            "runtime.connectionState",
            "hardware.memorySize",
            "hardware.systemInfo.model",
            "hardware.biosInfo.biosVersion",
            "vm",
        ]
        container = None
        obj = None
        if cluster is not None:
            obj = self.manager.get_object(cluster, [vim.ClusterComputeResource], container=container)

        view = self.manager.get_container_view(obj_type=[vim.HostSystem], container=obj)
        data = self.manager.collect_properties(
            view_ref=view, obj_type=vim.HostSystem, path_set=props, include_mors=True
        )
        return data

    def get(self, morid):
        """Get cluster by managed object reference id. Some important properties: name, parent._moId, _moId"""
        container = None
        obj = self.manager.get_object(morid, [vim.HostSystem], container=container)
        return obj

    def add(self, network):
        """ """
        pass

    def update(self, network):
        """ """
        pass

    def remove(self, network):
        """ """
        pass

        #

    # summary
    #
    def info(self, obj):
        """Get info

        :param obj: obj morid
        :return: dict like {'id':.., 'name':..}
        """
        memory_free = round(
            obj.get("hardware.memorySize") / 1024 / 1024 - obj.get("summary.quickStats.overallMemoryUsage")
        )
        data = {
            "id": obj.get("obj")._moId,
            "parent": obj.get("parent")._moId,
            "name": obj.get("name"),
            "overallStatus": obj.get("overallStatus"),
            "biosVersion": obj.get("hardware.biosInfo.biosVersion"),
            "numCpuThreads": obj.get("hardware.cpuInfo.numCpuThreads"),
            "memorySize": round(obj.get("hardware.memorySize") / 1024 / 1024),
            "memoryFree": memory_free,
            "memoryUsage": obj.get("summary.quickStats.overallMemoryUsage"),
            "model": obj.get("hardware.systemInfo.model"),
            "bootTime": obj.get("runtime.bootTime"),
            "connectionState": obj.get("runtime.connectionState"),
            "server": len(obj.get("vm")),
            "host_ip": obj.get("config.network.vnic")[0].spec.ip.ipAddress,
        }
        return data

    def detail(self, host):
        """ """
        hw = host.hardware
        data = {
            "id": host._moId,
            "parent": host.parent._moId,
            "name": host.name,
            "overallStatus": host.overallStatus,
            "rebootRequired": host.summary.rebootRequired,
            "currentEVCModeKey": host.summary.currentEVCModeKey,
            "maxEVCModeKey": host.summary.maxEVCModeKey,
            "network": {
                "atBootIpV6Enabled": host.config.network.atBootIpV6Enabled,
                "ipV6Enabled": host.config.network.ipV6Enabled,
            },
            "bios": hw.biosInfo.biosVersion,
            "cpu": {
                "hz": hw.cpuInfo.hz,
                "numCpuCores": hw.cpuInfo.numCpuCores,
                "numCpuPackages": hw.cpuInfo.numCpuPackages,
                "numCpuThreads": hw.cpuInfo.numCpuThreads,
            },
            "memory": round(hw.memorySize / 1024 / 1024 / 1024),
            "system": {
                "model": hw.systemInfo.model,
                "uuid": hw.systemInfo.uuid,
                "vendor": hw.systemInfo.vendor,
            },
            "licensableResource": [{r.key: r.value} for r in host.licensableResource.resource],
            "bootTime": host.runtime.bootTime,
            "connectionState": host.runtime.connectionState,
            "inMaintenanceMode": host.runtime.inMaintenanceMode,
            "inQuarantineMode": host.runtime.inQuarantineMode,
            "powerState": host.runtime.powerState,
        }
        return data

    def hardware(self, host):
        """Manifacturer, model, CPU, Memory, Virtual Flash, Network, Storage"""
        return host.hardware

    def capability(self, host):
        """Host capability"""
        return host.capability

    def runtime(self, host):
        """ """
        return {
            "boot_time": host.runtime.bootTime,
            "maintenance": host.runtime.inMaintenanceMode,
            "power_state": host.runtime.powerState,
        }

    def configuration(self, host):
        """Esxi version, ha state, Fault tolerance, EVC mode"""
        return {}

    def usage(self, host):
        """Cpu, memory, storage usage"""
        return host.summary.quickStats

    def related_objects(self, host):
        """ """
        pass

    def services(self, host):
        """ """
        return host.config.service

    #
    # monitor
    #

    def issues(self):
        """ """
        pass

    def performance(self):
        """ """
        pass

    def log_browser(self):
        """ """
        pass

    def tasks(self):
        """ """
        pass

    def events(self):
        """ """
        pass

    def hardware_status(self):
        """ """
        pass

        #

    # manage
    #

    def connect(self):
        """ """
        pass

    def disconnect(self):
        """ """
        pass

    def enter_maintenance(self):
        """ """
        pass

    def exit_maintenance(self):
        """ """
        pass

    def power_on(self):
        """ """
        pass

    def power_off(self):
        """ """
        pass

    def standby(self):
        """ """
        pass

    def reboot(self):
        """ """
        pass

    #
    # related object
    #

    def get_servers(self, morid):
        """ """
        container = None
        obj = self.manager.get_object(morid, [vim.HostSystem], container=container)
        view = self.manager.get_container_view(obj_type=[vim.VirtualMachine], container=obj)
        vm_data = self.manager.collect_properties(
            view_ref=view,
            obj_type=vim.VirtualMachine,
            path_set=self.manager.server_props,
            include_mors=True,
        )
        return vm_data
