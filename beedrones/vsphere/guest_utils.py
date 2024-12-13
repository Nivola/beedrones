# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

import time
from datetime import datetime
from requests import get as req_get
from pyVmomi import vim, vmodl
from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereGuestUtils(VsphereObject):
    """
    VsphereCustomization is the class to handle the vsphere server customization.
    """

    def __init__(self, server):
        VsphereObject.__init__(self, server.manager)
        self.server = server

    def check_exit_command(self, pid_exitcode, pid, program, check_status_code, full_command=""):
        """
        Check process exit code.

        :param pid_exitcode:
        :param pid:
        :param program:
        :param check_status_code:
        :return:
        :raise VsphereError:
        """
        start_msg = f'Command "{full_command}" ("{program}") completed with'
        if check_status_code:
            if pid_exitcode == 0:
                self.logger.debug("%s success, PID is %s", start_msg, pid)
                return True
            # Look for non-zero code to fail
            msg = f"{start_msg} with wrong status code: {pid_exitcode}, PID is {pid}"
            raise VsphereError(msg)
        self.logger.warning("%s status code: %s, PID is %d", start_msg, pid_exitcode, pid)
        return True

    def guest_list_process(self, server, user, pwd, pids=None):
        """
        Get a list of active processes using guest tool.

        :param server: server instance
        :param user: user used to autenticate
        :param pwd: user password
        :param pids: list of process id. [optional]
        """
        VsphereGuestUtils.check_guest_tools(server)

        try:
            content = self.manager.si.RetrieveContent()
            creds = vim.vm.guest.NamePasswordAuthentication(username=user, password=pwd)
            process_manager = content.guestOperationsManager.processManager
            procs = process_manager.ListProcessesInGuest(server, creds, pids=pids)
            self.logger.warning("List of server %s processes: %s", server, procs)
            return procs
        except vmodl.MethodFault as error:
            raise VsphereError(error.msg) from error

    def __guest_list_processes(self, server, creds, pids=None, tollerant=True):
        default_res = 0, "1999"
        try:
            content = self.manager.si.RetrieveContent()
            process_manager = content.guestOperationsManager.processManager
            proc_info = process_manager.ListProcessesInGuest(server, creds, pids=pids)[0]
            self.logger.debug2(proc_info)
            return proc_info.exitCode, proc_info.endTime
        except Exception as exc:
            if tollerant:
                return default_res
            raise VsphereError("Unable to list processes with guest tools") from exc

    @staticmethod
    def check_guest_tools(server):
        """
        Check if guest tool is running. Raise exception if tool is not running.
        """
        # get guest tools status
        tools_status = server.guest.toolsRunningStatus
        if tools_status == "guestToolsNotRunning":
            msg = (
                "VMwareTools is either not running or not installed. "
                + "Rerun the script after verifying that VMwareTools is running"
            )
            raise VsphereError(msg)

    @staticmethod
    def check_guest_tools_is_updated(server):
        """
        Check if guest tools are updated.

        :return: True if guest tools are updated
        """
        if server.guest.toolsStatus != vim.vm.GuestInfo.ToolsStatus.toolsOk:
            msg = "VMwareTools is not updated. " + "Rerun the script after verifying that VMwareTools is updated"
            raise VsphereError(msg)

    def guest_read_environment_variable(self, server, user, pwd):
        """
        Get a list of environment variable using guest tool.

        :param server: server instance
        :param user: user used to authenticate
        :param pwd: user password
        """
        VsphereGuestUtils.check_guest_tools(server)
        try:
            content = self.manager.si.RetrieveContent()
            creds = vim.vm.guest.NamePasswordAuthentication(username=user, password=pwd)
            process_manager = content.guestOperationsManager.processManager
            env = process_manager.ReadEnvironmentVariableInGuest(server, creds)
            self.logger.debug("List of server %s environment variables: %s", server, env)
            return env
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg) from error

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
        stdout_redirect=None,
    ):
        """
        Execute a command over the server using guest tool.

        :param server: server instance
        :param user: user used to authenticate
        :param pwd: user password
        :param path_to_program: path to command to execute
        :param program_arguments: command arguments
        :param maxtime: max time in second you attend guest tools finish to run command.
                        After that time an error is raised [default=60]
        :param delta: interval in seconds between a check and the last check
                      of the process status [default=6]
        :param program: program description
        :param check_status_code: if True check exit status code
        :param stdout_redirect: file where redirect the stdout
        :return:
        """
        VsphereGuestUtils.check_guest_tools(server)

        try:
            content = self.manager.si.RetrieveContent()
            creds = vim.vm.guest.NamePasswordAuthentication(username=user, password=pwd)
            process_manager = content.guestOperationsManager.processManager
            if stdout_redirect is not None:
                program_arguments += f" > {stdout_redirect}"
            program_spec = vim.vm.guest.ProcessManager.ProgramSpec(
                programPath=path_to_program, arguments=program_arguments
            )
            pid = process_manager.StartProgramInGuest(server, creds, program_spec)

            if pid > 0:
                full_command = path_to_program + " " + program_arguments
                self.logger.debug('Command "%s" submitted, PID is %d', full_command, pid)
                pid_exitcode, p_endtime = self.__guest_list_processes(server, creds, pids=[pid])

                # If its not a numeric result code, it says None on submit
                elapsed = 0
                while p_endtime is None:
                    self.logger.debug('Command "%s" ("%s") running, PID is %d', full_command, program, pid)
                    time.sleep(delta)
                    elapsed += delta

                    # check elapsed
                    if elapsed > maxtime:
                        pid_exitcode = 1000
                        p_endtime = "1999"
                        msg = 'Command "%s" ("%s") completed with timeout, PID is %d'
                        self.logger.error(msg, full_command, program, pid)
                        break

                    # check process
                    pid_exitcode, p_endtime = self.__guest_list_processes(server, creds, pids=[pid])

                self.check_exit_command(pid_exitcode, pid, program, check_status_code, full_command=full_command)
            return pid
        except IOError as error:
            self.logger.error(error)
            raise VsphereError(error) from error
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg) from error

    def guest_sudo_execute_command(
        self,
        server,
        user,
        pwd,
        path_to_program="/bin/cat",
        program_arguments="/etc/network/interfaces",
        maxtime=90,
        delta=3,
        program="",
        check_status_code=True,
        stdout_redirect=None,
    ):
        """
        Execute a command with sudo over the server using guest tool.

        :param server: server instance
        :param user: user used to authenticate
        :param pwd: user password
        :param path_to_program: path to command to execute
        :param program_arguments: command arguments
        :param maxtime: max time in second you attend guest tools finish to run command.
                        After that time an error is raised [default=60]
        :param delta: interval in seconds between a check and the last check
                      of the process status [default=6]
        :param program: program description
        :param check_status_code: if True check exit status code
        :param stdout_redirect: file where redirect the stdout
        :return:
        """
        sudo_path_to_program = path_to_program
        sudo_program_arguments = program_arguments
        if VsphereGuestUtils.guest_is_linux(server) and user != "root":
            sudo_program_arguments = f"/bin/sh -c '{path_to_program} {program_arguments}'"
            sudo_path_to_program = "/usr/bin/sudo"
        return self.guest_execute_command(
            server,
            user,
            pwd,
            path_to_program=sudo_path_to_program,
            program_arguments=sudo_program_arguments,
            maxtime=maxtime,
            delta=delta,
            program=program,
            check_status_code=check_status_code,
            stdout_redirect=stdout_redirect,
        )

    def guest_powershell_execute_command(
        self,
        server,
        user,
        pwd,
        program_arguments="",
        maxtime=90,
        delta=3,
        program="powershell execute",
        check_status_code=True,
    ):
        """
        Execute a command in powershell over the server using guest tool.

        :param server: server instance
        :param user: user used to authenticate
        :param pwd: user password
        :param program_arguments: command arguments
        :param maxtime: max time in second you attend guest tools finish to run command.
                        After that time an error is raised [default=60]
        :param delta: interval in seconds between a check and the last check
                      of the process status [default=6]
        :param program: program description
        :param check_status_code: if True check exit status code
        :return:
        """
        prefix_arguments = "/C powershell -NonInteractive"
        return self.guest_execute_command(
            server,
            user,
            pwd,
            path_to_program="C:\\Windows\\System32\\cmd.exe",
            program_arguments=prefix_arguments + " " + program_arguments,
            maxtime=maxtime,
            delta=delta,
            program=program,
            check_status_code=check_status_code,
        )

    def exists_command(self, server, command_name, username, password, timeout=60):
        """
        Check that command exists in server.
        """
        out_file = "/tmp/out"
        out_redirection = "> " + out_file
        try:
            self.guest_execute_command(
                server,
                username,
                password,
                path_to_program="/usr/bin/which",
                program=f"is {command_name} installed",
                program_arguments=command_name + " " + out_redirection,
                check_status_code=False,
            )
        except VsphereError:
            return False
        creds = vim.vm.guest.NamePasswordAuthentication(username=username, password=password)
        file_manager = self.manager.si.RetrieveContent().guestOperationsManager.fileManager
        fti = file_manager.InitiateFileTransferFromGuest(server, creds, out_file)
        return req_get(fti.url, timeout=timeout, verify=False).text != ""

    @staticmethod
    def guest_is_windows(server):
        """
        Check if server family is windows using guest tool.

        :param server: server instance
        :return: True or False
        """
        return "window" in server.summary.config.guestFullName.lower()

    @staticmethod
    def guest_is_redhat_derivative(server):
        """
        Check if server use a distro derivative of Redhat, the package manager is yum.

        :param server: server instance
        :return: True or False
        """
        redhat_family = ("red hat", "redhat", "rhel", "centos", "fedora", "oracle", "alma", "rocky")
        return any(x in server.summary.config.guestFullName.lower() for x in redhat_family)

    @staticmethod
    def guest_is_debian_derivative(server):
        """
        Check if server use a distro derivative of Debian, the package manager is apt.

        :param server: server instance
        :return: True or False
        """
        debian_family = ("ubuntu", "debian")
        return any(x in server.summary.config.guestFullName.lower() for x in debian_family)

    @staticmethod
    def guest_is_linux(server):
        """
        Check if server family is linux using guest tool.

        :param server: server instance
        :return: True or False
        """
        return not (VsphereGuestUtils.guest_is_windows(server) or VsphereGuestUtils.guest_is_bsd_family(server))

    @staticmethod
    def guest_is_freebsd(server):
        """
        Check if server family is linux centos using guest tool.

        :param server: server instance
        :return: True or False
        """
        return "freebsd" in server.summary.config.guestFullName.lower()

    @staticmethod
    def guest_is_bsd_family(server):
        """
        Check if server is in bsd family using guest tool.

        :param server: server instance
        :return: True or False
        """
        return "bsd" in server.summary.config.guestFullName.lower()

    @staticmethod
    def disk_guest_info(vs_vm):
        """
        Disks info for server vm

        :param vs_vm: server instance
        :return: List of disks
        """
        return [
            {
                "diskPath": conf.diskPath,
                "capacity": f"{conf.capacity / 1024 ** 2}MB",
                "free_space": f"{conf.freeSpace / 1024 ** 2}MB",
            }
            for conf in vs_vm.disk
        ]

    @staticmethod
    def ip_stack_guest_info(vs_vm):
        """
        Ip  stack info for server vm

        :param vs_vm: server instance
        :return: List of ipstack
        """
        return [
            {
                "dns_config": {
                    "dhcp": conf.dnsConfig.dhcp,
                    "hostname": conf.dnsConfig.hostName,
                    "domainname": conf.dnsConfig.domainName,
                    "ip_address": list(conf.dnsConfig.ipAddress),
                    "search_domain": list(conf.dnsConfig.searchDomain),
                },
                "ip_route_config": [
                    {
                        "network": f"{c.network}/{c.prefixLength}",
                        "gateway": c.gateway.ipAddress,
                    }
                    for c in conf.ipRouteConfig.ipRoute
                ],
                "ipStackConfig": list(conf.ipStackConfig),
                "dhcpConfig": conf.dhcpConfig,
            }
            for conf in vs_vm.ipStack
        ]

    @staticmethod
    def net_guest_info(vs_vm):
        """
        Net nic info for server vm

        :param vs_vm: server instance
        :return: List of net
        """
        return [
            {
                "network": nic.network,
                "mac_address": nic.macAddress,
                "connected": nic.connected,
                "device_config_id": nic.deviceConfigId,
                "dnsConfig": nic.dnsConfig,
                "ip_config": {
                    "dhcp": nic.ipConfig.dhcp,
                    "ip_address": [f"{i.ipAddress}/{i.prefixLength}" for i in nic.ipConfig.ipAddress],
                },
                "netbios_config": nic.netBIOSConfig,
            }
            for nic in vs_vm.net
        ]

    @staticmethod
    def base_guest_info(vs_vm):
        """
        Base guest info for server vm

        :param vs_vm: server instance
        :return: dict
        """
        info = {
            "hostname": vs_vm.hostName,
            "ip_address": vs_vm.ipAddress,
            "tools": {
                "status": vs_vm.toolsStatus,
                "version_status": vs_vm.toolsVersionStatus,
                "version_status2": vs_vm.toolsVersionStatus2,
                "running_status": vs_vm.toolsRunningStatus,
                "version": vs_vm.toolsVersion,
            },
            "guest": {
                "id": vs_vm.guestId,
                "family": vs_vm.guestFamily,
                "fullname": vs_vm.guestFullName,
                "state": vs_vm.guestState,
                "app_heartbeat_status": vs_vm.appHeartbeatStatus,
                "guest_kernel_crashed": vs_vm.guestKernelCrashed,
                "app_state": vs_vm.appState,
                "operations_ready": vs_vm.guestOperationsReady,
                "interactive_operations_ready": vs_vm.interactiveGuestOperationsReady,
                "state_change_supported": vs_vm.guestStateChangeSupported,
                "generation_info": vs_vm.generationInfo,
            },
            "ip_stack": [],
            "nics": [],
            "disk": [],
            "screen": {"width": vs_vm.screen.width, "height": vs_vm.screen.height},
        }
        return info

    @staticmethod
    def is_linked_clone(server):
        """
        Check if virtual machine is a linked clone and return parent virtual machine

        :param server: server instance
        :return: dictionary with linked clone check and linked server name
        """
        name = server.name
        linked_server = None
        for item in server.layoutEx.file:
            # check if server contain backing file
            if name in item.name:
                # get parent server name
                start = item.name.index("] ") + 2
                end = item.name.index("/", start)
                linked_server = item.name[start:end]

        return {"linked": linked_server is not None, "parent": linked_server}

    @staticmethod
    def build_net_detail(device, fixed_ips, net_ips, ip_stack):
        """
        Build net detail

        :param device: nic device
        :param fixed_ips: fixed ips
        :param net_ips: net ips
        :param ip_stack: ip stack
        :return: List of net
        """
        mac = device.macAddress

        fixed_ipv4ss = net_ips.get(mac, [[]])
        if fixed_ipv4ss is not None and len(fixed_ipv4ss) > 0:
            fixed_ipv4s = fixed_ipv4ss[0]
        else:
            fixed_ipv4s = []

        fixed_ipv6ss = net_ips.get(mac, [[], []])
        if fixed_ipv6ss and len(fixed_ipv6ss) > 0:
            fixed_ipv6s = fixed_ipv6ss[0]
        else:
            fixed_ipv6s = []

        net = {
            "name": device.deviceInfo.label,
            "mac_addr": device.macAddress,
            "fixed_ips": fixed_ips,
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
            net_ext_id = VsphereGuestUtils.get_mo_id(device.backing.network)
            net["net_id"] = net_ext_id

        loopback_ip = "127.0.0.1"
        for conf in ip_stack:
            net["dns"] = [ip for ip in conf.dnsConfig.ipAddress if ip != loopback_ip]
        return net

    @staticmethod
    def build_vol_detail(device):
        """
        Build volume detail

        :param device: volume device
        :return: dict
        """
        backing = device.backing
        vol = {
            "bootable": None,
            "format": None,
            "id": backing.fileName,
            "disk_object_id": device.diskObjectId,
            "mode": backing.diskMode,
            "name": device.deviceInfo.label,
            "size": round(device.capacityInBytes / 1024**3, 0),
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
        return vol

    @staticmethod
    def build_vm_detail(vs_vm, networks, server_volumes, launched):
        """
        Build vm detail

        :param vs_vm: server instance
        :param networks: networks
        :param server_volumes: server volumes
        :param launched: launched
        :return: dict
        """
        vs_hw = vs_vm.config.hardware
        vsphere_managed = vs_vm.config.managedBy
        if vsphere_managed is not None:
            vsphere_managed = vars(vs_vm.config.managedBy)
        info = {
            "id": VsphereGuestUtils.get_mo_id(vs_vm),
            "parent": VsphereGuestUtils.get_mo_id(vs_vm.parent),
            "name": vs_vm.name,
            "overallStatus": vs_vm.overallStatus,
            "hostname": vs_vm.guest.hostName,
            "os": vs_vm.summary.config.guestFullName,
            "state": vs_vm.runtime.powerState,
            "flavor": {
                "id": None,
                "memory": vs_hw.memoryMB,
                "cpu": int(vs_hw.numCPU) * int(vs_hw.numCoresPerSocket),
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
            "vsphere:version": vs_vm.config.version,
            "vsphere:firmware": vs_vm.config.firmware,
            "vsphere:template": vs_vm.config.template,
            "vsphere:uuid": vs_vm.config.instanceUuid,
            "vsphere:managed": vsphere_managed,
            "vsphere:tools": {
                "status": vs_vm.guest.toolsRunningStatus,
                "version": vs_vm.guest.toolsVersion,
            },
            "vsphere:notes": vs_vm.config.annotation,
            "vsphere:vapp": None,
            "vsphere:linked": VsphereGuestUtils.is_linked_clone(vs_vm),
        }
        return info

    def disable_proxy_windows(self, server, user, pwd):
        """
        Disable proxy on Windows.

        :param server: server instance
        :param user: admin user name
        :param pwd: admin password
        """
        prop_name = "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
        params = f"Set-ItemProperty -Path '{prop_name}' -Name ProxyEnable -Value 0"
        self.guest_powershell_execute_command(
            server,
            user,
            pwd,
            program_arguments=params,
            program="disable http proxy",
        )

    def disable_proxy_linux(self, server, user, pwd):
        """
        Disable proxy on Linux.

        :param server: server instance
        :param user: admin user name
        :param pwd: admin password
        """
        self.guest_sudo_execute_command(
            server,
            user,
            pwd,
            path_to_program="/usr/bin/grep",
            program_arguments="-v -E http[s]?_proxy /etc/environment",
            program="disable proxy in environment",
        )
        if VsphereGuestUtils.guest_is_redhat_derivative(server):
            date = datetime.today().strftime("%Y-%m-%d")
            params = "/etc/yum.conf /etc/yum.conf." + date
            self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/cp",
                program_arguments=params,
                program="setup root ssh key",
            )
            self.logger.debug("create backup of yum .conf")
            params = f"'/^proxy/d' /etc/yum.conf.{date} > /etc/yum.conf"
            self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/sed",
                program_arguments=params,
                program="setup root ssh key",
            )
            self.logger.debug("create backup of yum .conf")
        elif VsphereGuestUtils.guest_is_debian_derivative(server):
            self.guest_sudo_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/rm",
                program_arguments="/etc/apt/apt.conf.d/proxy.conf",
                program="disable proxy for apt",
            )

    def disable_proxy(self, server, user, pwd):
        """
        Disable proxy.

        :param server: server
        :param user: admin user
        :param pwd: admin password
        """
        if VsphereGuestUtils.guest_is_windows(server):
            self.disable_proxy_windows(server, user, pwd)
        elif VsphereGuestUtils.guest_is_linux(server):
            self.disable_proxy_linux(server, user, pwd)

    @staticmethod
    def build_power_shell_proxy_commands(http_proxy):
        """
        Set proxy with powershell

        :param http_proxy: http proxy
        """
        prop_name = "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
        enable_cmd = f"Set-ItemProperty -Path '{prop_name}' -Name ProxyEnable -Value 1"
        http_proxy = http_proxy.replace("http://", "")
        set_cmd = f"Set-ItemProperty -Path '{prop_name}' -Name ProxyServer -Value '{http_proxy}'"
        return {"enable http proxy": enable_cmd, f"set http proxy {http_proxy}": set_cmd}

    def configure_proxy_windows(self, server, user, pwd, http_proxy):
        """
        Set proxy on Windows.

        :param http_proxy: http proxy
        """
        cmd_d = VsphereGuestUtils.build_power_shell_proxy_commands(http_proxy)
        for key, value in cmd_d.items():
            self.guest_powershell_execute_command(server, user, pwd, program_arguments=value, program=key)

    def configure_proxy_linux(self, server, user, pwd, http_proxy):
        """
        Set proxy on Linux.

        :param http_proxy: http proxy
        """
        content = f"export http_proxy={http_proxy}\nexport https_proxy={http_proxy}"
        self.guest_sudo_execute_command(
            server,
            user,
            pwd,
            path_to_program="/bin/echo",
            program_arguments=f"-e '{content}' >> /etc/environment",
            program="config proxy environment",
        )
        if VsphereGuestUtils.guest_is_debian_derivative(server):
            content = 'Acquire::http::Proxy "{http_proxy}";\nAcquire::https::Proxy "{http_proxy}";'
            self.guest_sudo_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=f"-e '{content}' > /etc/apt/apt.conf.d/proxy.conf",
                program="config proxy for apt",
            )
        if VsphereGuestUtils.guest_is_redhat_derivative(server):
            params = f"'proxy={http_proxy}' >> /etc/yum.conf"
            self.guest_sudo_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=params,
                program="config proxy for yum",
            )

    def configure_proxy(self, server, user, pwd, http_proxy):
        """
        Configure proxy.

        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param http_proxy: http proxy
        """
        self.disable_proxy(server, user, pwd)
        if VsphereGuestUtils.guest_is_windows(server):
            self.configure_proxy_windows(server, user, pwd, http_proxy)
        elif VsphereGuestUtils.guest_is_linux(server):
            self.configure_proxy_linux(server, user, pwd, http_proxy)

    def guest_info(self, vs_vm):
        """
        Guest info.

        :param vs_vm: server vm
        """
        info = VsphereGuestUtils.base_guest_info(vs_vm)
        info["disk"] = VsphereGuestUtils.disk_guest_info(vs_vm)
        info["ip_stack"] = VsphereGuestUtils.ip_stack_guest_info(vs_vm)
        info["nics"] = VsphereGuestUtils.net_guest_info(vs_vm)
        return info

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
        Please USE THIS METHOD ONLY IF IT IS NEED; THE NETWORK CONFIGURATION MUST BE DONE
        WITH VSPHERE API

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

        # bypass network configuration for windows os
        if VsphereGuestUtils.guest_is_windows(server):
            return

        if VsphereGuestUtils.guest_is_linux(server):
            # set hostname
            fqdn = hostname + "." + dns_search
            self.guest_sudo_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/hostname",
                program_arguments=fqdn,
                program="setup hostname: " + hostname,
            )
            params = f'-e "{fqdn}" > /etc/hostname'
            self.guest_sudo_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=params,
                program="setup hostname: " + hostname,
            )
            params = f'-e "{ipaddr} {fqdn} {hostname}" >> /etc/hosts'
            self.guest_sudo_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=params,
                program="setup hostname: " + hostname,
            )

        # delete connection with the same name
        if VsphereGuestUtils.guest_is_redhat_derivative(server):
            to_del = "`/bin/nmcli -t -f uuid,name con show |grep System |awk -F ':' '{print $1}'`"
            params = "con delete " + to_del
            self.guest_sudo_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/nmcli",
                program_arguments=params,
                program="delete active connection",
            )

            # create new connection
            params = f'con add type ethernet con-name {conn_name} ifname "*" mac {macaddr} \
        ip4 {ipaddr}/{prefix} gw4 {gateway}'

            self.guest_sudo_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/nmcli",
                program_arguments=params,
                program="configure network " + ipaddr,
            )

            # setup dns
            params = f'con modify {conn_name} ipv4.dns "{dns}" ipv4.dns-search {dns_search}'
            self.guest_sudo_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/nmcli",
                program_arguments=params,
                program="configure dns " + dns,
            )

            # restart network
            self.guest_sudo_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/systemctl",
                program_arguments="restart network",
                program="restart NetworkManager",
            )

        # Pre-requirements Debian template must have netplan installed.
        elif VsphereGuestUtils.guest_is_debian_derivative(server) or self.exists_command(server, "netplan", user, pwd):
            # Create netplan config file.
            dns_ips = dns.split(",")
            # Take the interface name.
            net_interface = "ens160"
            netplan_yaml = f"""
        network:
            version: 2
            ethernets:
                {net_interface}:
                    match:
                        macaddress: {macaddr}
                    set-name: {net_interface}
                    addresses:
                        - {ipaddr}/{prefix}
                    routes:
                        - to: 0.0.0.0/0
                          via: {gateway}
                    nameservers:
                        addresses:
                            - {dns_ips[0]}
                            - {dns_ips[1]}
                        search:
                            - {dns_search}
                    """
            self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/bin/echo",
                program_arguments=f'"{netplan_yaml}" > /etc/netplan/00-installer-config.yaml',
                program="create netplan config",
            )

            # apply netplan config
            self.guest_execute_command(
                server,
                user,
                pwd,
                path_to_program="/usr/sbin/netplan",
                program_arguments="apply",
                program="apply netplan config",
            )

        self.logger.debug(
            "Configure server network interface of server %s with mac %s and ip %s", server, macaddr, ipaddr
        )
