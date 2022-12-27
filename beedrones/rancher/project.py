# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte
import json

from beecell.types.type_dict import dict_get
from beedrones.rancher.client import RancherObject
from beecell.simple import truncate


class RancherProject(RancherObject):
    """RancherProject
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.base_uri = '/v1/management.cattle.io.projects'

    def list(self, **filter):
        """List projects

        :param filter: custom filter
        :return: list of projects
        :raise RancherError:
        """
        cluster_id = filter.get('cluster_id', None)
        name = filter.get('name', None)
        res = self.http_list('', **filter)
        if name is not None:
            res = [p for p in res if dict_get(p, 'spec.displayName') == name]
        if cluster_id is not None:
            res = [p for p in res if p['id'].split('/')[0] == cluster_id]
        self.logger.debug('list projects: %s' % truncate(res))
        return res

    def get(self, project):
        """Get project info

        :param project: project id
        :return: project info
        :raise RancherError:
        """
        res = self.http_get('/%s' % project)
        self.logger.debug('get project: %s' % truncate(res))
        return res

    def add(self, name, cluster_id, limits=None, quotas=None, **kwargs):
        """create project

        :param name: namespace name
        :param cluster_id: cluster id
        :param project_id: project id
        :param labels: dict with labels. Ex {'product': 'prova'} [optional]
        :param limits: dict with limits. Ex {'requestsCpu':'1000m','requestsMemory':'128Mi'} [optional]
        :param quotas: dict with limits. Ex {'pods': 20, 'services': 10} [optional]
        :param kwargs.desc: namespace description [optional]
        :param kwargs.annotations: dict with annotation [optional]
        :param kwargs.labels: dict with labels [optional]
        :return:
        """
        # "creatorId": "local://user-5kj4h"
        data = {
            'type': 'project',
            'name': name,
            'description': kwargs.get('desc', name),
            'annotations': kwargs.get('annotations', {}),
            'labels': kwargs.get('labels', {}),
            'clusterId': cluster_id
        }
        if limits is not None:
            data['containerDefaultResourceLimit'] = limits
        if quotas is not None:
            data['namespaceDefaultResourceQuota']['limit'] = quotas
            data['resourceQuota']['limit'] = quotas
        data.update(self.format_request_data(kwargs, []))
        self.base_uri = '/v3/projects'
        res = self.http_post('', **data)
        self.logger.debug('create project %s in cluster %s' % (name, cluster_id))
        return res

    def delete(self, project_id):
        """delete project

        :param project_id: project id
        :return:
        """
        project_id = project_id.replace('/', ':')
        self.base_uri = '/v3/projects'
        res = self.http_delete('/%s' % project_id)
        self.logger.debug('delete project %s' % project_id)
        return res

    def set_podsecuritypolicy(self, project_id):
        """set project security policy template

        :param cluster_id: cluster id
        :param project_id: project id
        """
        project_id = project_id.replace('/', ':')
        data = {'podSecurityPolicyTemplateId': None}
        self.base_uri = '/v3/projects/%s?action=setpodsecuritypolicytemplate' % project_id
        res = self.http_post('', **data)
        self.logger.debug('set project %s security policy template' % project_id)
        return res

    def list_namespaces(self, cluster_id, **filter):
        """List project namespaces

        :param cluster_id: cluster id
        :param filter: custom filter
        :return: list of namespaces
        :raise RancherError:
        """
        self.base_uri = '/k8s/clusters/%s/v1/namespaces' % cluster_id
        res = self.http_list('', **filter)
        self.logger.debug('list project namespaces: %s' % truncate(res))
        return res

    def get_namespace(self, cluster_id, namespace_id):
        """Get project namespace info

        :param cluster_id: cluster id
        :param namespace_id: namespace id
        :return: namespace info
        :raise RancherError:
        """
        self.base_uri = '/k8s/clusters/%s/v1/namespaces/%s' % (cluster_id, namespace_id)
        res = self.http_get('')
        self.logger.debug('get project: %s' % truncate(res))
        return res

    def add_namespace(self, name, project_id, labels=None, limits=None, **kwargs):
        """create namespace in project

        :param name: namespace name
        :param project_id: project id
        :param labels: dict with labels. Ex {'product': 'prova'} [optional]
        :param limits: dict with limits. Ex {'requestsCpu':'1000m','requestsMemory':'128Mi'} [optional]
        :param kwargs.desc: namespace description [optional]
        :return:
        """
        project_id = project_id.replace('/', ':')
        cluster_id, project_id_small = project_id.split(':')
        data = {
            'type': 'namespace',
            'metadata': {
                'annotations': {
                    'field.cattle.io/description': kwargs.get('desc', name),
                    'field.cattle.io/projectId': project_id,
                },
                'labels': {'field.cattle.io/projectId': project_id_small},
                'name': name
            }
        }
        if labels is not None:
            data['metadata']['labels'].update(labels)
        if limits is not None:
            data['metadata']['annotations']['field.cattle.io/containerDefaultResourceLimit'] = json.dumps(limits)
        data.update(self.format_request_data(kwargs, []))
        self.base_uri = '/k8s/clusters/%s/v1/namespaces' % cluster_id
        res = self.http_post('', **data)
        self.logger.debug('create namespace %s in project %s' % (name, project_id))
        return res

    def del_namespace(self, cluster_id, namespace_id):
        """delete namespace in project

        :param cluster_id: cluster id
        :param namespace_id: namespace id
        :return:
        """
        self.base_uri = '/k8s/clusters/%s/v1/namespaces/%s' % (cluster_id, namespace_id)
        res = self.http_delete('')
        self.logger.debug('delete namespace %s' % namespace_id)
        return res
