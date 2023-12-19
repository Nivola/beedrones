# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

import ssl
import time
import traceback
from datetime import datetime
import OpenSSL
from pyVmomi import vim, vmodl
from six import ensure_text
from beecell.types.type_string import truncate
from beecell.types.type_date import format_date
from beecell.simple import get_attrib
from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereServer(VsphereObject):
    """ """

    from .client import VsphereManager

    def __init__(self, manager: VsphereManager):
        VsphereObject.__init__(self, manager)
        self.monitor = VsphereServerMonitor(self)
        self.hardware = VsphereServerHardware(self)
        self.snapshot = VsphereServerSnapshot(self)

    def __list(self, template=False):
        """Get servers with some properties.

        :param template: if True search only template server
        """
        manager = self.manager
        view = manager.get_container_view(obj_type=[vim.VirtualMachine], container=None)
        vm_data = manager.collect_properties(
            view_ref=view,
            obj_type=vim.VirtualMachine,
            path_set=manager.server_props,
            include_mors=True,
        )

        if template is True:
            vm_data = [vm for vm in vm_data if vm["config.template"] is True]

        self.logger.debug("Get server list : %s" % truncate(vm_data))

        return vm_data

    def get_by_morid(self, morid):
        """Get server by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        container = None
        obj = self.manager.get_object(morid, [vim.VirtualMachine], container=container)
        return obj

    def get_by_uuid(self, uuid):
        """Get server by uuid."""
        search_index = self.manager.si.content.searchIndex

        obj = search_index.FindByUuid(None, uuid, True, True)
        return obj

    def get_by_dnsname(self, name):
        """Get server by dnsname."""
        search_index = self.manager.si.content.searchIndex

        obj = search_index.FindByDnsName(None, name, True)
        return obj

    def get_by_name(self, name):
        """Get server by name."""
        container = None
        obj = self.manager.get_object_by_name(name, [vim.VirtualMachine], container=container)
        return obj

    def get_by_names(self, name):
        """Get server by name like."""
        container = None
        objs = self.manager.get_objects_by_name(name, [vim.VirtualMachine], container=container)
        return objs

    def get_by_ip(self, ipaddress):
        """Get server by ipaddress."""
        search_index = self.manager.si.content.searchIndex

        obj = search_index.FindByIp(None, ipaddress, True)
        return obj

    def list(
        self,
        template=False,
        morid=None,
        uuid=None,
        name=None,
        names=None,
        ipaddress=None,
        dnsname=None,
    ):
        if morid is not None:
            return [self.get_by_morid(morid)]
        elif uuid is not None:
            return [self.get_by_uuid(uuid)]
        elif dnsname is not None:
            return [self.get_by_dnsname(dnsname)]
        elif name is not None:
            return [self.get_by_name(name)]
        elif names is not None:
            return self.get_by_names(names)
        elif ipaddress is not None:
            return [self.get_by_ip(ipaddress)]
        else:
            return self.__list(template)

    def get(self, oid):
        return self.get_by_morid(oid)

    def create(
        self,
        name,
        guest_id,
        datastore,
        folder,
        network,
        memory_mb=1024,
        cpu=1,
        core_x_socket=1,
        disk_size_gb=5,
        version="vmx-14",
        power_on=False,
        resource_pool=None,
        cluster=None,
    ):
        """Creates a VirtualMachine.

        :param name: String Name for the VirtualMachine
        :param folder: Folder to place the VirtualMachine in
        :param resource_pool: ResourcePool to place the VirtualMachine in [optional]
        :param cluster: cluster to place the VirtualMachine in [optional]
        :param datastore: DataStrore to place the VirtualMachine on
        :param network: Network to attach
        :param memory_mb:
        :param cpu:
        :param core_x_socket:
        :param disk_size_gb:
        :param version: vmx-8 , vmx-9, vmx-10, vmx-11, vmx-14
        :param power_on: power_on status [defualt=False]
        """
        try:
            datastore_path = "[" + datastore + "] " + name

            # bare minimum VM shell, no disks. Feel free to edit
            vmx_file = vim.vm.FileInfo(
                logDirectory=None,
                snapshotDirectory=None,
                suspendDirectory=None,
                vmPathName=datastore_path,
            )

            dev_changes = []

            # add pci controller
            pci_spec = vim.vm.device.VirtualDeviceSpec()
            pci_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            pci_spec.device = vim.vm.device.VirtualPCIController()
            pci_spec.device.key = 100
            dev_changes.append(pci_spec)

            # add scsi controller
            scsi_spec = vim.vm.device.VirtualDeviceSpec()
            scsi_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            scsi_spec.device = vim.vm.device.ParaVirtualSCSIController()
            scsi_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing
            scsi_spec.device.key = 5000
            dev_changes.append(scsi_spec)

            # add disk
            disk_type = "thin"
            new_disk_kb = disk_size_gb * 1024 * 1024
            disk_spec = vim.vm.device.VirtualDeviceSpec()
            disk_spec.fileOperation = "create"
            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            disk_spec.device = vim.vm.device.VirtualDisk()
            disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            if disk_type == "thin":
                disk_spec.device.backing.thinProvisioned = True
            disk_spec.device.backing.diskMode = "persistent"
            disk_spec.device.unitNumber = 0
            disk_spec.device.capacityInKB = new_disk_kb
            disk_spec.device.controllerKey = scsi_spec.device.key
            dev_changes.append(disk_spec)

            dev_spec = vim.vm.device.VirtualDeviceSpec()
            dev_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            dev_spec.device = vim.vm.device.VirtualCdrom()
            dev_spec.device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
            dev_spec.device.controllerKey = 200  # ide_spec.device.key
            dev_changes.append(dev_spec)

            # add network card
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            nic_spec.device = vim.vm.device.VirtualVmxnet3()
            nic_spec.device.addressType = "Generated"
            nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            nic_spec.device.backing.port = vim.dvs.PortConnection()
            nic_spec.device.backing.port.portgroupKey = network.key
            nic_spec.device.backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid
            nic_spec.device.wakeOnLanEnabled = False
            dev_changes.append(nic_spec)

            config = vim.vm.ConfigSpec(
                name=name,
                memoryMB=memory_mb,
                numCPUs=cpu,
                numCoresPerSocket=core_x_socket,
                deviceChange=dev_changes,
                files=vmx_file,
                guestId=guest_id,
                version=version,
            )

            if resource_pool is None and cluster is not None:
                resource_pool = cluster.resourcePool

            task = folder.CreateVM_Task(config=config, pool=resource_pool)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def create_from_library(self):
        """"""
        pass

    def create_linked_clone(
        self,
        server,
        name,
        folder,
        datastore,
        power_on=False,
        resource_pool=None,
        cluster=None,
    ):
        """Clone a linked clone VirtualMachine from another.
        Ref: http://pubs.vmware.com/vsphere-60/index.jsp#com.vmware.wssdk.pg.doc/PG_VM_Manage.13.4.html#1115589
        https://www.vmware.com/support/ws55/doc/ws_clone_template_enabling.html

        :param name: String Name for the VirtualMachine
        :param folder: Folder to place the VirtualMachine in
        :param resource_pool: ResourcePool to place the VirtualMachine in [optional]
        :param cluster: cluster to place the VirtualMachine in [optional]
        :param server: parent VirtualMachine
        :param power_on: power_on status [defualt=False]
        """
        try:
            if resource_pool is None and cluster is not None:
                resource_pool = cluster.resourcePool

            # set relospec
            relospec = vim.vm.RelocateSpec()
            relospec.diskMoveType = vim.vm.RelocateSpec.DiskMoveOptions.createNewChildDiskBacking
            relospec.datastore = datastore
            relospec.pool = resource_pool

            clonespec = vim.vm.CloneSpec()
            clonespec.location = relospec
            clonespec.powerOn = power_on
            clonespec.memory = False
            clonespec.template = False
            clonespec.snapshot = server.snapshot.currentSnapshot

            task = server.CloneVM_Task(folder=folder, name=name, spec=clonespec)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def create_from_template(
        self,
        template,
        name,
        folder,
        datastore,
        power_on=False,
        resource_pool=None,
        cluster=None,
        *args,
        **kvargs,
    ):
        """Creates a VirtualMachine from template.

        :param name: String Name for the VirtualMachine
        :param folder: Folder to place the VirtualMachine in
        :param resource_pool: ResourcePool to place the VirtualMachine in [optional]
        :param cluster: cluster to place the VirtualMachine in [optional]
        :param template: template VirtualMachine
        :param network: Network to attach
        :param version: vmx-8 , vmx-9, vmx-10, vmx-11
        :param power_on: power_on status [defualt=False]
        """
        try:
            if resource_pool is None and cluster is not None:
                resource_pool = cluster.resourcePool

            # set relospec
            relospec = vim.vm.RelocateSpec()
            relospec.datastore = datastore
            relospec.pool = resource_pool

            clonespec = vim.vm.CloneSpec()
            clonespec.location = relospec
            clonespec.powerOn = power_on

            task = template.Clone(folder=folder, name=name, spec=clonespec)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def create_from_template_library(self):
        """"""
        pass

    def create_from_template_with_customization(
        self,
        template,
        name,
        folder,
        datastore,
        guest_host_name,
        guest_admin_pwd,
        power_on=True,
        resource_pool=None,
        cluster=None,
        customization_spec_name=None,
        network_config={},
        **kwargs,
    ):
        """Creates a VirtualMachine from template.

        :param template: template where to clone from
        :param name: String Name for the VirtualMachine
        :param folder: Folder to place the VirtualMachine in
        :param datastore:
        :param guest_host_name: hostname of the guest vm
        :param guest_admin_pwd: administrator password of the guest vm
        :param power_on:
        :param resource_pool: ResourcePool to place the VirtualMachine in [optional]
        :param cluster: cluster to place the VirtualMachine in [optional]
        :param customization_spec_name: customization name to use
        :param network_config: Network parameters to use {"ip_address":"192.168.216.120",
                                                          "ip_netmask":"255.255.255.0",
                                                          "ip_gateway":"192.168.216.1",
                                                          "dns_server_list":"['10.103.48.1', '10.103.48.2']",
                                                          "dns_domain":"tenant-demo.site03.nivolapiemonte.csi.it"}
        """
        if guest_host_name is None and guest_admin_pwd is None:
            raise VsphereError("host_name and admim_pwd cannot be Null")

        # self.manager.si.content
        mycust = self.manager.si.content.customizationSpecManager.GetCustomizationSpec(customization_spec_name)

        # by miko: adapter
        adaptermap = vim.vm.customization.AdapterMapping()
        adaptermap.adapter = vim.vm.customization.IPSettings()
        adaptermap.adapter.ip = vim.vm.customization.FixedIp()
        adaptermap.adapter.ip.ipAddress = network_config["ip_address"]
        adaptermap.adapter.subnetMask = network_config["ip_netmask"]
        adaptermap.adapter.gateway = network_config["ip_gateway"]
        adaptermap.adapter.dnsServerList = network_config["dns_server_list"]
        adaptermap.adapter.dnsDomain = network_config["dns_domain"]

        # by miko: guest name & password
        mycust.spec.identity.userData.computerName.name = guest_host_name

        mycust.spec.identity.guiUnattended.password.plainText = True
        mycust.spec.identity.guiUnattended.password.value = guest_admin_pwd

        # by miko: adding network conf
        mycust.spec.nicSettingMap[0].adapter = adaptermap.adapter

        try:
            if resource_pool is None and cluster is not None:
                resource_pool = cluster.resourcePool

            # set relospec
            relospec = vim.vm.RelocateSpec()
            relospec.datastore = datastore
            relospec.pool = resource_pool

            # This constructs the clone specification and adds the customization spec and location spec to it
            clonespec = vim.vm.CloneSpec(
                powerOn=power_on,
                template=False,
                location=relospec,
                customization=mycust.spec,
            )

            # clonespec = vim.vm.CloneSpec()
            # clonespec.location = relospec
            # clonespec.powerOn = power_on

            # TO DO: verificare che il datastore e il dvpg siano coerenti col cluster di destinazione

            task = template.Clone(folder=folder, name=name, spec=clonespec)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def customize(
        self,
        server,
        customization_spec_name,
        guest_host_name,
        guest_admin_pwd,
        network_config,
    ):
        """Apply a customization to a VirtualMachine.

        :param server: server object
        :param guest_host_name: hostname of the guest vm
        :param guest_admin_pwd: administrator password of the guest vm
        :param customization_spec_name: customization name to use
        :param network_config: Network parameters to use {"ip_address":"192.168.216.120",
                                                          "ip_netmask":"255.255.255.0",
                                                          "ip_gateway":"192.168.216.1",
                                                          "dns_server_list":"['10.103.48.1', '10.103.48.2']",
                                                          "dns_domain":"tenant-demo.site03.nivolapiemonte.csi.it"}
        """
        if guest_host_name is None or guest_admin_pwd is None:
            raise VsphereError("host_name or admim_pwd cannot be Null")

        try:
            # self.manager.si.content
            cust = self.manager.si.content.customizationSpecManager.GetCustomizationSpec(customization_spec_name)

            # by miko: adapter
            adaptermap = vim.vm.customization.AdapterMapping()
            adaptermap.adapter = vim.vm.customization.IPSettings()
            adaptermap.adapter.ip = vim.vm.customization.FixedIp()
            adaptermap.adapter.ip.ipAddress = network_config["ip_address"]
            adaptermap.adapter.subnetMask = network_config["ip_netmask"]
            adaptermap.adapter.gateway = network_config["ip_gateway"]
            adaptermap.adapter.dnsServerList = network_config["dns_server_list"]
            adaptermap.adapter.dnsDomain = network_config["dns_domain"]

            # by miko: guest name & password
            cust.spec.identity.userData.computerName.name = guest_host_name

            cust.spec.identity.guiUnattended.password.plainText = True
            cust.spec.identity.guiUnattended.password.value = guest_admin_pwd

            # by miko: adding network conf
            cust.spec.nicSettingMap[0].adapter = adaptermap.adapter

            self.logger.debug2(cust)

            task = server.CustomizeVM_Task(spec=cust.spec)
            self.logger.debug("Start reconfigure server %s" % server.config.name)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def reconfigure(self, server, network, net_number=1, disks=[], *args, **kvargs):
        """Change server configuration

        :param server: server object
        :param network: network info
        :param net_number: network device number [default=1]
        :param disks: server additional disks. List of
            {'type': 'main|secondary', 'name':.., 'size':.., 'thin': False, 'datastore':..} [optional]
        :param memoryMB: ram size in MByte [optional]
        :param numCPUs: number of cpu [optional]
        :param numCoresPerSocket: number if core per socket [optional]
        :param version: virtual machine vsphere version [optional]
        :param guest_id: guest id [optional]
        :return:
        """
        try:
            dev_changes = []

            # todo: detach cdrom if attached to file iso

            # configure network
            if network is not None:
                # check network already attached
                net_label = "Network adapter %s" % net_number
                virtual_net_device = None
                for dev in server.config.hardware.device:
                    if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.label == net_label:
                        virtual_net_device = dev

                if virtual_net_device is not None:
                    # configure existing network device
                    nic_spec = vim.vm.device.VirtualDeviceSpec()
                    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                    nic_spec.device = virtual_net_device

                    nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                    nic_spec.device.backing.port = vim.dvs.PortConnection()
                    nic_spec.device.backing.port.portgroupKey = network.key
                    nic_spec.device.backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid

                    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
                    nic_spec.device.connectable.startConnected = True
                    nic_spec.device.connectable.connected = True
                    nic_spec.device.connectable.allowGuestControl = True

                    nic_spec.device.wakeOnLanEnabled = False
                    dev_changes.append(nic_spec)
                    self.logger.debug(
                        "Configure new network device %s to server %s" % (network.key, server.config.name)
                    )
                else:
                    # add new network device
                    nic_spec = vim.vm.device.VirtualDeviceSpec()
                    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                    nic_spec.device = vim.vm.device.VirtualVmxnet3()
                    nic_spec.device.addressType = "Generated"

                    nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                    nic_spec.device.backing.port = vim.dvs.PortConnection()
                    nic_spec.device.backing.port.portgroupKey = network.key
                    nic_spec.device.backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid

                    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
                    nic_spec.device.connectable.startConnected = True
                    nic_spec.device.connectable.connected = True
                    nic_spec.device.connectable.allowGuestControl = True

                    nic_spec.device.wakeOnLanEnabled = False
                    dev_changes.append(nic_spec)
                    self.logger.debug("Add new network device %s to server %s" % (network.key, server.config.name))

            main_disk = None

            if len(disks) > 0:
                # get all disks on a VM, set unit_number to the next available
                for dev in server.config.hardware.device:
                    if hasattr(dev.backing, "fileName"):
                        unit_number = int(dev.unitNumber) + 1

                    if isinstance(dev, vim.vm.device.VirtualSCSIController):
                        controller = dev

                    if isinstance(dev, vim.vm.device.VirtualDisk) and dev.deviceInfo.label == "Hard disk 1":
                        main_disk = dev

            for disk in disks:
                disk_type = disk.get("type", "secondary")

                # add new disk
                if disk_type == "secondary":
                    # unit_number 7 reserved for scsi controller
                    if unit_number == 7:
                        unit_number += 1
                    if not self.is_scsi_unit_number_free(server, unit_number):
                        self.raise_too_many_disk()
                    # add disk here
                    new_disk_kb = int(disk.get("size")) * 1024 * 1024
                    disk_spec = vim.vm.device.VirtualDeviceSpec()
                    disk_spec.fileOperation = "create"
                    disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                    disk_spec.device = vim.vm.device.VirtualDisk()
                    disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
                    if disk.get("thin", False) is True:
                        disk_spec.device.backing.thinProvisioned = True
                    disk_spec.device.backing.datastore = disk.get("datastore")
                    disk_spec.device.backing.diskMode = "persistent"
                    disk_spec.device.unitNumber = unit_number
                    disk_spec.device.capacityInKB = new_disk_kb
                    disk_spec.device.controllerKey = controller.key
                    dev_changes.append(disk_spec)
                    self.logger.debug(
                        "Add new disk of % GB, datastore %s, to server %s"
                        % (new_disk_kb, disk.get("datastore"), server.config.name)
                    )

                # reconfigure main disk
                elif disk_type == "main":
                    new_disk_kb = int(disk.get("size")) * 1024 * 1024
                    disk_spec = vim.vm.device.VirtualDeviceSpec()
                    disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                    disk_spec.device = main_disk
                    disk_spec.device.capacityInKB = new_disk_kb
                    dev_changes.append(disk_spec)
                    self.logger.debug("Change main disk size to % GB for server %s" % (new_disk_kb, server.config.name))

            config = vim.vm.ConfigSpec(deviceChange=dev_changes, **kvargs)

            self.logger.debug2(dev_changes)

            task = server.ReconfigVM_Task(spec=config)
            self.logger.debug("Start reconfigure server %s" % server.config.name)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def get_server_virtual_hw_version(self, server):
        guest = server.guest
        hw_version_str = guest.hwVersion
        hw_version = None
        if hw_version_str[0:4] == "vmx-":
            hw_version_str_num = hw_version_str[4:]
            try:
                hw_version = float(hw_version_str_num)
            except:
                pass
        return hw_version

    def get_server_scsi_devs_per_bus(self, server):
        hw_version_to_scsi_devs_per_bus = [(14, 64), (0, 16)]
        hw_version = self.get_server_virtual_hw_version(server)
        scsi_devs_per_bus = 16
        for version, scsi_devs_per_bus in self.hw_version_to_scsi_devs_per_bus:
            if hw_version is not None and hw_version >= version:
                return scsi_devs_per_bus
        return scsi_devs_per_bus

    def get_max_scsi_devs_per_bus(self):
        return self.hw_version_to_scsi_devs_per_bus[0][0]

    def raise_too_many_disk(self):
        max_devs_per_bus = self.get_max_scsi_devs_per_bus()
        max_hw_version = self.get_max_hw_version()
        msg = "Too many disks configured; "
        "please udgrade Virtual Hardware to version %s or higher " "to support up to %s disks" % (
            max_hw_version,
            max_devs_per_bus,
        )
        raise VsphereError("Too many disks configured")

    def get_max_hw_version(self):
        return self.hw_version_to_scsi_devs_per_bus[0][1]

    def is_scsi_unit_number_free(self, server, unit_number):
        devs_per_bus = self.get_server_scsi_devs_per_bus(server)
        if unit_number >= devs_per_bus:
            return False
        return True

    def get_available_hard_disk_unit_number(self, server):
        """Get available hard disk unit number

        :param server: server instance
        :return: unit_number
        """
        # get all disks on a VM, set unit_number to the next available
        unit_numbers = []
        for dev in server.config.hardware.device:
            if hasattr(dev.backing, "fileName"):
                unit_numbers.append(int(dev.unitNumber))

        # find missing unit numbers if there are any
        unit_numbers = sorted(unit_numbers)
        missings = [n for n in range(unit_numbers[0], unit_numbers[-1] + 1) if n not in unit_numbers and n != 7]
        if len(missings) > 0:
            unit_number = min(missings)
        else:
            unit_number = max(unit_numbers) + 1

        # unit_number 7 reserved for scsi controller
        if unit_number == 7:
            unit_number += 1
        if not self.is_scsi_unit_number_free(server, unit_number):
            self.raise_too_many_disk()

        return unit_number

    def update(self, server, name=None, notes=None):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            spec = vim.vm.ConfigSpec()
            if notes is not None:
                spec.annotation = notes
            if name is not None:
                spec.name = name

            task = server.ReconfigVM_Task(spec)
            self.logger.debug("Update server %s in vSphere" % server)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def remove(self, server):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.Destroy_Task()
            self.logger.debug("Destroying server %s from vSphere" % server)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    #
    # summary
    #
    def data(self, server):
        try:
            server.config
            return self.detail(server)
        except Exception as error:
            self.logger.error(error, exc_info=True)
            return self.info(server)

    def info(self, server):
        """Get server info

        :param server: server object obtained from api request
        :return: dict like

            {
                'cpu': 2,
                'hostname': 'tst-beehive-04',
                'id': 'vm-2287',
                'ip_address': ['10.102.184.54'],
                'memory': 2048,
                'name': 'tst-beehive-04',
                'os': 'CentOS 4/5/6/7(64-bit)',
                'state': 'poweredOn',
                'template': False,
                'disk': None,
                'disks': []
            }
        """
        try:
            if type(server) == dict:
                layout_ex_files = get_attrib(server, "layoutEx.file", [])
                # sum volumes in bytes and convert Gb
                disk_tot = sum(d.size for d in layout_ex_files if d.type == "diskExtent") / 1073741824
                # get nets ipv4
                net_ipv4s = [n for n in get_attrib(server, "guest.net", []) if "." in n.ipAddress]
                data = {
                    "id": server.get("obj")._moId,
                    "parent": server.get("parent")._moId,
                    "name": get_attrib(server, "name", ""),
                    "os": get_attrib(server, "config.guestFullName", ""),
                    "ram": get_attrib(server, "config.hardware.memoryMB", ""),
                    "cpu": get_attrib(server, "config.hardware.numCPU", ""),
                    "state": get_attrib(server, "runtime.powerState", ""),
                    "template": get_attrib(server, "config.template", ""),
                    "hostname": get_attrib(server, "guest.hostName", ""),
                    "ip_address": [get_attrib(server, "guest.ipAddress", "")],
                    "ipv4_address": net_ipv4s,
                    "disk": disk_tot,
                    "disks": [],
                }
            else:
                layout_ex_files = server.layoutEx.file
                # sum volumes in bytes and convert Gb
                disk_tot = sum(d.size for d in layout_ex_files if d.type == "diskExtent") / 1073741824
                # get nets ipv4
                net_ipv4s = [n for n in server.guest.net if "." in n.ipAddress]
                data = {
                    "id": server._moId,
                    "parent": server.parent._moId,
                    "name": server.name,
                    "os": server.config.guestFullName,
                    "ram": server.config.hardware.memoryMB,
                    "cpu": server.config.hardware.numCPU,
                    "state": server.runtime.powerState,
                    "template": server.config.template,
                    "hostname": server.guest.hostName,
                    "ip_address": server.guest.ipAddress,
                    "ipv4_address": net_ipv4s,
                    "disk": disk_tot,
                    "disks": [],
                }
        except Exception as error:
            self.logger.error(error, exc_info=True)
        return data

    def detail(self, server):
        """Get server detail

        :param server: server object
        :return: dict like

            {'date': {'created': None, 'launched': '2017-03-10T17:49:39', 'terminated': None, 'updated': None},
             'flavor': {'cpu': 4, 'id': None, 'memory': 2048},
             'hostname': 'prova01',
             'id': 'vim.VirtualMachine:vm-2739',
             'metadata': None,
             'name': 'instance04-server',
             'networks': [{'dns': ['10.102.184.2', '10.102.184.3'],
                            'fixed_ips': '10.102.184.55',
                            'mac_addr': '00:50:56:a1:55:4e',
                            'name': 'Network adapter 1',
                            'net_id': 'dvportgroup-82',
                            'port_state': True}],
             'os': 'CentOS 4/5/6/7(64-bit)',
             'state': 'poweredOn',
             'volumes': [{'bootable': None,
                           'format': None,
                           'id': '[DS_EX_OPSTK_VSP_LUN_00] instance04-server/instance04-server.vmdk',
                           'mode': 'persistent',
                           'name': 'Hard disk 1',
                           'size': 50.0,
                           'storage': 'DS_EX_OPSTK_VSP_LUN_00',
                           'type': None}],
             'vsphere:firmware': 'bios',
             'vsphere:linked': {'linked': False, 'parent': None},
             'vsphere:managed': None,
             'vsphere:notes': '',
             'vsphere:template': False,
             'vsphere:tools': {'status': 'guestToolsRunning', 'version': '10246'},
             'vsphere:uuid': '5021ebf0-a489-6876-a94c-ac58d9d02fed',
             'vsphere:vapp': None,
             'vsphere:version': 'vmx-11'}
        """
        try:
            server_volumes = []
            networks = []

            vm = server
            hw = server.config.hardware

            # get nets ip and order by mac address
            nets = vm.guest.net

            net_ips = {}
            for net in nets:
                net_ips[net.macAddress] = net.ipAddress

            for device in hw.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    mac = device.macAddress
                    try:
                        fixed_ipv4s = net_ips.get(mac, [""])[0]
                    except:
                        fixed_ipv4s = []
                    try:
                        fixed_ipv6s = net_ips.get(mac, ["", ""])[1]
                    except:
                        fixed_ipv6s = []
                    net = {
                        "name": device.deviceInfo.label,
                        "mac_addr": device.macAddress,
                        "fixed_ips": vm.guest.ipAddress,
                        "fixed_ipv4s": fixed_ipv4s,
                        "fixed_ipv6s": fixed_ipv6s,
                        "dns": None,
                        "net_id": None,
                        "port_state": device.connectable.connected,
                    }

                    if hasattr(device.backing, "port"):
                        port_group_ext_id = device.backing.port.portgroupKey
                        net["net_id"] = port_group_ext_id
                    else:
                        net_ext_id = device.backing.network._moId
                        net["net_id"] = net_ext_id

                    try:
                        self.check_guest_tools(vm)

                        for conf in vm.guest.ipStack:
                            net["dns"] = [ip for ip in conf.dnsConfig.ipAddress if ip != "127.0.0.1"]
                    except Exception as ex:
                        pass

                    networks.append(net)

                elif isinstance(device, vim.vm.device.VirtualDisk):
                    backing = device.backing
                    vol = {
                        "bootable": None,
                        "format": None,
                        "id": backing.fileName,
                        "disk_object_id": device.diskObjectId,
                        "mode": backing.diskMode,
                        "name": device.deviceInfo.label,
                        "size": round(device.capacityInBytes / 1073741824, 0),
                        "storage": None,
                        "slot_info": device.slotInfo,
                        "unit_number": device.unitNumber,
                        "type": backing.__class__.__name__,
                        "backing_uuid": backing.uuid,
                        "v_disk_id": device.vDiskId,
                    }
                    if hasattr(backing, "thinProvisioned"):
                        vol["thin"] = backing.thinProvisioned

                    datastore = backing.datastore
                    if datastore is not None:
                        vol["storage"] = datastore.name
                    server_volumes.append(vol)

            try:
                launched = ensure_text(vm.runtime.bootTime.strftime("%Y-%m-%dT%H:%M:%S"))
            except:
                traceback.print_exc()
                launched = None

            info = {
                "id": server._moId,
                "parent": server.parent._moId,
                "name": server.name,
                "overallStatus": server.overallStatus,
                "hostname": server.guest.hostName,
                "os": vm.summary.config.guestFullName,
                "state": vm.runtime.powerState,
                "flavor": {
                    "id": None,
                    "memory": hw.memoryMB,
                    "cpu": int(hw.numCPU) * int(hw.numCoresPerSocket),
                },
                "networks": networks,
                "volumes": server_volumes,
                "date": {
                    "created": None,
                    "updated": None,
                    "launched": launched,
                    "terminated": None,
                },
                "metadata": None,
                "vsphere:version": vm.config.version,
                "vsphere:firmware": vm.config.firmware,
                "vsphere:template": vm.config.template,
                "vsphere:uuid": vm.config.instanceUuid,
                "vsphere:managed": vm.config.managedBy,
                "vsphere:tools": {
                    "status": vm.guest.toolsRunningStatus,
                    "version": vm.guest.toolsVersion,
                },
                "vsphere:notes": vm.config.annotation,
                "vsphere:vapp": None,
                "vsphere:linked": self.is_linked_clone(server),
            }

            # vapp info
            if vm.parentVApp is not None:
                info["vsphere:vapp"] = {
                    "ext_id": vm.parentVApp._moId,
                    "name": vm.parentVApp.name,
                }
        except Exception as error:
            self.logger.error(error, exc_info=True)
            info = {}

        return info

    def is_running(self, server):
        """Return True if server is running"""
        status = self.info(server).get("state")
        if status is not None and status == "poweredOn":
            return True
        else:
            return False

    def is_linked_clone(self, server):
        """Check if virtual machine is a linked clone and return parent
        virtual machine

        :param server: server instance
        :return: dictionary with linked clone check and linked server name
        """
        name = server.name
        linked = False
        linked_server = None
        for item in server.layoutEx.file:
            # checK if server contain backing file
            if not item.name.find(name) >= 0:
                linked = True
                # get parent server name
                start = item.name.index("] ") + 2
                end = item.name.index("/", start)
                linked_server = item.name[start:end]

        return {"linked": linked, "parent": linked_server}

    def guest_info(self, server):
        """Server guest info"""
        try:
            vm = server.guest

            info = {
                "hostname": vm.hostName,
                "ip_address": vm.ipAddress,
                "tools": {
                    "status": vm.toolsStatus,
                    "version_status": vm.toolsVersionStatus,
                    "version_status2": vm.toolsVersionStatus2,
                    "running_status": vm.toolsRunningStatus,
                    "version": vm.toolsVersion,
                },
                "guest": {
                    "id": vm.guestId,
                    "family": vm.guestFamily,
                    "fullname": vm.guestFullName,
                    "state": vm.guestState,
                    "app_heartbeat_status": vm.appHeartbeatStatus,
                    "guest_kernel_crashed": vm.guestKernelCrashed,
                    "app_state": vm.appState,
                    "operations_ready": vm.guestOperationsReady,
                    "interactive_operations_ready": vm.interactiveGuestOperationsReady,
                    "state_change_supported": vm.guestStateChangeSupported,
                    "generation_info": vm.generationInfo,
                },
                "ip_stack": [],
                "nics": [],
                "disk": [],
                "screen": {"width": vm.screen.width, "height": vm.screen.height},
            }

            for conf in vm.disk:
                info["disk"].append(
                    {
                        "diskPath": conf.diskPath,
                        "capacity": "%sMB" % (conf.capacity / 1048576),
                        "free_space": "%sMB" % (conf.freeSpace / 1048576),
                    }
                )

            for conf in vm.ipStack:
                info["ip_stack"].append(
                    {
                        "dns_config": {
                            "dhcp": conf.dnsConfig.dhcp,
                            "hostname": conf.dnsConfig.hostName,
                            "domainname": conf.dnsConfig.domainName,
                            "ip_address": [ip for ip in conf.dnsConfig.ipAddress],
                            "search_domain": [c for c in conf.dnsConfig.searchDomain],
                        },
                        "ip_route_config": [
                            {
                                "network": "%s/%s" % (c.network, c.prefixLength),
                                "gateway": c.gateway.ipAddress,
                            }
                            for c in conf.ipRouteConfig.ipRoute
                        ],
                        "ipStackConfig": [i for i in conf.ipStackConfig],
                        "dhcpConfig": conf.dhcpConfig,
                    }
                )

            for nic in vm.net:
                info["nics"].append(
                    {
                        "network": nic.network,
                        "mac_address": nic.macAddress,
                        "connected": nic.connected,
                        "device_config_id": nic.deviceConfigId,
                        "dnsConfig": nic.dnsConfig,
                        "ip_config": {
                            "dhcp": nic.ipConfig.dhcp,
                            "ip_address": ["%s/%s" % (i.ipAddress, i.prefixLength) for i in nic.ipConfig.ipAddress],
                        },
                        "netbios_config": nic.netBIOSConfig,
                    }
                )

        except Exception as error:
            self.logger.error(error, exc_info=True)
            info = {}

        return info

    def network(self, server):
        """Server network"""
        res = []
        for n in server.network:
            try:
                nid = self.container.get_networks(ext_id=n._moId)[0].oid
            except:
                nid = None
            res.append({"id": n._moId, "name": n.name, "type": type(n).__name__})
        return res

    def volumes(self, server):
        """get server volumes

        :param server: server object
        :return: list of server volumes
        """
        server_volumes = []

        try:
            hw = server.config.hardware

            for device in hw.device:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    backing = device.backing
                    vol = {
                        "bootable": None,
                        "format": None,
                        "id": backing.fileName,
                        "disk_object_id": device.diskObjectId,
                        "mode": backing.diskMode,
                        "name": device.deviceInfo.label,
                        "size": round(device.capacityInBytes / 1073741824, 0),
                        "storage": None,
                        "unit_number": device.unitNumber,
                        "type": None,
                    }

                    if hasattr(backing, "thinProvisioned"):
                        vol["thin"] = backing.thinProvisioned

                    datastore = device.backing.datastore
                    if datastore is not None:
                        vol["storage"] = datastore.name
                    server_volumes.append(vol)
        except Exception as error:
            self.logger.error(error, exc_info=True)

        return server_volumes

    def runtime(self, server):
        """Server runtime info"""
        try:
            vm = server.runtime

            res = {
                "boot_time": vm.bootTime,
                "resource_pool": {
                    "id": server.resourcePool._moId,
                    "name": server.resourcePool.name,
                },
                "host": {
                    "id": vm.host._moId,
                    "name": vm.host.name,
                    "parent_id": vm.host.parent._moId,
                    "parent_name": vm.host.parent.name,
                },
            }
        except Exception as error:
            self.logger.error(error, exc_info=True)
            res = {}

        return res

    def usage(self, server):
        """Cpu, memory, storage usage"""
        try:
            res = server.summary.quickStats
        except Exception as error:
            self.logger.error(error, exc_info=True)
            res = {}

        return res

    def security_tags(self):
        """ """
        pass

    def security_groups(self, server):
        """List server security groups

        :param moid: server morid
        """
        vmid = server._moId
        res = self.call("/api/2.0/services/securitygroup/lookup/virtualmachine/%s" % vmid, "GET", "")
        self.logger.debug(truncate(res))
        res = res["securityGroups"]["securityGroups"]
        if res is None:
            return []
        else:
            return res.get("securitygroup")

    def security_group_add(self, server, security_group):
        """Add security group to server

        :param moid: server morid
        :param security_group: security group id
        """
        res = self.call(
            "/api/2.0/services/securitygroup/%s/members/%s" % (security_group, server),
            "PUT",
            "",
            timeout=600,
        )
        self.logger.debug(truncate(res))
        return True

    def security_group_del(self, server, security_group):
        """Remove security group from server

        :param moid: server morid
        :param security_group: security group id
        """
        res = self.call(
            "/api/2.0/services/securitygroup/%s/members/%s" % (security_group, server),
            "DELETE",
            "",
            timeout=600,
        )
        self.logger.debug(truncate(res))
        return True

    def advanced_configuration(self):
        """ """
        pass

    def related_objects(self):
        """Cluster, host, networks, storage"""
        pass

    def vapp_details(self):
        """ """
        pass

    #
    # remote console
    #
    def get_console_esxi_uri(self, server):
        """Get server remote console on esxi

        :param server: server instance
        :return:
        """
        data = server.AcquireTicket("webmks")

        res = {
            "ticket": data.ticket,
            "cfgFile": data.cfgFile,
            "host": data.host,
            "port": data.port,
            "sslThumbprint": data.sslThumbprint,
            "uri": "wss://%s:%s/ticket/%s" % (data.host, data.port, data.ticket),
        }

        return res

    def remote_console(self, server, to_host=True, to_vcenter=False):
        """Get server remote console

        :param server: server instance
        :param to_host: if True open ticket and session over esxi host
        :param to_vcenter: if True open ticket and session over esxi host
        """
        try:
            content = self.manager.si.RetrieveContent()

            vm = server
            vm_moid = vm._moId

            vcenter_data = content.setting
            vcenter_settings = vcenter_data.setting

            for item in vcenter_settings:
                key = getattr(item, "key")
                if key == "VirtualCenter.FQDN":
                    vcenter_fqdn = getattr(item, "value")

            session_manager = content.sessionManager
            ticket = session_manager.AcquireCloneTicket()

            host = self.manager.vcenter_conn["host"]
            port = self.manager.vcenter_conn["port"]
            vc_cert = ssl.get_server_certificate((host, port))
            vc_pem = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, vc_cert)
            vc_fingerprint = vc_pem.digest("sha1")

            uri = [
                "https://%s:%s/ui/webconsole.html?",
                "vmId=%s&vmName=%s&host=%s:%s&sessionTicket=%s",
                "&thumbprint=%s",
                "&serverGuid=&locale=it-IT",
            ]
            uri = "".join(uri) % (
                host,
                port,
                vm_moid,
                server.name,
                host,
                port,
                ticket,
                vc_fingerprint,
            )

            self.logger.debug("Get remote console for server %s" % server.name)
            return {"type": "webconsole", "url": uri}
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    #
    # guest access
    #
    def check_guest_tools(self, server):
        """Check if guest tool is running. Raise exception if tool is not running"""
        # get guest tools status
        tools_status = server.guest.toolsRunningStatus
        if tools_status == "guestToolsNotRunning":
            raise vmodl.MethodFault(
                msg="VMwareTools is either not running or not installed. Rerun the script after "
                "verifying that VMwareTools is running"
            )

    def guest_tools_is_running(self, server):
        """Check if guest tool is running

        :return: True if guest tools are running
        """
        # get guest tools status
        tools_status = server.guest.toolsRunningStatus
        if tools_status == "guestToolsNotRunning" or tools_status == "guestToolsExecutingScripts":
            return False
        elif tools_status == "guestToolsRunning":
            return True

    def wait_guest_tools_is_running(self, server, delta=2, maxtime=180):
        """Wait until guest tool is not running. After maxtime an exception is raised.

        :param server:
        :param delta:
        :param maxtime:
        :param sleep:
        :return:
        """
        # wait until guest tools are running
        elapsed = 0
        status = self.guest_tools_is_running(server)
        while status is not True:
            status = self.guest_tools_is_running(server)
            # sleep a little
            time.sleep(delta)
            elapsed += delta
            self.logger.debug("Wait guest tools is running")
            if elapsed > maxtime:
                raise VsphereError("Guest tools are not still running after %s s" % maxtime)

    def wait_guest_hostname_is_set(self, server, hostname, delta=2, maxtime=180):
        """Wait until guest guest hostname is set. After maxtime an exception is raised.

        :param server:
        :param hostname:
        :param delta:
        :param maxtime:

        :return:
        """
        # wait until guest tools are running
        elapsed = 0

        while server.guest.hostName != hostname:
            time.sleep(delta)
            elapsed += delta
            self.logger.debug("Wait during setting guest hostname:%s with %s" % (server.guest.hostName, hostname))
            if elapsed > maxtime:
                self.logger.error("setting guest hostname take too long; exceded maxtime of %s s" % maxtime)
                raise VsphereError("setting guest hostname take too long; exceded maxtime of %s s" % maxtime)

    def check_exit_command(self, pid_exitcode, pid, program, check_status_code):
        """Check process exit code

        :param pid_exitcode:
        :param pid:
        :param program:
        :param check_status_code:
        :return:
        :raise VsphereError:
        """
        if check_status_code is True:
            if pid_exitcode == 0:
                self.logger.debug('Command "%s" completed with success, PID is %d' % (program, pid))
                return True
            # Look for non-zero code to fail
            elif pid_exitcode > 0 or pid_exitcode < 0:
                self.logger.error('Command "%s" completed with failure, PID is %d' % (program, pid))
                raise VsphereError(
                    'Command "%s", PID %s exit with wrong status code: %s' % (program, pid, pid_exitcode)
                )
        else:
            self.logger.warning('Command "%s" completed with status code: %s, PID is %d' % (program, pid_exitcode, pid))
            return True

    def guest_execute_command(
        self,
        server,
        user,
        pwd,
        path_to_program="/bin/cat",
        program_arguments="/etc/network/interfaces",
        maxtime=90,
        delta=2,
        program="",
        check_status_code=True,
    ):
        """Execute a command over the server using guest tool

        :param server: server instance
        :param user: user used to autenticate
        :param pwd: user password
        :param path_to_program: path to command to execute
        :param program_arguments: command arguments
        :param maxtime: max time in second you attend guest tools finish to run command. After that time an error is
            rised [default=60]
        :param delta: interval in seconds between a check and the last cechk of the process status [default=6]
        :param program: program description
        :param check_status_code: if True check exit status code
        :return:
        """
        self.check_guest_tools(server)

        try:
            content = self.manager.si.RetrieveContent()
            creds = vim.vm.guest.NamePasswordAuthentication(username=user, password=pwd)
            pm = content.guestOperationsManager.processManager
            ps = vim.vm.guest.ProcessManager.ProgramSpec(programPath=path_to_program, arguments=program_arguments)
            pid = pm.StartProgramInGuest(server, creds, ps)
            pids = [pid]

            if pid > 0:
                self.logger.debug('Command "%s" submitted, PID is %d' % (program, pid))
                proc_info = pm.ListProcessesInGuest(server, creds, pids=pids).pop()
                self.logger.debug2(proc_info)
                pid_exitcode = proc_info.exitCode
                pid_endtime = proc_info.endTime

                # If its not a numeric result code, it says None on submit
                elapsed = 0
                while pid_endtime is None:
                    self.logger.debug('Command "%s" running, PID is %d' % (program, pid))
                    time.sleep(delta)
                    elapsed += delta

                    # check elapsed
                    if elapsed > maxtime:
                        pid_exitcode = 1000
                        pid_endtime = "1999"
                        self.logger.error('Command "%s" completed with timeout, PID is %d' % (program, pid))
                        break

                    # check process
                    try:
                        proc_info = pm.ListProcessesInGuest(server, creds, pids=pids).pop()
                        pid_exitcode = proc_info.exitCode
                        pid_endtime = proc_info.endTime
                    except:
                        pid_exitcode = 0
                        pid_endtime = "1999"

                self.check_exit_command(pid_exitcode, pid, program, check_status_code)
            return pid
        except IOError as error:
            self.logger.error(error)
            raise VsphereError(error)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)
        except VsphereError:
            raise

    def guest_is_windows(self, server):
        """Check if server family is windows using guest tool

        :param server: server instance
        :return: True or False
        """
        if server.summary.config.guestFullName.lower().find("window") >= 0:
            return True
        return False

    def guest_is_linux(self, server):
        """Check if server family is linux using guest tool

        :param server: server instance
        :return: True or False
        """
        if (
            server.summary.config.guestFullName.lower().find("linux") >= 0
            or server.summary.config.guestFullName.lower().find("centos") >= 0
            or server.summary.config.guestFullName.lower().find("ubuntu") >= 0
            or server.summary.config.guestFullName.lower().find("freebsd") >= 0
        ):
            return True
        return False

    def guest_is_centos(self, server):
        """Check if server family is linux centos using guest tool

        :param server: server instance
        :return: True or False
        """
        if server.summary.config.guestFullName.lower().find("centos") >= 0:
            return True
        return False

    def guest_is_oracle_linux(self, server):
        """Check if server family is oracle linux using guest tool

        :param server: server instance
        :return: True or False
        """
        if server.summary.config.guestFullName.lower().find("oracle") >= 0:
            return True
        return False

    def guest_is_ubuntu(self, server):
        """Check if server family is linux centos using guest tool

        :param server: server instance
        :return: True or False
        """
        if server.summary.config.guestFullName.lower().find("ubuntu") >= 0:
            return True
        return False

    def guest_is_freebsd(self, server):
        """Check if server family is linux centos using guest tool

        :param server: server instance
        :return: True or False
        """
        if server.summary.config.guestFullName.lower().find("freebsd") >= 0:
            return True
        return False

    def guest_is_redhat(self, server):
        """Check if server family is Red Hat Enterprise Linux using guest tool

        :param server: server instance
        :return: True or False
        """
        if server.summary.config.guestFullName.lower().find("red hat enterprise linux") >= 0:
            return True
        return False

    def guest_list_process(self, server, user, pwd, pids=None):
        """Get a list of active processes using guest tool

        :param server: server instance
        :param user: user used to autenticate
        :param pwd: user password
        :param pids: list of process id. [optional]
        """
        self.check_guest_tools(server)

        try:
            content = self.manager.si.RetrieveContent()
            creds = vim.vm.guest.NamePasswordAuthentication(username=user, password=pwd)
            pm = content.guestOperationsManager.processManager
            procs = pm.ListProcessesInGuest(server, creds, pids=pids)
            self.logger.warning("List of server %s processes: %s" % (server, procs))
            return procs
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    def guest_read_environment_variable(self, server, user, pwd):
        """Get a list of environemnt variable using guest tool

        :param server: server instance
        :param user: user used to autenticate
        :param pwd: user password
        """
        self.check_guest_tools(server)

        try:
            content = self.manager.si.RetrieveContent()
            creds = vim.vm.guest.NamePasswordAuthentication(username=user, password=pwd)
            pm = content.guestOperationsManager.processManager
            env = pm.ReadEnvironmentVariableInGuest(server, creds)
            self.logger.debug("List of server %s environment variables: %s" % (server, env))
            return env
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    def guest_disable_firewall(self, server, pwd, user="administrator"):
        """Disable firewall

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :return:
        """
        if self.guest_is_linux(server) is True:
            pass
        elif self.guest_is_windows(server) is True:
            ps_path = "C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe"
            # disable firewall
            params = "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False"
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program=ps_path,
                program_arguments=params,
                program="Disable firewall",
            )
            self.logger.debug("Disable firewall on server %s" % server)

    def guest_setup_network(
        self,
        server,
        pwd,
        ipaddr,
        macaddr,
        gw,
        hostname,
        dns,
        dns_search,
        conn_name="net01",
        user="root",
        prefix=24,
        http_proxy=None,
    ):
        """Setup server network

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param ipaddr: ip address
        :param macaddr: mac address
        :param gw: default gateway
        :param device: network device [default=eth0]
        :param hostname: host name
        :param conn_name: connection name
        :param dns: dns list. Ex. '8.8.8.8,8.8.8.4'
        :param dns_search: dns search domain. Ex. local.domain
        :param prefix: network prefix
        """
        # bypass network configuration for windows os
        if self.guest_is_windows(server) is True:
            return None

        if self.guest_is_linux(server) is True:
            # set hostname
            fqdn = "%s.%s" % (hostname, dns_search)
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/hostname",
                program_arguments=fqdn,
                program="setup hostname: %s" % hostname,
                check_status_code=False,
            )
            params = '-e "%s" > /etc/hostname' % fqdn
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=params,
                program="setup hostname: %s" % hostname,
                check_status_code=False,
            )
            params = '-e "%s %s %s" >> /etc/hosts' % (ipaddr, fqdn, hostname)
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=params,
                program="setup hostname: %s" % hostname,
                check_status_code=False,
            )

        # delete connection with the same name
        if self.guest_is_redhat(server) is True:
            params = "con delete `/bin/nmcli -t -f uuid,name con show | grep System | tr ':' ' ' | " "awk '{print $1}'`"
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/nmcli",
                program_arguments=params,
                program="delete active connection",
                check_status_code=False,
            )

        if (
            self.guest_is_redhat(server) is True
            or self.guest_is_centos(server) is True
            or self.guest_is_oracle_linux(server) is True
        ):
            # create new connection
            params = 'con add type ethernet con-name %s ifname "*" mac %s ip4 %s/%s gw4 %s' % (
                conn_name,
                macaddr,
                ipaddr,
                prefix,
                gw,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/nmcli",
                program_arguments=params,
                program="configure network %s" % ipaddr,
                check_status_code=False,
            )

            # setup dns
            params = 'con modify %s ipv4.dns "%s" ipv4.dns-search %s' % (
                conn_name,
                dns,
                dns_search,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/nmcli",
                program_arguments=params,
                program="configure dns %s" % dns,
                check_status_code=False,
            )

            # disable ipv6
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments='"net.ipv6.conf.all.disable_ipv6 = 1" >> /etc/sysctl.conf',
                program="disable ipv6",
                check_status_code=False,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments='"net.ipv6.conf.default.disable_ipv6 = 1" >> /etc/sysctl.conf',
                program="disable ipv6",
                check_status_code=False,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/usr/sbin/sysctl",
                program_arguments="-p",
                program="disable ipv6",
                check_status_code=False,
            )

            # restart network
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/systemctl",
                program_arguments="restart NetworkManager",
                program="restart network",
                check_status_code=False,
            )

        if self.guest_is_ubuntu(server) is True:
            # create netplan config file
            dns_ips = dns.split(",")
            content = [
                "network:",
                "    version: 2",
                "    ethernets:",
                "        ens160:",
                "            addresses:",
                "            - %s/%s" % (ipaddr, prefix),
                "            gateway4: %s" % gw,
                "            nameservers:",
                "                addresses:",
                "                - %s" % dns_ips[0],
                "                - %s" % dns_ips[1],
                "                search:",
                "                - %s" % dns_search,
            ]
            self.logger.warn("\n".join(content))
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments='"%s" > /etc/netplan/00-installer-config.yaml' % "\n".join(content),
                program="create netplan config",
                check_status_code=False,
            )

            # apply netplan config
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/usr/sbin/netplan",
                program_arguments="apply",
                program="apply netplan config",
                check_status_code=False,
            )

        self.logger.debug("Configure server %s device %s ip %s" % (server, macaddr, ipaddr))

    def guest_setup_network_orig(
        self,
        server,
        pwd,
        ipaddr,
        macaddr,
        gw,
        hostname,
        dns,
        dns_search,
        conn_name="net01",
        user="root",
        prefix=24,
    ):
        """Setup server network

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param ipaddr: ip address
        :param macaddr: mac address
        :param gw: default gateway
        :param device: network device [default=eth0]
        :param hostname: host name
        :param conn_name: connection name
        :param dns: dns list. Ex. '8.8.8.8 8.8.8.4'
        :param dns_search: dns search domain. Ex. local.domain
        :param prefix: network prefix
        """
        if self.guest_is_linux(server) is True:
            # set hostname
            fqdn = "%s.%s" % (hostname, dns_search)
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/hostname",
                program_arguments=fqdn,
                program="setup hostname: %s" % hostname,
                check_status_code=False,
            )
            params = '-e "%s" > /etc/hostname' % fqdn
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=params,
                program="setup hostname: %s" % hostname,
                check_status_code=False,
            )
            params = '-e "%s %s %s" >> /etc/hosts' % (ipaddr, fqdn, hostname)
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=params,
                program="setup hostname: %s" % hostname,
                check_status_code=False,
            )

            # delete connection with the same name
            if self.guest_is_redhat(server) is True:
                params = (
                    "con delete `/bin/nmcli -t -f uuid,name con show | grep System | tr ':' ' ' | " "awk '{print $1}'`"
                )
                proc = self.guest_execute_command(
                    server,
                    user,
                    pwd,
                    path_to_program="/bin/nmcli",
                    program_arguments=params,
                    program="delete active connection",
                    check_status_code=False,
                )

            # create new connection
            params = 'con add type ethernet con-name %s ifname "*" mac %s ip4 %s/%s gw4 %s' % (
                conn_name,
                macaddr,
                ipaddr,
                prefix,
                gw,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/nmcli",
                program_arguments=params,
                program="configure network %s" % ipaddr,
                check_status_code=False,
            )

            # setup dns
            params = 'con modify %s ipv4.dns "%s" ipv4.dns-search %s' % (
                conn_name,
                dns,
                dns_search,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/nmcli",
                program_arguments=params,
                program="configure dns %s" % dns,
                check_status_code=False,
            )

            # disable ipv6
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments='"net.ipv6.conf.all.disable_ipv6 = 1" >> / etc / sysctl.conf',
                program="disable ipv6",
                check_status_code=False,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments='"net.ipv6.conf.default.disable_ipv6 = 1" >> / etc / sysctl.conf',
                program="disable ipv6",
                check_status_code=False,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/usr/sbin/sysctl",
                program_arguments="-p",
                program="disable ipv6",
                check_status_code=False,
            )

            # restart network
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/systemctl",
                program_arguments="restart NetworkManager",
                program="restart network",
                check_status_code=False,
            )

            self.logger.debug("Configure server %s device %s ip %s" % (server, macaddr, ipaddr))
        elif self.guest_is_windows(server) is True:
            pass

    def guest_setup_network2(
        self,
        server,
        pwd,
        ipaddr,
        macaddr,
        gw,
        hostname,
        dns,
        dns_search,
        conn_name="net01",
        user="root",
        prefix=24,
    ):
        """Setup server network

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param ipaddr: ip address
        :param macaddr: mac address
        :param gw: default gateway
        :param device: network devide [default=eth0]
        :param hostname: host name
        :param conn_name: connection name
        :param dns: dns list. Ex. '8.8.8.8 8.8.8.4'
        :param dns_search: dns search domain. Ex. local.domain
        :param prefix: network prefix
        """
        if self.guest_is_linux(server) is True:
            # set hostname
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/hostname",
                program_arguments=hostname,
                program="setup hostname: %s" % hostname,
                check_status_code=False,
            )
            fqdn = "%s.%s" % (hostname, dns_search)
            params = '-e "%s" > /etc/hostname' % fqdn
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=params,
                program="setup hostname: %s" % hostname,
                check_status_code=False,
            )
            params = '-e "%s %s" >> /etc/hosts' % (ipaddr, fqdn)
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=params,
                program="setup hostname: %s" % hostname,
                check_status_code=False,
            )

            # create new connection
            params = 'con add type ethernet con-name %s ifname "*" mac %s ip4 %s/%s gw4 %s' % (
                conn_name,
                macaddr,
                ipaddr,
                prefix,
                gw,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/nmcli",
                program_arguments=params,
                program="configure network %s" % ipaddr,
                check_status_code=False,
            )

            # setup dns
            params = 'con modify %s ipv4.dns "%s" ipv4.dns-search %s' % (
                conn_name,
                dns,
                dns_search,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/nmcli",
                program_arguments=params,
                program="configure dns %s" % dns,
                check_status_code=False,
            )

            # disable ipv6
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments='"net.ipv6.conf.all.disable_ipv6 = 1" >> / etc / sysctl.conf',
                program="disable ipv6",
                check_status_code=False,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments='"net.ipv6.conf.default.disable_ipv6 = 1" >> / etc / sysctl.conf',
                program="disable ipv6",
                check_status_code=False,
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/usr/sbin/sysctl",
                program_arguments="-p",
                program="disable ipv6",
                check_status_code=False,
            )

            # restart network
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/systemctl",
                program_arguments="restart NetworkManager",
                program="restart network",
                check_status_code=False,
            )

            self.logger.debug("Configure server %s device %s ip %s" % (server, macaddr, ipaddr))
        elif self.guest_is_windows(server) is True:
            ps_path = "C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe"

            # create new connection
            params = (
                "New-NetIPAddress -IPAddress %s -DefaultGateway %s -PrefixLength %s -InterfaceIndex "
                "(Get-NetAdapter).InterfaceIndex" % (ipaddr, gw, prefix)
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program=ps_path,
                program_arguments=params,
                program="setup network: %s" % ipaddr,
            )

            # setup dns
            dns = ",".join(dns.split(" "))
            params = (
                "Set-DNSClientServerAddress -InterfaceIndex (Get-NetAdapter).InterfaceIndex "
                "-ServerAddresses %s" % dns
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program=ps_path,
                program_arguments=params,
                program="setup dns: %s" % dns,
            )

            # disable firewall
            params = "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False"
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program=ps_path,
                program_arguments=params,
                program="Disable firewall",
            )

            # set hostname
            params = (
                "$host_name=C:\\WINDOWS\\system32\\hostname.exe; netdom renamecomputer $host_name "
                "/newname:%s /force" % hostname
            )
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program=ps_path,
                program_arguments=params,
                program="Setup hostname: %s" % hostname,
            )

            self.logger.debug("Configure server %s device %s ip %s" % (server, macaddr, ipaddr))

    def guest_destroy_network_config(self, server, pwd, ipaddr, user="root"):
        """Destroy server network configuration

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param ipaddr: ip address
        """
        if self.guest_is_linux(server) is True:
            pass
        elif self.guest_is_windows(server) is True:
            ps_path = "C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe"

            # create new connection
            params = "Remove-NetIPAddress -IPAddress %s -Confirm false" % ipaddr
            self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program=ps_path,
                program_arguments=params,
                program="destroy network configuration: %s" % ipaddr,
            )

    def guest_setup_install_software(self, server, user, pwd, pkgs=None):
        """install software

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param pkgs: list of packages to install [optional]
        """
        # ubuntu server
        if self.guest_is_ubuntu(server) is True:
            base_pkgs = ["sshpass", "scsitools"]
            if pkgs is not None:
                base_pkgs.extend(pkgs)
            base_pkgs = " ".join(base_pkgs)
            params = "install -y %s" % base_pkgs
            self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/usr/bin/apt-get",
                program_arguments=params,
                program="install pkgs %s" % base_pkgs,
                check_status_code=False,
            )

    def guest_setup_admin_password(self, server, user, pwd, new_pwd):
        """Setup admin password

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param new_pwd: new admin password
        """
        proc = None
        # ubuntu server
        if self.guest_is_ubuntu(server) is True:
            params = "--password $(echo '%s' | openssl passwd -1 -stdin) ubuntu" % new_pwd
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/usr/sbin/usermod",
                program_arguments=params,
                program="setup ubuntu password",
                check_status_code=False,
            )
            self.logger.debug("Setup server %s ubuntu password" % server)

        # other linux server
        if (
            self.guest_is_redhat(server) is True
            or self.guest_is_centos(server) is True
            or self.guest_is_oracle_linux(server) is True
        ):
            params = '-e "%s" | passwd root --stdin > /dev/null' % new_pwd
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=params,
                program="setup root password",
                check_status_code=False,
            )
            self.logger.debug("Setup server %s admin password" % server)

        # windows server
        elif self.guest_is_windows(server) is True:
            pass
        return proc

    def guest_setup_ssh_key(self, server, user, pwd, key):
        """Setup server ssh key

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param key: ssh public key
        """
        proc = None
        if self.guest_is_linux(server) is True:
            params = "-e %s >> /root/.ssh/authorized_keys" % key
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=params,
                program="setup root ssh key",
                check_status_code=False,
            )
            self.logger.debug("Setup server %s ssh key" % server)
        elif self.guest_is_windows(server) is True:
            pass
        return proc

    def disable_proxy(self, server, user, pwd):
        """disable_proxy

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        """
        proc = None

        if self.guest_is_linux(server) is True:
            date = datetime.today().strftime("%Y-%m-%d")
            params = "/etc/yum.conf /etc/yum.conf.%s" % date
            self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/cp",
                program_arguments=params,
                program="setup root ssh key",
                check_status_code=False,
            )
            self.logger.debug("create backup of yum .conf")
            params = "'/^proxy/d' /etc/yum.conf.%s > /etc/yum.conf" % date
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/sed",
                program_arguments=params,
                program="setup root ssh key",
                check_status_code=False,
            )
            self.logger.debug("create backup of yum .conf")
        elif self.guest_is_windows(server) is True:
            pass
        return proc

    def configure_proxy(self, server, user, pwd, http_proxy):
        """configure proxy

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param http_proxy: http proxy
        """
        # configure proxy
        if self.guest_is_ubuntu(server) is True:
            self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/usr/bin/rm",
                program_arguments="-r /etc/apt/apt.conf.d/90curtin-aptproxy",
                program="delete file /etc/apt/apt.conf.d/90curtin-aptproxy",
                check_status_code=False,
            )
            content = [
                'Acquire::http::Proxy "%s";' % http_proxy,
                'Acquire::http::Proxy "%s";' % http_proxy,
            ]
            self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments="'%s' > /etc/apt/apt.conf" % "\n".join(content),
                program="config proxy for apt",
                check_status_code=False,
            )
            content = [
                "export http_proxy=%s" % http_proxy,
                "export https_proxy=%s" % http_proxy,
            ]
            self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments="'%s' > /etc/environment" % "\n".join(content),
                program="config proxy environment",
                check_status_code=False,
            )

        elif self.guest_is_windows(server) is True:
            pass

    def guest_rescan_scsi_bus(self, server, user, pwd):
        """rescan scsi bus

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        """
        proc = None
        if self.guest_is_ubuntu(server) is True:
            params = ""
            proc = self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/usr/sbin/rescan-scsi-bus",
                program_arguments=params,
                program="rescan scsi bus",
                check_status_code=False,
            )
            self.logger.debug("rescan server %s scsi bus " % server)
        elif self.guest_is_windows(server) is True:
            pass
        return proc

    #
    # fault tolerance
    #
    def fault_tolerance(self):
        """"""
        pass

    #
    # system logs
    #
    def export_system_logs(self):
        """"""
        pass

    #
    # clone
    #
    def clone(self):
        """"""
        pass

    def clone_to_template(self):
        """"""
        pass

    def clone_to_template_library(self):
        """"""
        pass

    #
    # convert

    def convert_to_template(self):
        """"""
        pass

    def convert_from_template(self):
        """"""
        pass

        #

    # ovf

    def export_ovf_template(self):
        """"""
        pass

    def deploy_ovf_template(self):
        """"""
        pass

        #

    # manage
    #

    def start(self, server):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.PowerOnVM_Task()
            self.logger.debug("Attempting to power on %s" % server)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    def stop(self, server):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            from pyVmomi import vim
            from gevent import sleep

            virtualMachine: vim.VirtualMachine = server
            virtualMachine.ShutdownGuest()
            # task = server.PowerOffVM_Task()
            self.logger.debug("stop - Attempting to shutdown  %s" % server)

            state = virtualMachine.runtime.powerState
            while format(state) != "poweredOff":
                sleep(1)
                state = virtualMachine.runtime.powerState
                self.logger.debug("stop - state %s" % state)

            self.logger.debug("stop end - state %s" % state)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    def reboot(self, server):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            server.RebootGuest()
            self.logger.debug("Attempting to reboot %s" % server)
            return None
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    def suspend(self, server):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.SuspendVM_Task()
            self.logger.debug("Attempting to suspend %s" % server)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    def reset(self, server):
        """TODO
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.SuspendVM_Task()
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    def stop_guest_os(self, server):
        """TODO
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.SuspendVM_Task()
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    def restart_guest_os(self, server):
        """TODO
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.SuspendVM_Task()
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    def migrate(self, server):
        """TODO
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.SuspendVM_Task()
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)


class VsphereServerHardware(VsphereObject):
    """ """

    def __init__(self, server):
        VsphereObject.__init__(self, server.manager)
        self.server = server

    def get_config_data(self, server):
        """ """
        try:
            cfg = server.config
            hw = server.config.hardware

            info = {
                "bios_uuid": cfg.uuid,
                "version": cfg.version,
                "firmware": cfg.firmware,
                "swap_placement": cfg.swapPlacement,
                "boot": {
                    "boot_delay": cfg.bootOptions.bootDelay,
                    "enter_bios_setup": cfg.bootOptions.enterBIOSSetup,
                    "retry_enabled": cfg.bootOptions.bootRetryEnabled,
                    "retry_delay": cfg.bootOptions.bootRetryDelay,
                    "network_protocol": cfg.bootOptions.networkBootProtocol,
                    "order": [],
                },
            }
            for item in cfg.bootOptions.bootOrder:
                info["boot"]["order"].append(item)

            # server files on storage
            info["file_layout"] = {
                "vmPathName": cfg.files.vmPathName,
                "snapshotDirectory": cfg.files.snapshotDirectory,
                "suspendDirectory": cfg.files.suspendDirectory,
                "logDirectory": cfg.files.logDirectory,
                "files": [],
            }

            # add file info
            for item in server.layoutEx.file:
                info["file_layout"]["files"].append(
                    {
                        "key": item.key,
                        "name": item.name,
                        "type": item.type,
                        "size": item.size,
                        "uniqueSize": item.uniqueSize,
                        "accessible": item.accessible,
                    }
                )

            # server cpu
            reservation = "%s MHz" % cfg.cpuAllocation.reservation
            shares = "%s(%s)" % (
                cfg.cpuAllocation.shares.shares,
                cfg.cpuAllocation.shares.level,
            )
            limit = cfg.cpuAllocation.limit
            if limit < 0:
                limit = "unlimited"
            info["cpu"] = {
                "num": hw.numCPU,
                "core": hw.numCoresPerSocket,
                "reservation": reservation,
                "limit": limit,
                "shares": shares,
                "hardware_utilization": None,
                "performance_counters": None,
            }

            # server memory
            reservation = "%s MB" % (cfg.memoryAllocation.reservation)
            shares = "%s(%s)" % (
                cfg.memoryAllocation.shares.shares,
                cfg.memoryAllocation.shares.level,
            )
            limit = cfg.memoryAllocation.limit
            if limit < 0:
                limit = "unlimited"
            info["memory"] = {
                "total": hw.memoryMB,
                "reservation": reservation,
                "limit": limit,
                "shares": shares,
                "vm_overhead_consumed": None,
            }

            # server network adapter
            info["network"] = []

            # server hard disk
            info["storage"] = []

            # server floppy
            info["floppy"] = None

            # server cdrom
            info["cdrom"] = None

            # server video card
            info["video"] = None

            # server other
            info["other"] = {
                "scsi_adapters": [],
                "controllers": [],
                "input_devices": [],
                "pci": [],
                "other": [],
            }

            for device in hw.device:
                if device.backing is None:
                    if type(device).__name__.find("Controller") > -1:
                        dev = {
                            "name": device.deviceInfo.label,
                            "type": type(device).__name__,
                            "key": device.key,
                        }

                        info["other"]["controllers"].append(dev)

                    elif isinstance(device, vim.vm.device.VirtualKeyboard):
                        dev = {
                            "name": device.deviceInfo.label,
                            "type": type(device).__name__,
                            "key": device.key,
                        }

                        info["other"]["input_devices"].append(dev)
                        # TODO

                    elif isinstance(device, vim.vm.device.VirtualVideoCard):
                        dev = {
                            "name": device.deviceInfo.label,
                            "type": type(device).__name__,
                            "key": device.key,
                        }

                        info["video"] = dev
                        # TODO

                    elif isinstance(device, vim.vm.device.VirtualVMCIDevice):
                        dev = {
                            "name": device.deviceInfo.label,
                            "type": type(device).__name__,
                            "key": device.key,
                        }

                        info["other"]["pci"].append(dev)

                    elif isinstance(device, vim.vm.device.VirtualSoundCard):
                        # TODO
                        pass

                elif isinstance(device, vim.vm.device.VirtualPointingDevice):
                    dev = {
                        "name": device.deviceInfo.label,
                        "type": type(device).__name__,
                        "backing": type(device.backing).__name__,
                        "key": device.key,
                    }

                    info["other"]["input_devices"].append(dev)

                elif isinstance(device, vim.vm.device.VirtualCdrom):
                    dev = {
                        "name": device.deviceInfo.label,
                        "type": type(device).__name__,
                        "backing": type(device.backing).__name__,
                        "key": device.key,
                    }
                    if isinstance(device.backing, vim.vm.device.VirtualCdrom.IsoBackingInfo):
                        datastore = device.backing.datastore
                        if datastore is not None:
                            dev["dstastore"] = datastore._moId
                            dev["path"] = device.backing.fileName

                    info["cdrom"] = dev
                    # TODO

                elif isinstance(device, vim.vm.device.VirtualFloppy):
                    dev = {
                        "name": device.deviceInfo.label,
                        "type": type(device).__name__,
                        "key": device.key,
                    }

                    info["floppy"] = dev
                    # TODO

                elif isinstance(device, vim.vm.device.VirtualEthernetCard):
                    net = {
                        "key": device.key,
                        "unit_number": device.unitNumber,
                        "name": device.deviceInfo.label,
                        "type": type(device).__name__,
                        "backing": type(device.backing).__name__,
                        "macaddress": device.macAddress,
                        "direct_path_io": None,
                        "network": None,
                        "shares": None,
                        "reservation": None,
                        "limit": None,
                        "connected": device.connectable.connected,
                    }

                    if hasattr(device.backing, "port"):
                        port_group_ext_id = device.backing.port.portgroupKey
                        dvp = self.manager.network.get_network(port_group_ext_id)
                        cfg = dvp.config.defaultPortConfig
                        net["network"] = {
                            "id": port_group_ext_id,
                            "name": dvp.name,
                            "vlan": cfg.vlan.vlanId,
                            "dvs": dvp.config.distributedVirtualSwitch._moId,
                        }

                    info["network"].append(net)

                elif isinstance(device, vim.vm.device.VirtualDisk):
                    backing_type = type(device).__name__
                    dev = {
                        "name": device.deviceInfo.label,
                        "type": backing_type,
                        "backing": type(device.backing).__name__,
                        "size": device.capacityInBytes / 1024 / 1024,
                        "flashcache": device.vFlashCacheConfigInfo,
                        "datastore": None,
                    }
                    backing = device.backing
                    datastore = backing.datastore
                    if datastore is not None:
                        dev["datastore"] = {
                            "file_name": backing.fileName,
                            "name": datastore.name,
                            "id": datastore._moId,
                            "sharing": backing.sharing,
                            "disk_mode": backing.diskMode,
                            "delta_grain_size": backing.deltaGrainSize,
                            "delta_disk_format": backing.deltaDiskFormat,
                            "delta_grain_size": backing.deltaGrainSize,
                            "parent": None,
                        }
                        if backing_type == "vim.vm.device.VirtualDisk.FlatVer2BackingInfo":
                            dev["datastore"].update(
                                {
                                    "write_through": backing.writeThrough,
                                    "thin_provisioned": backing.thinProvisioned,
                                    "split": backing.split,
                                    "delta_disk_format_variant": backing.deltaDiskFormatVariant,
                                    "digest_enabled": backing.digestEnabled,
                                }
                            )
                        if device.backing.parent is not None:
                            dev["datastore"]["parent"] = {
                                "file_name": backing.parent.fileName,
                                "name": backing.parent.datastore.name,
                                "id": backing.parent.datastore._moId,
                                "write_through": backing.parent.writeThrough,
                                "thin_provisioned": backing.parent.thinProvisioned,
                                "split": backing.parent.split,
                                "sharing": backing.parent.sharing,
                                "disk_mode": backing.parent.diskMode,
                                "digest_enabled": backing.parent.digestEnabled,
                                "delta_grain_size": backing.parent.deltaGrainSize,
                                "delta_disk_format_variant": backing.parent.deltaDiskFormatVariant,
                                "delta_disk_format": backing.parent.deltaDiskFormat,
                                "delta_grain_size": backing.parent.deltaGrainSize,
                            }

                    info["storage"].append(dev)
                else:
                    dev = {
                        "name": device.deviceInfo.label,
                        "type": type(device).__name__,
                        "key": device.key,
                    }

                    info["other"]["other"].append(dev)

        except Exception as error:
            self.logger.error(error, exc_info=False)
            info = {}

        return info

    def info(self, server):
        """Server hardware details: CPU, Ram, HD, Net, CD, Floppy, Video,
        Compatibility(vm version), Other(SCSI Adapters, Controllers, Input
        devices)
        """
        info = self.get_config_data(server)
        return info

    def get_devices(self, server, dev_type=None):
        """

        :param dev_type: device type. Ex. vim.vm.device.VirtualVmxnet3. If None
                         get all device types.
        """
        devices = []
        try:
            for device in server.config.hardware.device:
                dtype = type(device).__name__
                if dev_type is not None and dtype != dev_type:
                    continue

                # diving into each device, we pull out a few interesting bits
                dev_details = {
                    "key": device.key,
                    "unitNumber": device.unitNumber,
                    "summary": device.deviceInfo.summary,
                    "label": device.deviceInfo.label,
                    "device type": dtype,
                    "backing": {"type": type(device.backing).__name__},
                }

                devices.append(dev_details)
        except:
            self.logger.warning(traceback.format_exc())

        return devices

    def get_hard_disks(self, server):
        """

        :return:
        """
        res = []
        hw = server.config.hardware

        for device in hw.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                res.append(device)

        return res

    def get_original_devices(self, server, dev_type=None):
        """

        :param dev_type: device type. Ex. vim.vm.device.VirtualVmxnet3. If None
                         get all device types.
        """
        devices = []
        try:
            for device in server.config.hardware.device:
                dtype = type(device).__name__
                if dev_type is not None and dtype != dev_type:
                    continue
                devices.append(device)
        except:
            self.logger.warning(traceback.format_exc())

        return devices

    def add_hard_disk(
        self,
        server,
        size,
        datastore,
        disk_type="thin",
        disk_unit_number=None,
        existing=False,
        backing_filename=None,
    ):
        """
        Supported virtual disk backings:
        - Sparse disk format, version 1 and 2 : The virtual disk backing grows when needed. Supported only for
        VMware Server.
        - Flat disk format, version 1 and 2 : The virtual disk backing is preallocated. Version 1 is supported only
        for VMware Server.
        - Space efficient sparse disk format : The virtual disk backing grows on demand and incorporates additional
        space optimizations.
        - Raw disk format, version 2  : The virtual disk backing uses a full physical disk drive to back the virtual
        disk. Supported only for VMware Server.
        - Partitioned raw disk format, version 2 : The virtual disk backing uses one or more partitions on a physical
        disk drive to back a virtual disk. Supported only for VMware Server.
        - Raw disk mapping, version 1 : The virtual disk backing uses a raw device mapping to back the virtual disk.
        Supported for ESX Server 2.5 and 3.x.

        TODO: extend backing support. Now support only FlatVer2BackingInfo

        :param server: server instance
        :param size: disk size in GB
        :param disk_type: disk type [default=thick]
        :param datastore: datastore object
        :param existing: if True add existing hard disk
        :param backing_filename: vdmk file to use
        """
        try:
            spec = vim.vm.ConfigSpec()

            # get all disks on a VM, set unit_number to the next available
            # unit_numbers = []
            for dev in server.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualSCSIController):
                    controller = dev

            # add disk here
            dev_changes = []
            new_disk_kb = int(size) * 1024 * 1024
            if not self.has_free_datastore_space(datastore, new_disk_kb):
                msg = "Cannot add new disk of %s GB of server %s to %s GB.\n" "No space left on datastore %s " % (
                    size,
                    datastore,
                    server.config.name,
                )
                raise vmodl.MethodFault(msg=msg)
            disk_spec = vim.vm.device.VirtualDeviceSpec()
            disk_spec.fileOperation = "create"
            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            disk_spec.device = vim.vm.device.VirtualDisk()
            disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            if disk_type == "thin":
                disk_spec.device.backing.thinProvisioned = True
            if existing:
                disk_spec.device.backing.fileName = backing_filename

            disk_spec.device.backing.datastore = datastore
            disk_spec.device.backing.diskMode = "persistent"
            disk_spec.device.unitNumber = disk_unit_number
            disk_spec.device.capacityInKB = new_disk_kb
            disk_spec.device.controllerKey = controller.key
            dev_changes.append(disk_spec)
            spec.deviceChange = dev_changes
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug(
                "Add new disk of %s GB, datastore %s, to server %s" % (size, datastore, server.config.name)
            )
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return task

    def add_network(self, server, network):
        """ """
        try:
            spec = vim.vm.ConfigSpec()
            dev_changes = []
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            nic_spec.device = vim.vm.device.VirtualVmxnet3()
            nic_spec.device.addressType = "Generated"
            nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            nic_spec.device.backing.port = vim.dvs.PortConnection()
            nic_spec.device.backing.port.portgroupKey = network.key
            nic_spec.device.backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid
            nic_spec.device.wakeOnLanEnabled = False
            dev_changes.append(nic_spec)
            spec.deviceChange = dev_changes
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug("Network %s added to %s" % (network.name, server.config.name))
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return task

    def add_cdrom(self, server):
        """ """
        try:
            task = None
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return task

    def add_floppy(self):
        """ """
        pass

    def add_serial_port(self):
        """ """
        pass

    def add_parallel_port(self):
        """ """
        pass

    def add_usb_device(self):
        """ """
        pass

    def add_usb_controller(self):
        """ """
        pass

    def add_scsi_device(self):
        """ """
        pass

    def add_pci_device(self):
        """ """
        pass

    def add_shared_pci_device(self):
        """ """
        pass

    def add_scsi_controller(self):
        """ """
        pass

    def add_sata_controller(self):
        """ """
        pass

    #
    # update action
    #

    def update_hard_disk(self, server, disk_number, new_disk_kb=None):
        """Update server disk

        :param server: server instance
        :param disk_number: Hard Disk Unit Number
        :param new_disk_kb: new size of the hard_disk [optional]
        :return: task
        """
        try:
            hdd_prefix_label = "Hard disk "
            hdd_label = hdd_prefix_label + str(disk_number)
            virtual_hdd_device = None
            for dev in server.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualDisk) and dev.deviceInfo.label == hdd_label:
                    virtual_hdd_device = dev
            if not virtual_hdd_device:
                raise vmodl.MethodFault(msg="Virtual %s could not be found." % hdd_label)

            if new_disk_kb is not None:
                virtual_hdd_device.capacityInKB = new_disk_kb
            virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_hdd_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            virtual_hdd_spec.device = virtual_hdd_device

            spec = vim.vm.ConfigSpec()
            spec.deviceChange = [virtual_hdd_spec]
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug("Update disk %s on server %s" % (hdd_label, server.name))
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return task

    def update_network(
        self,
        server,
        net_number,
        network=None,
        nic_start_connected=True,
        nic_connected=False,
    ):
        """Update server network

        :param server:
        :param net_number:
        :param network:
        :param nic_start_connected:
        :param nic_connected:

        :return:
        """
        try:
            spec = vim.vm.ConfigSpec()
            dev_changes = []

            net_prefix_label = "Network adapter "
            net_label = net_prefix_label + str(net_number)
            virtual_net_device = None
            for dev in server.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.label == net_label:
                    virtual_net_device = dev
            if not virtual_net_device:
                raise vmodl.MethodFault(msg="%s could not be found." % (net_label))

            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            nic_spec.device = virtual_net_device
            nic_spec.device.wakeOnLanEnabled = False

            if network is not None:
                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                nic_spec.device.backing.port = vim.dvs.PortConnection()
                nic_spec.device.backing.port.portgroupKey = network.key
                nic_spec.device.backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid

            nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            nic_spec.device.connectable.startConnected = nic_start_connected
            nic_spec.device.connectable.connected = nic_connected
            nic_spec.device.connectable.allowGuestControl = True

            dev_changes.append(nic_spec)
            spec.deviceChange = dev_changes
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug("Nic %s updated for server %s" % (net_label, server.name))
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return task

    def update_cdrom(self, server, cdrom_number, full_path_to_iso=None):
        """Updates Virtual Machine CD/DVD backend device

        :param server: server instance
        :param cdrom_number: CD/DVD drive unit number
        :param full_path_to_iso: Full path to iso. i.e. "[ds1] folder/Ubuntu.iso"
        :return: True or false in case of success or error
        """
        try:
            cdrom_prefix_label = "CD/DVD drive "
            cdrom_label = cdrom_prefix_label + str(cdrom_number)
            virtual_cdrom_device = None
            for dev in server.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualCdrom) and dev.deviceInfo.label == cdrom_label:
                    virtual_cdrom_device = dev

            if not virtual_cdrom_device:
                raise vmodl.MethodFault(msg="Virtual {} could not be found.".format(cdrom_label))

            virtual_cd_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_cd_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            virtual_cd_spec.device = vim.vm.device.VirtualCdrom()
            virtual_cd_spec.device.controllerKey = virtual_cdrom_device.controllerKey
            virtual_cd_spec.device.key = virtual_cdrom_device.key
            virtual_cd_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            # if full_path_to_iso is provided it will mount the iso
            if full_path_to_iso:
                virtual_cd_spec.device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
                virtual_cd_spec.device.backing.fileName = full_path_to_iso
                virtual_cd_spec.device.connectable.connected = True
                virtual_cd_spec.device.connectable.startConnected = True
            else:
                virtual_cd_spec.device.backing = vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo()
            # Allowing guest control
            virtual_cd_spec.device.connectable.allowGuestControl = True

            dev_changes = []
            dev_changes.append(virtual_cd_spec)
            spec = vim.vm.ConfigSpec()
            spec.deviceChange = dev_changes
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug("Cdorm %s updated for server %s" % (cdrom_label, server.name))
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return task

    def update_floppy(self):
        """ """
        pass

    def update_serial_port(self):
        """ """
        pass

    def update_parallel_port(self):
        """ """
        pass

    def update_usb_device(self):
        """ """
        pass

    def update_usb_controller(self):
        """ """
        pass

    def update_scsi_device(self):
        """ """
        pass

    def update_pci_device(self):
        """ """
        pass

    def update_shared_pci_device(self):
        """ """
        pass

    def update_scsi_controller(self):
        """ """
        pass

    def update_sata_controller(self):
        """ """
        pass

    def get_virtual_disk_by_unit_number(self, server, disk_number):
        """Get visrtual disk by unit number

        :param server: server instance
        :param disk_number: Hard Disk Unit Number;
               this may be the position of disk on first scsi
               or the diskObjectId. These are the two ext_id
               that we use.
        :return: task
        """
        virtual_hdd_device = None
        positional = disk_number.isdigit() or type(disk_number) == int
        for dev in server.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk):
                if not positional and dev.diskObjectId == disk_number:
                    virtual_hdd_device = dev
                    break
                elif positional and dev.unitNumber == int(disk_number):
                    virtual_hdd_device = dev
                    break
        return virtual_hdd_device

    def delete_hard_disk(self, server, disk_number):
        """Delete hard disk

        :param server: server instance
        :param disk_number: Hard Disk Unit Number
        :return: task
        """
        try:
            virtual_hdd_device = self.get_virtual_disk_by_unit_number(server, disk_number)
            if not virtual_hdd_device:
                raise vmodl.MethodFault(msg="Virtual with unitNumber %s could not be found." % disk_number)

            virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_hdd_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
            virtual_hdd_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.destroy
            virtual_hdd_spec.device = virtual_hdd_device

            spec = vim.vm.ConfigSpec()
            spec.deviceChange = [virtual_hdd_spec]
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug("Remove disk with unitNumber %s from server %s" % (disk_number, server.name))
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return task

    def has_free_datastore_space(self, datastore, size):
        datastore_summary = datastore.summary
        datastore_freespace_gb = datastore_summary.freeSpace
        if size < datastore_freespace_gb * 1024 * 1024:
            return True
        return False

    def extend_hard_disk(self, server, disk_number, size):
        """Extends the size of a volume to a requested size, in gibibytes (GiB).

        :param server: server instance
        :param disk_number: Hard Disk Unit Number
        :param size: Size in GiB
        :return: task
        """
        try:
            virtual_hdd_device = self.get_virtual_disk_by_unit_number(server, disk_number)
            if not virtual_hdd_device:
                msg = "Cannot extend the volume %s of server %s\n" "Volume not found." % (
                    disk_number,
                    server.config.name,
                )
                raise vmodl.MethodFault(msg=msg)
            size = int(size)
            old_disk_kb = virtual_hdd_device.capacityInKB
            old_disk_gb = old_disk_kb / 1024 / 1024
            new_disk_kb = size * 1024 * 1024
            if new_disk_kb < old_disk_kb:
                msg = (
                    "Cannot extend the volume %s of server %s to %s GB.\n"
                    "It is an extends. You can only increase the volume size! "
                    "The volume size is %s GB." % (disk_number, server.config.name, size, old_disk_gb)
                )
                raise vmodl.MethodFault(msg=msg)

            datastore = virtual_hdd_device.backing.datastore
            if not self.has_free_datastore_space(datastore, new_disk_kb - old_disk_kb):
                msg = "Cannot extend the volume %s of server %s to %s GB.\n" "No space left on datastore %s " % (
                    disk_number,
                    server.config.name,
                    size,
                    datastore,
                )
                raise vmodl.MethodFault(msg=msg)

            virtual_hdd_device.capacityInKB = new_disk_kb
            virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_hdd_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            virtual_hdd_spec.device = virtual_hdd_device
            spec = vim.vm.ConfigSpec()
            spec.deviceChange = [virtual_hdd_spec]
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug(
                "Extend the volume unit %s of server %s to %s GB" % (disk_number, server.config.name, size)
            )
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return task

    def delete_network(self, server, net_number):
        """ """
        try:
            net_prefix_label = "Network adapter "
            net_label = net_prefix_label + str(net_number)
            virtual_net_device = None
            for dev in server.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.label == net_label:
                    virtual_net_device = dev
            if not virtual_net_device:
                raise vmodl.MethodFault(msg="%s could not be found." % (net_label))

            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
            nic_spec.device = virtual_net_device

            spec = vim.vm.ConfigSpec()
            spec.deviceChange = [nic_spec]
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug("Remove network %s from server %s" % (net_label, server.name))
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return task

    def delete_cdrom(self):
        """ """
        pass

    def delete_floppy(self):
        """ """
        pass

    def delete_serial_port(self):
        """ """
        pass

    def delete_parallel_port(self):
        """ """
        pass

    def delete_usb_device(self):
        """ """
        pass

    def delete_usb_controller(self):
        """ """
        pass

    def delete_scsi_device(self):
        """ """
        pass

    def delete_pci_device(self):
        """ """
        pass

    def delete_shared_pci_device(self):
        """ """
        pass

    def delete_scsi_controller(self):
        """ """
        pass

    def delete_sata_controller(self):
        """ """
        pass


class VsphereServerMonitor(VsphereObject):
    """ """

    def __init__(self, server):
        VsphereObject.__init__(self, server.manager)
        self.server = server

    def issues(self):
        """"""
        pass

    def performances(self):
        """"""
        pass

    def policies(self):
        """"""
        pass

    def tasks(self):
        """"""
        pass

    def events(self):
        """"""
        pass

    def utilization(self):
        """"""
        pass

    def activity(self):
        """"""
        pass

    def service_composer(self):
        """"""
        pass

    def data_security(self):
        """"""
        pass

    def flow(self):
        """"""
        pass


class VsphereServerSnapshot(VsphereObject):
    """ """

    def __init__(self, server):
        VsphereObject.__init__(self, server.manager)
        self.server = server

    def __get_childs(self, snapshots, childs):
        """Recursive function to visit all childs, sub-childs, and so on for a given snapshot.

        :param snapshots: list of snapshot details to populate
        :param childs: list of childs of a given snapshot
        """
        if len(childs) == 0:
            return snapshots
        for item in childs:
            snapshot = {
                "id": item.snapshot._moId,
                "name": item.name,
                "desc": item.description,
                "creation_date": format_date(item.createTime),
                "state": item.state,
                "quiesced": item.quiesced,
                "backup_manifest": item.backupManifest,
                "replaysupported": item.replaySupported,
                "childs": [],
            }
            for child in item.childSnapshotList:
                snapshot["childs"].append(child.snapshot._moId)
            snapshots.append(snapshot)
            self.__get_childs(snapshots, item.childSnapshotList)

    def list(self, server):
        """List server snapshots.

        :param server: server instance
        :return: list of dictionary with snapshot info
        """
        try:
            snapshots = []
            if server.snapshot is not None:
                for item in server.snapshot.rootSnapshotList:
                    snapshot = {
                        "id": item.snapshot._moId,
                        "name": item.name,
                        "desc": item.description,
                        "creation_date": format_date(item.createTime),
                        "state": item.state,
                        "quiesced": item.quiesced,
                        "backup_manifest": item.backupManifest,
                        "replaysupported": item.replaySupported,
                        "childs": [],
                    }
                    for child in item.childSnapshotList:
                        snapshot["childs"].append(child.snapshot._moId)
                    snapshots.append(snapshot)
                    self.__get_childs(snapshots, item.childSnapshotList)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return snapshots

    def __get(self, server, childs, snapshot_id):
        """Recursive function to visit all childs, sub-childs, and so on for a given snapshot.

        :param childs: list of childs of a given snapshot
        :param snapshot_id: snapshot id to look for
        :return: snapshot instance
                :raise vmodl.MethodFault:
        """
        if server is not None:
            for item in server.snapshot.rootSnapshotList:
                if str(item.snapshot._moId) == snapshot_id:
                    self.logger.debug("Found snapshot: %s" % item.snapshot)
                    return item
                sn = self.__get(None, item.childSnapshotList, snapshot_id)
                if sn is not None:
                    return sn
        else:
            if len(childs) == 0:
                return None
            for item in childs:
                if str(item.snapshot._moId) == snapshot_id:
                    self.logger.debug("Found snapshot: %s" % item.snapshot)
                    return item
                return self.__get(None, item.childSnapshotList, snapshot_id)

    def get(self, server, snapshot_id):
        """Get server snapshot by managed object reference id.

        :param server: server instance
        :param snapshot_id: snapshot id
        :return: dict with snapshot info
        :raise VsphereError:
        """
        try:
            if server.snapshot is None:
                self.logger.error("Snapshot %s does not exist" % snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg="Snapshot %s does not exist" % snapshot_id)

            sn = self.__get(server, None, snapshot_id)
            if sn is None:
                self.logger.error("Snapshot %s does not exist" % snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg="Snapshot %s does not exist" % snapshot_id)

            snapshot = {
                "id": sn.snapshot._moId,
                "name": sn.name,
                "desc": sn.description,
                "creation_date": format_date(sn.createTime),
                "state": sn.state,
                "quiesced": sn.quiesced,
                "backup_manifest": sn.backupManifest,
                "replaysupported": sn.replaySupported,
                "childs": [],
            }
            for child in sn.childSnapshotList:
                snapshot["childs"].append(child.snapshot._moId)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return snapshot

    def get_current(self, server):
        """Get current server snapshot.

        :param server: server instance
        :return: dictionary with snapshot info
        :raise VsphereError:
        """
        try:
            item = server.rootSnapshot[0]
            hw = VsphereServerHardware(self.server)

            snapshot = {
                "id": item.snapshot._moId,
                "config": hw.get_config_data(item.config),
                "childs": [],
            }
            for child in item.childSnapshot:
                snapshot["childs"].append(child.snapshot._moId)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

        return snapshot

    def create(self, server, name, desc=None, memory=False, quiesce=True):
        """Creates a new snapshot of this virtual machine. As a side effect, this updates the current snapshot.
        Snapshots are not supported for Fault Tolerance primary and secondary virtual machines.

        Any %(percent) character used in this name parameter must be escaped, unless it is used to start an escape
        sequence. Clients may also escape any other characters in this name parameter.

        :param server: server instance
        :param name: The name for this snapshot. The name need not be unique for this virtual machine.
        :param desc: A description for this snapshot. If omitted, a default description may be provided. [optional]
        :param memory: If TRUE, a dump of the internal state of the virtual machine(basically a memory dump) is
            included in the snapshot. Memory snapshots consume time and resources, and thus take longer to create.
            When set to FALSE, the power state of the snapshot is set to powered off. capabilities indicates whether
            or not this virtual machine supports this operation. [default=False]
        :param quiesce: If TRUE and the virtual machine is powered on when the snapshot is taken, VMware Tools is used
            to quiesce the file system in the virtual machine. This assures that a disk snapshot represents a
            consistent state of the guest file systems. If the virtual machine is powered off or VMware Tools are not
            available, the quiesce flag is ignored. [default=True]
        :return: task
        :raise VsphereError:
        """
        try:
            if desc is None:
                desc = name
            task = server.CreateSnapshot_Task(name=name, description=desc, memory=memory, quiesce=quiesce)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def rename(self, server, snapshot_id, name, description=None):
        """Rename server snapshot snapshot_id.

        :param server: server instance
        :param snapshot_id: snapshot id
        :return: True
        :raise VsphereError:
        """
        try:
            if server.snapshot is None:
                self.logger.error("Snapshot %s does not exist" % snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg="Snapshot %s does not exist" % snapshot_id)

            sn = self.__get(server, None, snapshot_id)
            if sn is None:
                self.logger.error("Snapshot %s does not exist" % snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg="Snapshot %s does not exist" % snapshot_id)

            sn.RenameSnapshot(name=name, description=description)
            return True
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def revert(self, server, snapshot_id, suppress_power_on=False):
        """Revert to server snapshot snapshot_id.

        :param server: server instance
        :param snapshot_id: snapshot id
        :param suppress_power_on: (optional) If set to true, the virtual machine will not be powered on regardless of
            the power state when the snapshot was created. Default to false.
        :return: task
        :raise VsphereError:
        """
        try:
            if server.snapshot is None:
                self.logger.error("Snapshot %s does not exist" % snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg="Snapshot %s does not exist" % snapshot_id)

            sn = self.__get(server, None, snapshot_id)
            if sn is None:
                self.logger.error("Snapshot %s does not exist" % snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg="Snapshot %s does not exist" % snapshot_id)

            task = sn.snapshot.RevertToSnapshot_Task(suppressPowerOn=suppress_power_on)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def remove(self, server, snapshot_id):
        """Remove server snapshot snapshot_id.

        :param server: server instance
        :param snapshot_id: snapshot id
        :return: task
        :raise VsphereError:
        """
        try:
            if server.snapshot is None:
                self.logger.error("Snapshot %s does not exist" % snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg="Snapshot %s does not exist" % snapshot_id)

            sn = self.__get(server, None, snapshot_id)
            if sn is None:
                self.logger.error("Snapshot %s does not exist" % snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg="Snapshot %s does not exist" % snapshot_id)

            task = sn.snapshot.RemoveSnapshot_Task(removeChildren=True, consolidate=True)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)
