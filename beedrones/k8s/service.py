# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte
from beecell.types.type_dict import dict_get
from beecell.types.type_string import truncate
from beedrones.k8s.client import k8sEntity, api_request


class K8sService(k8sEntity):
    """K8sService"""

    @property
    def api(self):
        return self.manager.core_api

    @api_request
    def list(self, name=None):
        """list services in a namespace or in all the namespaces

        :param name: service partial name
        :return: list of services
        """
        if self.all_namespaces is True:
            services = self.api.list_service_for_all_namespaces()
        else:
            services = self.api.list_namespaced_service(self.default_namespace)

        res = services.to_dict().get("items", [])

        # filter services
        res = [s for s in res if name is None or (name is not None and dict_get(s, "metadata.name").find(name) >= 0)]

        for i in res:
            i["metadata"]["creation_timestamp"] = str(i["metadata"]["creation_timestamp"])

        self.logger.debug("list services: %s" % truncate(res))
        return res

    @api_request
    def get(self, name):
        """get service

        :param name: name of the service
        :return:
        """
        service = self.api.read_namespaced_service(name, self.default_namespace)
        res = self.get_dict(service)
        self.logger.debug("get namespace %s service: %s" % (self.default_namespace, truncate(res)))
        return res

    @api_request
    def add(self, name, selector, port, target_port):
        """add service

        :param name: service name
        :param selector: service selector. Ex. {'app': 'deployment'}
        :param port: service port
        :param target_port: service target port
        :return: service
        """
        body = self.client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=self.client.V1ObjectMeta(name=name),
            spec=self.client.V1ServiceSpec(
                selector=selector,
                ports=[self.client.V1ServicePort(port=port, target_port=target_port)],
            ),
        )
        res = self.api.create_namespaced_service(namespace=self.default_namespace, body=body)
        self.logger.debug("create namespace %s service: %s" % (self.default_namespace, truncate(res)))
        return res

    @api_request
    def delete(self, name):
        """delete service

        :param name: service name
        """
        namespace = self.default_namespace
        res = self.api.delete_namespaced_service(name, namespace)
        self.logger.debug("delete namespace %s service: %s" % (self.default_namespace, truncate(res)))
        return res
