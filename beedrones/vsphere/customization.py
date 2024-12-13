# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

import time
import ssl
from requests import get as req_get
from OpenSSL import crypto
from pyVmomi import vim
from beecell.crypto import check_vault
from beedrones.vsphere.client import VsphereObject, VsphereError
from beedrones.vsphere.guest_utils import VsphereGuestUtils


class VsphereServerCustomization(VsphereObject):
    """
    VsphereCustomization is the class to handle the vsphere server customization.
    """

    def __init__(self, server):
        VsphereObject.__init__(self, server.manager)
        self.server = server
        self.guest_utils = VsphereGuestUtils(self)

    def get_vm_events(self, server, event_type_id_list):
        """
        Get vm events for vsphere.
        """
        by_entity = vim.event.EventFilterSpec.ByEntity(entity=server, recursion="self")
        filter_spec = vim.event.EventFilterSpec(entity=by_entity, eventTypeId=event_type_id_list)
        return self.manager.si.content.eventManager.QueryEvent(filter_spec)

    def wait_for_customization(self, server, timeout=600, interval=10):
        """
        Wait for the customization of a vsphere vm to complete.
        """
        poll = int(timeout // interval)
        thispoll = 0
        error_msg = ""
        customization_valid_exit_events = [
            "CustomizationFailed",
            "CustomizationLinuxIdentityFailed",
            "CustomizationNetworkSetupFailed",
            "CustomizationSucceeded",
            "CustomizationSysprepFailed",
            "CustomizationUnknownFailure",
        ]

        customization_start_event = "CustomizationStartedEvent"
        while thispoll <= poll:
            event_started = self.get_vm_events(server, [customization_start_event])
            if len(event_started) > 0:
                thispoll = 0
                events_finished_result = []
                while thispoll <= poll:
                    events_finished_result = self.get_vm_events(server, customization_valid_exit_events)
                    events_len = len(events_finished_result)
                    if events_len < 1:
                        time.sleep(interval)
                        thispoll += 1
                        continue
                    errors_msg = []
                    for event_finished_result in iter(events_finished_result):
                        if not isinstance(event_finished_result, vim.event.CustomizationSucceeded):
                            error_msg = "Customization failed with error: " + event_finished_result.fullFormattedMessage
                            self.logger.debug(error_msg)
                            errors_msg.append(error_msg)
                            continue
                        return True, "\n".join(errors_msg)
                    return False, "\n".join(errors_msg)
                if len(events_finished_result) == 0:
                    error_msg = "Waiting for customization result event timed out."
                    return False, error_msg
            else:
                time.sleep(interval)
                thispoll += 1
        if len(event_started) > 0:
            error_msg = "Waiting for customization result event timed out."
        else:
            error_msg = "Waiting for customization start event timed out."
        return False, error_msg

    def __cloud_init_customization_check(self, server, username, password, customization_type="LinuxPrep"):
        """
        Check the requirements to start the cloud init customization.
        """
        is_cloud_init = self.guest_utils.exists_command(server, "cloud-init", username, password)
        msg = f"VMware {customization_type} Customization requires "
        if customization_type == "LinuxPrep" and is_cloud_init:
            msg += "that you uninstall cloud-init\n"
            if VsphereGuestUtils.guest_is_debian_derivative(server):
                msg += "Please run 'apt-get purge cloud-init' and remove files under /etc/cloud"
            elif VsphereGuestUtils.guest_is_redhat_derivative(server):
                msg += "Please run 'yum remove cloud-init' and remove files under /etc/cloud"
            self.logger.error(msg, exc_info=False)
            raise VsphereError(msg)
        if customization_type == "CloudInitPrep" and not is_cloud_init:
            msg += "that you have cloud-init installed and configured\n"
            if VsphereGuestUtils.guest_is_debian_derivative(server):
                msg += "Run 'apt-get install cloud-init' and configure cloud-init under /etc/cloud"
            if VsphereGuestUtils.guest_is_redhat_derivative(server):
                msg += "Run 'yum install cloud-init' and configure cloud-init under /etc/cloud"
            self.logger.error(msg, exc_info=False)
            raise VsphereError(msg)

    def are_custom_scripts_enabled(self, server, username, password, timeout=60):
        """
        Check that the customization script are enabled.
        This is a pre requirements for LinuxPrep customization.
        It is done with the vmware_toolbox-cmd,
        username must be root or a sudoer non root usr.
        This code use the command directly if username is root or with sudo for other username.
        """
        out_file = "/tmp/out"
        bin_path = "/usr/bin"
        vmware_toolbox_binary = bin_path + "/vmware-toolbox-cmd"
        vmware_toolbox_arguments = "config get deployPkg enable-custom-scripts"
        path_to_program = vmware_toolbox_binary
        program_arguments = vmware_toolbox_arguments

        # check_status_code=False because if enable-custom-scripts is undef it return exit code 69.
        self.guest_utils.guest_sudo_execute_command(
            server,
            username,
            password,
            path_to_program=path_to_program,
            program="are custom scripts enabled",
            program_arguments=program_arguments,
            check_status_code=False,
            stdout_redirect=out_file,
        )
        creds = vim.vm.guest.NamePasswordAuthentication(username=username, password=password)
        file_manager = self.manager.si.RetrieveContent().guestOperationsManager.fileManager
        fti = file_manager.InitiateFileTransferFromGuest(server, creds, out_file)
        return "true" in req_get(fti.url, verify=False, timeout=timeout).text

    def __check_enable_custom_scripts(self, server, username, password, customization_type="LinuxPrep"):
        """
        Check if enable custom script are enabled.
        """
        custom_script_enabled = self.are_custom_scripts_enabled(server, username, password)
        if not custom_script_enabled:
            custom_script = "vmware-toolbox-cmd config set deployPkg enable-custom-scripts true"
            msg = (
                "VMware "
                + customization_type
                + " customization requires custom scripts enabled.\n"
                + "Please run on vm to be cloned: "
                + custom_script
            )
            self.logger.error(msg, exc_info=False)
            return False, msg
        return True, ""

    def __credential_check(self, server, username, password):
        """
        Check the credentials trying to do a minimal operation with guest tools.
        """
        if password is None:
            return False
        try:
            content = self.manager.si.RetrieveContent()
            process_manager = content.guestOperationsManager.processManager
            creds = vim.vm.guest.NamePasswordAuthentication(username=username, password=password)
            process_manager.ListProcessesInGuest(server, creds)
        except vim.fault.InvalidGuestLogin:
            return False
        return True

    def customization_prerequirements_check(self, server, username, password, customization_type="LinuxPrep"):
        """
        Run a doable subset of the customization vsphere prerequirements in our domain.
        NOTICE: Vsphere does not check nothing...
                Normal behavoiur is FAIL on error at the first vm boot
                when perl customization scripts.
                Pyvmomi does not pyvmomi doesn't return errors because has finished after
                vm build. Then we are not able to catch errors. The only way is see directly
                on hipervisor on events tab of the vm.
                Please update this comment when/if something change.
        """
        msg = ""
        result = False
        server_name = server.config.name
        are_credential_valid = self.__credential_check(server, username, password)
        if not are_credential_valid:
            msg = (
                f"I Can't check customization requirements for clone of vm {server_name}, "
                + "I need the correct username and password."
            )
            self.logger.error(msg, exc_info=False)
            return result, msg

        VsphereGuestUtils.check_guest_tools(server)
        # On windows do not check guest tools is updated because currently in all seen templates it is outdated.
        # This does not fault because sysprep customization is robust.
        # @TODO When all the templates have guest tools updated enable this check on Windows.
        if customization_type != "SysPrep":
            VsphereGuestUtils.check_guest_tools_is_updated(server)

        self.__cloud_init_customization_check(server, username, password, customization_type=customization_type)
        is_linux = VsphereGuestUtils.guest_is_linux(server)
        if is_linux:
            if customization_type == "LinuxPrep":
                result, msg = self.__check_enable_custom_scripts(server, username, password)
                if not result:
                    return result, msg
            if customization_type == "CloudInitPrep":
                msg = "Prerequirements check for cloudinit is not implemented yet"
                msg += "\nPlease fix your cloudinit file reading the vmware documentation\n"
                msg += """
                Reference: https://kb.vmware.com/s/article/80934
                rm -rf /etc/cloud/cloud.cfg.d/subiquity-disable-cloudinit-networking.cfg
                rm -rf /etc/cloud/cloud.cfg.d/99-installer.cf

                Below is an example of the begginning of the file /etc/cloud/cloud.cfg
                disable_vmware_customization: true
                datasource:
                  OVF:
                    allow_raw_data: true
                vmware_cust_file_max_wait: 100
                """
                return result, msg
        return True, ""

    @staticmethod
    def discriminate_customization_type(server):
        """
        Discriminate Customization type for vsphere  Windows uses SysPrep customization.
        Linux uses LinuxPrep customization on other possibility is use CloudInitPrep with Ubuntu;
        This code it is already set up to be integrated.

        :param server: vsphere server vim
        """
        debian_family_customization = "LinuxPrep"
        redhat_family_customization = "LinuxPrep"
        # Uncomment the line below in order to use CloudInit for Ubuntu
        # ubuntu_customization = "CloudInitPrep"
        if VsphereGuestUtils.guest_is_windows(server):
            return "SysPrep"
        if VsphereGuestUtils.guest_is_linux(server):
            if VsphereGuestUtils.guest_is_debian_derivative(server):
                return debian_family_customization
            if VsphereGuestUtils.guest_is_redhat_derivative(server):
                return redhat_family_customization
            return "LinuxPrep"
        if VsphereGuestUtils.guest_is_bsd_family(server):
            msg = "Unsupported customization; vmware does not support Bsd customization"
            raise VsphereError(msg)
        return None

    @staticmethod
    def __get_netplan_fix_cmd():
        """
        Rename netplan file with the same name of our template;
        The file because the Vsphere custom init scripts expect the file as 00-installer-config.yaml
        or the customization will FAIL.
        """
        return """
if [ -f /etc/netplan/99-netcfg-vmware.yaml ]; then
    /usr/bin/mv /etc/netplan/99-netcfg-vmware.yaml /etc/netplan/00-installer-config.yaml
fi"""

    @staticmethod
    def __get_debian_set_proxy_cmd(http_proxy, https_proxy):
        """
        This code put http(s) proxy in /etc/apt/apt.conf.d/proxy.conf.
        All handmade because not supported.
        REGARDS:
        - vspshere, netplan, cloud init do not allow to set a proxy.
        - http protocol is DEPRECATED
        - http(s) proxy MUST BE TRASPARENT; in this way we can neglect proxy setting on vm's.
        - http proxy is DEPRECATED
        """
        return f"""
if [[ -d /etc/apt/apt.conf.d && -f /etc/apt/apt.conf.d/proxy.conf ]]; then
    /usr/bin/echo 'Acquire::http::proxy "{http_proxy}";' > /etc/apt/apt.conf.d/proxy.conf
    /usr/bin/echo 'Acquire::https::proxy "{https_proxy}";' >> /etc/apt/apt.conf.d/proxy.conf
fi"""

    @staticmethod
    def __get_redhat_set_proxy_cmd(https_proxy):
        """
        This code put http(s) proxy in /etc/yum.conf.
        All handmade because not supported.
        REGARDS:
        - vspshere, netplan, cloud init do not allow to set a proxy.
        - http is DEPRECATED; pay attention to /etc/yum.conf this supports proxy option and it
          is used for https only.
        - http proxy is DEPRECATED
        - http(s) proxy MUST BE TRASPARENT; in this way we can neglect proxy setting on vm's.
        """
        return f"""
if [[ -f /etc/yum.conf ]]; then
    /usr/bin/sed -i '/^proxy/d' /etc/yum.conf  # Remove existing proxy lines
    /usr/bin/echo "proxy={https_proxy}" >> /etc/yum.conf
fi"""

    @staticmethod
    def __get_debian_derivative_postcust_cmds(http_proxy, https_proxy):
        postcust_commands_l = [VsphereServerCustomization.__get_netplan_fix_cmd()]
        if https_proxy is not None:
            deb_set_proxy_cmd_cmd = VsphereServerCustomization.__get_debian_set_proxy_cmd(http_proxy, https_proxy)
            postcust_commands_l.append(deb_set_proxy_cmd_cmd)
        return postcust_commands_l

    @staticmethod
    def __get_redhat_derivative_postcust_cmds(https_proxy):
        postcust_commands_l = []
        if https_proxy is not None:
            postcust_commands_l = [VsphereServerCustomization.__get_redhat_set_proxy_cmd(https_proxy)]
        return postcust_commands_l

    @staticmethod
    def __get_debian_derivative_precust_cmds():
        """
        Delete netplan configuration;
        if the vsphere customization find a netplan yaml different by 99-netcfg-vmware.yaml
        occurs a vsphere bug that create a new yaml and this cause a duplicate ip;
        usually in our domain ip of cloned vm plus the right one).
        There are two ways to work around this;
        1) call the netplan yaml in all templates as 99-netcfg-vmware.yaml
        2) remove the file.
        Current choice is 2) because a lot of cmp have the assumption that netplan file
        is called 00-installer-config.yaml.
        Then in postcustomization rename 99-netcfg-vmware.yaml in 00-installer-config.yaml.
        We can remove this patch when creation and our code don't make assumptions about
        the configuration file.
        """
        return ["rm -f /etc/netplan/*"]

    @staticmethod
    def __get_fix_resolv_conf_cmd():
        """
        If resolv.conf is not a symbolic link and is used systemd fix resolv.conf,
        if it is need.
        This fix need  to use dns server defined in netplan yml.
        We can remove this when all template and vm will be fixed.
        NOTICE: If you call this wrongly on a not systemd distro this do nothing.
        """
        return """
if [ -f /run/systemd/resolve/stub-resolv.conf ] && [ ! -L /etc/resolv.conf ]; then
    /usr/bin/rm /etc/resolv.conf
    /usr/bin/ln -s /run/systemd/resolve/stub-resolv.conf  /etc/resolv.conf
fi"""

    @staticmethod
    def __get_proxy_environment_cmd(http_proxy, https_proxy):
        """
        This code put http(s) proxy is /etc/environment.
        REGARDS: vspshere, netplan, cloud init do not allow to set a proxy.
        http(s) proxy MUST BE TRASPARENT; in this way we can neglect proxy setting on vm's.
        """
        return f"""
if [ -f /etc/environment ]; then
    /usr/bin/sed -i "/_proxy/d" /etc/environment
    /usr/bin/echo export http_proxy={http_proxy} >> /etc/environment
    /usr/bin/echo export https_proxy={https_proxy} >> /etc/environment
fi"""

    @staticmethod
    def __get_change_pwd_cmd(username, password):
        """
        This code change password and is the low level standard way on all Linux distro's.
        We use this because Vsphere customization does not allow to change password with with sysprep.
        """
        quoted_pwd = "".join(a if a.isalnum() else f"\\{a}" for a in password)
        return f"echo {username}:{quoted_pwd} | chpasswd"

    @staticmethod
    def __get_linux_sysprep_customization_script(precust_commands_l, postcust_commands_l):
        """
        This code build the Vsphere linux prep customization init for its "API".
        All this code is LEGACY and MUST be DEPRECATED when/id updated with present.
        """
        postcust_commands = "\n    ".join(postcust_commands_l)
        precust_commands = "\n    ".join(precust_commands_l)
        return f"""
#!/bin/bash
DEBUG_FILE=/var/log/customization
if [ $1 = "postcustomization" ]; then
    echo executing postscustomization  >> $DEBUG_FILE
    {postcust_commands}
elif [ $1 = "precustomization" ]; then
    echo executing precustomization  >> $DEBUG_FILE
    {precust_commands}
fi
echo executed customization scipt $1  >> $DEBUG_FILE
"""

    @staticmethod
    def __create_linux_prep_customization_script(server, password, http_proxy, https_proxy, username="root"):
        """
        NOTICE: all this code are hacks to use old vsphere, not idea about if something
        is fixed in the current Vsphere/pyvmomi  relase.
        IMPERATIVE PREREQUIREMENTS (consult Vsphere the others...):
        - guest tools running
        - cloud init uninstalled: "apt-get purge cloud-init" or similar
        - customization script enable:
            "vmware-toolbox-cmd config set deployPkg enable-custom-scripts true"
        This customization script is need for LinuxPrep, it does:
        - configure root password
        - configure http(s) proxy in /etc/environment ; LinuxPrep does not allow to configure proxies
        Further step for Debian derivatives (Ubuntu):
        - fix the actual template in order to fix the duplicate ip caused by netplan conf inherithed
          by the cloned vm (/etc/netplan/00-installer-config.yaml);
          may be that this can be removed after a rationalization of the code
        - configure http(s) proxy in /etc/apt/apt.conf.d; LinuxPrep does not allow to configure proxies
        Further step for Redhat derivatives (Ubuntu):
        - configure http(s) proxy in /etc/yum.conf; LinuxPrep does not allow to configure proxies
        """
        precust_commands_l = [VsphereServerCustomization.__get_fix_resolv_conf_cmd()]
        postcust_commands_l = []
        if https_proxy is not None:
            postcust_commands_l += [VsphereServerCustomization.__get_proxy_environment_cmd(http_proxy, https_proxy)]
        if VsphereGuestUtils.guest_is_debian_derivative(server):
            precust_commands_l += VsphereServerCustomization.__get_debian_derivative_precust_cmds()
            postcust_commands_l += VsphereServerCustomization.__get_debian_derivative_postcust_cmds(
                http_proxy, https_proxy
            )
        if VsphereGuestUtils.guest_is_redhat_derivative(server):
            # http proxy not passed because redhat/yum support only generic proxy used for http(s)
            # and http is DEPRECATED.
            postcust_commands_l += VsphereServerCustomization.__get_redhat_derivative_postcust_cmds(https_proxy)
        postcust_commands_l += [VsphereServerCustomization.__get_change_pwd_cmd(username, password)]
        return VsphereServerCustomization.__get_linux_sysprep_customization_script(
            precust_commands_l, postcust_commands_l
        )

    @staticmethod
    def __build_linux_prep_identity(
        server, host_name, password, domain, http_proxy=None, https_proxy=None, username="root"
    ):
        """
        Build LinuxPrep identity for LinuxPrep customization.
        We use this for Linux because Vsphere is not updated and have a limited cloud-init support
        and because all template are not compliantt with CloudInitPrep.
        This method works on Linux only.
        """

        script_text = None
        # Put script enabled to False if vsphere customization does need patch or put here script condition
        script_enabled = True
        if script_enabled:
            script_text = VsphereServerCustomization.__create_linux_prep_customization_script(
                server, password, http_proxy, https_proxy, username=username
            )
        identity = vim.vm.customization.LinuxPrep(
            hostName=host_name,
            domain=domain,
            timeZone="Europe/Rome",
            hwClockUTC=True,
            scriptText=script_text,
        )
        return identity

    @staticmethod
    def __netmask_to_cidr(netmask):
        """
        Convert netmask ip to cidr number.

        :param netmask: netmask ip addr (eg: 255.255.255.0)
        :return: equivalent cidr number to given netmask ip (eg: 24)
        """
        return sum(bin(int(x)).count("1") for x in netmask.split("."))

    @staticmethod
    def __build_cloud_init_identity(
        server,
        ip_addr,
        subnet_mask,
        gateway,
        host_name,
        password,
        domain,
        nameservers,
        http_proxy=None,
        https_proxy=None,
        username="root",
    ):
        """
        Build CloudInitPrep identity for CloudInit customization.
        This may be the future if Broadcom or our "companies" do not fail.
        This is a present and a probe to try new "MODERN" architecture.
        This was tested on Ubuntu only; all hypervisors and libraries are OUTDATED.

        Requirements: the vm must have:
        - guest tools running
        - pyvmomi >= 7.0.3 (back to the future),
          cloud-init must be configured correctly and raw data is allowed
        - rm -rf /etc/cloud/cloud.cfg.d/subiquity-disable-cloudinit-networking.cfg
        - rm -rf /etc/cloud/cloud.cfg.d/99-installer.cf
        Reference: https://kb.vmware.com/s/article/80934
        Below is an example of the begginning of the file /etc/cloud/cloud.cfg
            disable_vmware_customization: true
            datasource:
              OVF:
                allow_raw_data: true
            vmware_cust_file_max_wait: 100
        """
        userdata = ""
        if VsphereGuestUtils.guest_is_debian_derivative(server):
            userdata = f"""
#cloud-config
runcmd:
 - /usr/bin/mv /etc/netplan/50-cloud-init.yaml /etc/netplan/00-installer-config.yaml
 - /usr/sbin/netplan -apply
chpasswd:
 list: |
   {username}:{password}
 expire: False"""
            if https_proxy is not None or http_proxy is not None:
                userdata += """
write_files:
 - path: /etc/apt/apt.conf.d/proxy.conf
   permissions: 0640
   owner: root
   content: |
     Acquire::http { Proxy "%s"; };
     Acquire::https { Proxy "%s"; };
 - path: /etc/environment
   permissions: 0640
   owner: root
   content: |
     http_proxy=%s
     https_proxy=%s
""" % (
                    http_proxy,
                    https_proxy,
                    http_proxy,
                    https_proxy,
                )
        else:
            userdata = f"""
#cloud-config
chpasswd:
 list: |
   root:{password}
 expire: False"""

        cidr = ip_addr + "/" + VsphereServerCustomization.__netmask_to_cidr(subnet_mask)
        metadata = f"""
instance-id: {host_name.name}
local-hostname: {host_name.name}
network:
 version: 2
 ethernets:
   ens192:
     addresses: [{cidr}]
     gateway4: {gateway}
     nameservers:
       addresses:
         - {nameservers[0]}
         - {nameservers[1]}
       search:
         - {domain} """
        identity = vim.vm.customization.CloudinitPrep(metadata=metadata, userdata=userdata)
        return identity

    @staticmethod
    def __build_sys_prep_identity(password, host_name, domain):
        """
        Build SysPrep identity for SysPrep customization.
        This is used but all is DEPRECATED.
        Please port all the templates to cloud init and use this code
        after Vsphere upgrade.
        """
        gui_unattended = vim.vm.customization.GuiUnattended(autoLogon=False)
        if password is not None:
            pwd = vim.vm.customization.Password()
            # Such as creation... Security happiness!
            pwd.plainText = True
            pwd.value = password
            gui_unattended.password = pwd

        user_data = vim.vm.customization.UserData(
            computerName=host_name,
            # Ohhhh... compliant with the rest of code
            orgName="CSI Piemonte",
            fullName=host_name.name + "." + domain,
        )
        identity = vim.vm.customization.Sysprep(
            guiUnattended=gui_unattended, userData=user_data, identification=vim.vm.customization.Identification()
        )

        return identity

    @staticmethod
    def build_adapter(network_config):
        """
        Build adapter by network config.

        :param network_config: Example of network parameters to use {
                "ip_address":"192.168.216.120", "ip_netmask":"255.255.255.0",
                "ip_gateway":"192.168.216.1", "dns_server_list":"['10.103.48.1', '10.103.48.2']",
                "dns_domain":"tenant-demo.site03.nivolapiemonte.csi.it"
            }
        """
        if network_config is None:
            return None
        adapter = vim.vm.customization.IPSettings()
        adapter.ip = vim.vm.customization.FixedIp()
        adapter.ip.ipAddress = network_config["ip_address"]
        adapter.subnetMask = network_config["ip_netmask"]
        adapter.gateway = network_config["ip_gateway"]
        adapter.dnsServerList = network_config["dns_server_list"]
        adapter.dnsDomain = network_config["dns_domain"]
        return adapter

    @staticmethod
    def __build_adaptermap(ip_addr, subnet_mask, gateway, domain, nameservers):
        """
        Build adapter map. This represents the tcp/ip settings on device.
        """
        adaptermap = None
        if ip_addr is not None:
            fixed_ip = vim.vm.customization.FixedIp(ipAddress=ip_addr)
            adapter = vim.vm.customization.IPSettings(ip=fixed_ip)
            if subnet_mask is not None:
                adapter.subnetMask = subnet_mask
            if gateway is not None:
                adapter.gateway = gateway
            if nameservers is not None and len(nameservers) > 0:
                adapter.dnsServerList = nameservers
            if domain is not None:
                adapter.dnsDomain = domain
            adaptermap = vim.vm.customization.AdapterMapping(adapter=adapter)
        return adaptermap

    @staticmethod
    def __build_identity(
        customization_type,
        server,
        ip_addr,
        subnet_mask,
        gateway,
        host_name,
        username,
        password,
        domain,
        nameservers,
        http_proxy,
        https_proxy,
    ):
        """
        Build Vsphere identity.
        """
        identity = None
        if customization_type != "SysPrep":
            if customization_type == "LinuxPrep":
                # WARNING: To be used without cloudinit installed;
                # if cloudinit is installed does not start the customization.
                # This might be the past but for us is the present.
                identity = VsphereServerCustomization.__build_linux_prep_identity(
                    server,
                    host_name,
                    password,
                    domain,
                    http_proxy=http_proxy,
                    https_proxy=https_proxy,
                    username=username,
                )
            elif customization_type == "CloudInitPrep":
                # To be used when vsphere and pyvmomi >= 7.0.3 with cloudinit configured correctly
                # Shortly this may be the present but may be the future.
                identity = VsphereServerCustomization.__build_cloud_init_identity(
                    server,
                    ip_addr,
                    subnet_mask,
                    gateway,
                    host_name,
                    password,
                    domain,
                    nameservers,
                    http_proxy=http_proxy,
                    https_proxy=https_proxy,
                )
        else:
            # Customization for Windows
            identity = VsphereServerCustomization.__build_sys_prep_identity(password, host_name, domain)
        return identity

    @staticmethod
    def get_service_locator(client_dest):
        """
        Instantiate a service locator taking the connection info and credential from client.
        """
        conn = client_dest.vcenter_conn
        password = check_vault(conn["pwd"], client_dest.key)
        vc_cert = ssl.get_server_certificate((conn["host"], conn["port"]))
        vc_pem = crypto.load_certificate(crypto.FILETYPE_PEM, vc_cert)
        ssl_thumbprint = vc_pem.digest("sha1").decode()
        service_locator = vim.ServiceLocator(
            url=f"https://{client_dest.vsphere_id}/sdk",
            sslThumbprint=ssl_thumbprint,
            instanceUuid=client_dest.si.content.about.instanceUuid,
            credential=vim.ServiceLocatorNamePassword(username=conn["user"], password=password),
        )
        return service_locator

    @staticmethod
    def build_customization(
        server,
        password,
        ip_addr,
        subnet_mask,
        gateway,
        hostname,
        domain,
        nameservers,
        http_proxy,
        https_proxy,
        customization_type="LinuxPrep",
        username="root",
    ):
        """
        Build Vsphere customization.
        """
        customization = vim.vm.customization.Specification()
        adaptermap = VsphereServerCustomization.__build_adaptermap(ip_addr, subnet_mask, gateway, domain, nameservers)

        customization.identity = VsphereServerCustomization.__build_identity(
            customization_type,
            server,
            ip_addr,
            subnet_mask,
            gateway,
            vim.vm.customization.FixedName(name=hostname),
            username,
            password,
            domain,
            nameservers,
            http_proxy,
            https_proxy,
        )
        global_ip_settings = vim.vm.customization.GlobalIPSettings()
        global_ip_settings.dnsServerList = nameservers
        global_ip_settings.dnsSuffixList = [domain]
        customization.globalIPSettings = global_ip_settings
        customization.nicSettingMap = [adaptermap] if adaptermap is not None else []
        return customization

    def build_custom_spec(
        self,
        server,
        customization_spec_name,
        network_config,
        host_name,
        admin_pwd,
        admin_username="root",
        http_proxy=None,
        https_proxy=None,
    ):
        """
        Build vsphere custom spec.
        """
        if host_name is None or admin_pwd is None:
            raise VsphereError("host_name or admin_pwd cannot be None")
        cust_spec = None
        if self.guest_utils.guest_is_windows(server):
            cust = self.manager.si.content.customizationSpecManager.GetCustomizationSpec(customization_spec_name)
            cust.spec.nicSettingMap[0].adapter = VsphereServerCustomization.build_adapter(network_config)
            cust.spec.identity.userData.computerName.name = host_name
            cust.spec.identity.guiUnattended.password.plainText = True
            cust.spec.identity.guiUnattended.password.value = admin_pwd
            if http_proxy is not None:
                cmd_d = VsphereGuestUtils.build_power_shell_proxy_commands(http_proxy)
                commands = cust.spec.identity.guiRunOnce.commandList
                new_commands = (
                    [c for c in commands if c != "logoff"]
                    + [f"powershell.exe {v}" for k, v in cmd_d.items()]
                    + ["logoff"]
                )
                cust.spec.identity.guiRunOnce.commandList = new_commands
            cust_spec = cust.spec
        else:
            customization_type = VsphereServerCustomization.discriminate_customization_type(server)
            cust_spec = VsphereServerCustomization.build_customization(
                server,
                admin_pwd,
                network_config["ip_address"],
                network_config["ip_netmask"],
                network_config["ip_gateway"],
                host_name,
                network_config["dns_domain"],
                network_config["dns_server_list"],
                http_proxy,
                https_proxy,
                customization_type=customization_type,
                username=admin_username,
            )
        return cust_spec
