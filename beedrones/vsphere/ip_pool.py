# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from six import ensure_str, ensure_text

from beecell.simple import dict_get
from beedrones.vsphere.client import VsphereObject, VsphereError
from ipaddress import ip_address
import xml.etree.ElementTree as et


class VsphereNetworkIpPool(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def _list(self):
        """Ippool internal list method

        :return:
        """
        res = (
            self.call("/api/2.0/services/ipam/pools/scope/globalroot-0", "GET", "")
            .get("ipamAddressPools")
            .get("ipamAddressPool")
        )
        if isinstance(res, dict):
            res = [res]
        return res

    def list(self, pool_id=None, pool_range=None):
        """Get a list of ippools

        :param pool_id: id of a pool [optional]
        :param pool_range: tupla with start_ip and end_ip [optional]
        :return: list of ippools
        """
        res = []
        if pool_id is not None:
            try:
                res = [self.get(pool_id)]
            except:
                res = []
        elif pool_range is not None and len(pool_range) > 1:
            start_ip = ip_address(pool_range[0])
            end_ip = ip_address(pool_range[1])
            pools = self._list()
            for item in pools:
                ip_range_dto = dict_get(item, "ipRanges.ipRangeDto")
                if not isinstance(ip_range_dto, list):
                    ip_range_dto = [ip_range_dto]
                for ip in ip_range_dto:
                    pool_start_ip = ip_address(ip.get("startAddress"))
                    pool_end_ip = ip_address(ip.get("endAddress"))
                    # range is internal
                    if start_ip >= pool_start_ip and end_ip <= pool_end_ip:
                        res.append(item)
                    # range overlap from the start
                    elif pool_start_ip <= start_ip < pool_end_ip:
                        res.append(item)
                    # range overlap from the end
                    elif pool_end_ip >= end_ip > pool_start_ip:
                        res.append(item)
        else:
            res = self._list()
        return res

    def get(self, oid):
        """Get an ippool

        :param oid: ippool id
        :return: None if security group does not exist
        """
        res = self.call("/api/2.0/services/ipam/pools/%s" % oid, "GET", "")
        return res["ipamAddressPool"]

    def exists(self, pool_id=None, pool_range=None):
        """Check if ippool exist

        :param pool_id: id of a pool [optional]
        :param pool_range: tupla with start_ip and end_ip [optional]
        :return: True
        :raise VsphereError:
        """
        res = self.list(pool_id=pool_id, pool_range=pool_range)
        if pool_id is not None and len(res) == 0:
            raise VsphereError("Ippool %s does not exist" % pool_id)
        elif pool_range is not None and len(res) > 0:
            raise VsphereError("Ippool for range %s already exists" % str(pool_range))
        return True

    def info(self, pool):
        """ """
        ip_range_dto = dict_get(pool, "ipRanges.ipRangeDto")
        if not isinstance(ip_range_dto, list):
            pool["ipRanges"]["ipRangeDto"] = [ip_range_dto]
        return pool

    def detail(self, pool):
        """ """
        return pool

    def create(
        self,
        name,
        prefix=24,
        gateway="10.0.0.1",
        dnssuffix=None,
        dns1="8.8.8.8",
        dns2="8.8.4.4",
        startip="10.0.0.2",
        stopip="10.0.0.254",
    ):
        """Create ip pool

        :param name: pool name
        :param prefix: pool prefix. Ex. /24
        :param gateway: pool gateway. Ex. 10.102.34.1
        :param dnssuffix: pool dns suffix. Ex. localdomain.local
        :param dns1: pool dns1 ip address
        :param dns2: pool dns2 ip address
        :param startip: start pool ip address
        :param stopip: end pool ip address
        :return: ippool id
        """
        if ip_address(startip) >= ip_address(stopip):
            raise VsphereError("Start ip must be lower than stop ip")
        data = [
            "<ipamAddressPool>",
            "<name>{name}</name>",
            "<prefixLength>{prefix}</prefixLength>",
            "<gateway>{gateway}</gateway>",
            "<dnsSuffix>{dnssuffix}</dnsSuffix>",
            "<dnsServer1>{dns1}</dnsServer1>",
            "<dnsServer2>{dns2}</dnsServer2>",
            "<ipRanges>",
            "<ipRangeDto>",
            "<startAddress>{startip}</startAddress>",
            "<endAddress>{stopip}</endAddress>",
            "</ipRangeDto>",
            "</ipRanges>",
            "</ipamAddressPool>",
        ]
        data = ("".join(data)).format(
            name=name,
            gateway=gateway,
            prefix=prefix,
            dnssuffix=dnssuffix,
            dns1=dns1,
            dns2=dns2,
            startip=startip,
            stopip=stopip,
        )
        res = self.call(
            "/api/2.0/services/ipam/pools/scope/globalroot-0",
            "POST",
            data,
            headers={"Content-Type": "text/xml"},
            timeout=600,
        )
        return ensure_text(res)

    def update(self, oid, **kvargs):
        """Update ippool

        :param oid: pool id
        :param kvargs.name: pool name [optional]
        :param kvargs.prefix: pool prefix. Ex. /24 [optional]
        :param kvargs.gateway: pool gateway. Ex. 10.102.34.1 [optional]
        :param kvargs.dnssuffix: pool dns suffix. Ex. localdomain.local [optional]
        :param kvargs.dns1: pool dns1 ip address [optional]
        :param kvargs.dns2: pool dns2 ip address [optional]
        :param kvargs.startip: start pool ip address [optional]
        :param kvargs.stopip: end pool ip address [optional]
        :return: ippool id
        """
        orig = self.call("/api/2.0/services/ipam/pools/%s" % oid, "GET", "")
        orig_data = orig.get("ipamAddressPool")
        revision = int(orig_data["revision"]) + 1

        data = et.Element("ipamAddressPool")
        self.xml_set_key(data, kvargs, "objectId", default=orig_data["objectId"], required=False)
        self.xml_set_key(
            data,
            kvargs,
            "objectTypeName",
            default=orig_data["objectTypeName"],
            required=False,
        )
        obj_type = et.SubElement(data, "type")
        self.xml_set_key(
            obj_type,
            kvargs,
            "typeName",
            default=dict_get(orig_data, "type.typeName"),
            required=False,
        )
        self.xml_set_key(data, kvargs, "vsmUuid", default=orig_data["vsmUuid"], required=False)
        self.xml_set_key(data, kvargs, "revision", default=revision, required=False)
        self.xml_set_key(data, kvargs, "name", default=orig_data["name"], required=False)
        self.xml_set_key(
            data,
            kvargs,
            "prefixLength",
            default=orig_data["prefixLength"],
            required=False,
        )
        self.xml_set_key(data, kvargs, "gateway", default=orig_data["gateway"], required=False)
        self.xml_set_key(data, kvargs, "dnsSuffix", default=orig_data["dnsSuffix"], required=False)
        self.xml_set_key(data, kvargs, "dnsServer1", default=orig_data["dnsServer1"], required=False)
        self.xml_set_key(data, kvargs, "dnsServer2", default=orig_data["dnsServer2"], required=False)
        self.xml_set_key(data, kvargs, "subnetId", default=orig_data["subnetId"], required=False)
        ip_ranges = et.SubElement(data, "ipRanges")
        ip_range_dto = et.SubElement(ip_ranges, "ipRangeDto")
        self.xml_set_key(
            ip_range_dto,
            kvargs,
            "id",
            default=dict_get(orig_data, "ipRanges.ipRangeDto.id"),
            required=False,
        )
        self.xml_set_key(
            ip_range_dto,
            kvargs,
            "startAddress",
            default=dict_get(orig_data, "ipRanges.ipRangeDto.startAddress"),
            required=False,
        )
        self.xml_set_key(
            ip_range_dto,
            kvargs,
            "endAddress",
            default=dict_get(orig_data, "ipRanges.ipRangeDto.endAddress"),
            required=False,
        )
        data = ensure_str(et.tostring(data))

        res = self.call(
            "/api/2.0/services/ipam/pools/%s" % oid,
            "PUT",
            data,
            headers={"Content-Type": "text/xml"},
        )
        self.logger.debug("update nsx ippool: %s" % oid)
        return res

    def delete(self, oid):
        """Delete an ip pool

        :param oid: pool id
        """
        res = self.call("/api/2.0/services/ipam/pools/%s" % oid, "DELETE", "", timeout=600)
        return True

    def allocations(self, pool):
        """Retrieves all allocated IP addresses from the specified pool.

        :param pool: pool id
        :return:
        """
        res = self.call("/api/2.0/services/ipam/pools/%s/ipaddresses" % pool, "GET", "")
        res = res.get("allocatedIpAddresses", {})
        if res is not None:
            res = res.get("allocatedIpAddress", [])
        else:
            res = []
        return res

    def allocate(self, pool, static_ip=None):
        """Allocate an IP Address from the pool. Use ALLOCATE in the allocationMode field in the body to allocate
        the next available IP. To allocate a specific one use RESERVE and pass the IP to reserve in the ipAddress
        fields in the body.

        :param pool: pool id
        :return:
        """
        data = "<ipAddressRequest>"
        if static_ip is not None:
            data += "<allocationMode>RESERVE</allocationMode><ipAddress>%s</ipAddress>" % static_ip
        else:
            data += "<allocationMode>ALLOCATE</allocationMode>"
        data += "</ipAddressRequest>"

        res = self.call(
            "/api/2.0/services/ipam/pools/%s/ipaddresses" % pool,
            "POST",
            data,
            headers={"Content-Type": "text/xml"},
        )
        self.logger.debug("Allocate ip: %s" % res)
        return res.get("allocatedIpAddress")

    def release(self, pool, ip):
        """Release an IP address allocation in the pool.

        :param pool: pool id
        :param ip: ip id to release
        :return:
        """
        res = self.call("/api/2.0/services/ipam/pools/%s/ipaddresses/%s" % (pool, ip), "DELETE", "")
        self.logger.debug("Release ip: %s" % res)
        return res
