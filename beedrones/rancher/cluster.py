# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beedrones.rancher.client import RancherObject
from beecell.simple import truncate
from re import sub
from re import match
from time import sleep


class RancherCluster(RancherObject):
    """RancherCluster"""

    def __init__(self, manager, rke_version=1):
        super().__init__(manager)
        self._rke_version = rke_version

    @property
    def rke_version(self):
        """RKE Version

        :return: rke version number
        """
        return self._rke_version

    @rke_version.setter
    def rke_version(self, value):
        self._rke_version = value

    @rke_version.deleter
    def rke_version(self):
        del self._rke_version

    def list(self, **filter):
        """List clusters

        :param filter: custom filter
        :return: list of clusters
        """
        res = self.http_list("/clusters", **filter)
        self.logger.debug("List clusters: %s" % truncate(res))
        return res

    def get(self, cluster_id):
        """Get cluster info

        :param cluster_id: cluster id
        :return: cluster info
        """
        res = self.http_get("/clusters/%s" % cluster_id)
        self.logger.debug("Get cluster: %s" % truncate(res))
        return res

    def get_id(self, name):
        """Get cluster id from the name

        :param name: cluster name
        :return: cluster_id
        """
        cluster_id = None
        clusters = self.list(name=name)
        if len(clusters) == 1:
            cluster = clusters[0]
            cluster_id = cluster.get("id")
        else:
            cluster_id = None
        self.logger.debug(f"Get cluster id: {cluster_id}")
        return cluster_id

    def get_projects(self, cluster_id):
        """Get projects within a cluster

        :param cluster_id: cluster id
        :return: list of projects
        """
        res = self.http_get("/clusters/%s/projects" % cluster_id)
        self.logger.debug("List projects: %s" % truncate(res))
        return res

    def get_registration_cmd(self, cluster_id):
        """Get registration command to be run on each virtual machine you want to become a node of your cluster

        :param cluster_id: cluster id
        :return: command string
        """
        res = self.http_get("/clusters/%s/clusterregistrationtokens" % cluster_id)
        reg_cmd = res.get("data")[0]
        self.logger.debug("Registration command: %s" % truncate(reg_cmd))
        return reg_cmd

    def __is_camel_case(self, s):
        pattern = r"^[a-zA-Z]+([A-Z][a-z]+)+$"
        return bool(match(pattern, s))

    def __camel_case(self, s):
        s = sub(r"(_)+", " ", s).title().replace(" ", "")
        return "".join([s[0].lower(), s[1:]])

    def __convert_key(self, data):
        if isinstance(data, dict):
            data1 = {}
            for k, v in data.items():
                if k.find("-") > 0:
                    data1[k] = self.__convert_key(v)
                else:
                    data1[self.__camel_case(k)] = self.__convert_key(v)
        else:
            data1 = data
        return data1

    def add(self, data, *args, **kvargs):
        """Create cluster

        :param data: cluster configuration data
        :param kvargs: cluster param
        :return: cluster id
        """
        self.logger.debug(f"self.rke_version : {self.rke_version}")
        if self.rke_version == 1:
            data = self.__convert_key(data)
            data["type"] = "cluster"
            res = self.http_post("/clusters", **data)
        elif self.rke_version == 2:
            # some formal control in data config, to improve in a dedicated module
            if "apiVersion" in data:
                del data["apiVersion"]
            if "kind" in data:
                del data["kind"]
            data["type"] = "provisioning.cattle.io.cluster"
            res_provisioned = self.http_post_provisioning("/provisioning.cattle.io.clusters", **data)
            id_provisioned = res_provisioned.get("id")
            self.logger.debug(f"Get id from provisioning: {id_provisioned}")
            name_provisioned = res_provisioned.get("metadata").get("name")
            self.logger.debug(f"Get name from provisioning: {name_provisioned}")
            if id_provisioned is not None and name_provisioned is not None:
                # some delay after provisioning, we need an event/callback to notify cluster is ready
                sleep(3)
                cluster_id = self.get_id(name=name_provisioned)
                res = self.get(cluster_id)
            else:
                res = None
        else:
            res = self.http_post("/clusters", **data)

        self.logger.debug("Add cluster: %s" % res.get("id"))
        return res

    def delete(self, cluster_id):
        """Delete cluster

        :param cluster_id: cluster id
        :return: True
        """
        self.http_delete("/clusters/%s" % cluster_id)
        self.logger.debug("Delete cluster: %s" % cluster_id)
        return True
