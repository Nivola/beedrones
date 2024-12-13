# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

import traceback
from pyVmomi import vim, vmodl
from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereServerHardware(VsphereObject):
    """
    Get and modify Vsphere server hardware.
    """

    def __init__(self, server):
        VsphereObject.__init__(self, server.manager)
        self.server = server

    @staticmethod
    def pci_controller_spec_add(pci_controller_key=100):
        """
        Return pci controller specification for add operation.
        """
        device = vim.vm.device.VirtualPCIController(key=pci_controller_key)
        return vim.vm.device.VirtualDeviceSpec(operation=vim.vm.device.VirtualDeviceSpec.Operation.add, device=device)

    @staticmethod
    def scsi_controller_spec_add(scsi_controller_key=5000):
        """
        Return scsi controller specification for add operation.
        """
        device = vim.vm.device.ParaVirtualSCSIController(
            key=scsi_controller_key, sharedBus=vim.vm.device.VirtualSCSIController.Sharing.noSharing
        )
        return vim.vm.device.VirtualDeviceSpec(device=device, operation=vim.vm.device.VirtualDeviceSpec.Operation.add)

    @staticmethod
    def virtual_disk_spec_add(scsi_device, disk_size_gb, disk_mode="persistent", thin_provisioned=True, unit_number=0):
        """
        Return virtual disk specification for add operation.
        """
        new_disk_kb = disk_size_gb * 1024**2
        backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo(diskMode=disk_mode, thinProvisioned=thin_provisioned)
        device = vim.vm.device.VirtualDisk(
            unitNuber=unit_number, capacityInKB=new_disk_kb, controllerKey=scsi_device.key, backing=backing
        )
        return vim.vm.device.VirtualDeviceSpec(
            fileOperation="create", device=device, operation=vim.vm.device.VirtualDeviceSpec.Operation.add
        )

    @staticmethod
    def cdrom_spec_add(ide_controller_key=200):
        """
        Return cdrom specification for add operation.
        """
        device = vim.vm.device.VirtualCdrom(
            controllerKey=ide_controller_key, backing=vim.vm.device.VirtualCdrom.IsoBackingInfo()
        )
        return vim.vm.device.VirtualDeviceSpec(device=device, operation=vim.vm.device.VirtualDeviceSpec.Operation.add)

    @staticmethod
    def net_card_spec_add(network, address_type="Generated", wake_on_lan=False):
        """
        Return network card specification for add operation.
        """
        port = vim.dvs.PortConnection(portgroupKey=network.key, switchUuid=network.config.distributedVirtualSwitch.uuid)
        device = vim.vm.device.VirtualVmxnet3(
            addressType=address_type,
            wakeOnLanEnabled=wake_on_lan,
            backing=vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo(port=port),
        )
        return vim.vm.device.VirtualDeviceSpec(device=device, operation=vim.vm.device.VirtualDeviceSpec.Operation.add)

    @staticmethod
    def build_network_device_spec(server, network):
        """
        Take the first network of server and modify it with new network informations.
        """
        device_spec = None
        if network is not None:
            # get old device network9
            old_device = next(a for a in server.config.hardware.device if isinstance(a, vim.vm.device.VirtualVmxnet3))
            if old_device is None:
                return device_spec
            switch_uuid = network.config.distributedVirtualSwitch.uuid
            port = vim.dvs.PortConnection(portgroupKey=network.key, switchUuid=switch_uuid)
            old_device.addressType = "Generated"
            old_device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo(port=port)
            old_device.deviceInfo.summary = "DVSwitch: " + switch_uuid
            device_spec = vim.vm.device.VirtualDeviceSpec(
                operation=vim.vm.device.VirtualDeviceSpec.Operation.edit, device=old_device
            )

        return device_spec

    @staticmethod
    def get_ethernet_card(server, net_label):
        """
        Get Ethernet card.

        :param server: server instance
        :param net_label: net label
        :return vim.vm.device.VirtualEthernetCard
        """
        devs = server.config.hardware.device
        inst_t = vim.vm.device.VirtualEthernetCard
        return next((d for d in devs if d.deviceInfo.label == net_label and isinstance(d, inst_t)), None)

    def get_nic_spec_instance(self, server, network, net_number=1):
        """
        Get Nic spec instance.

        :param server: server instance
        :param network: network
        :param net_number: integer
        :return vim.vm.device.VirtualDeviceSpec
        """
        # check network already attached
        net_label = f"Network adapter {net_number}"
        virtual_net_device = VsphereServerHardware.get_ethernet_card(server, net_label)
        port_connection = vim.dvs.PortConnection(
            portgroupKey=network.key, switchUuid=network.config.distributedVirtualSwitch.uuid
        )
        backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo(port=port_connection)

        device = None
        operation = None
        if virtual_net_device is not None:
            # configure existing network device
            operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            device = virtual_net_device
            self.logger.debug("Configure new network device %s to server %s", network.key, server.config.name)
        else:
            # add new network device
            operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            device = vim.vm.device.VirtualVmxnet3(addressType="Generated")
            self.logger.debug("Add new network device %s to server %s", network.key, server.config.name)
        device.wakeOnLanEnabled = False
        device.backing = backing
        device.connectable = vim.vm.device.VirtualDevice.ConnectInfo(
            startConnected=True, connected=True, allowGuestControl=True
        )
        nic_spec = vim.vm.device.VirtualDeviceSpec(operation=operation, device=device)
        return nic_spec

    @staticmethod
    def get_server_virtual_hw_version(server):
        """
        Get the vm virtual hw version.
        """
        guest = server.guest
        hw_version_str = guest.hwVersion
        hw_version = None
        if hw_version_str[0:4] == "vmx-":
            hw_version_str_num = hw_version_str[4:]
            try:
                hw_version = float(hw_version_str_num)
            except ValueError:
                pass
        return hw_version

    def get_server_scsi_devs_per_bus(self, server):
        """
        Get the number of devices supported by the Vsphere para virtual scsi bus.
        This depends by the virtual hw version.
        """
        hw_version = VsphereServerHardware.get_server_virtual_hw_version(server)
        scsi_devs_per_bus = 16
        for version, scsi_devs_per_bus in self.hw_version_to_scsi_devs_per_bus:
            if hw_version is not None and hw_version >= version:
                return scsi_devs_per_bus
        return scsi_devs_per_bus

    def get_max_scsi_devs_per_bus(self):
        """
        Get the max number of devices supported by the Vsphere para virtual scsi bus.
        """
        return self.hw_version_to_scsi_devs_per_bus[0][0]

    def raise_too_many_disk(self):
        """
        Raise many disk is used when user try to attach a new scsi device to the para virtual
        scsi bus and all the unit numbers are already used.
        """
        max_devs_per_bus = self.get_max_scsi_devs_per_bus()
        max_hw_version = self.get_max_hw_version()
        msg = (
            "Too many disks configured; please upgrade Virtual Hardware to version >= "
            + f"{max_hw_version} + to support up to {max_devs_per_bus} disks"
        )
        raise VsphereError(msg)

    def get_max_hw_version(self):
        """
        Get the max hw version supported by Vsphere.
        """
        return self.hw_version_to_scsi_devs_per_bus[0][1]

    def is_scsi_unit_number_free(self, server, unit_number):
        """
        Check that the unit number on paravirtual scsi controller is free.
        """
        devs_per_bus = self.get_server_scsi_devs_per_bus(server)
        if unit_number >= devs_per_bus:
            return False
        return True

    def get_available_hard_disk_unit_number(self, server):
        """
        Get available hard disk unit number.

        :param server: server instance
        :return: unit_number
        """
        # unit_number 7 reserved for scsi controller
        scsi_unit_number = 7
        # get all disks on a VM, set unit_number to the next available
        unit_numbers = []
        for dev in server.config.hardware.device:
            if hasattr(dev.backing, "fileName"):
                unit_numbers.append(int(dev.unitNumber))

        # find missing unit numbers if there are any
        unit_numbers = sorted(unit_numbers)
        missings = [
            n for n in range(unit_numbers[0], unit_numbers[-1] + 1) if n not in unit_numbers and n != scsi_unit_number
        ]
        if len(missings) > 0:
            unit_number = min(missings)
        else:
            unit_number = max(unit_numbers) + 1

        if unit_number == scsi_unit_number:
            unit_number += 1
        if not self.is_scsi_unit_number_free(server, unit_number):
            self.raise_too_many_disk()

        return unit_number

    @staticmethod
    def __populate_info_device_backing(info_dev, device):
        backing = device.backing
        datastore = backing.datastore
        backing_type = type(device).__name__
        if datastore is not None:
            info_dev["datastore"] = {
                "file_name": backing.fileName,
                "name": datastore.name,
                "id": VsphereServerHardware.get_mo_id(datastore),
                "sharing": backing.sharing,
                "disk_mode": backing.diskMode,
                "delta_grain_size": backing.deltaGrainSize,
                "delta_disk_format": backing.deltaDiskFormat,
            }
            if backing_type == "vim.vm.device.VirtualDisk.FlatVer2BackingInfo":
                info_dev["datastore"].update(
                    {
                        "write_through": backing.writeThrough,
                        "thin_provisioned": backing.thinProvisioned,
                        "split": backing.split,
                        "delta_disk_format_variant": backing.deltaDiskFormatVariant,
                        "digest_enabled": backing.digestEnabled,
                    }
                )
                if device.backing.parent is not None:
                    datastore_parent = {
                        "file_name": backing.parent.fileName,
                        "name": backing.parent.datastore.name,
                        "id": VsphereServerHardware.get_mo_id(backing.parent.datastore),
                        "write_through": backing.parent.writeThrough,
                        "thin_provisioned": backing.parent.thinProvisioned,
                        "split": backing.parent.split,
                        "sharing": backing.parent.sharing,
                        "disk_mode": backing.parent.diskMode,
                        "digest_enabled": backing.parent.digestEnabled,
                        "delta_grain_size": backing.parent.deltaGrainSize,
                        "delta_disk_format_variant": backing.parent.deltaDiskFormatVariant,
                        "delta_disk_format": backing.parent.deltaDiskFormat,
                    }
                    info_dev["datastore"].update({"parent": datastore_parent})
        return info_dev

    def __populate_info_for_device(self, info, device):
        info_dev = {
            "name": device.deviceInfo.label,
            "type": type(device).__name__,
            "key": device.key,
        }
        if device.backing is None:
            if type(device).__name__.find("Controller") > -1:
                info["other"]["controllers"].append(info_dev)
            elif isinstance(device, vim.vm.device.VirtualKeyboard):
                info["other"]["input_devices"].append(info_dev)
            elif isinstance(device, vim.vm.device.VirtualVideoCard):
                info["video"] = info_dev
            elif isinstance(device, vim.vm.device.VirtualVMCIDevice):
                info["other"]["pci"].append(info_dev)
        elif isinstance(device, vim.vm.device.VirtualPointingDevice):
            info_dev["backing"] = type(device.backing).__name__
            info["other"]["input_devices"].append(info_dev)
        elif isinstance(device, vim.vm.device.VirtualCdrom):
            info_dev["backing"] = type(device.backing).__name__
            if isinstance(device.backing, vim.vm.device.VirtualCdrom.IsoBackingInfo):
                datastore = device.backing.datastore
                if datastore is not None:
                    info["datastore"] = VsphereServerHardware.get_mo_id(datastore)
                info_dev["path"] = device.backing.fileName
            info["cdrom"] = info_dev
        elif isinstance(device, vim.vm.device.VirtualFloppy):
            info["floppy"] = info_dev
        elif isinstance(device, vim.vm.device.VirtualEthernetCard):
            info_dev.update(
                {
                    "unit_number": device.unitNumber,
                    "backing": type(device.backing).__name__,
                    "macaddress": device.macAddress,
                    "connected": device.connectable.connected,
                }
            )
            if hasattr(device.backing, "port"):
                port_group_ext_id = device.backing.port.portgroupKey
                dvp = self.manager.network.get_network(port_group_ext_id)
                cfg = dvp.config.defaultPortConfig
                info_dev["network"] = {
                    "id": port_group_ext_id,
                    "name": dvp.name,
                    "vlan": cfg.vlan.vlanId,
                    "dvs": VsphereServerHardware.get_mo_id(dvp.config.distributedVirtualSwitch),
                }
                info["network"].append(info_dev)
        elif isinstance(device, vim.vm.device.VirtualDisk):
            info_dev.update(
                {
                    "backing": type(device.backing).__name__,
                    "size": device.capacityInBytes / 1024 / 1024,
                    "flashcache": device.vFlashCacheConfigInfo,
                }
            )
            info_dev = VsphereServerHardware.__populate_info_device_backing(info_dev, device)
            info["storage"].append(info_dev)
        else:
            info["other"]["other"].append(info_dev)
        return info

    def get_config_data(self, server):
        """
        Get config data.

        :param server: server instance.
        """
        try:
            cfg = server.config
            vs_hw = server.config.hardware
            cpu_allocation = cfg.cpuAllocation
            cpu_shares = f"{cpu_allocation.shares.shares}({cpu_allocation.shares.level})"
            cpu_limit = cpu_allocation.limit if cpu_allocation.limit >= 0 else "unlimited"
            mem_reservation = f"{cfg.memoryAllocation.reservation} MB"
            mem_allocation = cfg.memoryAllocation
            mem_shares = f"{mem_allocation.shares.shares}({mem_allocation.shares.level})"
            mem_limit = mem_allocation.limit if mem_allocation.limit >= 0 else "unlimited"
            layout_files = [
                {"key": i.key, "name": i.name, "type": i.type, "size": i.size, "uniqueSize": i.uniqueSize}
                for i in server.layoutEx.file
            ]

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
                    "order": list(cfg.bootOptions.bootOrder),
                },
                "file_layout": {
                    "vmPathName": cfg.files.vmPathName,
                    "snapshotDirectory": cfg.files.snapshotDirectory,
                    "suspendDirectory": cfg.files.suspendDirectory,
                    "logDirectory": cfg.files.logDirectory,
                    "files": layout_files,
                },
                "cpu": {
                    "num": vs_hw.numCPU,
                    "core": vs_hw.numCoresPerSocket,
                    "reservation": f"{cfg.cpuAllocation.reservation} MHz",
                    "limit": cpu_limit,
                    "shares": cpu_shares,
                },
                "network": [],
                "storage": [],
                "other": {
                    "scsi_adapters": [],
                    "controllers": [],
                    "input_devices": [],
                    "pci": [],
                    "other": [],
                },
                "memory": {
                    "total": vs_hw.memoryMB,
                    "reservation": mem_reservation,
                    "limit": mem_limit,
                    "shares": mem_shares,
                },
            }

            for device in vs_hw.device:
                info = self.__populate_info_for_device(info, device)

        except Exception as error:
            self.logger.error(error, exc_info=False)
            info = {}

        return info

    def info(self, server):
        """
        Server hardware details: CPU, Ram, HD, Net, CD, Floppy, Video, Compatibility(vm version),
        Other(SCSI Adapters, Controllers, Input devices)
        """
        info = self.get_config_data(server)
        return info

    def get_devices(self, server, dev_type=None):
        """
        Get devices.

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
                    "diskObjectId": device.diskObjectId,
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
        Get hard disks.

        :return:
        """
        return [d for d in server.config.hardware.device if isinstance(d, vim.vm.device.VirtualDisk)]

    def get_original_devices(self, server, dev_type=None):
        """
        Get original devices.

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

    @staticmethod
    def __get_first_scsi_controller(server):
        return next(d for d in server.config.hardware.device if isinstance(d, vim.vm.device.VirtualSCSIController))

    def add_hard_disk(
        self, server, size, datastore, disk_type="thin", disk_unit_number=None, existing=False, backing_filename=None
    ):
        """
        Supported virtual disk backings:
        - Sparse disk format, version 1 and 2: The virtual disk backing grows when needed.
          Supported only for VMware Server.
        - Flat disk format, version 1 and 2: The virtual disk backing is preallocated.
          Version 1 is supported only for VMware Server.
        - Space efficient sparse disk format:
          The virtual disk backing grows on demand and incorporates additional space optimizations.
        - Raw disk format, version 2:
          The virtual disk backing uses a full physical disk drive to back the virtual
        disk. Supported only for VMware Server.
        - Partitioned raw disk format, version 2:
          The virtual disk backing uses one or more partitions on a physical disk drive to back a
          virtual disk. Supported only for VMware Server.
        - Raw disk mapping, version 1:
          The virtual disk backing uses a raw device mapping to back the virtual disk.
        Supported for ESX Server 2.5 and 3.x.

        @TODO: extend backing support. Now support only FlatVer2BackingInfo

        :param server: server instance
        :param size: disk size in GB
        :param datastore: datastore object
        :param disk_type: disk type [default=thick]
        :param disk_unit_number: disk unit number
        :param existing: if True add existing hard disk
        :param backing_filename: vdmk file to use
        """
        try:
            spec = vim.vm.ConfigSpec()
            controller = VsphereServerHardware.__get_first_scsi_controller(server)

            # add disk here
            new_disk_kb = int(size) * 1024**2
            if not VsphereServerHardware.__has_free_datastore_space(datastore, new_disk_kb):
                msg = (
                    f"Cannot add new disk of {size} GB of server {server.config.name}.\n"
                    "No space left on datastore {datastore}"
                )
                raise VsphereError(msg)
            backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo(datastore=datastore, diskMode="persistent")
            if disk_type == "thin":
                backing.thinProvisioned = True
            if existing:
                backing.fileName = backing_filename
            device = vim.vm.device.VirtualDisk(backing=backing, unitNumber=disk_unit_number, capacityInKB=new_disk_kb)
            disk_spec = vim.vm.device.VirtualDeviceSpec(
                fileOperation="create", operation=vim.vm.device.VirtualDeviceSpec.Operation.add, device=device
            )
            if controller is not None:
                disk_spec.device.controllerKey = controller.key
            spec.deviceChange = [disk_spec]
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug("Add new disk of %s GB, datastore %s, to server %s", size, datastore, server.config.name)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

        return task

    def add_network(self, server, network):
        """
        Add network.
        """
        try:
            port = vim.dvs.PortConnection(
                portgroupKey=network.key, switchUuid=network.config.distributedVirtualSwitch.uuid
            )
            backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo(port=port)
            device = vim.vm.device.VirtualVmxnet3(backing=backing, addressType="Generated", wakeOnLanEnabled=False)
            nic_spec = vim.vm.device.VirtualDeviceSpec(
                operation=vim.vm.device.VirtualDeviceSpec.Operation.add, device=device
            )
            task = server.ReconfigVM_Task(spec=vim.vm.ConfigSpec(deviceChange=[nic_spec]))
            self.logger.debug("Network %s added to %s", network.name, server.config.name)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

        return task

    @staticmethod
    def __get_virtual_disk_device(server, hdd_label):
        return next(
            d
            for d in server.config.hardware.device
            if d.deviceInfo.label == hdd_label and isinstance(d, vim.vm.device.VirtualDisk)
        )

    def update_hard_disk(self, server, disk_number, new_disk_kb=None):
        """
        Update server disk.

        :param server: server instance
        :param disk_number: Hard Disk Unit Number
        :param new_disk_kb: new size of the hard_disk [optional]
        :return: task
        """
        try:
            hdd_label = "Hard disk " + str(disk_number)
            virtual_hdd_device = VsphereServerHardware.__get_virtual_disk_device(server, hdd_label)
            if not virtual_hdd_device:
                raise VsphereError(f"Virtual {hdd_label} could not be found.")

            if new_disk_kb is not None:
                virtual_hdd_device.capacityInKB = new_disk_kb
            virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec(
                operation=vim.vm.device.VirtualDeviceSpec.Operation.edit, device=virtual_hdd_device
            )
            task = server.ReconfigVM_Task(spec=vim.vm.ConfigSpec(deviceChange=[virtual_hdd_spec]))
            self.logger.debug("Updated disk %s on server %s", hdd_label, server.name)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

    @staticmethod
    def __get_network_device(server, net_label):
        return next(
            d
            for d in server.config.hardware.device
            if d.deviceInfo.label == net_label and isinstance(d, vim.vm.device.VirtualEthernetCard)
        )

    @staticmethod
    def __build_backing(network):
        port = vim.dvs.PortConnection(portgroupKey=network.key, switchUuid=network.config.distributedVirtualSwitch.uuid)
        return vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo(port=port)

    def update_network(self, server, net_number, network=None, nic_start_connected=True, nic_connected=False):
        """
        Update server network.

        :param server:
        :param net_number:
        :param network:
        :param nic_start_connected:
        :param nic_connected:

        :return:
        """
        try:
            net_prefix_label = "Network adapter "
            net_label = net_prefix_label + str(net_number)

            virtual_net_device = VsphereServerHardware.__get_network_device(server, net_label)
            if not virtual_net_device:
                raise VsphereError(f"{net_label} could not be found.")

            virtual_net_device.wakeOnLanEnabled = False
            nic_spec = vim.vm.device.VirtualDeviceSpec(
                operation=vim.vm.device.VirtualDeviceSpec.Operation.edit, device=virtual_net_device
            )

            if network is not None:
                nic_spec.device.backing = VsphereServerHardware.__build_backing(network)

            nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo(
                startConnected=nic_start_connected, connected=nic_connected, allowGuestControl=True
            )

            task = server.ReconfigVM_Task(spec=vim.vm.ConfigSpec(deviceChange=[nic_spec]))
            self.logger.debug("Nic %s updated for server %s", net_label, server.name)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

        return task

    @staticmethod
    def __get_cdrom_dev(server, cdrom_label):
        return next(
            d
            for d in server.config.hardware.device
            if d.deviceInfo.label == cdrom_label and isinstance(d, vim.vm.device.VirtualCdrom)
        )

    def update_cdrom(self, server, cdrom_number, full_path_to_iso=None):
        """
        Updates Virtual Machine CD/DVD backend device.

        :param server: server instance
        :param cdrom_number: CD/DVD drive unit number
        :param full_path_to_iso: Full path to iso. i.e. "[ds1] folder/Ubuntu.iso"
        :return: True or false in case of success or error
        """
        try:
            cdrom_prefix_label = "CD/DVD drive "
            cdrom_label = cdrom_prefix_label + str(cdrom_number)
            virtual_cdrom_device = VsphereServerHardware.__get_cdrom_dev(server, cdrom_label)
            if not virtual_cdrom_device:
                raise VsphereError(f"Virtual {cdrom_label} could not be found.")

            device = vim.vm.device.VirtualCdrom(
                controllerKey=virtual_cdrom_device.controllerKey,
                key=virtual_cdrom_device.key,
                connectable=vim.vm.device.VirtualDevice.ConnectInfo(allowGuestControl=True),
            )
            virtual_cd_spec = vim.vm.device.VirtualDeviceSpec(
                operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
                device=device,
            )

            backing = None
            # if full_path_to_iso is provided it will mount the iso
            if full_path_to_iso:
                backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=full_path_to_iso)
                virtual_cd_spec.device.connectable.connected = True
                virtual_cd_spec.device.connectable.startConnected = True
            else:
                backing = vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo()

            virtual_cd_spec.device.backing = backing
            task = server.ReconfigVM_Task(spec=vim.vm.ConfigSpec(dev_changes=[virtual_cd_spec]))
            self.logger.debug("Cdorm %s updated for server %s", cdrom_label, server.name)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

        return task

    @staticmethod
    def __get_virtual_disk_by_unit_number(server, disk_number):
        """
        Get visrtual disk by unit number.

        :param server: server instance
        :param disk_number: Hard Disk Unit Number;
               this may be the position of disk on first scsi
               or the diskObjectId. These are the two ext_id
               that we use.
        :return: task
        """
        virtual_hdd_device = None
        positional = disk_number.isdigit() or isinstance(disk_number, int)
        for dev in server.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk):
                if not positional and dev.diskObjectId == disk_number:
                    virtual_hdd_device = dev
                    break
                if positional and dev.unitNumber == int(disk_number):
                    virtual_hdd_device = dev
                    break
        return virtual_hdd_device

    def delete_hard_disk(self, server, disk_number, delete_backing_file=True):
        """
        Delete hard disk.

        :param server: server instance
        :param disk_number: Hard Disk Unit Number
        :return: task
        """
        try:
            virtual_hdd_device = VsphereServerHardware.__get_virtual_disk_by_unit_number(server, disk_number)
            if not virtual_hdd_device:
                raise VsphereError(f"Virtual with unitNumber {disk_number} could not be found.")

            virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec(
                operation=vim.vm.device.VirtualDeviceSpec.Operation.remove, device=virtual_hdd_device
            )
            log_msg = f"Remove disk with unitNumber {disk_number} from server {server.name}"
            if delete_backing_file:
                virtual_hdd_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.destroy
                log_msg += " PRESERVING BACKING FILE"

            task = server.ReconfigVM_Task(spec=vim.vm.ConfigSpec(deviceChange=[virtual_hdd_spec]))
            self.logger.debug(log_msg)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

        return task

    @staticmethod
    def __has_free_datastore_space(datastore, size):
        datastore_summary = datastore.summary
        datastore_freespace_gb = datastore_summary.freeSpace
        if size < datastore_freespace_gb * 1024 * 1024:
            return True
        return False

    def extend_hard_disk(self, server, disk_number, size):
        """
        Extends the size of a volume to a requested size, in gibibytes (GiB).

        :param server: server instance
        :param disk_number: Hard Disk Unit Number
        :param size: Size in GiB
        :return: task
        """
        try:
            virtual_hdd_device = VsphereServerHardware.__get_virtual_disk_by_unit_number(server, disk_number)
            server_name = server.config.name
            if not virtual_hdd_device:
                msg = f"Cannot extend the volume {disk_number} of server {server_name}\n" "Volume not found."
                raise VsphereError(msg)
            size = int(size)
            old_disk_kb = virtual_hdd_device.capacityInKB
            old_disk_gb = old_disk_kb / 1024 / 1024
            new_disk_kb = size * 1024 * 1024
            msg = f"Cannot extend the volume {disk_number} of server {server_name} to {size} GB.\n"
            if new_disk_kb < old_disk_kb:
                msg += (
                    "It is an extends. You can only increase the volume size!" f"The volume size is {old_disk_gb} GB."
                )
                raise VsphereError(msg)

            datastore = virtual_hdd_device.backing.datastore
            if not VsphereServerHardware.__has_free_datastore_space(datastore, new_disk_kb - old_disk_kb):
                msg += f"No space left on datastore {datastore}"
                raise VsphereError(msg)

            virtual_hdd_device.capacityInKB = new_disk_kb
            virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec(
                operation=vim.vm.device.VirtualDeviceSpec.Operation.edit, device=virtual_hdd_device
            )
            task = server.ReconfigVM_Task(spec=vim.vm.ConfigSpec(deviceChange=[virtual_hdd_spec]))
            self.logger.debug("Extend the volume unit %s of server %s to %s GB", disk_number, server.config.name, size)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

    def delete_network(self, server, net_number):
        """
        Delete network.
        """
        try:
            net_prefix_label = "Network adapter "
            net_label = net_prefix_label + str(net_number)
            virtual_net_device = VsphereServerHardware.__get_network_device(server, net_label)
            if not virtual_net_device:
                raise VsphereError(f"{net_label} could not be found.")

            nic_spec = vim.vm.device.VirtualDeviceSpec(
                operation=vim.vm.device.VirtualDeviceSpec.Operation.remove, device=virtual_net_device
            )

            task = server.ReconfigVM_Task(spec=vim.vm.ConfigSpec(deviceChange=[nic_spec]))
            self.logger.debug("Remove network %s from server %s", net_label, server.name)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

    def build_main_dev_changes(self, server, network, net_number=1, disks=None):
        """
        Build main dev changes.
        """
        if disks is None:
            disks = []
        dev_changes = []
        # @TODO: detach cdrom if attached to file iso

        # configure network
        if network is not None:
            nic_spec = self.get_nic_spec_instance(server, network, net_number=net_number)
            dev_changes.append(nic_spec)

        main_disk = None
        controller = None
        unit_number = -1
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
            new_disk_kb = int(disk.get("size")) * 1024**2
            # add new disk
            if disk_type == "secondary":
                # unit_number 7 reserved for scsi controller
                if unit_number == 7:
                    unit_number += 1
                if not self.is_scsi_unit_number_free(server, unit_number):
                    self.raise_too_many_disk()
                # add disk here
                disk_spec = VsphereServerHardware.virtual_disk_spec_add(
                    controller, disk.get("size"), thin_provisioned=disk.get("thin", False), unit_number=unit_number
                )
                disk_spec.device.backing.datastore = disk.get("datastore")
                self.logger.debug(
                    "Add new disk of % GB, datastore %s, to server %s",
                    new_disk_kb,
                    disk.get("datastore"),
                    server.config.name,
                )
            # reconfigure main disk
            elif disk_type == "main":
                main_disk.capacityInKB = new_disk_kb
                disk_spec = vim.vm.device.VirtualDeviceSpec(
                    operation=vim.vm.device.VirtualDeviceSpec.Operation.edit, device=main_disk
                )
                dev_changes.append(disk_spec)
                self.logger.debug("Change main disk size to % GB for server %s", new_disk_kb, server.config.name)

        return dev_changes
