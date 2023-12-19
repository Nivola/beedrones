# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from logging import getLogger
import requests
import ujson as json
from datetime import datetime
from six import ensure_text
from re import search


class GraphiteError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "GraphiteError: %s" % self.value

    def __str__(self):
        return "GraphiteError: %s" % self.value


class GraphiteNotFound(GraphiteError):
    def __init__(self):
        GraphiteError.__init__(self, "NOT_FOUND", 404)


class GraphiteManager(object):
    """Graphite Manager

    :param uri: graphite api endpoint
    :param env: graphite internal tree environment
    """

    def __init__(self, host, env=None):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        self.host = host
        self.uri = "http://%s/render?" % host
        self.uri2 = "http://%s/metrics/find?" % host
        self.env = env

        self.supported_platform = {
            "vsphere": [
                self.__get_vsphere_host_path,
                self.__get_vsphere_vm_path,
                self.__parse_vsphere_field,
                self.__list_vsphere,
                self.__parse_vsphere_nodes,
            ],
            "kvm": [
                self.__get_kvm_host_path,
                self.__get_kvm_vm_path,
                self.__parse_kvm_field,
                self.__list_kvm,
                self.__parse_kvm_nodes,
            ],
        }

    def set_search_path(self, search_path):
        """Set metrics search path

        :param search_path: graphite tree search path
        """
        self.env = search_path

    #
    # vsphere
    #
    def __get_vsphere_host_path(self, oid):
        """Get graphite vsphere esxi path of the metrics

        :param oid: vsphere esxi host morid
        :return: metrics path
        """
        vpshere_host_key = "HostSystem_*_%s_*" % oid
        vpshere_path = "%s.collectsphere.%s" % (self.env, vpshere_host_key)
        return vpshere_path

    def __get_vsphere_vm_path(self, oid):
        """Get graphite vsphere virtual machine path of the metrics

        :param oid: vsphere virtual machine host morid
        :return: metrics path
        """
        vpshere_vm_key = "VirtualMachine_*_%s_*" % oid
        vpshere_path = "%s.collectsphere.%s" % (self.env, vpshere_vm_key)
        return vpshere_path

    def __parse_vsphere_field(self, oid, field):
        """Parse metric field and extract the name

        :param oid: vsphere oid
        :param field: original field
        :return: parsed field
        """
        # virtual machine
        pre = "%s.collectsphere.VirtualMachine_" % (self.env)
        field = field.replace(pre, "")

        # physical node
        pre = "%s.collectsphere.HostSystem_" % (self.env)
        field = field.replace(pre, "")
        pos = field.find("-")
        pos2 = field.find(oid) + len(oid) + 1

        field = "%s_%s" % (field[0:pos], field[pos2:])
        return field

    def __list_vsphere(self):
        """ """
        return "%s.collectsphere.*" % (self.env)

    def __parse_vsphere_nodes(self, nodes):
        """Parse node list and extract only the useful node names

        :param nodes: original graphite nodes list
        """
        # VirtualMachine_net_average_usage_kiloBytesPerSecond-domain-c54_vm_3054_vmnic1
        res = {}
        for item in nodes:
            m = search(r"vm_[0-9]*", item)
            if m:
                res[m.group(0)] = ""
            m = search(r"host_[0-9]*", item)
            if m:
                res[m.group(0)] = ""

        return res.keys()

    #
    # kvm
    #
    def __get_kvm_host_path(self, oid):
        """Get graphite kvm host path of the metrics

        :param oid: kvm host name
        :return: metrics path
        """
        kvm_path = "%s.%s.*.*" % (self.env, oid)
        return kvm_path

    def __get_kvm_vm_path(self, oid):
        """Get graphite kvm virtual machine path of the metrics

        :param oid: kvm virtual machine name
        :return: metrics path
        """
        kvm_path = [
            "%s.%s.virt.*" % (self.env, oid),
            "%s.%s.virt.*.*" % (self.env, oid),
            "%s.%s.libvirt.*" % (self.env, oid),
            "%s.%s.libvirt.*.*" % (self.env, oid),
        ]
        return kvm_path

    def __parse_kvm_field(self, oid, field):
        """Parse metric field and extract the name

        :param oid: kvm oid
        :param field: original field
        :return: parsed field
        """
        pos = field.find("virt")
        # kvm virtual machine
        if pos >= 0:
            pos += 5
        else:
            pos = field.find(oid) + len(oid) + 1
        field = field[pos:]
        return field

    def __list_kvm(self):
        """ """
        return "%s.*" % (self.env)

    def __parse_kvm_nodes(self, nodes):
        """Parse node list and extract only the useful node names

        :param nodes: original graphite nodes list
        """
        return nodes

    #
    # metrics
    #
    def __check_platform(self, platform):
        """ """
        if platform not in self.supported_platform.keys():
            raise GraphiteNotFound("Platform %s is not supported" % platform)

    def __get_metrics(self, target, minutes):
        """ """
        headers = {"Content-Type": "application/json"}
        params = {"target": target, "format": "json", "from": "-%smin" % minutes}
        f = requests.get(self.uri, headers=headers, params=params)
        res = json.loads(f.text)
        return res

    def get_physical_node_metrics(self, platform, oid, minutes):
        """Get physical node metrics

        :param platform: required paltform. Ex. kvm, vsphere
        :param oid: id of the node
        :param minutes: number of minutes to filter
        """
        self.__check_platform(platform)
        target = self.supported_platform.get(platform)[0](oid)
        res = self.__get_metrics(target, minutes)
        return res

    def get_virtual_node_metrics(self, platform, oid, minutes):
        """Get virtual machine metrics

        :param platform: required paltform. Ex. kvm, vsphere
        :param oid: id of the node
        :param minutes: number of minutes to filter
        """
        self.__check_platform(platform)
        target = self.supported_platform.get(platform)[1](oid)
        res = self.__get_metrics(target, minutes)
        return res

    def convert_timestamp(self, timestamp):
        """ """
        timestamp = datetime.fromtimestamp(timestamp)
        return ensure_text(timestamp.strftime("%d-%m-%Y %H:%M:%S.%f"))

    def format_metrics(self, oid, metrics, platform):
        """

        :param oid: id of the node
        :param metrics: metrics list
        :param platform: required paltform. Ex. kvm, vsphere
        """
        res = {}
        for item in metrics:
            target = self.supported_platform.get(platform)[2](oid, item.get("target"))
            res[target] = []
            for data in item.get("datapoints"):
                res[target].append([data[0], self.convert_timestamp(data[1])])
        return res

    #
    # node list
    #
    def get_nodes(self, platform):
        """ """
        self.__check_platform(platform)

        headers = {"Content-Type": "application/json"}
        params = {"query": self.supported_platform.get(platform)[3]()}
        f = requests.get(self.uri2, headers=headers, params=params)
        res = json.loads(f.text)
        nodes = [i.get("text") for i in res]
        resp = self.supported_platform.get(platform)[4](nodes)
        return resp
