# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.types.type_string import truncate
from beedrones.k8s.client import k8sEntity, api_request


class K8sCronJob(k8sEntity):
    """K8sCronJob"""

    @property
    def api(self):
        return self.manager.batch_beta_api

    @api_request
    def list(self, name=None):
        """list cronjobs in a namespace or in all the namespaces

        :return: list of cronjobs
        """
        if self.all_namespaces is True:
            services = self.api.list_cron_job_for_all_namespaces()
        else:
            services = self.api.list_namespaced_cron_job(self.default_namespace)

        res = services.to_dict().get("items", [])
        for i in res:
            i["metadata"]["creation_timestamp"] = str(i["metadata"]["creation_timestamp"])
            i["status"]["last_schedule_time"] = str(i["status"]["last_schedule_time"])

        self.logger.debug("list cronjobs: %s" % truncate(res))
        return res

    @api_request
    def get(self, name):
        """get cronjob

        :param name: name of the cronjob
        :return:
        """
        cronjob = self.api.read_namespaced_cron_job(name, self.default_namespace)
        res = self.get_dict(cronjob)
        res["metadata"]["creation_timestamp"] = str(res["metadata"]["creation_timestamp"])
        res["metadata"]["managed_fields"][0]["time"] = str(res["metadata"]["managed_fields"][0]["time"])
        self.logger.debug("get namespace %s cronjob: %s" % (self.default_namespace, truncate(res)))
        return res

    @api_request
    def add(self, name, **kwargs):
        namespace = self.default_namespace

        # Configurate CronJob metadata
        metadata = self.client.V1ObjectMeta(
            name=name,
            namespace=namespace,
        )
        # Instantiate the cronjob object
        cronjob = self.client.V1CronJob(
            api_version="v1",
            kind="CronJob",
            # How do I modify here ?
            data=dict(**kwargs),
            metadata=metadata,
        )

        res = self.api.create_namespaced_cron_job(namespace, body=cronjob)
        return res

    @api_request
    def delete(self, name):
        namespace = self.default_namespace
        res = self.api.delete_namespaced_cron_job(name, namespace)
        return res
