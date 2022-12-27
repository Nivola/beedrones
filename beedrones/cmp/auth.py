# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

import binascii
from urllib.parse import quote
import requests
from beecell.types.type_string import truncate
from beedrones.cmp.client import CmpBaseService, CmpApiClientError
from beedrones.cmp.jwtclient import JWTClient


class CmpAuthService(CmpBaseService):
    """Cmp authorization service
    """
    SUBSYSTEM = 'auth'
    PREFIX = 'nas'
    VERSION = 'v1.0'

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

    def get_uri(self, uri):
        return '/%s/%s/%s' % (self.VERSION, self.PREFIX, uri)

    #
    # auth provider
    #
    def get_providers(self):
        """Get authentication providers

        :return: list of dict
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = ''
        uri = self.get_uri('providers')
        res = self.api_get(uri, data=data)
        self.logger.debug('get authentication providers: %s' % truncate(res))
        return res

    #
    # auth token
    #
    def list_tokens(self, *args, **kwargs):
        """get tokens

        :param page: query page number [default=0]
        :param size: query page size [default=20]
        :param field: query field [default=id]
        :param order: query order [default=DESC]
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = []
        aliases = {}
        data = self.format_paginated_query(kwargs, params, aliases=aliases)
        uri = self.get_uri('tokens')
        res = self.api_get(uri, data=data)
        self.logger.debug('get tokens: %s' % truncate(res))
        return res

    def get_token(self, oid):
        """get token

        :param oid: token id or uuid
        :return: token
        :raise CmpApiClientError:
        """
        uri = self.get_uri('tokens/%s' % oid)
        res = self.api_get(uri).get('token', {})
        self.logger.debug('get token %s: %s' % (oid, truncate(res)))
        return res

    def create_token(self, api_user=None, api_user_pwd=None, api_user_secret=None, headers=None):
        """Login module internal user

        :param api_user: api user
        :param api_user_pwd: api user password
        :param api_user_secret: api user secret
        :param headers: other headers
        :return: {'access_token': .. , 'seckey':.. }
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        res = None
        if api_user is None:
            api_user = self.api_user
        if api_user_pwd is None:
            api_user_pwd = self.api_user_pwd
        if api_user_secret is None:
            api_user_secret = self.api_user_secret

        if self.api_authtype == 'keyauth':
            data = {'user': api_user, 'password': api_user_pwd}
            uri = self.get_uri('keyauth/token')
            res = self.manager.client.api_request('auth', uri, 'POST', data=data, headers=headers)
            self.logger.info('Login user %s with token: %s' % (self.api_user, res['access_token']))
            self.token = res['access_token']
            self.seckey = res['seckey']
        elif self.api_authtype == 'oauth2' and self.oauth2_grant_type == 'jwt':
            # get client
            client_id = self.api_client_config['uuid']
            client_email = self.api_client_config['client_email']
            client_scope = self.api_client_config['scopes']
            private_key = binascii.a2b_base64(self.api_client_config['private_key'])
            client_token_uri = self.api_client_config['token_uri']
            sub = '%s:%s' % (api_user, api_user_secret)

            res = JWTClient.create_token(client_id, client_email, client_scope, private_key, client_token_uri, sub)
            self.token = res['access_token']
            self.seckey = ''
        elif self.api_authtype == 'oauth2' and self.oauth2_grant_type == 'client':
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.api_client_config['uuid'],
                'client_secret': self.api_client_config['secret']
            }
            endpoint = self.endpoint('auth')
            uri = '%s://%s:%s/v1.0/nas/oauth2/token' % (endpoint['proto'], endpoint['host'], endpoint['port'])
            res = requests.post(uri, data=data, headers=headers)
            res = res.json()
            self.logger.info('Login client %s with token: %s' % (self.api_client_config['uuid'], res['access_token']))
            self.token = res['access_token']
            self.seckey = ''

        self.logger.debug('Get %s token: %s' % (self.api_authtype, self.token))
        return res

    def exist_token(self, token, headers=None):
        """Verify if token already exists

        :param token: token
        :param headers: other headers
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        try:
            uri = self.get_uri('tokens/%s' % token)
            self.self.manager.client.api_request('auth', uri, 'GET', data='', headers=headers)
            res = True
        except CmpApiClientError as ex:
            if ex.code == 401:
                res = False

        self.logger.debug('Check token %s is valid: %s' % (token, res))
        return res

    #
    # auth permission object
    #
    def list_objects(self, *args, **kwargs):
        """get objects

        :param objid: authorization id [optional]
        :param subsystem: object subsystem [optional]
        :param type: object type [optional]
        :param page: query page number [default=0]
        :param size: query page size [default=20]
        :param field: query field [default=id]
        :param order: query order [default=DESC]
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ['objid', 'subsystem', 'type']
        aliases = {}
        data = self.format_paginated_query(kwargs, params, aliases=aliases)
        uri = self.get_uri('objects')
        res = self.api_get(uri, data=data)
        self.logger.debug('get objects: %s' % truncate(res))
        return res

    def get_object(self, oid):
        """get object

        :param oid: object id or uuid
        :return: object
        :raise CmpApiClientError:
        """
        uri = self.get_uri('objects/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get object %s: %s' % (oid, truncate(res)))
        return res

    def add_object(self, subsystem, type, objid, desc, **kvargs):
        """Add authorization object with all related permissions

        :param subsystem: subsystem
        :param type: object type
        :param objid: authorization id
        :param desc: object description
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'subsystem': subsystem,
            'type': type,
            'objid': objid,
            'desc': desc
        }

        uri = self.get_uri('objects')
        res = self.api_post(uri, data={'objects': [data]})
        self.logger.debug('Add object: %s:%s %s' % (objtype, objdef, objid))
        return res

    def del_object(self, subsystem, type, objid, **kvargs):
        """Remove authorization object with all related permissions

        :param subsystem: subsystem
        :param type: object type
        :param objid: authorization id
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        objid = objid.replace('//', '__')
        uri = self.get_uri('objects/%s' % quote('%s:%s:%s' % (subsystem, type, objid)))
        res = self.api_delete(uri)
        self.logger.debug('Remove object: %s:%s %s' % (subsystem, type, objid))
        return res

    #
    # auth permission object type
    #
    def list_object_types(self, *args, **kwargs):
        """get object types

        :param subsystem: object subsystem [optional]
        :param type: object type [optional]
        :param page: query page number [default=0]
        :param size: query page size [default=20]
        :param field: query field [default=id]
        :param order: query order [default=DESC]
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ['subsystem', 'type']
        aliases = {}
        data = self.format_paginated_query(kwargs, params, aliases=aliases)
        uri = self.get_uri('objects/types')
        res = self.api_get(uri, data=data)
        self.logger.debug('get object types: %s' % truncate(res))
        return res

    def add_object_type(self, objtype, objdef):
        """Add authorization object type

        :param objtype: obj type
        :param objdef: obj definition
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'subsystem': objtype,
            'type': objdef
        }

        uri = self.get_uri('objects/types')
        res = self.api_post(uri, data={'object_types': [data]})
        self.logger.debug('Add object type: %s:%s' % (objtype, objdef))
        return res

    def del_object_type(self, type_id):
        """Delete authorization object type

        :param type_id: obj type id
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('objects/types/%s' % type_id)
        res = self.api_delete(uri)
        self.logger.debug('Delete object type: %s' % type_id)
        return res

    #
    # auth permission object action
    #
    def list_actions(self, *args, **kwargs):
        """get actions

        :return: list of entities
        :raise CmpApiClientError:
        """
        params = []
        aliases = {}
        data = self.format_paginated_query(kwargs, params, aliases=aliases)
        uri = self.get_uri('objects/actions')
        res = self.api_get(uri, data=data)
        self.logger.debug('get object actions: %s' % truncate(res))
        return res

    #
    # auth permission object
    #
    def list_object_perms(self, *args, **kwargs):
        """get object permissions

        :param oid: object id [optional]
        :param objid: authorization id [optional]
        :param subsystem: object subsystem [optional]
        :param type: object type [optional]
        :param page: query page number [default=0]
        :param size: query page size [default=20]
        :param field: query field [default=id]
        :param order: query order [default=DESC]
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ['oid', 'objid', 'subsystem', 'type']
        aliases = {}
        data = self.format_paginated_query(kwargs, params, aliases=aliases)
        uri = self.get_uri('objects/perms')
        res = self.api_get(uri, data=data)
        self.logger.debug('get object permissions: %s' % truncate(res))
        return res

    def get_object_perm(self, oid):
        """get object permission

        :param oid: permission id
        :return: object permission
        :raise CmpApiClientError:
        """
        uri = self.get_uri('objects/perms/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get object permission %s: %s' % (oid, truncate(res)))
        return res

    def get_permissions2(self, objtype, objdef, objid):
        """Get object permissions

        :param objtype: obj type list comma separated
        :param objdef: obj definition
        :param objid: authorization id
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = ''
        objid = objid.replace('//', '_')
        uri = '/api/nas/object/perm/T:%s+D:%s+I:%s' % (objtype, objdef, objid)
        res = self.api_request('auth', uri, 'GET', data, silent=True)
        self.logger.debug('Get permission : %s:%s %s' % (objtype, objdef, objid))
        return res

    def get_permissions(self, objtype, objdef, objid, cascade=False, **kvargs):
        """Get object permissions

        :param objtype: obj type list comma separated
        :param objdef: obj definition
        :param objid: authorization id
        :param cascade: If true filter by objid and childs until objid+'//*//*//*//*//*//*'
        :param kvargs: kvargs
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'subsystem': objtype,
            'type': objdef,
            'objid': objid,
            'cascade': cascade
        }
        data.update(kvargs)
        uri = '/v1.0/nas/objects/perms'
        res = self.api_request('auth', uri, 'GET', urlencode(data), parse=True, silent=True)
        self.logger.debug('Get permission : %s:%s %s, cascade: %s' % (objtype, objdef, objid, cascade))
        return res.get('perms'), res.get('total')

    #
    # auth role
    #
    def list_roles(self, *args, **kwargs):
        """get roles

        :param user: user id [optional]
        :param group: group id [optional]
        :param names: name like [optional]
        :param alias: role alias [optional]
        :param perms: list of permission ids [optional]
        :param page: query page number [default=0]
        :param size: query page size [default=20]
        :param field: query field [default=id]
        :param order: query order [default=DESC]
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ['user', 'group', 'names', 'alias', 'perms']
        aliases = {'perms': 'perms.N'}
        data = self.format_paginated_query(kwargs, params, aliases=aliases)
        uri = self.get_uri('roles')
        res = self.api_get(uri, data=data)
        self.logger.debug('get roles: %s' % truncate(res))
        return res

    def get_role(self, oid):
        """get role

        :param oid: role id or uuid
        :return: role
        :raise CmpApiClientError:
        """
        uri = self.get_uri('roles/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get role %s: %s' % (oid, truncate(res)))
        return res

    def exist_role(self, name):
        """Check role exists

        :param name: role name
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = urlencode({'names': name})
        uri = '/v1.0/nas/roles'
        roles = self.api_request('auth', uri, 'GET', data, silent=True).get('roles')
        res = None
        if len(roles) > 0:
            res = roles[0]
        self.logger.debug('Check role %s exists: %s' % (name, res))
        return res

    def append_role_permissions(self, role, objtype, objdef, objid, objaction):
        """Append permission to role

        :param role: role uuid
        :param objtype: obj type
        :param objdef: obj definition
        :param objid: authorization id
        :param objaction: obj action
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'role': {
                'perms': {
                    'append': [{'subsystem': objtype, 'type': objdef, 'objid': objid, 'action': objaction}],
                    'remove': []
                }
            }
        }
        uri = '/v1.0/nas/roles/%s' % role
        res = self.api_request('auth', uri, 'PUT', data, parse=True, silent=True)
        self.logger.debug('Append permission %s:%s %s %s to role %s' % (objtype, objdef, objid, objaction, role))
        return res

    def append_role_permission_list(self, role, perms):
        """Append permissions to role

        :param role: role uuid
        :param perms: list of {'subsystem': objtype, 'type': objdef, 'objid': objid, 'action': objaction}
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'role': {
                'perms': {
                    'append': perms,
                    'remove': []
                }
            }
        }
        uri = '/v1.0/nas/roles/%s' % role
        res = self.api_request('auth', uri, 'PUT', data, parse=True, silent=True)
        self.logger.debug('Append permissions %s ' % truncate(perms))
        return res

    def add_role(self, name, desc):
        """Add role

        :param name: role name
        :param desc: role desc
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'role': {
                'name': name,
                'desc': desc
            }
        }
        uri = '/v1.0/nas/roles'
        res = self.api_request('auth', uri, 'POST', data, parse=True, silent=True)
        self.logger.debug('Add role: %s' % name)
        return res

    def remove_role(self, oid):
        """Remove role

        :param oid: role uuid
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = ''
        uri = '/v1.0/nas/roles/%s' % oid
        res = self.api_request('auth', uri, 'DELETE', data, parse=True, silent=True)
        self.logger.debug('Remove role: %s' % oid)
        return res

    #
    # auth user
    #
    def list_users(self, *args, **kwargs):
        """get users

        :param role: role id [optional]
        :param group: group id [optional]
        :param desc: user description [optional]
        :param email: user email [optional]
        :param names: name like [optional]
        :param perms: list of permission ids [optional]
        :param page: query page number [default=0]
        :param size: query page size [default=20]
        :param field: query field [default=id]
        :param order: query order [default=DESC]
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ['role', 'group', 'names', 'perms', 'desc', 'email']
        aliases = {'perms': 'perms.N'}
        mappings = {'desc': lambda n: '%' + n + '%'}
        data = self.format_paginated_query(kwargs, params, aliases=aliases, mappings=mappings)
        uri = self.get_uri('users')
        res = self.api_get(uri, data=data)
        self.logger.debug('get users: %s' % truncate(res))
        return res

    def get_user(self, oid):
        """get user

        :param oid: user id or uuid
        :return: user
        :raise CmpApiClientError:
        """
        uri = self.get_uri('users/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get user %s: %s' % (oid, truncate(res)))
        return res

    def get_user_secret(self, oid):
        """get user secret

        :param oid: user id or uuid
        :return: user secret
        :raise CmpApiClientError:
        """
        uri = self.get_uri('users/%s/secret' % oid)
        res = self.api_get(uri)
        self.logger.debug('get user %s secret: %s' % (oid, truncate(res)))
        return res

    def get_perms_users(self, perms):
        """Get users associated to some permissions

        :param perms: list of permissions like (objtype, subsystem, objid, action)
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'size': -1,
            'perms.N': perms
        }
        uri = '/v1.0/nas/users'
        res = self.api_request('auth', uri, 'GET', urlencode(data, doseq=True), parse=True, silent=True)
        self.logger.debug('Permissions %s are used by users: %s' % (perms, truncate(res)))
        return res.get('users')

    def add_user(self, name, password, desc):
        """Add user

        :param name: user name
        :param password: user password
        :param desc: user description
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'user': {
                'name': name,
                'desc': desc,
                'active': True,
                'expirydate': '2099-12-31',
                'password': password,
                'base': True
            }
        }

        uri = '/v1.0/nas/users'
        res = self.api_request('auth', uri, 'POST', data, parse=True, silent=True)
        self.logger.debug('Add base user: %s' % name)
        return res

    def add_system_user(self, name, password, desc):
        """Add system user

        :param name: user name
        :param password: user password
        :param desc: user description
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'user': {
                'name': name,
                'password': password,
                'desc': desc,
                'system': True
            }
        }
        uri = '/v1.0/nas/users'
        res = self.api_request('auth', uri, 'POST', data, parse=True, silent=True)
        self.logger.debug('Add system user: %s' % name)
        return res

    def update_user(self, name, new_name, new_pwd, new_desc,
                    uid=None, seckey=None):
        """Update user

        :param name: user name
        :param new_name: user new name
        :param new_pwd: user new password
        :param new_desc: user new description
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'user': {
                'name': new_name,
                'password': new_pwd,
                'desc': new_desc,
            }
        }
        uri = '/v1.0/nas/users/%s' % name
        res = self.api_request('auth', uri, 'PUT', data, parse=True, silent=True)
        self.logger.debug('Update user: %s' % name)
        return res

    def remove_user(self, oid):
        """Remove user

        :param oid: user uuid
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = '/v1.0/nas/users/%s' % oid
        res = self.api_request('auth', uri, 'DELETE', '', silent=True)
        self.logger.debug('Remove user: %s' % oid)
        return res

    def append_user_roles(self, oid, roles):
        """Append roles to user

        :param oid: user uuid
        :param roles: list of role uuids
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'user': {
                'roles': {
                    'append': roles,
                    'remove': []
                },
            }
        }
        uri = '/v1.0/nas/users/%s' % oid
        res = self.api_request('auth', uri, 'PUT', data, parse=True, silent=True)
        self.logger.debug('Append roles %s to user %s' % (roles, oid))
        return res

    def remove_user_roles(self, oid, roles):
        """Remove roles from user

        :param oid: user uuid
        :param roles: list of role uuids
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'user': {
                'roles': {
                    'append': [],
                    'remove': roles
                },
            }
        }
        uri = '/v1.0/nas/users/%s' % oid
        res = self.api_request('auth', uri, 'PUT', data, parse=True, silent=True)
        self.logger.debug('Remove roles %s from user %s' % (roles, oid))
        return res

    def append_user_permissions(self, user, perms):
        """Append permissions to user

        :param user: user uuid
        :param perms: list of {'subsystem': objtype, 'type': objdef, 'objid': objid, 'action': objaction}
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'user': {
                'perms': {
                    'append': perms,
                    'remove': []
                }
            }
        }
        uri = '/v1.0/nas/users/%s' % user
        res = self.api_request('auth', uri, 'PUT', data, parse=True, silent=True)
        self.logger.debug('Append user permissions %s ' % truncate(perms))
        return res

    def remove_user_permissions(self, user, perms):
        """Remove permissions from user

        :param user: user uuid
        :param perms: list of {'subsystem': objtype, 'type': objdef, 'objid': objid, 'action': objaction}
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'user': {
                'perms': {
                    'append': [],
                    'remove': perms
                }
            }
        }
        uri = '/v1.0/nas/users/%s' % user
        res = self.api_request('auth', uri, 'PUT', data, parse=True, silent=True)
        self.logger.debug('Append user permissions %s ' % truncate(perms))
        return res

    #
    # auth group
    #
    def list_groups(self, *args, **kwargs):
        """get groups

        :param user: user id [optional]
        :param role: role id [optional]
        :param names: name like [optional]
        :param perms: list of permission ids [optional]
        :param page: query page number [default=0]
        :param size: query page size [default=20]
        :param field: query field [default=id]
        :param order: query order [default=DESC]
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ['user', 'role', 'names', 'perms']
        aliases = {'perms': 'perms.N'}
        data = self.format_paginated_query(kwargs, params, aliases=aliases)
        uri = self.get_uri('groups')
        res = self.api_get(uri, data=data)
        self.logger.debug('get groups: %s' % truncate(res))
        return res

    def get_group(self, oid):
        """get group

        :param oid: group id or uuid
        :return: group
        :raise CmpApiClientError:
        """
        uri = self.get_uri('groups/%s' % oid)
        res = self.api_get(uri)
        self.logger.debug('get group %s: %s' % (oid, truncate(res)))
        return res

    def get_perms_groups(self, perms):
        """Get groups associated to some permissions

        :param perms: list of permissions like (objtype, subsystem, objid, action)
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'size': -1,
            'perms.N': perms
        }
        uri = '/v1.0/nas/groups'
        res = self.api_request('auth', uri, 'GET', urlencode(data, doseq=True), parse=True, silent=True)
        self.logger.debug('Permissions %s are used by groups: %s' % (perms, truncate(res)))
        return res.get('groups')

    def append_group_roles(self, oid, roles):
        """Append roles to group

        :param oid: role uuid
        :param roles: list of role uuids
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'group': {
                'roles': {
                    'append': roles,
                    'remove': []
                },
            }
        }
        uri = '/v1.0/nas/groups/%s' % oid
        res = self.api_request('auth', uri, 'PUT', data, parse=True, silent=True)
        self.logger.debug('Append roles %s to group %s' % (roles, oid))
        return res

    def remove_group_roles(self, oid, roles):
        """Remove roles from group

        :param oid: role uuid
        :param roles: list of role uuids
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'group': {
                'roles': {
                    'append': [],
                    'remove': roles
                },
            }
        }
        uri = '/v1.0/nas/groups/%s' % oid
        res = self.api_request('auth', uri, 'PUT', data, parse=True, silent=True)
        self.logger.debug('Remove roles %s from group %s' % (roles, oid))
        return res

    def append_group_permissions(self, group, perms):
        """Append permissions to group

        :param group: group uuid
        :param perms: list of {'subsystem': objtype, 'type': objdef, 'objid': objid, 'action': objaction}
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'group': {
                'perms': {
                    'append': perms,
                    'remove': []
                }
            }
        }
        uri = '/v1.0/nas/groups/%s' % group
        res = self.api_request('auth', uri, 'PUT', data, parse=True, silent=True)
        self.logger.debug('Append group permissions %s ' % truncate(perms))
        return res

    def remove_group_permissions(self, group, perms):
        """Remove permissions from group

        :param group: group uuid
        :param perms: list of {'subsystem': objtype, 'type': objdef, 'objid': objid, 'action': objaction}
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'group': {
                'perms': {
                    'append': [],
                    'remove': perms
                }
            }
        }
        uri = '/v1.0/nas/groups/%s' % group
        res = self.api_request('auth', uri, 'PUT', data, parse=True, silent=True)
        self.logger.debug('Append group permissions %s ' % truncate(perms))
        return res
