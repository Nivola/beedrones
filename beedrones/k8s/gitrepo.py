# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.types.type_dict import dict_get
from beecell.types.type_string import truncate
from beedrones.k8s.client import k8sEntity, api_request


class K8sGitRepo(k8sEntity):
    """K8sGitRepo"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_group = "fleet.cattle.io"
        self.api_ver = "v1alpha1"
        self.api_plural = "gitrepos"
        self.kind = "GitRepo"

    def __get_api_version(self):
        return "%s/%s" % (self.api_group, self.api_ver)

    @property
    def api(self):
        return self.manager.custom_api

    @api_request
    def list(self, name=None):
        """list deploy in a namespace or in all the namespaces

        :param name: deploy partial name
        :return: list of deploy
        """
        if self.all_namespaces is True:
            deploy = self.api.list_custom_object_for_all_namespaces()
        else:
            deploy = self.api.list_namespaced_custom_object(
                self.api_group, self.api_ver, self.default_namespace, self.api_plural
            )

        res = deploy.get("items", [])
        self.logger.debug("list git repos: %s" % truncate(res))
        return res

    @api_request
    def get(self, name):
        """get deploy

        :param name: name of the gitrepo
        :return:
        """
        res = self.api.get_namespaced_custom_object(
            self.api_group, self.api_ver, self.default_namespace, self.api_plural, name
        )
        self.logger.debug("get namespace %s git repo: %s" % (self.default_namespace, truncate(res)))
        return res

    @api_request
    def add(
        self,
        name,
        gitlab_project_uri,
        paths,
        targets,
        gitlab_project_branch="master",
        gitlab_secret=None,
        **kwargs,
    ):
        """add git repo

        :param name: git repo name
        :param gitlab_project_uri: gitlab project uri
        :param gitlab_project_branch: gitlab project branch [default=master]
        :param paths: list of fleet path to run
        :param targets: list of target where run fleet
        :param gitlab_secret: gitlab secret [optional]
        :param kwargs:
        :return: git repo
        """
        namespace = self.default_namespace

        # definition of custom resource
        body = {
            "apiVersion": self.__get_api_version(),
            "kind": self.kind,
            "metadata": {"name": name, "namespace": namespace},
            "spec": {
                "repo": gitlab_project_uri,
                "branch": gitlab_project_branch,
                "paths": paths,
                "targets": targets,
            },
        }
        if gitlab_secret is not None:
            body["spec"]["clientSecretName"] = gitlab_secret

        res = self.api.create_namespaced_custom_object(self.api_group, self.api_ver, namespace, self.api_plural, body)
        self.logger.debug("create namespace %s git repo: %s" % (self.default_namespace, truncate(res)))
        return res

    @api_request
    def delete(self, name):
        """delete git repo

        :param name:
        :return:
        """
        namespace = self.default_namespace
        res = self.api.delete_namespaced_custom_object(self.api_group, self.api_ver, namespace, self.api_plural, name)
        self.logger.debug("delete namespace %s git repo: %s" % (self.default_namespace, truncate(res)))
        return res
