# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte
from beecell.types.type_dict import dict_get
from beecell.types.type_string import truncate
from beedrones.k8s.client import k8sEntity, api_request


class K8sIngress(k8sEntity):
    """K8sIngress"""

    @property
    def api(self):
        return self.manager.networking_api

    @api_request
    def list(self, name=None):
        """list ingress in a namespace or in all the namespaces

        :param name: ingress partial name
        :return: list of ingress
        """
        if self.all_namespaces is True:
            ingress = self.api.list_ingress_for_all_namespaces()
        else:
            ingress = self.api.list_namespaced_ingress(self.default_namespace)

        res = ingress.to_dict().get("items", [])

        # # filter ingress
        # res = [s for s in res if name is None or (name is not None and dict_get(s, 'metadata.name').find(name) >= 0)]

        for i in res:
            i["metadata"]["creation_timestamp"] = str(i["metadata"]["creation_timestamp"])
            i["metadata"]["managed_fields"][0]["time"] = str(i["metadata"]["managed_fields"][0]["time"])

        self.logger.debug("list ingress: %s" % truncate(res))
        return res

    @api_request
    def get(self, name):
        """get ingress

        :param name: name of the ingress
        :return:
        """
        ingress = self.api.read_namespaced_ingress(name, self.default_namespace)
        res = self.get_dict(ingress)
        self.logger.debug("get namespace %s ingress: %s" % (self.default_namespace, truncate(res)))
        return res
