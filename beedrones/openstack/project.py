# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import jsonDumps

import ujson as json
from six.moves.urllib.parse import urlencode
from beecell.simple import truncate
from beedrones.openstack.client import OpenstackObject, OpenstackClient, setup_client, OpenstackError


class OpenstackProjectObject(OpenstackObject):
    def setup(self):
        self.client = OpenstackClient(self.manager.uri, self.manager.proxy, timeout=self.manager.timeout)
        self.compute = OpenstackClient(self.manager.endpoint('nova'), self.manager.proxy, timeout=self.manager.timeout)
        # self.blockstore = OpenstackClient(self.manager.endpoint('cinderv2'), self.manager.proxy,
        #                                   timeout=self.manager.timeout)
        self.blockstore = OpenstackClient(self.manager.endpoint('cinderv3'), self.manager.proxy,
                                          timeout=self.manager.timeout)
        self.network = OpenstackClient(self.manager.endpoint('neutron'), self.manager.proxy,
                                       timeout=self.manager.timeout)
        self.manila = OpenstackClient(self.manager.endpoint('manilav2'), self.manager.proxy,
                                      timeout=self.manager.timeout)


class OpenstackDomain(OpenstackProjectObject):
    """
    """
    def __init__(self, manager):
        OpenstackProjectObject.__init__(self, manager)

    @setup_client
    def list(self):
        """list openstack domains

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/domains?'
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack domains: %s' % truncate(res[0]))
        return res[0]['domains']

    @setup_client
    def get(self, oid):
        """
        :param oid: domain id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/domains/%s' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack domains: %s' % truncate(res[0]))
        return res[0]['domain']

    @setup_client
    def create(self, name, domain, is_domain=False, description=""):
        """Create domain
        TODO

        :param name:
        :param domain:
        :param is_domain: Indicates whether the project also acts as a domain.
                          Set to true to define this project as both a project
                          and domain. As a domain, the project provides a name
                          space in which you can create users, groups, and other
                          projects. Set to false to define this project as a
                          regular project that contains only resources.
                          You cannot update this parameter after you create
                          the project. [default=False]
        :param description: [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"project": {
            "description": description,
            "domain_id": domain,
            "enabled": True,
            "name": name,
            "is_domain": is_domain
        }
        }

        path = '/projects'
        res = self.client.call(path, 'POST', data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug('Create openstack project: %s' % truncate(res[0]))
        return res[0]['project']

    @setup_client
    def update(self, oid, name=None, domain=None, enabled=None, description=None):
        """Updates a domain.  TODO

        :param oid: user id
        :param name: [optional]
        :param domain: [optional]
        :param enabled: [optional]
        :param description: [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"project": {}}

        if name is not None:
            data['project']['name'] = name
        if domain is not None:
            data['project']['domain_id'] = domain
        if enabled is not None:
            data['project']['enabled'] = enabled
        if description is not None:
            data['project']['description'] = description

        path = '/projects/%s' % oid
        res = self.client.call(path, 'PATCH', data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug('Update openstack project: %s' % truncate(res[0]))
        return res[0]['project']

    @setup_client
    def delete(self, oid):
        """Deletes a domain. TODO

        :param oid: user id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/projects/%s' % oid
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack project: %s' % truncate(res[0]))
        return True


class OpenstackProject(OpenstackProjectObject):
    """
    """
    def __init__(self, manager):
        OpenstackProjectObject.__init__(self, manager)

    @setup_client
    def list(self, domain=None, parent=None, name=None):
        """List openstack projects

        :param domain: domain id
        :param parent: parent project id
        :param name: project name
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/projects'
        query = {}
        if domain is not None:
            query['domain_id'] = domain
        if parent is not None:
            query['parent_id'] = parent
        if name is not None:
            query['name'] = name

        path = '%s?%s' % (path, urlencode(query))
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack projects: %s' % truncate(res[0]['projects']))
        return res[0]['projects']

    @setup_client
    def get(self, oid=None, name=None):
        """
        :param oid: project id
        :param name: project name
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = '/projects/%s' % oid
        elif name is not None:
            path = '/projects?name=%s' % name
        else:
            raise OpenstackError('Specify at least project id or name')
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack project: %s' % truncate(res[0]))
        if oid is not None:
            project = res[0]['project']
        elif name is not None:
            project = res[0]['projects'][0]

        return project

    @setup_client
    def create(self, name, domain, is_domain=False, parent_id=None, description="", enabled=True):
        """Create project 

        :param name: The project name, which must be unique within the owning 
                     domain. The project can have the same name as its domain. 
        :param domain: The ID of the domain for the project.
                       If you omit the domain ID, default is the domain to which 
                       your token is scoped.
        :param parent_id: The ID of the parent project.
                          If you omit the parent project ID, the project is a 
                          top-level project. 
        :param is_domain: Indicates whether the project also acts as a domain.
                          Set to true to define this project as both a project 
                          and domain. As a domain, the project provides a name 
                          space in which you can create users, groups, and other 
                          projects. Set to false to define this project as a 
                          regular project that contains only resources.
                          You cannot update this parameter after you create 
                          the project. [default=False] 
        :param description: [optional] The project description.
        :param enabled: [default=True] Enables or disables the project.         
        :return: 
            {
                "is_domain": true,
                "description": "My new project",
                "links": {
                    "self": "http://localhost:5000/v3/projects/93ebbcc35335488b96ff9cd7d18cbb2e"
                },
                "enabled": true,
                "id": "93ebbcc35335488b96ff9cd7d18cbb2e",
                "parent_id": null,
                "domain_id": "default",
                "name": "myNewProject"
            }
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "project": {
                "description": description,
                "domain_id": domain,
                "enabled": enabled,
                "name": name,
                "is_domain": is_domain
            }
        }

        if parent_id is not None:
            data['project']['parent_id'] = parent_id

        path = '/projects'
        res = self.client.call(path, 'POST', data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug('Create openstack project: %s' % truncate(res[0]))
        return res[0]['project']

    @setup_client
    def update(self, oid, name=None, domain=None, enabled=None,
               description=None, parent_id=None):
        """Updates a project. 

        :param name: The project name, which must be unique within the owning 
                     domain. The project can have the same name as its domain.
                     [optional] 
        :param domain: The ID of the domain for the project.
                       If you omit the domain ID, default is the domain to which 
                       your token is scoped. [optional] 
        :param parent_id: The ID of the parent project.
                          If you omit the parent project ID, the project is a 
                          top-level project. [optional] 
        :param is_domain: Indicates whether the project also acts as a domain.
                          Set to true to define this project as both a project 
                          and domain. As a domain, the project provides a name 
                          space in which you can create users, groups, and other 
                          projects. Set to false to define this project as a 
                          regular project that contains only resources.
                          You cannot update this parameter after you create 
                          the project. [optional] 
        :param description: [optional] The project description.        
        :param enabled: [optional] Enables or disables the project. 
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {'project': {}}

        if name is not None:
            data['project']['name'] = name
        if domain is not None:
            data['project']['domain_id'] = domain
        if enabled is not None:
            data['project']['enabled'] = enabled
        if description is not None:
            data['project']['description'] = description
        if parent_id is not None:
            data['project']['parent_id'] = parent_id

        path = '/projects/%s' % oid
        res = self.client.call(path, 'PATCH', data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug('Update openstack project %s: %s' % (oid, truncate(res[0])))
        return res[0]['project']

    @setup_client
    def delete(self, oid):
        """Deletes a project. 

        :param oid: user id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/projects/%s' % oid
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack project %s: %s' % (oid, truncate(res[0])))
        return True

    @setup_client
    def get_quotas(self, oid):
        """
        :param oid: project id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        resp = {}
        path = '/os-quota-sets/%s/detail' % oid
        res = self.compute.call(path, 'GET', data='', token=self.manager.identity.token)
        resp['compute'] = res[0]['quota_set']
        resp['compute'].pop('id')

        path = '/os-quota-sets/%s?usage=true' % oid
        res = self.blockstore.call(path, 'GET', data='', token=self.manager.identity.token)
        resp['block'] = res[0]['quota_set']
        resp['block'].pop('id')

        path = '/v2.0/quotas/%s?detail=true' % oid
        res = self.network.call(path, 'GET', data='', token=self.manager.identity.token)
        resp['network'] = res[0]['quota']

        path = '/os-quota-sets/%s' % oid
        res = self.manila.call(path, 'GET', data='', token=self.manager.identity.token)
        resp['share'] = res[0]['quota_set']

        self.logger.debug('Get openstack project quotas: %s' % truncate(res[0]))
        return resp

    @setup_client
    def get_default_quotas(self):
        """Get default quotas

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        resp = {}
        path = '/os-quota-sets/default'
        res = self.compute.call(path, 'GET', data='', token=self.manager.identity.token)
        resp['compute'] = res[0]['quota_set']

        # path = '/os-quota-sets/defaults'
        # res = self.blockstore.call(path, 'GET', data='', 
        #                           token=self.manager.identity.token)
        # resp['block'] = res[0]['quota_set']
        resp['block'] = None

        path = '/v2.0/quotas/default'
        res = self.network.call(path, 'GET', data='', token=self.manager.identity.token)
        resp['network'] = res[0]['quota']

        # path = '/os-quota-sets/%s' % oid
        # res = self.manila.call(path, 'GET', data='', token=self.manager.identity.token)
        # resp['share'] = res[0]['quota_set']

        self.logger.debug('Get openstack project quotas: %s' % truncate(res[0]))
        return resp

    @setup_client
    def update_quota(self, oid, quota_type, quota, value):
        """
        :param oid: project id
        :param quota_type: can be compute, block or network
        :param quota: name of quota param to set
        :param vale: value to set
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        resp = None

        if quota_type == 'compute':
            path = '/os-quota-sets/%s' % oid
            data = {u"quota_set": {quota: value}}
            res = self.compute.call(path, 'PUT', data=jsonDumps(data), token=self.manager.identity.token)
            resp = res[0]['quota_set']

        elif quota_type == 'block':
            path = '/os-quota-sets/%s' % oid
            data = {u"quota_set": {quota: value}}
            res = self.blockstore.call(path, 'PUT', data=jsonDumps(data), token=self.manager.identity.token)
            resp = res[0]['quota_set']

        elif quota_type == 'network':
            path = '/v2.0/quotas/%s' % oid
            data = {u"quota": {quota: value}}
            res = self.network.call(path, 'PUT', data=jsonDumps(data), token=self.manager.identity.token)
            resp = res[0]['quota']

        elif quota_type == 'share':
            path = '/os-quota-sets/%s' % oid
            data = {'quota_set': {quota: value}}
            res = self.manila.call(path, 'PUT', data=jsonDumps(data), token=self.manager.identity.token)
            resp = res[0]['quota_set']

        self.logger.debug('Set openstack project %s quota %s to %s: %s' % (oid, quota, value, truncate(res[0])))

        return resp

    @setup_client
    def get_limits(self):
        """
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        resp = {}
        path = '/limits'
        res = self.compute.call(path, 'GET', data='', token=self.manager.identity.token)
        resp['compute'] = res[0]['limits']['absolute']

        path = '/limits'
        res = self.blockstore.call(path, 'GET', data='', token=self.manager.identity.token)
        resp['block'] = res[0]['limits']['absolute']

        self.logger.debug('Get openstack project quotas: %s' % truncate(res[0]))
        return resp

    @setup_client
    def get_members(self, prj_id):
        """Get project members

        :param prj_id: project id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        # get users
        path = '/users'
        users = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        user_idx = {u.get('id'): u for u in users[0].get('users', [])}

        # get roles
        path = '/roles'
        roles = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        role_idx = {r.get('id'): r for r in roles[0].get('roles', [])}

        # get role assignements
        path = '/role_assignments?scope.project.id=%s' % prj_id
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        members = res[0].get('role_assignments', [])
        resp = []
        for m in members:
            resp.append({
                'role_id': m.get('role').get('id'),
                'role_name': role_idx.get(m.get('role').get('id')).get('name'),
                'user_id': m.get('user').get('id'),
                'user_name': user_idx.get(m.get('user').get('id')).get('name'),
            })
        self.logger.debug('Get openstack project %s members: %s' % (prj_id, resp))
        return resp

    @setup_client
    def assign_member(self, project_id, user_id, role_id):
        """Grants a role to a user on a project. 

        :param project_id: The project ID.
        :param user_id: The user ID.
        :param role_id: The role ID.
        :raise OpenstackError: raise :class:`.OpenstackError` 
        """
        resp = {}
        path = '/projects/%s/users/%s/roles/%s' % (project_id, user_id, role_id)
        res = self.client.call(path, 'PUT', data='', token=self.manager.identity.token)

        self.logger.debug('Grant role %s to user %s on project %s' % (project_id, user_id, role_id))
        return True

    @setup_client
    def remove_member(self, project_id, user_id, role_id):
        """Revokes a role from a user on a project. 

        :param project_id: The project ID.
        :param user_id: The user ID.
        :param role_id: The role ID.
        :raise OpenstackError: raise :class:`.OpenstackError` 
        """
        resp = {}
        path = '/projects/%s/users/%s/roles/%s' % (project_id, user_id, role_id)
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)

        self.logger.debug('Revoke role %s to user %s on project %s' % (project_id, user_id, role_id))
        return True
