# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

import time
import logging
from xmltodict import parse as xmltodict
import libvirt


class VirtDomainMonitorError(Exception):
    pass


class VirtDomainMonitor(object):
    """ """

    logger = logging.getLogger("beedrones.virt")

    def __init__(self, server, name=None, domain_id=None):
        """
        :param server: instance of KvmServer
        """
        # open connection to libvirt server if it isn't already open
        self.server = server
        if server.ping():
            self.conn = server.conn
        else:
            self.conn = server.connect()

        self.server_mem = self.server.info()["info"][1] * 1024
        self._name = name
        self._domain = self._get_domain(name=name, domain_id=domain_id)

        self._enable_cpu_stats = True
        self._enable_mem_stats = True
        self._enable_net_stats = True
        self._enable_disk_stats = True

        self.disks = [disk["target"]["dev"] for disk in self.get_disk_devices()]
        self.nets = [net["target"]["dev"] for net in self.get_network_devices()]

        # stats
        self.record = [
            {
                "timestamp": 0,
                "cpuTime": 0,
                "cpuTimeAbs": 0,
                "cpuHostPercent": 0,
                "cpuGuestPercent": 0,
                "curmem": 0,
                "currMemPercent": 0,
                "diskRdKB": 0,
                "diskRdKBAbs": {k: 0 for k in self.disks},
                "diskWrKB": 0,
                "diskWrKBAbs": {k: 0 for k in self.disks},
                "netRxKB": 0,
                "netRxKBAbs": {k: 0 for k in self.nets},
                "netTxKB": 0,
                "netTxKBAbs": {k: 0 for k in self.nets},
            }
        ]
        self.maxRecord = {
            "diskRdRate": 10.0,
            "diskWrRate": 10.0,
            "netTxRate": 10.0,
            "netRxRate": 10.0,
        }

        # init
        self.toggle_sample_network_traffic()
        self.toggle_sample_disk_io()

    @property
    def domain(self):
        """Get domain."""
        return self._domain

    @property
    def name(self):
        """Get name."""
        return self._name

    def info(self):
        """Get virtual machine description. Specify at least name or id.

        Exception: VirtDomainMonitorError.

        :param name: [optional] name of virtual machine
        :param id: [optional] id of virtual machine
        """
        # try:
        if True:
            data = xmltodict(self._domain.XMLDesc(8), dict_constructor=dict, attr_prefix="")
            self.logger.debug("Get libvirt domain info: %s" % self._name)
            return data

    def _get_domain(self, name=None, domain_id=None):
        """Get virtual machine domain object. Specify at least name or did.

        Exception: VirtDomainMonitorError.

        :param name: [optional] name of virtual machine
        :param did: [optional] id of virtual machine
        """
        try:
            if name != None:
                domain = self.conn.lookupByName(name)
            elif domain_id != None:
                domain = self.conn.lookupByNamtoprettyxmle(domain_id)

            self.logger.debug("Get libvirt domain: %s" % name)
            return domain
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainMonitorError(ex)

    def tick(self, now=None):
        if (
            self._enable_cpu_stats is False
            and self._enable_mem_stats is False
            and self._enable_net_stats is False
            and self._enable_disk_stats is False
        ):
            raise VirtDomainMonitorError("No stats enabled")

        if self.server.ping() is False:
            return

        if now is None:
            now = time.time()

        # Invalidate cached values
        # self._invalidate_xml()

        info = self._domain.info()
        expected = 10
        current = len(self.record)
        if current > expected:
            del self.record[expected:current]

        # Xen reports complete crap for Dom0 max memory
        # (ie MAX_LONG) so lets clamp it to the actual
        # physical RAM in machine which is the effective
        # real world limit
        (cpuTime, cpuTimeAbs, pcentHostCpu, pcentGuestCpu) = self._sample_cpu_stats(info, now)
        pcentCurrMem, curmem = self._sample_mem_stats()
        rdBytes, rdBytesAbs, wrBytes, wrBytesAbs = self._sample_disk_io()
        rxBytes, rxBytesAbs, txBytes, txBytesAbs = self._sample_network_traffic()

        newStats = {
            "timestamp": now,
            "cpuTime": cpuTime,
            "cpuTimeAbs": cpuTimeAbs,
            "cpuHostPercent": pcentHostCpu,
            "cpuGuestPercent": pcentGuestCpu,
            "curmem": curmem,
            "currMemPercent": pcentCurrMem,
            "diskRdKB": rdBytes / 1024,
            "diskRdKBAbs": rdBytesAbs,
            "diskWrKB": wrBytes / 1024,
            "diskWrKBAbs": wrBytesAbs,
            "netRxKB": rxBytes / 1024,
            "netRxKBAbs": rxBytesAbs,
            "netTxKB": txBytes / 1024,
            "netTxKBAbs": txBytesAbs,
        }

        for r in ["diskRd", "diskWr", "netRx", "netTx"]:
            newStats[r + "Rate"] = self._get_cur_rate(r + "KB")
            self._set_max_rate(newStats, r + "Rate")

        self.record.insert(0, newStats)
        self.logger.debug("Resources sampled for domain: %s" % self._name)

    def _get_cur_rate(self, what):
        if len(self.record) > 1:
            ret = float(self.record[0][what] - self.record[1][what]) / float(
                self.record[0]["timestamp"] - self.record[1]["timestamp"]
            )
        else:
            ret = 0.0
        return max(ret, 0, 0)  # avoid negative values at poweroff

    def _set_max_rate(self, record, what):
        if record[what] > self.maxRecord[what]:
            self.maxRecord[what] = record[what]

    def _sample_cpu_stats(self, info, now):
        if not self._enable_cpu_stats:
            return 0, 0, 0, 0

        prevCpuTime = 0
        prevTimestamp = 0
        cpuTime = 0
        cpuTimeAbs = 0
        pcentHostCpu = 0
        pcentGuestCpu = 0

        if len(self.record) > 0:
            prevTimestamp = self.record[0]["timestamp"]
            prevCpuTime = self.record[0]["cpuTimeAbs"]

        if not (info[0] in [libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_CRASHED]):
            guestcpus = info[3]
            cpuTime = info[4] - prevCpuTime
            cpuTimeAbs = info[4]
            hostcpus = self.server.info()["info"][2]

            pcentbase = ((cpuTime) * 100.0) / ((now - prevTimestamp) * 1000.0 * 1000.0 * 1000.0)
            pcentHostCpu = round(pcentbase / hostcpus, 1)
            pcentGuestCpu = round(pcentbase / guestcpus, 1)

        pcentHostCpu = max(0.0, min(100.0, pcentHostCpu))
        pcentGuestCpu = max(0.0, min(100.0, pcentGuestCpu))

        return cpuTime, cpuTimeAbs, pcentHostCpu, pcentGuestCpu

    def _sample_mem_stats(self):
        if not self._enable_mem_stats:
            return 0, 0

        curmem = 0
        totalmem = 1

        try:
            stats = self._domain.memoryStats()
            # did we get both required stat items back?
            curmem = stats["rss"]
            totalmem = self.server_mem
        except libvirt.libvirtError as ex:
            self.logger.error("Error reading mem stats: %s", ex)

        pcentCurrMem = round(curmem * 100.0 / totalmem, 1)
        pcentCurrMem = max(0.0, min(pcentCurrMem, 100.0))

        return pcentCurrMem, curmem

    def _sample_network_traffic(self):
        if not self._enable_net_stats:
            return 0, 0, 0, 0

        rx = 0
        rxAbs = self.record[0]["netRxKBAbs"]
        tx = 0
        txAbs = self.record[0]["netTxKBAbs"]

        for netdev in self.get_network_devices():
            dev = netdev["target"]["dev"]
            if not dev:
                continue

            try:
                io = self._domain.interfaceStats(dev)
                if io:
                    rx += io[0] - rxAbs[dev]
                    rxAbs[dev] = io[0]
                    tx += io[4] - txAbs[dev]
                    txAbs[dev] = io[4]
            except libvirt.libvirtError as ex:
                self.logger.error(
                    "Error reading net stats for '%s' dev '%s': %s",
                    self.get_name(),
                    dev,
                    ex,
                )
                if self.is_active():
                    self.logger.debug("Adding %s to skip list", dev)
                    self._stats_net_skip.append(dev)
                else:
                    self.logger.debug("Aren't running, don't add to skiplist")

        return rx, rxAbs, tx, txAbs

    def _sample_disk_io(self):
        if not self._enable_disk_stats:
            return 0, 0, 0, 0

        rd = 0
        rdAbs = self.record[0]["diskRdKBAbs"]
        wr = 0
        wrAbs = self.record[0]["diskWrKBAbs"]

        # did not work, iterate over all disks
        for disk in self.get_disk_devices():
            dev = disk["target"]["dev"]
            if not dev:
                continue

            try:
                io = self._domain.blockStats(dev)
                if io:
                    rd += io[1] - rdAbs[dev]
                    rdAbs[dev] = io[1]
                    wr += io[3] - wrAbs[dev]
                    wrAbs[dev] = io[3]
            except libvirt.libvirtError as ex:
                self.logger.error(
                    "Error reading disk stats for " "'%s' dev '%s': %s",
                    self.get_name(),
                    dev,
                    ex,
                )
                if self.is_active():
                    self.logger.debug("Adding %s to skip list", dev)
                    self._stats_disk_skip.append(dev)
                else:
                    self.logger.debug("Aren't running, don't add to skiplist")
        return rd, rdAbs, wr, wrAbs

    def toggle_sample_network_traffic(self):
        if self._enable_net_stats and len(self.record) > 1:
            # resample the current value before calculating the rate in
            # self.tick() otherwise we'd get a huge spike when switching
            # from 0 to bytes_transfered_so_far
            rxBytes, txBytes = self._sample_network_traffic()
            self.record[0]["netRxKB"] = rxBytes / 1024
            self.record[0]["netTxKB"] = txBytes / 1024

    def toggle_sample_disk_io(self):
        if self._enable_disk_stats and len(self.record) > 1:
            # resample the current value before calculating the rate in
            # self.tick() otherwise we'd get a huge spike when switching
            # from 0 to bytes_transfered_so_far
            rdBytes, wrBytes = self._sample_disk_io()
            self.record[0]["diskRdKB"] = rdBytes / 1024
            self.record[0]["diskWrKB"] = wrBytes / 1024

    def get_metrics(self):
        r = self.record[0]
        return (
            time.time(),
            r["cpuHostPercent"],
            r["currMemPercent"],
            r["netRxKB"],
            r["netTxKB"],
            r["diskRdKB"],
            r["diskWrKB"],
        )

    #
    # XML Device listing
    #
    def get_serial_devs(self):
        devs = self.get_char_devices()
        devlist = []

        devlist += filter(lambda x: x.virtual_device_type == "serial", devs)
        devlist += filter(lambda x: x.virtual_device_type == "console", devs)
        return devlist

    def _build_device_list(self, device_type):
        devs = xmltodict(self._domain.XMLDesc(8), dict_constructor=dict, attr_prefix="")["devices"][device_type]
        if type(devs) is not list:
            devs = [devs]
        count = 0
        for dev in devs:
            dev["vmmindex"] = count
            count += 1

        return devs

    def get_network_devices(self):
        return self._build_device_list("interface")

    def get_video_devices(self):
        return self._build_device_list("video")

    def get_hostdev_devices(self):
        return self._build_device_list("hostdev")

    def get_watchdog_devices(self):
        return self._build_device_list("watchdog")

    def get_input_devices(self):
        return self._build_device_list("input")

    def get_graphics_devices(self):
        return self._build_device_list("graphics")

    def get_sound_devices(self):
        return self._build_device_list("sound")

    def get_controller_devices(self):
        return self._build_device_list("controller")

    def get_filesystem_devices(self):
        return self._build_device_list("filesystem")

    def get_smartcard_devices(self):
        return self._build_device_list("smartcard")

    def get_redirdev_devices(self):
        return self._build_device_list("redirdev")

    def get_disk_devices(self):
        devs = self._build_device_list("disk")

        # Iterate through all disks and calculate what number they are
        # HACK: We are making a variable in VirtualDisk to store the index
        idx_mapping = {}
        for dev in devs:
            devtype = dev["target"]["dev"]
            bus = dev["target"]["bus"]
            key = devtype + (bus or "")

            if key not in idx_mapping:
                idx_mapping[key] = 1

            dev.disk_bus_index = idx_mapping[key]
            idx_mapping[key] += 1

        return devs

    def get_char_devices(self):
        devs = []
        serials = self._build_device_list("serial")
        parallels = self._build_device_list("parallel")
        consoles = self._build_device_list("console")
        channels = self._build_device_list("channel")

        for devicelist in [serials, parallels, consoles, channels]:
            devs.extend(devicelist)

        # Don't display <console> if it's just a duplicate of <serial>
        if len(consoles) > 0 and len(serials) > 0:
            con = consoles[0]
            ser = serials[0]

            if con.char_type == ser.char_type and con.target_type is None or con.target_type == "serial":
                ser.virtmanager_console_dup = con
                devs.remove(con)

        return devs
