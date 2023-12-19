# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereSystem(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

        self._nsx = VsphereSystemNsx(manager)

    @property
    def nsx(self):
        if self.manager.nsx is None:
            raise VsphereError("Nsx is not configured")
        else:
            return self._nsx

    def has_nsx(self):
        if self.manager.nsx is not None:
            return True
        else:
            return False

    def ping_vsphere(self):
        """Ping vsphere.

        :return: True if ping ok, False otherwise
        """
        try:
            self.manager.si.content.sessionManager.currentSession
            self.logger.info("Ping vsphere %s : OK" % self.manager.vsphere_id)
        except Exception as error:
            self.logger.error("Ping vcenter %s : KO" % self.manager.vsphere_id)
            return False
        return True

    def ping_nsx(self):
        """Ping nsx.

        :return: True if ping ok, False otherwise
        """
        try:
            self.nsx.info()
            self.logger.info("Ping nsx %s : OK" % self.manager.nsx_id)
        except Exception as error:
            self.logger.error("Ping nsx %s : KO" % self.manager.nsx_id)
            return False
        return True

    def ping(self):
        """Ping all components

        :return: True if ping ok, False otherwise
        """
        res = self.ping_vsphere()
        if self.has_nsx() is True:
            res = res and self.ping_nsx()
        self.logger.info("Ping vsphere: %s" % res)
        return res

    def version(self):
        """Get vsphere version

        :return: {'nsx':.., 'vcenter':.. }
        """
        version = {"nsx": None, "vcenter": None}
        if self.has_nsx():
            nsx_info = self.nsx.info().get("globalInfo").get("versionInfo")
            version["nsx"] = "%s.%s.%s.%s" % (
                nsx_info["majorVersion"],
                nsx_info["minorVersion"],
                nsx_info["patchVersion"],
                nsx_info["buildNumber"],
            )

        about = self.manager.si.content.about
        version["vcenter"] = "%s.%s" % (about.version, about.build)
        self.logger.debug("vsphere version: %s" % version)
        return version


