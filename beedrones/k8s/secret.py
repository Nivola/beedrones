# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.types.type_dict import dict_get
from beecell.types.type_string import truncate
from beedrones.k8s.client import k8sEntity, api_request


class K8sSecret(k8sEntity):
    """K8sSecret"""

    @property
    def api(self):
        return self.manager.core_api

    @api_request
    def list(self, name=None):
        """list secret in a namespace or in all the namespaces

        :param name: secret partial name
        :return: list of secret
        """
        if self.all_namespaces is True:
            secret = self.api.list_secret_for_all_namespaces()
        else:
            secret = self.api.list_namespaced_secret(self.default_namespace)

        res = secret.to_dict().get("items", [])

        # # filter secret
        # res = [s for s in res if name is None or (name is not None and dict_get(s, 'metadata.name').find(name) >= 0)]

        for i in res:
            i["metadata"]["creation_timestamp"] = str(i["metadata"]["creation_timestamp"])

        self.logger.debug("list secret: %s" % truncate(res))
        return res

    @api_request
    def get(self, name):
        """get secret

        :param name: name of the secret
        :return:
        """
        secret = self.api.read_namespaced_secret(name, self.default_namespace)
        res = self.get_dict(secret)
        self.logger.debug("get namespace %s secret: %s" % (self.default_namespace, truncate(res)))
        return res
