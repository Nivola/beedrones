# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

import requests
import urllib3
from logging import getLogger
from beecell.crypto_util.rsa_crypto import RasCrypto
from beecell.simple import truncate

urllib3.disable_warnings()


def http_request(method):
    def inner(ref, *args, **kwargs):
        try:
            res = method(ref, *args, **kwargs)
            ref.logger.debug('response headers: %s' % res.headers)
            ref.logger.debug('response data: %s' % res.text)
            if res.status_code == requests.codes.ok:
                res = res.json()
            else:
                raise CmpApiConnectionManagerError(res.json().get('detail'), code=res.status_code)
        except CmpApiConnectionManagerError as ex:
            ref.logger.error(ex.value, exc_info=True)
            raise
        except Exception as ex:
            ref.logger.error(ex, exc_info=True)
            raise CmpApiConnectionManagerError(str(ex))
        return res
    return inner


class CmpApiConnectionManagerError(Exception):
    def __init__(self, value, code=400):
        self.code = code
        self.value = value
        Exception.__init__(self, value, code)

    def __repr__(self):
        return 'CmpConnectionManagerError: %s' % self.value

    def __str__(self):
        return '%s, %s' % (self.value, self.code)


class CmpApiConnectionManager(object):
    """Cmp client to db and vm connection manager

    :param endpoint: api endpoint. Ex. https://dev-node01.tstsddc.csi.it
    :param token: authentication token
    :param key: public key used to encrypt some params [optional]
    """
    def __init__(self, endpoint, token, key=None, timeout=5.0, tls_verify=False):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        # api endpoint
        self.endpoint = endpoint
        # api token
        self.token = token
        # encryption public key
        self.key = key
        # tls cert verify
        self.tls_verify = tls_verify
        # http(s) timeout
        self.timeout = timeout
        # crypto
        self.cripto_client = None
        self.public_key = None
        self.__load_pem()

        # services
        self.sys = CmpApiConnectionManagerPluginSystem(self)
        self.db = CmpApiConnectionManagerPluginDb(self)

    def __load_pem(self):
        if self.key is not None:
            self.cripto_client = RasCrypto()
            self.public_key = self.cripto_client.import_public_key(self.key)

    def encrypt(self, data):
        if self.cripto_client is not None and self.public_key is not None:
            return self.cripto_client.encrypt(self.public_key, data)
        else:
            raise CmpApiConnectionManagerError('client cryptography is not configured')