class VsphereSystemNsx(VsphereSystem):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def info(self):
        """ """
        res = self.call("/api/1.0/appliance-management/global/info", "GET", "")
        return res

    def global_info(self):
        """ """
        res = self.call("/api/1.0/appliance-management/global/info", "GET", "")
        return res

    def summary_info(self):
        """ """
        res = self.call("/api/1.0/appliance-management/summary/system", "GET", "")
        if "systemSummary" in res.keys():
            res = res.get("systemSummary")
        return res

    #
    # appliance management
    #
    def reboot_appliance(self):
        """Reboots the appliance manager."""
        res = self.call("/api/1.0/appliance-management/system/restart", "POST", "")
        return res

    def query_appliance_cpu(self):
        """Query Appliance Manager CPU"""
        res = self.call("/api/1.0/appliance-management/system/cpuinfo", "GET", "")
        return res

    def query_appliance_uptime(self):
        """Query Appliance Manager Uptime"""
        res = self.call("/api/1.0/appliance-management/system/uptime", "GET", "", parse=False)
        return res

    def query_appliance_memory(self):
        """Query Appliance Manager Memory"""
        res = self.call("/api/1.0/appliance-management/system/meminfo", "GET", "")
        return res

    def query_appliance_storage(self):
        """Query Appliance Manager Storage"""
        res = self.call("/api/1.0/appliance-management/system/storageinfo", "GET", "")
        return res

    # network, dns
    def query_appliance_network(self):
        """Query Network Information"""
        res = self.call("/api/1.0/appliance-management/system/network", "GET", "")
        return res

    def configure_appliance_dns(self, ipv4_address="", ipv6A_adress="", domain_list=""):
        """Configures DNS servers.

        :param ipv4_address:
        :param ipv4_address:
        :param domain_list:
        :return:
        :raise:
        """
        data = [
            "<dns>",
            "<ipv4Address>%s</ipv4Address>",
            "<ipv6Address>%s</ipv6Address>",
            "<domainList>%s</domainList>",
            "</dns>",
        ]
        data = "".join(data) % (ipv4_address, ipv6A_adress, domain_list)
        res = self.call(
            "/api/1.0/appliance-management/system/network/dns",
            "PUT",
            data,
            headers={"Content-Type": "text/xml"},
            timeout=60,
        )
        return res

    def delete_appliance_dns(self):
        """Deletes DNS servers."""
        res = self.call("/api/1.0/appliance-management/system/network/dns", "DELETE", "")
        return res

        # time settings

    def query_appliance_time_settings(self):
        """Retrieves time settings like timezone or current date and time with
        NTP server, if configured."""
        res = self.call("/api/1.0/appliance-management/system/timesettings", "GET", "")
        return res

    def configure_appliance_time_settings(self, ntp_server="", datetime="", timezone=""):
        """You can either configure time or specify the NTP server to be used
        for time synchronization.

        :param ntpServer:
        :param datetime:
        :param timezone:
        :return:
        :raise:
        """
        data = [
            "<timeSettings>",
            "<ntpServer>",
            "<string>%s</string>",
            "</ntpServer>",
            "<datetime>%s</datetime>",
            "<timezone>%s</timezone>",
            "</timeSettings>",
        ]
        data = "".join(data) % (ntp_server, datetime, timezone)
        res = self.call(
            "/api/1.0/appliance-management/system/timesettings",
            "PUT",
            data,
            headers={"Content-Type": "text/xml"},
            timeout=60,
        )
        return res

    def delete_appliance_time_settings(self):
        """Deletes NTP server."""
        res = self.call("/api/1.0/appliance-management/system/timesettings/ntp", "DELETE", "")
        return res

    # locals
    def query_appliance_local(self):
        """Retrieves locale information."""
        res = self.call("/api/1.0/appliance-management/system/locale", "GET", "")
        return res

    def configure_appliance_local(self, language="en", country="US", timezone=""):
        """Configures locale.

        :param language:
        :param country:
        :return:
        :raise:
        """
        data = [
            "<locale>",
            "<language>%s</language>",
            "<country>%s</country>",
            "</locale>",
        ]
        data = "".join(data) % (language, country)
        res = self.call(
            "/api/1.0/appliance-management/system/locale",
            "PUT",
            data,
            headers={"Content-Type": "text/xml"},
            timeout=60,
        )
        return res

        # syslog

    def query_appliance_syslog(self):
        """Retrieves syslog servers."""
        res = self.call("/api/1.0/appliance-management/system/syslogserver", "GET", "")
        return res

    def configure_appliance_syslog(self, hosname, port, protocol):
        """Configures syslog servers.

        If you specify a syslog server, NSX Manager sends all audit logs and
        system events from NSX Manager to the syslog server.

        :param hosname:
        :param port:
        :param protocol:
        :return:
        :raise:
        """
        data = [
            "<syslogserver>",
            "<syslogServer>%s</syslogServer>",
            "<port>%s</port>",
            "<protocol>%s</protocol>",
            "</syslogserver>",
        ]
        data = "".join(data) % (hosname, port, protocol)
        res = self.call(
            "/api/1.0/appliance-management/system/syslogserver",
            "PUT",
            data,
            headers={"Content-Type": "text/xml"},
            timeout=60,
        )
        return res

    def delete_appliance_syslog(self):
        """Deletes syslog servers."""
        res = self.call("/api/1.0/appliance-management/system/syslogserver", "DELETE", "")
        return res

    #
    # appliance components Components Management
    #
    def components_summary(self):
        """Retrieves summary of all available components available and their
        status information."""
        res = self.call("/api/1.0/appliance-management/summary/components", "GET", "")
        return res["componentsSummary"]

    def query_appliance_components(self):
        """Retrieves all Appliance Manager components."""
        res = self.call("/api/1.0/appliance-management/components", "GET", "")
        return res["components"]

    def query_appliance_component(self, component):
        """Retrieves details for the specified component id.

        :param component: component id
        """
        res = self.call(
            "/api/1.0/appliance-management/components/component/%s" % component,
            "GET",
            "",
        )
        return res

    def query_appliance_component_dependency(self, component):
        """Retrieves dependency details for the specified component id.

        :param component: component id
        """
        res = self.call(
            "/api/1.0/appliance-management/components/component/%s/dependencies" % component,
            "GET",
            "",
        )
        return res

    def query_appliance_component_status(self, component):
        """Retrieves current status for the specified component id.

        :param component: component id
        """
        res = self.call(
            "/api/1.0/appliance-management/components/component/%s/status" % component,
            "GET",
            "",
        )
        return res

    def toggle_appliance_component_status(self, component):
        """Toggles component status.

        :param component: component id
        """
        res = self.call(
            "/api/1.0/appliance-management/components/component/%s/toggleStatus/command" % component,
            "GET",
            "",
        )
        return res

    def restart_appliance_webapp(self):
        """Restarts appliance management web application."""
        res = self.call(
            "/api/1.0/appliance-management/components/component/APPMGMT/restart",
            "POST",
            "",
        )
        return res

    #
    # appliance backup
    #
    """You can back up and restore your NSX Manager data, which can include 
    system configuration, events, and audit log tables. Configuration tables are 
    included in every backup. Backups are saved to a remote location that must 
    be accessible by the NSX Manager.
    For information on backing up controller data, see Backup Controller Data
    on page 34."""

    # Configure Backup Settings
    # Configure On-Demand Backup
    # Query Backup Settings
    # Delete Backup Configuration
    # Query Available Backups
    # Restore Data

    #
    # Working with Tech Support Logs
    #

    #
    # Querying NSX Manager Logs
    #
    def get_system_events(self, start_index=0, page_size=10, sort_order_ascending=False):
        """You can retrieve NSX Manager system events.

        :param start_index: start index is an optional parameter which specifies
            the starting point for retrieving the logs. If this parameter is not
            specified, logs are retrieved from the beginning.
        :param page_size: page size is an optional parameter that limits the
            maximum number of entries returned by the API. The default value for
            this parameter is 256 and the valid range is 1-1024.
        :param sort_order_ascending: if False sort item descendant by id
        """
        res = self.call(
            "/api/2.0/systemevent?startIndex=%s&pageSize=%s&sortOrderAscending=%s"
            % (start_index, page_size, sort_order_ascending),
            "GET",
            "",
        )
        return res["pagedSystemEventList"]["dataPage"]

    def get_system_audit_logs(self, start_index=0, page_size=10, sort_order_ascending=False):
        """You can get NSX Manager audit logs.

        :param start_index: start index is an optional parameter which specifies
            the starting point for retrieving the logs. If this parameter is not
            specified, logs are retrieved from the beginning.
        :param page_size: page size is an optional parameter that limits the
            maximum number of entries returned by the API. The default value for
            this parameter is 256 and the valid range is 1-1024.
        :param sort_order_ascending: if False sort item descendant by id
        """
        res = self.call(
            "/api/2.0/auditlog?startIndex=%s&pageSize=%s&sortOrderAscending=%s"
            % (start_index, page_size, sort_order_ascending),
            "GET",
            "",
        )
        return res["pagedAuditLogList"]["dataPage"]

    #
    # Working with Support Notifications
    #

    #
    # transport_zones
    #
    def list_transport_zones(self):
        """ """
        res = self.call("/api/2.0/vdn/scopes", "GET", "")
        self.logger.debug("Get transport scopes: %s" % res)
        return res

    #
    # controller
    #
    def list_controllers(self):
        """Retrieves details and runtime status for controller.
        Runtime status can be one of the following:

        - Deploying: controller is being deployed and the procedure has not completed yet.
        - Removing: controller is being removed and the procedure has not completed yet.
        - Running: controller has been deployed and can respond to API invocation.
        - Unknown: controller has been deployed but fails to respond to API invocation.
        """
        res = self.call("/api/2.0/vdn/controller", "GET", "")
        resp = res["controllers"]["controller"]
        if isinstance(resp, list):
            return resp
        else:
            return [resp]

    def query_controller_progress(self, job_id):
        """Retrieves status of controller creation or removal. The progress
        gives a percentage indication of current deploy / remove procedure.
        """
        res = self.call("/api/2.0/vdn/controller/progress/job_id", "GET", "")
        return res

    def delete_controller(self, controller):
        """Deletes NSX controller. When deleting the last controller from a
        cluster, the parameter forceRemovalForLast must be set to true.

        :param controller: controller id
        """
        res = self.call("/api/2.0/vdn/controller/%s?forceRemoval=true" % controller, "DELETE", "")
        return res
