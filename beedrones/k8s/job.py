# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.types.type_string import truncate
from beedrones.k8s.client import k8sEntity, api_request


class K8sJob(k8sEntity):
    """K8sJob
    """
    @property
    def api(self):
        return self.manager.batch_api

    @api_request
    def list(self, name=None):
        """list jobs in a namespace or in all the namespaces

        :return: list of jobs
        """
        if self.all_namespaces is True:
            services = self.api.list_job_for_all_namespaces()
        else:
            services = self.api.list_namespaced_job(self.default_namespace)

        res = services.to_dict().get('items', [])
        for i in res:
            i['metadata']['creation_timestamp'] = str(i['metadata']['creation_timestamp'])

        self.logger.debug('list jobs: %s' % truncate(res))
        return res

    @api_request
    def get(self, name):
        """get job

        :param name: name of the job
        :return:
        """
        job = self.api.read_namespaced_job(name, self.default_namespace)
        res = self.get_dict(job)
        res['metadata']['creation_timestamp'] = str(res['metadata']['creation_timestamp'])
        res['metadata']['managed_fields'][0]['time'] = str(res['metadata']['managed_fields'][0]['time'])
        self.logger.debug('get namespace %s job: %s' % (self.default_namespace, truncate(res)))
        return res

    @api_request
    def add(self, name, **kwargs):
        namespace = self.default_namespace

        # Configurate Job metadata
        metadata = self.client.V1ObjectMeta(
            name=name,
            namespace=namespace,
        )
        # Instantiate the job object
        job = self.client.V1Job(
            api_version='v1',
            kind='Job',
            # How do I modify here ?
            data=dict(**kwargs),
            metadata=metadata
        )

        res = self.api.create_namespaced_job(namespace, body=job)
        return res

    @api_request
    def delete(self, name):
        namespace = self.default_namespace
        res = self.api.delete_namespaced_job(name, namespace)
        return res
