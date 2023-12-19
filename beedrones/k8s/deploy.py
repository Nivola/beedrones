# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.types.type_dict import dict_get
from beecell.types.type_string import truncate
from beedrones.k8s.client import k8sEntity, api_request


class K8sDeploy(k8sEntity):
    """K8sDeploy"""

    @property
    def api(self):
        return self.manager.apps_api

    @api_request
    def list(self, name=None):
        """list deploy in a namespace or in all the namespaces

        :param name: deploy partial name
        :return: list of deploy
        """
        if self.all_namespaces is True:
            deploy = self.api.list_deployment_for_all_namespaces()
        else:
            deploy = self.api.list_namespaced_deployment(self.default_namespace)

        res = deploy.to_dict().get("items", [])

        # # filter deploy
        # res = [s for s in res if name is None or (name is not None and dict_get(s, 'metadata.name').find(name) >= 0)]

        for i in res:
            i["metadata"]["creation_timestamp"] = str(i["metadata"]["creation_timestamp"])

        self.logger.debug("list deploy: %s" % truncate(res))
        return res

    @api_request
    def get(self, name):
        """get deploy

        :param name: name of the deploy
        :return:
        """
        deploy = self.api.read_namespaced_deployment(name, self.default_namespace)
        res = self.get_dict(deploy)
        self.logger.debug("get namespace %s deploy: %s" % (self.default_namespace, truncate(res)))
        return res