class CmpApiConnectionManagerAbstractPlugin(object):
    """Cmp client to db and vm connection manager. Abstract plugin api
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.manager = manager
        self.headers = {}

    def __setup_headers(self):
        self.headers['Authorization'] = 'Bearer %s' % self.manager.token
        return self.headers

    def __set_params(self, params=''):
        data = {
            'params': params,
            'verify': self.manager.tls_verify,
            'headers': self.__setup_headers(),
            'timeout': self.manager.timeout
        }
        return data

    def set_headers(self, headers):
        self.headers.update(headers)

    def encrypt(self, data):
        return self.manager.encrypt(data)

    def get_uri(self, uri):
        return '%s/%s' % (self.manager.endpoint, uri)

    @http_request
    def api_get(self, uri, params=''):
        res = requests.get(self.get_uri(uri), **self.__set_params(params))
        return res

    @http_request
    def api_post(self, uri, params=''):
        res = requests.post(self.get_uri(uri), **self.__set_params(params))
        return res

    @http_request
    def api_put(self, uri, params=''):
        res = requests.put(self.get_uri(uri), **self.__set_params(params))
        return res

    @http_request
    def api_patch(self, uri, params=''):
        res = requests.patch(self.get_uri(uri), **self.__set_params(params))
        return res

    @http_request
    def api_delete(self, uri, params=''):
        res = requests.delete(self.get_uri(uri), **self.__set_params(params))
        return res


class CmpApiConnectionManagerPluginSystem(CmpApiConnectionManagerAbstractPlugin):
    """Cmp client to db and vm connection manager. System plugin api
    """
    def ping(self):
        res = self.api_get('status/ping')
        self.logger.debug('ping server: %s' % res)
        return res


class CmpApiConnectionManagerPluginDb(CmpApiConnectionManagerAbstractPlugin):
    """Cmp client to db and vm connection manager. Database plugin api
    """
    SUPPORTED_ENGINE = ['mysql', 'postgres', 'oracle', 'mssql']

    def __init__(self, manager):
        super().__init__(manager)

        self.db_params = None

    def setup(self, engine, host, pwd, **kwargs):
        """Setup database connection

        :param engine: database engine type. Supported are mysql, postgres, oracle, mssql
        :param host: database instance host
        :param pwd: database instance user password
        :param kwargs.port: database instance port [optional]
        :param kwargs.user: database instance user [optional]
        :param kwargs.db: database instance name [optional]
        :return:
        """
        if engine not in self.SUPPORTED_ENGINE:
            raise CmpApiConnectionManagerError('supported engine are %s' % self.SUPPORTED_ENGINE)
        self.db_params = {
            'engine': engine,
            'host': host,
            'pwd': self.encrypt(pwd)
        }
        self.db_params.update(kwargs)
        return self.db_params

    def __check_params(self):
        if self.db_params is None:
            raise CmpApiConnectionManagerError('database connection params are not configured')

    def ping(self):
        """ping database instance

        :return: container
        :raise CmpApiClientError:
        """
        self.__check_params()
        res = self.api_get('db/ping', params=self.db_params)
        self.logger.debug('ping database instance: %s' % res)
        return res

    def get_schemas(self):
        """get database schemas

        :return: dict
        :raise CmpApiClientError:
        """
        self.__check_params()
        res = self.api_get('db/schemas', params=self.db_params)
        self.logger.debug('get database schemas: %s' % truncate(res))
        return res

    def add_schema(self, name):
        """add database schema

        :param name: schema name
        :return: dict
        :raise CmpApiClientError:
        """
        self.__check_params()
        self.db_params.update({'schema_name': name})
        res = self.api_post('db/schemas', params=self.db_params)
        self.logger.debug('add database schema: %s' % res)
        return res

    def del_schema(self, name):
        """delete database schema

        :param name: schema name
        :return: dict
        :raise CmpApiClientError:
        """
        self.__check_params()
        self.db_params.update({'schema_name': name})
        res = self.api_delete('db/schemas', params=self.db_params)
        self.logger.debug('delete database schema: %s' % res)
        return res

    def get_tables(self, schema_name):
        """get database schema tables

        :return: dict
        :raise CmpApiClientError:
        """
        self.__check_params()
        self.db_params.update({'schema_name': schema_name})
        res = self.api_get('db/tables', params=self.db_params)
        self.logger.debug('get database schema %s tables: %s' % (schema_name, truncate(res)))
        return res

    def get_users(self):
        """get database users

        :return: dict
        :raise CmpApiClientError:
        """
        self.__check_params()
        res = self.api_get('db/users', params=self.db_params)
        self.logger.debug('get database users: %s' % truncate(res))
        return res

    def add_user(self, name, pwd):
        """add database user

        :param name: user name
        :param pwd: user password
        :return: dict
        :raise CmpApiClientError:
        """
        self.__check_params()
        self.db_params.update({'user_name': name, 'password': pwd})
        res = self.api_post('db/users', params=self.db_params)
        self.logger.debug('add database user: %s' % res)
        return res

    def del_user(self, name):
        """delete database user

        :param name: user name
        :return: dict
        :raise CmpApiClientError:
        """
        self.__check_params()
        self.db_params.update({'user_name': name})
        res = self.api_delete('db/users', params=self.db_params)
        self.logger.debug('delete database user: %s' % res)
        return res

    # params = {'engine': engine, 'host': host, 'pwd': client.encrypt(public_key, pwd), 'user_name': 'prova@%',
    #           'password': 'dhy76e-y3Er'}
    # res = requests.post(base_uri + '/db/users', params=params, verify=False, headers=headers)
    # print('add user: %s' % res.json())
    #
    # params = {'engine': engine, 'host': host, 'pwd': client.encrypt(public_key, pwd)}
    # res = requests.get(base_uri + '/db/users', params=params, verify=False, headers=headers)
    # print('list users: %s' % res.json())
    #
    # params = {'engine': engine, 'host': host, 'pwd': client.encrypt(public_key, pwd), 'user_name': 'prova@%'}
    # res = requests.delete(base_uri + '/db/users', params=params, verify=False, headers=headers)
    # print('delete user: %s' % res.json())
