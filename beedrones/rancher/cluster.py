# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beedrones.rancher.client import RancherObject
from beecell.simple import truncate
from re import sub


class RancherCluster(RancherObject):
    """RancherCluster
    """

    def list(self, **filter):
        """List clusters

        :param filter: custom filter
        :return: list of clusters
        """
        res = self.http_list('/clusters', **filter)
        self.logger.debug('List clusters: %s' % truncate(res))
        return res

    def get(self, cluster_id):
        """Get cluster info

        :param cluster_id: cluster id
        :return: cluster info
        """
        res = self.http_get('/clusters/%s' % cluster_id)
        self.logger.debug('Get cluster: %s' % truncate(res))
        return res

    def get_projects(self, cluster_id):
        """Get projects within a cluster

        :param cluster_id: cluster id
        :return: list of projects
        """
        res = self.http_get('/clusters/%s/projects' % cluster_id)
        self.logger.debug('List projects: %s' % truncate(res))
        return res

    def get_registration_cmd(self, cluster_id):
        """Get registration command to be run on each virtual machine you want to become a node of your cluster

        :param cluster_id: cluster id
        :return: command string
        """
        res = self.http_get('/clusters/%s/clusterregistrationtokens' % cluster_id)
        reg_cmd = res.get('data')[0]
        self.logger.debug('Registration command: %s' % truncate(reg_cmd))
        return reg_cmd

    def __camel_case(self, s):
        s = sub(r"(_)+", " ", s).title().replace(" ", "")
        return ''.join([s[0].lower(), s[1:]])

    def __convert_key(self, data):
        if isinstance(data, dict):
            data1 = {}
            for k, v in data.items():
                if k.find('-') > 0:
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
        data = self.__convert_key(data)
        data['type'] = 'cluster'
        res = self.http_post('/clusters', **data)
        self.logger.debug('Add cluster: %s' % res.get('id'))
        return res

    def delete(self, cluster_id):
        """Delete cluster

        :param cluster_id: cluster id
        :return: True
        """
        self.http_delete('/clusters/%s' % cluster_id)
        self.logger.debug('Delete cluster: %s' % cluster_id)
        return True
