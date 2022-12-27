# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.types.type_string import truncate
from beedrones.k8s.client import k8sEntity, api_request


class K8sNamespace(k8sEntity):
    """K8sNamespace
    """
    @property
    def api(self):
        return self.manager.core_api

    @api_request
    def list(self):
        """list nodes in the cluster

        :return: list of nodes
        """
        res = self.api.list_namespace()
        res = res.to_dict().get('items', [])
        for i in res:
            self.convert_date(i)
        self.logger.debug('list namespaces: %s' % truncate(res))
        return res

    @api_request
    def get(self, name):
        """get namespace

        :param name: name of the namespace
        :return:
        """
        configmap = self.api.read_namespace(name)
        res = self.get_dict(configmap)
        res = self.convert_date(res)
        self.logger.debug('get namespace: %s' % truncate(res))
        return res

    @api_request
    def add(self, name, **kwargs):
        """add namespace

        :param name: namespace name
        :return: namespace
        """
        body = self.client.V1Namespace(
            api_version='v1',
            kind='Namespace',
            metadata=self.client.V1ObjectMeta(
                name=name
            ),
            spec=self.client.V1NamespaceSpec(
            )
        )
        res = self.api.create_namespace(body=body)
        self.logger.debug('add namespace: %s' % truncate(res))
        return res

    @api_request
    def delete(self, name):
        """delete namespace

        :param name: service name
        """
        res = self.api.delete_namespace(name)
        self.logger.debug('delete namespace: %s' % truncate(res))
        return res
