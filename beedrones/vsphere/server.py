# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

import ssl
import time
from six import ensure_text
from OpenSSL import crypto
from pyVmomi import vim, vmodl
from beecell.types.type_string import truncate
from beecell.simple import get_attrib
from beedrones.vsphere.client import VsphereObject, VsphereError
from beedrones.vsphere.hardware import VsphereServerHardware
from beedrones.vsphere.snapshot import VsphereServerSnapshot
from beedrones.vsphere.customization import VsphereServerCustomization
from beedrones.vsphere.guest_utils import VsphereGuestUtils


class VsphereServer(VsphereObject):
    """
    VsphereServer is the main class representing a vsphere vm.
    """

    from .client import VsphereManager

    def __init__(self, manager: VsphereManager):
        VsphereObject.__init__(self, manager)
        self.guest_utils = VsphereGuestUtils(self)
        self.customization = VsphereServerCustomization(self)
        self.hardware = VsphereServerHardware(self)
        self.snapshot = VsphereServerSnapshot(self)

    def get_by_morid(self, morid):
        """
        Get server by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        return self.manager.get_object(morid, [vim.VirtualMachine], None, recursive=True)

    def get_by_uuid(self, uuid):
        """
        Get server by uuid.
        """
        return self.manager.si.content.searchIndex.FindByUuid(None, uuid, True, True)

    def get_by_dnsname(self, name):
        """
        Get server by dnsname.
        """
        return self.manager.si.content.searchIndex.FindByDnsName(None, name, True)

    def get_by_name(self, name):
        """
        Get server by name.
        """
        return self.manager.get_object_by_name(name, [vim.VirtualMachine])

    def get_by_names(self, name):
        """
        Get server by name like.
        """
        return self.manager.get_objects_by_name(name, [vim.VirtualMachine])

    def get_by_ip(self, ipaddress):
        """
        Get server by ipaddress.
        """
        return self.manager.si.content.searchIndex.FindByIp(None, ipaddress, True)

    def __list(self, template=False):
        """
        Get servers with some properties.

        :param template: if True search only template server
        """
        manager = self.manager
        vm_data = manager.collect_properties(
            view_ref=manager.get_container_view(obj_type=[vim.VirtualMachine]),
            obj_type=vim.VirtualMachine,
            path_set=manager.server_props,
            include_mors=True,
        )
        return vm_data if not template else [v for v in vm_data if v.get("config.template")]

    def list(self, template=False, morid=None, uuid=None, name=None, names=None, ipaddress=None, dnsname=None):
        """
        List vm based on the non-None parameter and on some precedence.
        """
        res = []
        if morid is not None:
            res = [self.get_by_morid(morid)]
        elif uuid is not None:
            res = [self.get_by_uuid(uuid)]
        elif dnsname is not None:
            res = [self.get_by_dnsname(dnsname)]
        elif name is not None:
            res = [self.get_by_name(name)]
        elif names is not None:
            res = self.get_by_names(names)
        elif ipaddress is not None:
            res = [self.get_by_ip(ipaddress)]
        else:
            res = self.__list(template)
        return res

    def get(self, oid):
        """
        Alias of get_by_morid.
        """
        return self.get_by_morid(oid)

    def get_available_hard_disk_unit_number(self, server):
        """
        Get available hard disk unit number.

        :param server: server instance
        :return: unit_number
        """
        return self.hardware.get_available_hard_disk_unit_number(server)

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
        resource_pool=None,
        cluster=None,
    ):
        """
        Creates a VirtualMachine.

        :param name: String Name for the VirtualMachine
        :param guest_id: Guest id.
        :param datastore: DataStrore to place the VirtualMachine on
        :param folder: Folder to place the VirtualMachine in
        :param network: Network to attach
        :param memory_mb: Memory in Mb
        :param cpu: Number of cpu's
        :param core_x_socket:
        :param disk_size_gb: Disck size in Gb
        :param version: vmx-8 , vmx-9, vmx-10, vmx-11, vmx-14
        :param resource_pool: ResourcePool to place the VirtualMachine in [optional]
        :param cluster: cluster to place the VirtualMachine in [optional]
        """
        try:
            scsi_spec = VsphereServerHardware.scsi_controller_spec_add()
            dev_changes = [
                VsphereServerHardware.pci_controller_spec_add(),
                scsi_spec,
                VsphereServerHardware.virtual_disk_spec_add(scsi_spec.device, disk_size_gb),
                VsphereServerHardware.cdrom_spec_add(),
                VsphereServerHardware.net_card_spec_add(network),
            ]
            config = vim.vm.ConfigSpec(
                name=name,
                memoryMB=memory_mb,
                numCPUs=cpu,
                numCoresPerSocket=core_x_socket,
                deviceChange=dev_changes,
                files=vim.vm.FileInfo(vmPathName="[" + datastore + "] " + name),
                guestId=guest_id,
                version=version,
            )
            resource_pool = cluster.resourcePool if resource_pool is None and cluster is not None else None
            return folder.CreateVM_Task(config=config, pool=resource_pool)
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def wait_for_customization(self, server, timeout=600, interval=10):
        return self.customization.wait_for_customization(server, timeout=timeout, interval=interval)

    def create_clone(
        self,
        server,
        clone_name,
        hostname,
        domain_name,
        client_dest,
        dest_folder,
        dest_datastore,
        cluster,
        network,
        password,
        ip_addr,
        subnet,
        default_gw,
        dns_servers,
        http_proxy,
        https_proxy,
        power_on=True,
        source_vm_username="root",
        source_vm_password=None,
    ):
        """
        Clone a  VirtualMachine from another.
        Ref: https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.vsphere.vm_admin.doc/GUID-853B1E2B-76CE-4240-A654-3806912820EB.html

        :param server: server id of the vm that must be cloned
        :param clone_name: String Name for the new VirtualMachine
        :param hostname: Host name for the new VirtualMachine
        :param domain_name: Domain name for the new VirtualMachine
        :param client_dest: Vsphere Manager for the dest pod where put the ner VirtualMachine
        :param dest_folder: Folder to place the new VirtualMachine
        :param dest_datastore: Datastore to place the new VirtualMachine
        :param cluster: Cluster to place the new VirtualMachine
        :param network: Network to assign to the new VirtualMachine
        :param password: Admin password for the new VirtualMachine
        :param ip_addr: Ip Address for the new VirtualMachine
        :param subnet: Subnet Mask for the new VirtualMachine
        :param default_gw: Default gateway for the new VirtualMachine
        :param dns_servers: List of ip of the dns server for the new VirtualMachine
        :param http_proxy: Http proxy with format ip_addr:port for the new VirtualMachine
        :param https_proxy: Https proxy with format ip_addr:port for the new VirtualMachine
        :param power_on: if True power_on the new VirtualMachine
        :param source_vm_username: administration user of the source vm (used to check requirements)
        :param source_vm_password: administration pwd of the source vm (used to check requirements)
        """
        if not self.is_running(server):
            raise VsphereError(f"I Can't clone vm {server.config.name}, it must be powered on and running.")

        customization_type = VsphereServerCustomization.discriminate_customization_type(server)
        if customization_type is None:
            raise VsphereError("Unknown operating system; unsupported customization")

        status, msg = self.customization.customization_prerequirements_check(
            server, source_vm_username, source_vm_password, customization_type=customization_type
        )
        if not status:
            raise VsphereError(msg)

        customization = self.customization.build_customization(
            server,
            password,
            ip_addr,
            subnet,
            default_gw,
            hostname,
            domain_name,
            dns_servers,
            http_proxy,
            https_proxy,
            customization_type=customization_type,
            username=source_vm_username,
        )

        resource_pool = cluster.resourcePool if cluster is not None else None

        # Change the network device only if valid.
        network_device_spec = VsphereServerHardware.build_network_device_spec(server, network)
        dev_changes = [network_device_spec] if network_device_spec is not None else []

        # It moves all VMDK files to the new datastore specified in the relocateSpec.
        # The original source VM and new cloned VM have separate unshared copies of the VMDK files.
        # This avoids using delta disks or sharing VMDK files between source and clone.
        disk_move_type = vim.vm.RelocateSpec.DiskMoveOptions.moveAllDiskBackingsAndDisallowSharing

        # Create relocate spec.
        relocate_spec = vim.vm.RelocateSpec(
            datastore=dest_datastore,
            pool=resource_pool,
            # Service locator of vcenter destination
            service=self.customization.get_service_locator(client_dest),
            deviceChange=dev_changes,
            diskMoveType=disk_move_type,
        )

        clone_spec = vim.vm.CloneSpec(customization=customization, powerOn=power_on, location=relocate_spec)

        return server.CloneVM_Task(folder=dest_folder, name=clone_name, spec=clone_spec)

    def create_linked_clone(self, server, name, folder, datastore, power_on=False, resource_pool=None, cluster=None):
        """
        Clone a linked clone VirtualMachine from another.
        Ref: http://pubs.vmware.com/vsphere-60/index.jsp#com.vmware.wssdk.pg.doc/PG_VM_Manage.13.4.html#1115589
        https://www.vmware.com/support/ws55/doc/ws_clone_template_enabling.html

        :param name: String Name for the VirtualMachine
        :param folder: Folder to place the VirtualMachine in
        :param resource_pool: ResourcePool to place the VirtualMachine in [optional]
        :param cluster: cluster to place the VirtualMachine in [optional]
        :param server: parent VirtualMachine
        :param power_on: power_on status [default=False]
        """
        try:
            if resource_pool is None and cluster is not None:
                resource_pool = cluster.resourcePool

            # set relospec
            relospec = vim.vm.RelocateSpec(
                diskMoveType=vim.vm.RelocateSpec.DiskMoveOptions.createNewChildDiskBacking,
                datastore=datastore,
                pool=resource_pool,
            )

            clonespec = vim.vm.CloneSpec(
                location=relospec, powerOn=power_on, memory=False, snapshot=server.snapshot.currentSnapshot
            )

            return server.CloneVM_Task(folder=folder, name=name, spec=clonespec)
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def create_from_template(
        self,
        template,
        name,
        folder,
        datastore,
        power_on=False,
        resource_pool=None,
        cluster=None,
        customization=None,
    ):
        """
        Creates a VirtualMachine from template.

        :param template: template VirtualMachine
        :param name: String Name for the VirtualMachine
        :param datastore: Datastore
        :param folder: Folder to place the VirtualMachine in
        :param power_on: power_on status [default=False]
        :param resource_pool: ResourcePool to place the VirtualMachine in [optional]
        :param cluster: cluster to place the VirtualMachine in [optional]
        :param customization: guest operating system customization specification [optional]
        """
        try:
            resource_pool = cluster.resourcePool if resource_pool is None and cluster is not None else None
            relospec = vim.vm.RelocateSpec(datastore=datastore, pool=resource_pool)
            clonespec = vim.vm.CloneSpec(location=relospec, powerOn=power_on)
            if customization is not None:
                clonespec.customization = customization
            # e.g. "template: 'vim.VirtualMachine:vm-261924' - folder: 'vim.Folder:group-v279549'
            #        - name: PROVA-db-abcd-op-03-server01-avz714-6-server
            self.logger.debug("template: %s - folder: %s - name: %s", template, folder, name)
            return template.Clone(folder=folder, name=name, spec=clonespec)
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

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
        network_config=None,
    ):
        """
        Creates a VirtualMachine from template.

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
        :param network_config: Example of network parameters to use {
                "ip_address":"192.168.216.120", "ip_netmask":"255.255.255.0",
                "ip_gateway":"192.168.216.1", "dns_server_list":"['10.103.48.1', '10.103.48.2']",
                "dns_domain":"tenant-demo.site03.nivolapiemonte.csi.it"
            }
        """
        try:
            cust = self.customization.build_custom_spec(
                template, customization_spec_name, network_config, guest_host_name, guest_admin_pwd
            )
            resource_pool = cluster.resourcePool if resource_pool is None and cluster is not None else None
            # build the clone specification and add the customization spec and location spec to it
            clonespec = vim.vm.CloneSpec(
                powerOn=power_on,
                location=vim.vm.RelocateSpec(datastore=datastore, pool=resource_pool),
                customization=cust.spec,
            )
            return template.Clone(folder=folder, name=name, spec=clonespec)
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def customize(
        self,
        server,
        customization_spec_name,
        guest_host_name,
        guest_admin_pwd,
        network_config,
        guest_admin_username="root",
        http_proxy=None,
        https_proxy=None,
    ):
        """
        Apply a customization to a VirtualMachine.

        :param server: server object
        :param guest_host_name: hostname of the guest vm
        :param guest_admin_pwd: administrator password of the guest vm
        :param customization_spec_name: customization name to use
        :param network_config: Example of network parameters to use {
                "ip_address":"192.168.216.120", "ip_netmask":"255.255.255.0",
                "ip_gateway":"192.168.216.1", "dns_server_list":"['10.103.48.1', '10.103.48.2']",
                "dns_domain":"tenant-demo.site03.nivolapiemonte.csi.it"
            }
        """
        try:
            cust_spec = self.customization.build_custom_spec(
                server,
                customization_spec_name,
                network_config,
                guest_host_name,
                guest_admin_pwd,
                admin_username=guest_admin_username,
                http_proxy=http_proxy,
                https_proxy=https_proxy,
            )
            return server.CustomizeVM_Task(spec=cust_spec)
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def reconfigure(self, server, network, net_number=1, disks=None, **kvargs):
        """
        Change server configuration.

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
            dev_changes = self.hardware.build_main_dev_changes(server, network, net_number=net_number, disks=disks)
            self.logger.debug2(dev_changes)
            self.logger.debug("Start reconfigure server %s", server.config.name)
            return server.ReconfigVM_Task(spec=vim.vm.ConfigSpec(deviceChange=dev_changes, **kvargs))
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def update(self, server, name=None, notes=None):
        """
        Update.

        :param server: server instance. Get with get_by_****
        """
        try:
            spec = vim.vm.ConfigSpec()
            if notes is not None:
                spec.annotation = notes
            if name is not None:
                spec.name = name
            self.logger.debug("Updating server %s in vSphere", server)
            return server.ReconfigVM_Task(spec)
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def remove(self, server):
        """
        Remove, destroy.

        :param server: server instance. Get with get_by_****
        """
        try:
            self.logger.debug("Destroying server %s from vSphere", server)
            return server.Destroy_Task()
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def data(self, server):
        """
        Summary.
        """
        try:
            return self.detail(server)
        except Exception as error:
            return self.info(server)

    def get_status(self, server):
        """
        Get server status.
        """
        try:
            if isinstance(server, dict):
                return get_attrib(server, "runtime.powerState", "")
            else:
                return server.runtime.powerState
        except:
            return None

    def info(self, server):
        """
        Get server info.

        :param server: server object obtained from api request
        :return: dict like: {'cpu': 2, 'hostname': 'tst-beehive-04', 'id': 'vm-2287',
                 'ip_address': ['10.102.184.54'], 'memory': 2048, 'name': 'tst-beehive-04',
                 'os': 'CentOS 4/5/6/7(64-bit)', 'state': 'poweredOn', 'template': False,
                 'disk': None, 'disks': [] }
        """
        data = None
        try:
            # bytes in Gb
            b_in_gb = 1024**3
            if isinstance(server, dict):
                layout_ex_files = get_attrib(server, "layoutEx.file", [])
                # sum volumes in bytes and convert Gb
                disk_tot = sum(d.size for d in layout_ex_files if d.type == "diskExtent") / b_in_gb
                net_ipv4s = [n for n in get_attrib(server, "guest.net", []) if "." in n.ipAddress]
                data = {
                    "id": VsphereServer.get_mo_id(server.get("obj")),
                    "parent": VsphereServer.get_mo_id(server.get("parent")),
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
                disk_tot = sum(d.size for d in layout_ex_files if d.type == "diskExtent") / b_in_gb
                net_ipv4s = [n for n in server.guest.net if "." in n.ipAddress]
                server_config = server.config
                server_config_hw = server_config.hardware
                server_guest = server.guest
                data = {
                    "id": VsphereServer.get_mo_id(server),
                    "parent": VsphereServer.get_mo_id(server.parent),
                    "name": server.name,
                    "os": server_config.guestFullName,
                    "ram": server_config_hw.memoryMB,
                    "cpu": server_config_hw.numCPU,
                    "state": server.runtime.powerState,
                    "template": server_config.template,
                    "hostname": server_guest.hostName,
                    "ip_address": server_guest.ipAddress,
                    "ipv4_address": net_ipv4s,
                    "disk": disk_tot,
                    "disks": [],
                }
        except Exception as error:
            self.logger.error(error, exc_info=True)
        return data

    def detail(self, vs_vm):
        """
        Get server detail.

        :param vs_vm: server object; the vm
        :return: dict like
        """
        info = {}
        try:
            if not self.guest_tools_is_running(vs_vm):
                self.logger.warn(f"Guest tools are not running in vm {vs_vm}")

            server_volumes = []
            networks = []
            net_ips = {n.macAddress: n.ipAddress for n in vs_vm.guest.net}
            ip_address = vs_vm.guest.ipAddress
            ip_stack = vs_vm.guest.ipStack

            for device in vs_vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    networks.append(VsphereGuestUtils.build_net_detail(device, ip_address, net_ips, ip_stack))
                elif isinstance(device, vim.vm.device.VirtualDisk):
                    server_volumes.append(VsphereGuestUtils.build_vol_detail(device))

            boot_time = vs_vm.runtime.bootTime
            if boot_time is not None:
                launched = ensure_text(boot_time.strftime("%Y-%m-%dT%H:%M:%S"))
            else:
                launched = "NEVER"

            info = VsphereGuestUtils.build_vm_detail(vs_vm, networks, server_volumes, launched)

            parent_v_app = vs_vm.parentVApp
            if parent_v_app is not None:
                info["vsphere:vapp"] = {
                    "ext_id": VsphereServer.get_mo_id(parent_v_app),
                    "name": parent_v_app.name,
                }
        except Exception as error:
            self.logger.error(error, exc_info=True)
        return info

    def is_running(self, server):
        """
        Return if server is running
        """
        return self.info(server).get("state") == "poweredOn"

    def guest_info(self, server):
        """
        Server guest info.
        """
        return self.guest_utils.guest_info(server.guest)

    def network(self, server):
        """
        Server network.
        """
        return [{"id": VsphereServer.get_mo_id(n), "name": n.name, "type": type(n).__name__} for n in server.network]

    def volumes(self, server):
        """
        Get server volumes.

        :param server: server object
        :return: list of server volumes
        """
        server_volumes = []
        try:
            vs_hw = server.config.hardware
            for device in vs_hw.device:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    backing = device.backing
                    server_volumes.append(
                        {
                            "id": backing.fileName,
                            "disk_object_id": device.diskObjectId,
                            "mode": backing.diskMode,
                            "name": device.deviceInfo.label,
                            "size": round(device.capacityInBytes / 1024**3, 0),
                            "unit_number": device.unitNumber,
                            "thin": getattr(backing, "thinProvisioned", False),
                            "storage": getattr(backing.datastore, "name"),
                        }
                    )
        except Exception as error:
            self.logger.error(error, exc_info=True)
        return server_volumes

    def runtime(self, server):
        """
        Server runtime info.
        """
        res = {}
        try:
            vs_vm = server.runtime
            res = {
                "boot_time": vs_vm.bootTime,
                "resource_pool": {
                    "id": VsphereServer.get_mo_id(server.resourcePool),
                    "name": server.resourcePool.name,
                },
                "host": {
                    "id": VsphereServer.get_mo_id(vs_vm.host),
                    "name": vs_vm.host.name,
                    "parent_id": VsphereServer.get_mo_id(vs_vm.host.parent),
                    "parent_name": vs_vm.host.parent.name,
                },
            }
        except Exception as error:
            self.logger.error(error, exc_info=True)
        return res

    def usage(self, server):
        """
        Cpu, memory, storage usage.
        """
        res = {}
        try:
            res = server.summary.quickStats
        except Exception as error:
            self.logger.error(error, exc_info=True)
        return res

    def security_groups(self, server):
        """
        List server security groups

        :param server: Server instance
        """
        vmid = VsphereServer.get_mo_id(server)
        res = self.call("/api/2.0/services/securitygroup/lookup/virtualmachine/" + vmid, "GET", "")
        self.logger.debug(truncate(res))
        sec_group_ext = res.get("securityGroups", {})
        if sec_group_ext is not None:
            sec_group_int = sec_group_ext.get("securityGroups", {})
            if sec_group_int is not None:
                return sec_group_int.get("securitygroup", [])
        return {}

    def security_group_add(self, server, security_group, timeout=300):
        """
        Add security group to server

        :param server: Server instance
        :param security_group: Security group id
        """
        res = self.call(
            f"/api/2.0/services/securitygroup/{security_group}/members/{server}",
            "PUT",
            "",
            timeout=timeout,
        )
        self.logger.debug(truncate(res))
        return True

    def security_group_del(self, server, security_group, timeout=300):
        """Remove security group from server

        :param server: Server instance
        :param security_group: Security group id
        """
        res = self.call(
            f"/api/2.0/services/securitygroup/{security_group}/members/{server}",
            "DELETE",
            "",
            timeout=timeout,
        )
        self.logger.debug(truncate(res))
        return True

    def get_console_esxi_uri(self, server):
        """
        Get server remote console on esxi.

        :param server: Server instance
        :return:
        """
        data = server.AcquireTicket("webmks")
        return {
            "ticket": data.ticket,
            "cfgFile": data.cfgFile,
            "host": data.host,
            "port": data.port,
            "sslThumbprint": data.sslThumbprint,
            "uri": f"wss://{data.host}:{data.port}/ticket/{data.ticket}",
        }

    def remote_console(self, server):
        """
        Get server remote console.

        :param server: Server instance
        """
        try:
            content = self.manager.si.RetrieveContent()
            vm_moid = VsphereServer.get_mo_id(server)
            conn = self.manager.vcenter_conn
            host = conn["host"]
            port = conn["port"]
            server_name = server.name
            vc_cert = ssl.get_server_certificate((host, int(port)))
            vc_pem = crypto.load_certificate(crypto.FILETYPE_PEM, vc_cert)
            vc_fingerprint = vc_pem.digest("sha1")
            uri = f"""\
https://{host}:{port}/ui/webconsole.html?vmId={vm_moid}&vmName={server_name}&numMksConnections=0&\
serverGuid={content.about.instanceUuid}&host={host}:{port}&\
sessionTicket={content.sessionManager.AcquireCloneTicket()}&\
thumbprint={vc_fingerprint}&locale=it-IT\
"""
            self.logger.debug("Get remote console for server %s", server_name)
            return {"type": "webconsole", "url": uri}
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def guest_tools_is_running(self, server):
        """
        Check if guest tool is running.

        :return: True if guest tools are running
        """
        return server.guest.toolsRunningStatus == "guestToolsRunning"

    def wait_guest_tools_is_running(self, server, delta=3, maxtime=180):
        """
        Wait until guest tool is not running. After maxtime an exception is raised.

        :param server: server instance
        :param delta: Time to expect between call polling
        :param maxtime: Max time in call polling loop
        :return:
        """
        # wait until guest tools are running
        elapsed = 0
        self.logger.debug("Wait guest tools is running")
        while self.guest_tools_is_running(server) is not True:
            time.sleep(delta)
            elapsed += delta
            if elapsed > maxtime:
                raise VsphereError(f"Guest tools are not still running after {maxtime} s")
        self.logger.debug("Guest tools is running")

    def wait_guest_hostname_is_set(self, server, hostname, delta=3, maxtime=180):
        """
        Wait until guest hostname is set. After maxtime an exception is raised.

        :param server: server instance
        :param hostname: Hostname for server
        :param delta: Time to expect between call polling
        :param maxtime: Max time in call polling loop

        :return:
        """
        elapsed = 0
        self.logger.debug("Waiting setting guest hostname: %s with %s", server.guest.hostName, hostname)
        while server.guest.hostName != hostname:
            time.sleep(delta)
            elapsed += delta
            if elapsed > maxtime:
                msg = f"setting guest hostname take too long; exceeded maxtime of {maxtime} s"
                raise VsphereError(msg)
        self.logger.debug("Set guest hostname dome: %s with %s", server.guest.hostName, hostname)

    def guest_disable_firewall(self, server, pwd, user="administrator"):
        """
        Disable firewall.

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :return:
        """
        if VsphereGuestUtils.guest_is_windows(server):
            self.guest_utils.guest_powershell_execute_command(
                server,
                user,
                pwd,
                program_arguments="Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False",
                program="Disable firewall",
            )
            self.logger.debug("Disable firewall on server %s", server)

    def guest_setup_network(
        self,
        server,
        pwd,
        ipaddr,
        macaddr,
        gateway,
        hostname,
        dns,
        dns_search,
        conn_name="net01",
        user="root",
        prefix=24,
    ):
        """
        Setup server network.

        :param server: server mor object
        :param user: admin user
        :param ipaddr: ip address
        :param macaddr: mac address
        :param gateway: default gateway
        :param hostname: host name
        :param conn_name: connection name
        :param dns: dns list. Ex. '8.8.8.8,8.8.8.4'
        :param dns_search: dns search domain. Ex. local.domain
        :param pwd: admin password
        :param prefix: network prefix
        """
        self.guest_utils.guest_setup_network(
            server,
            pwd,
            ipaddr,
            macaddr,
            gateway,
            hostname,
            dns,
            dns_search,
            conn_name=conn_name,
            user=user,
            prefix=prefix,
        )

    def guest_destroy_network_config(self, server, pwd, ipaddr, user="root"):
        """
        Destroy server network configuration.

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param ipaddr: ip address
        """
        if VsphereGuestUtils.guest_is_windows(server):
            self.guest_utils.guest_powershell_execute_command(
                server,
                user,
                pwd,
                program_arguments=f"Remove-NetIPAddress -IPAddress {ipaddr} -Confirm false",
                program="destroy network configuration: " + ipaddr,
            )

    def guest_setup_install_software(self, server, user, pwd, pkgs=None):
        """
        Install software

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param pkgs: list of packages to install [optional]
        """
        package_manager = None
        base_pkgs = []
        if pkgs is None or len(pkgs) <= 0:
            pkgs = []
        if VsphereGuestUtils.guest_is_debian_derivative(server):
            base_pkgs = ["sshpass", "scsitools"]
            package_manager = "/usr/bin/apt-get"
        elif VsphereGuestUtils.guest_is_redhat_derivative(server):
            package_manager = "yum"
        if package_manager is not None:
            pkgs += base_pkgs
            pkgs_s = " ".join(pkgs)
            self.guest_utils.guest_sudo_execute_command(
                server,
                user,
                pwd,
                path_to_program=package_manager,
                program_arguments="install -y " + pkgs_s,
                program="install pkgs " + pkgs_s,
            )

    def guest_setup_admin_password(self, server, user, pwd, new_pwd, admin_username="root"):
        """
        Setup admin password (can be root or a non root sudoers)

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param new_pwd: new admin password
        :param admin_username: admin username
        """
        proc = None
        program = (f"setup {admin_username} password on sever {server}",)
        if VsphereGuestUtils.guest_is_linux(server):
            self.logger.debug(program)
            quoted_pwd = "".join(a if a.isalnum() else f"\\{a}" for a in new_pwd)
            proc = self.guest_utils.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=f"{admin_username}:{quoted_pwd} | chpasswd",
                program=program,
                check_status_code=False,
            )
        elif VsphereGuestUtils.guest_is_windows(server):
            program_arguments = f"""\
-Command "Set-LocalUser -Name {user} -Password (ConvertTo-SecureString -String '{new_pwd}' -AsPlainText -Force)"\
"""
            proc = self.guest_utils.guest_powershell_execute_command(
                server,
                user,
                pwd,
                program_arguments=program_arguments,
                program=program,
            )
        return proc

    def guest_setup_ssh_key(self, server, user, pwd, key, admin_username="root"):
        """
        Setup server ssh key for admin username (can be root or a non root sudoers)

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param key: ssh public key
        :param admin_username: admin username
        """
        proc = None
        if VsphereGuestUtils.guest_is_linux(server):
            authorized_keys_file_home = "/root"
            if admin_username != "root":
                authorized_keys_file_home = "/home/" + admin_username
            proc = self.guest_utils.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=f"-e {key} >> {authorized_keys_file_home}/.ssh/authorized_keys",
                program="setup root ssh key",
                check_status_code=False,
            )
            self.logger.debug("Setup server %s ssh key", server)
        return proc

    def disable_proxy(self, server, user, pwd):
        """
        Disable proxy.

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        """
        return self.guest_utils.disable_proxy(server, user, pwd)

    def configure_proxy(self, server, user, pwd, http_proxy):
        """
        Configure proxy.

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param http_proxy: http proxy
        """
        return self.guest_utils.configure_proxy(server, user, pwd, http_proxy)

    def start(self, server):
        """
        Start the vm.

        :param server: server instance. Get with get_by_****
        """
        try:
            self.logger.debug("Attempting to power on %s", server)
            return server.PowerOnVM_Task()
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def stop(self, server, interval=3):
        """
        Stop the vm.

        :param server: server instance. Get with get_by_****
        :param interval: sleep interval
        """
        try:
            from gevent import sleep

            virtual_machine: vim.VirtualMachine = server
            virtual_machine.ShutdownGuest()
            self.logger.debug("stop - Attempting to shutdown  %s", server)

            state = virtual_machine.runtime.powerState
            while format(state) != "poweredOff":
                sleep(interval)
                state = virtual_machine.runtime.powerState

            self.logger.debug("stop - Shutdown done, state %s", state)
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def reboot(self, server):
        """
        Reboot the vm.

        :param server: server instance. Get with get_by_****
        """
        try:
            self.logger.debug("Attempting to reboot %s", server)
            return server.RebootGuest()
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def suspend(self, server):
        """
        Suspend the vm.

        :param server: server instance. Get with get_by_****
        """
        try:
            self.logger.debug("Attempting to suspend %s", server)
            return server.SuspendVM_Task()
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def reset(self, server):
        """
        Reset the vm.

        :param server: server instance.
        """
        try:
            self.logger.debug("Attempting to reset %s", server)
            return server.ResetVM_Task()
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error
