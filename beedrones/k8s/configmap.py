# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.types.type_string import truncate
from beedrones.k8s.client import k8sEntity, api_request


class K8sConfigMap(k8sEntity):
    """K8sConfigMap
    """
    @property
    def api(self):
        return self.manager.core_api

    @api_request
    def list(self, name=None):
        """list configmaps in a namespace or in all the namespaces

        :return: list of configmaps
        """
        if self.all_namespaces is True:
            services = self.api.list_config_map_for_all_namespaces()
        else:
            services = self.api.list_namespaced_config_map(self.default_namespace)

        res = services.to_dict().get('items', [])
        for i in res:
            i['metadata']['creation_timestamp'] = str(i['metadata']['creation_timestamp'])

        self.logger.debug('list configmaps: %s' % truncate(res))
        return res

    @api_request
    def get(self, name):
        """get configmap

        :param name: name of the configmap
        :return:
        """
        configmap = self.api.read_namespaced_config_map(name, self.default_namespace)
        res = self.get_dict(configmap)
        res['metadata']['creation_timestamp'] = str(res['metadata']['creation_timestamp'])
        res['metadata']['managed_fields'][0]['time'] = str(res['metadata']['managed_fields'][0]['time'])
        self.logger.debug('get namespace %s configmap: %s' % (self.default_namespace, truncate(res)))
        return res

    @api_request
    def add(self, name, **kwargs):
        """add configmap

        :param name: configmap name
        :param kwargs: custom config data
        :return: service
        """
        namespace = self.default_namespace

        # Configurate ConfigMap metadata
        metadata = self.client.V1ObjectMeta(
            name=name,
            namespace=namespace,
        )
        # Instantiate the configmap object
        configmap = self.client.V1ConfigMap(
            api_version='v1',
            kind='ConfigMap',
            # How do I modify here ?
            data=dict(**kwargs),
            metadata=metadata
        )

        res = self.api.create_namespaced_config_map(namespace, body=configmap)
        self.logger.debug('create namespace %s configmap: %s' % (self.default_namespace, truncate(res)))
        return res

    @api_request
    def delete(self, name):
        """delete configmap

        :param name: service name
        """
        namespace = self.default_namespace
        res = self.api.delete_namespaced_config_map(name, namespace)
        self.logger.debug('delete namespace %s configmap: %s' % (self.default_namespace, truncate(res)))
        return res
