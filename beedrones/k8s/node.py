# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.types.type_string import truncate
from beedrones.k8s.client import k8sEntity, api_request


class K8sNode(k8sEntity):
    """K8sNode"""

    @property
    def api(self):
        return self.manager.core_api

    @api_request
    def list(self):
        """list nodes in the cluster

        :return: list of nodes
        """
        nodes = self.api.list_node(watch=False)
        res = [
            {
                "uid": p.metadata.uid,
                "name": p.metadata.name,
                "ip": p.status.addresses[0].address,
                "cpu": p.status.capacity["cpu"],
                "memory": p.status.capacity["memory"],
                "images": len(p.status.images),
                "os_image": p.status.node_info.os_image,
                "kernel": p.status.node_info.kernel_version,
                "container": p.status.node_info.container_runtime_version,
            }
            for p in nodes.items
        ]
        self.logger.debug("list nodes: %s" % truncate(res))
        return res

    @api_request
    def get(self, name):
        """get node

        :param name: name of the node
        :return: node
        """
        node = self.api.read_node(name)
        res = {
            "uid": node.metadata.uid,
            "name": node.metadata.name,
            "ip": node.status.addresses[0].address,
            "capacity": node.status.capacity,
            "pod_cidr": node.spec.pod_cidr,
            "namespace": node.metadata.namespace,
            "info": {
                "architecture": node.status.node_info.architecture,
                "boot_id": node.status.node_info.boot_id,
                "container_runtime_version": node.status.node_info.container_runtime_version,
                "kernel_version": node.status.node_info.kernel_version,
                "kube_proxy_version": node.status.node_info.kube_proxy_version,
                "kubelet_version": node.status.node_info.kubelet_version,
                "machine_id": node.status.node_info.machine_id,
                "operating_system": node.status.node_info.operating_system,
                "os_image": node.status.node_info.os_image,
                "system_uuid": node.status.node_info.system_uuid,
            },
            "images": [{"names": v.names, "size": v.size_bytes} for v in node.status.images],
        }
        self.logger.debug("get node: %s" % truncate(res))
        return res
