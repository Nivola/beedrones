# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import truncate
from beedrones.haproxy.client import HaproxyEntity, HaproxyError


class HaproxyBackend(HaproxyEntity):
    """HaproxyBackend
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_uri = '/v2/services/haproxy/configuration'

    def list(self, **filter):
        """Get haproxy backends

        :return: list of backends
        :raise HaproxyError:
        """
        data = filter
        res = self.http_get('/backends', data=data).get('data', [])
        self.logger.debug('list backends: %s' % truncate(res))
        return res

    def get(self, name):
        """Get haproxy backend

        :param name: backend name
        :return: backend
        :raise HaproxyError:
        """
        res = self.http_get('/backends/%s' % name, data=None).get('data', [])
        self.logger.debug('get backend: %s' % truncate(res))
        return res

    def add(self, name, force_reload=True, check_timeout=30, connect_timeout=30, server_timeout=30, retries=3,
            balance='roundrobin', *args, **kwargs):
        """add haproxy backend

        :param str name: backend name
        :param int check_timeout: check timeout [default=30s]
        :param int connect_timeout: connect timeout [default=30s]
        :param int server_timeout: server timeout [default=30s]
        :param int retries: retries [default=3]
        :param str balance: balance algorithm. Allowed values: roundrobin, static-rr, leastconn, first, source, uri,
            url_param, hdr, random, rdp-cookie  [default=roundrobin]
        :param bool force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :return: backend
        :raise HaproxyError:
        """
        params = {'force_reload': force_reload, 'version': self.get_configuration_version}
        data = {
            'name': name,
            'check_timeout': check_timeout,
            'connect_timeout': connect_timeout,
            'server_timeout': server_timeout,
            'retries': retries,
            'balance': {'algorithm': balance},
        }
        data = data | kwargs
        res = self.http_post('/backends', params=params, data=data).get('data', [])
        self.logger.debug('add backend %s' % name)
        return res

    def add_tcp(self, name, adv_check='tcp-check', *args, **kwargs):
        """add haproxy tcp backend. Main params are explained. For the other params see base add method.

        :param str name: backend name
        :param str adv_check: advanced check. Allowed values: ssl-hello-chk, ldap-check, tcp-check, [default=tcp-check]
        :param balance: balance algorithm. Allowed values: roundrobin, static-rr, leastconn, first, source, uri,
            url_param, hdr, random, rdp-cookie  [default=source]
        :return: backend
        :raise HaproxyError:
        """
        new_kwargs = {
            'mode': 'tcp',
            'adv_check': adv_check,
            'option': 'tcplog',
        }
        kwargs = kwargs | new_kwargs
        res = self.add(name, *args, **kwargs)
        return res

    def add_smtp(self, name, domain, hello, *args, **kwargs):
        """add haproxy tcp smtp backend. Main params are explained. For the other params see base add method.

        :param str name: backend name
        :param str domain: stmp domain for check
        :param str hello: smtp hello for check
        :return: backend
        :raise HaproxyError:
        """
        new_kwargs = {
            'adv_check': 'smtpchk',
            'smtpchk_params': {'domain': domain, 'hello': hello}
        }
        kwargs = kwargs | new_kwargs
        res = self.add_tcp(name, *args, **kwargs)
        return res

    def add_mysql(self, name, username, *args, **kwargs):
        """add haproxy tcp mysql backend. Main params are explained. For the other params see base add method.

        :param str name: backend name
        :param str username: mysql username for check
        :return: backend
        :raise HaproxyError:
        """
        new_kwargs = {
            'adv_check': 'mysql-check',
            'mysql_check_params': {'username': username}
        }
        kwargs = kwargs | new_kwargs
        res = self.add_tcp(name, *args, **kwargs)
        return res

    def add_postgres(self, name, username, *args, **kwargs):
        """add haproxy tcp postgres backend. Main params are explained. For the other params see base add method.

        :param str name: backend name
        :param str username: mysql username for check
        :return: backend
        :raise HaproxyError:
        """
        new_kwargs = {
            'adv_check': 'pgsql-check',
            'pgsql_check_params': {'username': username}
        }
        kwargs = kwargs | new_kwargs
        res = self.add_tcp(name, *args, **kwargs)
        return res

    def add_redis(self, name, *args, **kwargs):
        """add haproxy tcp redis backend. Main params are explained. For the other params see base add method.

        :param str name: backend name
        :return: backend
        :raise HaproxyError:
        """
        new_kwargs = {
            'adv_check': 'redis-check',
            'redispatch': {'enabled': True, 'interval': 30000}
        }
        kwargs = kwargs | new_kwargs
        res = self.add_tcp(name, *args, **kwargs)
        return res

    def add_http(self, name, *args, **kwargs):
        """add haproxy http backend. Main params are explained. For the other params see base add method.

        :param str name: backend name
        :param str kwargs.cookie: cookie configuration. Type allowed: rewrite, insert, prefix.
            Ex. {'name':.., 'type':..} [optional]
        :param str kwargs.httpchk_path: http check path. [default=/]
        :param str kwargs.http_connection_mode: Allowed values: httpclose, http-server-close, http-keep-alive
        :param int kwargs.http_keep_alive_timeout: http keep alive timeout
        :param int kwargs.http_request_timeout: http request timeout
        :param str kwargs.http_reuse: http reuse. Allowed values: aggressive, always, never, safe
        :return: backend
        :raise HaproxyError:
        """
        httpchk_path = kwargs.get('httpchk_path', '/')
        http_kwargs = {
            'mode': 'http',
            'adv_check': 'httpchk',
            'forwardfor': {
                'enabled': 'enabled'
            },
            'httpchk_params': {
                'method': 'GET',
                'uri': httpchk_path,
                'version': 'HTTP/1.1'
            }
        }
        kwargs = kwargs | http_kwargs
        res = self.add(name, *args, **kwargs)
        return res

    def delete(self, name, force_reload=True):
        """delete haproxy backend

        :param name: backend name
        :param force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :return: True
        :raise HaproxyError:
        """
        params = {'force_reload': force_reload, 'version': self.get_configuration_version}
        res = self.http_delete('/backends/%s' % name, params=params)
        self.logger.debug('delete backend %s' % name)
        return res

    def get_acls(self, name):
        """Get haproxy backend acl

        :param name: backend name
        :return: list of backend acls
        :raise HaproxyError:
        """
        data = {'parent_name': name, 'parent_type': 'backend'}
        res = self.http_get('/acls', data=data).get('data', [])
        self.logger.debug('list backend %s acls: %s' % (name, truncate(res)))
        return res

    def add_acl(self, backend, name, value, force_reload=True, criterion='src', index=0):
        """add haproxy backend acl

        :param backend: backend name
        :param force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :param str name: acl name
        :param str criterion: acl criterion. [default=src]
        :param int index: acl index [defaul=0]
        :param str value: acl value
        :return: backend acl
        :raise HaproxyError:
        """
        params = {'parent_name': backend, 'parent_type': 'backend', 'force_reload': force_reload,
                  'version': self.get_configuration_version}
        data = {'acl_name': name, 'criterion': criterion, 'index': index, 'value': value,
                'version': self.get_configuration_version}
        res = self.http_post('/acls', params=params, data=data).get('data', [])
        self.logger.debug('add backend %s acl: %s' % (backend, name))
        return res

    def del_acl(self, backend, index, force_reload=True):
        """delete haproxy backend acl

        :param backend: backend name
        :param force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :param int index: acl index
        :return: True
        :raise HaproxyError:
        """
        params = {'parent_name': backend, 'parent_type': 'backend', 'force_reload': force_reload,
                  'version': self.get_configuration_version}
        res = self.http_delete('/acls/%s' % index, params=params)
        self.logger.debug('delete backend %s acl: %s' % (backend, index))
        return res

    def get_servers(self, name):
        """Get haproxy backend server

        :param name: backend name
        :return: list of backend servers
        :raise HaproxyError:
        """
        data = {'backend': name, 'parent_type': 'backend'}
        res = self.http_get('/servers', data=data).get('data', [])
        self.logger.debug('list backend %s servers: %s' % (name, truncate(res)))
        return res

    def add_server(self, backend, name, address, port, force_reload=True, *args, **kwargs):
        """add haproxy backend server

        :param backend: backend name
        :param force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :param str name: server name
        :param str address: server address
        :param int port: server port
        :param int kwargs.weight: server weight
        :return: backend server
        :raise HaproxyError:
        """
        params = {'backend': backend, 'force_reload': force_reload, 'version': self.get_configuration_version}
        data = {
            'address': address,
            'check': 'enabled',
            'name': name,
            'port': port,
            'weight': 80
        }
        data.update(kwargs)
        res = self.http_post('/servers', params=params, data=data).get('data', [])
        self.logger.debug('add backend %s server: %s' % (backend, name))
        return res

    def del_server(self, backend, name, force_reload=True):
        """delete haproxy backend server

        :param backend: backend name
        :param force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :param str name: server name
        :return: True
        :raise HaproxyError:
        """
        params = {'backend': backend, 'force_reload': force_reload, 'version': self.get_configuration_version}
        res = self.http_delete('/servers/%s' % name, params=params)
        self.logger.debug('delete backend %s server: %s' % (backend, name))
        return res

