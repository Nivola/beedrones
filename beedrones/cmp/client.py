# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from re import match
from uuid import uuid4
from requests import post
from ujson import loads, dumps
import ssl
from time import time, sleep
from logging import getLogger
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from binascii import a2b_base64, b2a_hex
from beecell.types.type_dict import dict_get
from beecell.password import obscure_string, obscure_data
from beecell.crypto import check_vault
from beecell.simple import truncate
from multiprocessing import current_process
from base64 import b64encode
from .jwtclient import JWTClient
from six.moves.urllib.parse import urlencode
from six.moves import http_client
from six import PY3, ensure_text


class CmpApiClientError(Exception):
    def __init__(self, value, code=400):
        self.code = code
        self.value = value
        Exception.__init__(self, value, code)

    def __repr__(self):
        return 'CmpApiClientError: %s' % self.value

    def __str__(self):
        return '%s, %s' % (self.value, self.code)


class CmpApiClient(object):
    """Beehive api client.

    :param auth_endpoints: api main endpoints
    :param authtype: api authentication filter: keyauth, aouth2, simplehttp
    :param user: api user
    :param pwd: api user password
    :param catalog_id: api catalog id
    :param proxy: http proxy server {'host': .., 'port': ..} [optional]
    :param prefixuri: custom prefix path to use in uri [default='']
    :param oauth2_grant_type: oauth2 grant type. Can be jwt or client [default=jwt]
    :param client_config: contains the oauth2 client config.
        Ex. jwt {'uuid':.., 'client_email':.., 'scopes':.., 'private_key':.., 'token_uri':..}
        Ex. client {'uuid':.., 'secret':..}
        Ex. user {'uuid':..}
    """
    def __init__(self, auth_endpoints, authtype, user, pwd, secret=None, catalog_id=None, client_config=None, 
                 proxy=None, oauth2_grant_type='jwt'):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        # atfork()
        self.pid = current_process().ident

        if len(auth_endpoints) > 0:
            self.main_endpoint = auth_endpoints[0]
        else:
            self.main_endpoint = None
        self.endpoints = {'auth': None, 'event': None, 'ssh': None, 'resource': None, 'service': None}
        # self.endpoint_weights = {'auth': [], 'event': [], 'ssh': [], 'resource': [], 'service': []}
        self.api_authtype = authtype  # can be: simplehttp, oauth2, keyauth
        self.oauth2_grant_type = oauth2_grant_type
        self.api_user = user
        self.api_user_pwd = pwd
        self.api_user_secret = secret
        self.api_client_config = client_config

        self.catalog_id = catalog_id

        self.max_attempts = 3  # number of attempt to get a valid endpoint

        self.prefixuri = None

        # token data
        self.token = None
        self.seckey = None
        self.filter = None

        # set if print extended log
        self.debug = False
        self.print_curl = False

        # curl string
        self.curl_string = None

        # http(s) proxy
        self.proxy = proxy

        # http request timeout
        self.timeout = 5.0

    def __parse_endpoint(self, endpoint_uri: str) -> dict:
        """Parse endpoint http://10.102.160.240:6060

        :param endpoint: http://10.102.160.240:6060
        :return: {'proto':.., 'host':.., 'port':..}
        :rtype: dict
        """
        try:
            t1 = endpoint_uri.split('://')
            t2 = t1[1].split(':')
            t3 = t2[1].split('/')
            port = t3[0]
            prefix = self.prefixuri
            if len(t3) > 1:
                prefix = '/' + t3[1]

            return {'proto': t1[0], 'host': t2[0], 'port': port, 'prefix': prefix}
        except Exception as ex:
            self.logger.error('Error parsing endpoint %s: %s' % (endpoint_uri, ex))

    def set_endpoints(self, endpoints):
        for name, uri in endpoints.items():
            self.endpoints[name] = self.__parse_endpoint(uri)
            # self.endpoints[name].append([self.__parse_endpoint(uri), 0])
        self.logger.debug('Set endpoints: %s' % self.endpoints)

    def endpoint(self, subsystem):
        """Select a subsystem endpoint from list

        :param subsystem: subsystem
        :return: endpoint of the subsystem api
        """
        endpoint = self.endpoints.get(subsystem)

        # get endpoint from catalog
        if endpoint is None:
            self.__load_catalog()
            # if subsystem does not already exist return error
            try:
                endpoint = self.endpoints.get(subsystem)
            except:
                raise CmpApiClientError('Subsystem %s reference is empty' % subsystem, code=404)

        return endpoint

    def set_prefixuri(self, prefixuri):
        """set api request prefixuri

        :param prefixuri: prefixuri like /stage
        :return:
        """
        self.prefixuri = prefixuri

    def set_timeout(self, timeout):
        """set api request timeout
        
        :param timeout: time in seconds
        :return: 
        """
        self.timeout = timeout

    def set_debug(self, debug):
        """enable or disable extended http request log

        :param debug: True or False
        :return: 
        """
        self.debug = debug
        
    def set_print_curl(self, print_curl):
        """enable or disable print curl in log

        :param print_curl: True or False
        :return: 
        """
        self.print_curl = print_curl

    def get_curl_request(self):
        """return request with curl syntax

        :return:
        """
        return self.curl_string

    def __sign_request(self, seckey64, data):
        """Sign data using public/private key signature. Signature algorithm used is 
        RSA. Hash algorithm is SHA256.

        :param seckey64: secret key encoded in base64
        :param data: data to sign
        :return: data signature
        :rtype: str 
        """
        try:
            # if current_process().ident != self.pid:
            #     atfork()

            # import key
            seckey = a2b_base64(seckey64)
            key = RSA.importKey(seckey)

            # create data hash
            if PY3:
                hash_data = SHA256.new()
                hash_data.update(bytes(data, encoding='utf-8'))
            else:
                hash_data = SHA256.new(data)

            # sign data
            signer = PKCS1_v1_5.new(key)
            signature = signer.sign(hash_data)

            # encode signature in base64
            signature64 = ensure_text(b2a_hex(signature))

            return signature64
        except Exception as ex:
            self.logger.error(ex, exc_info=True)
            raise CmpApiClientError('Error signing data: %s' % data, code=401)

    def __http_client(self, proto, host, path, method, data='', headers=None, port=80):
        """Http client

        :param proto: Request proto. Ex. http, https
        :param host: Request host. Ex. 10.102.90.30
        :param port: Request port. [default=80]
        :param path: Request path. Ex. /api/
        :param method: Request method. Ex. GET, POST, PUT, DELETE
        :param headers: Request headers. [optional]
            Ex. {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        :param data: Request data. Can be a string or a dict. [optional]
            Ex. {'@number': 12524, '@type': 'issue', '@action': 'show'}
        :raise CmpApiClientError:
        """
        try:
            # start time
            start = time()

            if headers is None:
                headers = {}

            #headers['env'] = 'lab5'
            #headers['Env'] = 'lab5'

            # append request-id to headers
            if 'request-id' not in headers:
                headers['request-id'] = str(uuid4())
            reqid = headers['request-id']

            # append user agent
            headers['User-Agent'] = 'beehive/1.0'

            # get content type
            content_type = headers.get('Content-type', 'application/json')

            send_data = obscure_data(data)
            self.logger.info('Api Request [%s] %s %s://%s:%s%s, timeout=%s' %
                             (reqid, method, proto, host, port, path, self.timeout))
            self.logger.debug('API Request: %s - Call: METHOD=%s, URI=%s://%s:%s%s, HEADERS=%s, DATA=%s' %
                              (reqid, method, proto, host, port, truncate(path), headers, truncate(send_data)))

            # format curl string
            if self.print_curl is True:
                curl_url = ['curl -k -v -S -X %s' % method.upper()]
                if data is not None and data != '':
                    curl_url.append("-d '%s'" % data)
                    curl_url.append('-H "Content-Type: %s"' % content_type)
                if headers is not None:
                    for header in headers.items():
                        curl_url.append('-H "%s: %s"' % header)
                curl_url.append('%s://%s:%s%s' % (proto, host, port, path))
                self.curl_string = ' '.join(curl_url)
                self.logger.debug(self.curl_string)

            if proto == 'http':
                conn = http_client.HTTPConnection(host, port, timeout=self.timeout)
                if self.proxy is not None and self.proxy.get('host') is not None:
                    conn.set_tunnel(self.proxy.get('host'), port=self.proxy.get('port'))
            else:
                try:
                    ssl._create_default_https_context = ssl._create_unverified_context
                except:
                    pass
                if self.proxy is not None and self.proxy.get('host') is not None:
                    conn = http_client.HTTPSConnection(self.proxy.get('host'), port=self.proxy.get('port'),
                                                       timeout=self.timeout)
                    conn.set_tunnel(host, port=port)
                else:
                    conn = http_client.HTTPSConnection(host, port, timeout=self.timeout)

            # set data
            if isinstance(data, dict) or isinstance(data, list):
                if method.upper() == 'GET' or content_type == 'application/x-www-form-urlencoded':
                    data = urlencode(data)
                else:
                    data = dumps(data)

            if method.upper() == 'GET' or content_type == 'application/x-www-form-urlencoded':
                path = '%s?%s' % (path, data)

            # get response
            conn.request(method, path, data, headers)
        except Exception as ex:
            self.logger.error(ex, exc_info=True)
            raise CmpApiClientError('Service Unavailable', code=503)

        response = None
        res = {}
        content_type = ''

        try:
            response = conn.getresponse()
            content_type = response.getheader('content-type')

            if response.status in [200, 201, 202, 400, 401, 403, 404, 405, 406, 408, 409, 415]:
                res = response.read()
                if content_type is not None and content_type.find('application/json') >= 0:
                    res = loads(res)

                # insert for compliance with oauth2 error message
                if getattr(res, 'error', None) is not None:
                    res['message'] = res['error_description']
                    res['description'] = res['error_description']
                    res['code'] = response.status

            elif response.status in [204]:
                res = {}
            elif response.status in [500]:
                res = {'code': 500, 'message': 'Internal Server Error', 'description': 'Internal Server Error'}
            elif response.status in [501]:
                res = {'code': 501, 'message': 'Not Implemented', 'description': 'Not Implemented'}
            elif response.status in [502]:
                res = {'code': 502, 'message': 'Bad Gateway Error', 'description': 'Bad Gateway Error'}
            elif response.status in [503]:
                res = {'code': 503, 'message': 'Service Unavailable', 'description': 'Service Unavailable'}
            else:
                res = {'code': response.status, 'message': res, 'description': res}
            conn.close()
        except Exception as ex:
            elapsed = time() - start
            self.logger.error(ex, exc_info=False)
            if response is not None:
                self.logger.error('API Request: %s - Response: HOST=%s, STATUS=%s, CONTENT-TYPE=%s, RES=%s, '
                                  'ELAPSED=%s' % (reqid, response.getheader('remote-server', ''),
                                                  response.status, content_type, truncate(res), elapsed))
            else:
                self.logger.error('API Request: %s - Response: HOST=%s, STATUS=%s, CONTENT-TYPE=%s, RES=%s, '
                                  'ELAPSED=%s' % (reqid, None, 'Timeout', content_type, truncate(res), elapsed))

            raise CmpApiClientError(str(ex), code=400)

        if response.status in [200, 201, 202]:
            elapsed = time() - start
            self.logger.debug('API Request: %s - Response: HOST=%s, STATUS=%s, CONTENT-TYPE=%s, RES=%s, '
                              'ELAPSED=%s' % (reqid, response.getheader('remote-server', ''), response.status,
                                              content_type, truncate(res), elapsed))
        elif response.status in [204]:
            elapsed = time() - start
            self.logger.debug('API Request: %s - Response: HOST=%s, STATUS=%s, CONTENT-TYPE=%s, RES=%s, '
                              'ELAPSED=%s' % (reqid, response.getheader('remote-server', ''), response.status,
                                              content_type, truncate(res), elapsed))
        else:
            if isinstance(res, dict):
                err = res.get('message', '')
                code = res.get('code', 400)
            else:
                err = res
                code = 400
            self.logger.error(err, exc_info=False)
            raise CmpApiClientError(err, code=int(code))

        return res

    def base_api_request(self, subsystem, path, method, data='', headers=None):
        """Send api request

        :param subsystem: subsystem
        :param path: request path
        :param method: http method
        :param data: request data
        :param headers: other headers
        :return: request response
        :rtype: dict
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        start = time()
        self.logger.info('======== CMP API - START ========')

        # get endpoint
        endpoint = self.endpoint(subsystem)
        proto = endpoint['proto']
        host = endpoint['host']
        port = endpoint['port']
        prefix = endpoint['prefix']

        base_headers = {'Accept': 'application/json'}
        if self.api_authtype == 'keyauth' and self.token is not None:
            base_path = path.split('?')[0]
            sign = self.__sign_request(self.seckey, base_path)
            base_headers.update({'uid': self.token, 'sign': sign})
        elif self.api_authtype == 'oauth2' and self.token is not None:
            base_headers.update({'Authorization': 'Bearer %s' % self.token})
        elif self.api_authtype == 'simplehttp':
            auth = b64encode('%s:%s' % (self.api_user, self.api_user_pwd))
            base_headers.update({'Authorization': 'Basic %s' % auth})
        # print(round(time() - start, 3))
        if prefix is not None:
            path = '%s%s' % (prefix, path)

        if headers is not None:
            base_headers.update(headers)

        elapsed = round(time() - start, 3)
        self.logger.info('======== CMP API - PRE: %s ========' % elapsed)

        res = self.__http_client(proto, host, path, method, port=port, data=data, headers=base_headers)

        elapsed = round(time() - start, 3)
        self.logger.info('======== CMP API - STOP: %s ========' % elapsed)
        return res

    def api_request(self, subsystem, path, method, data='', headers=None):
        """Make api request using subsystem

        :param subsystem: subsystem
        :param path: request path
        :param method: http method
        :param data: request data
        :param headers: other headers
        :return: request response
        :rtype: dict
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        try:
            res = self.base_api_request(subsystem, path, method, data, headers=headers)
        except CmpApiClientError as ex:
            # Request is not authorized
            if ex.code in [401]:
                # try to get token and retry api call
                self.token = None
                self.seckey = None
                self.create_token()
                res = self.base_api_request(subsystem, path, method, data, headers=headers)
            else:
                raise
        return res

    #
    # catalog query methods
    #
    def __load_catalog(self, catalog_id=None):
        """Load catalog endpoint

        :param catalog_id: catalog id
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        if catalog_id is not None:
            self.catalog_id = catalog_id

        if self.catalog_id is not None:
            # load catalog endpoints
            uri = '/v1.0/ncs/catalogs/%s' % self.catalog_id
            catalog = self.api_request('auth', uri, 'GET', '').get('catalog')

            services = catalog['services']
            for service in services:
                for endpoint in service['endpoints']:
                    self.endpoints[service['service']] = self.__parse_endpoint(endpoint)
        else:
            raise CmpApiClientError('Catalog id is undefined')

    #
    # token
    #
    def set_token(self, token, seckey=None):
        """set api token

        :param token: access token
        :param seckey: keyauth secret key
        """
        self.token = token
        self.seckey = seckey

    def get_token(self):
        """get api token

        :return: {'token':.., 'seckey':..}
        """
        return {'token': self.token, 'seckey': self.seckey}

    def save_token(self, token, seckey):
        """save token for next use. Extend to use from outside"""
        pass

    def __set_content_type_multipart(self, headers):
        try:
            headers['Content-type'] = 'application/x-www-form-urlencoded'
        except:
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
        return headers

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
            res = self.base_api_request('auth', '/v1.0/nas/keyauth/token', 'POST', data=data, headers=headers)
            self.logger.info('Login user %s with token: %s' % (self.api_user, res['access_token']))
            self.token = res['access_token']
            self.seckey = res['seckey']
        elif self.api_authtype == 'oauth2' and self.oauth2_grant_type == 'urn:ietf:params:oauth:grant-type:jwt-bearer':
            # get client
            client_id = self.api_client_config['uuid']
            client_email = self.api_client_config['client_email']
            client_scope = self.api_client_config['scopes']
            private_key = a2b_base64(self.api_client_config['private_key'])
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
            headers = self.__set_content_type_multipart(headers)
            res = self.base_api_request('auth', '/v1.0/nas/oauth2/token', 'POST', data=data, headers=headers)

            # endpoint = self.endpoint('auth')
            # uri = '%s://%s:%s/v1.0/nas/oauth2/token' % (endpoint['proto'], endpoint['host'], endpoint['port'])
            # res = post(uri, data=data, headers=headers)
            # res = res.json()
            self.logger.info('Login client %s with token: %s' % (self.api_client_config['uuid'], res['access_token']))
            self.token = res['access_token']
            self.seckey = ''
        elif self.api_authtype == 'oauth2' and self.oauth2_grant_type == 'user':
            data = {
                'grant_type': 'password',
                'username': api_user,
                'password': api_user_secret,
                'client_id': self.api_client_config['uuid'],
                # 'client_secret': self.api_client_config['secret']
            }
            headers = self.__set_content_type_multipart(headers)
            res = self.base_api_request('auth', '/v1.0/nas/oauth2/token', 'POST', data=data, headers=headers)

            # uri = '%s://%s:%s/v1.0/nas/oauth2/token' % (endpoint['proto'], endpoint['host'], endpoint['port'])
            # res = post(uri, data=data, headers=headers, verify=False)
            # res = res.json()
            self.logger.info('Login user %s with token: %s' % (self.api_client_config['uuid'], res['access_token']))
            self.token = res['access_token']
            self.seckey = ''

        # save token
        self.save_token(self.token, self.seckey)

        self.logger.debug('Get %s token: %s' % (self.api_authtype, self.token))
        return res


class CmpApiManagerError(Exception):
    def __init__(self, value, code=400):
        self.code = code
        self.value = value
        Exception.__init__(self, value, code)

    def __repr__(self):
        return 'CmpApiManagerError: %s' % self.value

    def __str__(self):
        return '%s, %s' % (self.value, self.code)


class CmpApiManager(object):
    """Cmp platform manager

    :param endpoints: api endpoints. Dict like {'auth':.., 'ssh':.., 'resource':..}
    :param authparams: api authentication params. Ex. 
        {'type':'keyauth', 'user':.., 'pwd':..}
        {'type':'oauth2', 'client_config':{'grant_type':.., }, 'user':.., 'secret':..}
    :param proxy: http proxy server {'host':.., 'port':..} [optional]
    :param key: [optional] fernet key used to decrypt encrypted password
    :param catalog: [optional] endpoints catalog id
    """
    def __init__(self, endpoints, authparams, proxy=None, key=None, catalog=None):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        # api endpoints
        self.endpoints = endpoints
        # api endpoints catalog
        self.catalog_id = catalog
        # authentication params
        self.authparams = authparams
        # http(s) proxy
        self.proxy = proxy
        # connection timeout in seconds
        self.timeout = 30.0
        # task timeout in seconds
        self.task_timeout = 1800.0
        # task delta time in seconds
        self.task_delta = 2.0
        # task trace function
        self.task_trace = None
        # api client
        self.client = None
        # fernet key
        self.key = key

        # cmp services
        from .auth import CmpAuthService
        from .catalog import CmpCatalogService
        from .scheduler import CmpSchedulerService
        from .event import CmpEventService
        from .resource import CmpResourceService
        from .business import CmpBusinessService
        from .ssh import CmpSshService
        from .platform import CmpPlatformService

        self.auth = CmpAuthService(self)
        self.catalog = CmpCatalogService(self)
        self.scheduler = CmpSchedulerService(self)
        self.event = CmpEventService(self)
        self.resource = CmpResourceService(self)
        self.business = CmpBusinessService(self)
        self.ssh = CmpSshService(self)
        self.platform = CmpPlatformService(self)

        self.__after_init()

    def __after_init(self):
        # get auth endpoint
        auth_endpoint = dict_get(self.endpoints, 'auth')
        if auth_endpoint is None:
            raise CmpApiManagerError('cmp auth endpoint is not configured')

        authtype = dict_get(self.authparams, 'type')
        user = dict_get(self.authparams, 'user')
        pwd = None
        secret = None
        client_config = None
        oauth2_grant_type = None
        if user is None:
            raise CmpApiManagerError('cmp user must be specified')

        if authtype == 'keyauth':
            pwd = dict_get(self.authparams, 'pwd')
            if pwd is None:
                raise CmpApiManagerError('cmp user password must be specified')
            pwd = check_vault(pwd, self.key)
        elif authtype == 'oauth2':
            secret = dict_get(self.authparams, 'secret')
            if secret is None:
                raise CmpApiManagerError('cmp user secret must be specified')
            secret = check_vault(secret, self.key)
            
            client_config = dict_get(self.authparams, 'client_config')
            if client_config is None:
                raise CmpApiManagerError('cmp oauth2 client config must be specified')
            oauth2_grant_type = client_config.get('grant_type', 'jwt')

        self.client = CmpApiClient(auth_endpoint, authtype, user, pwd, secret, client_config=client_config, 
                                   proxy=self.proxy, catalog_id=self.catalog_id, oauth2_grant_type=oauth2_grant_type)
        self.client.set_endpoints(self.endpoints)

    def set_prefixuri(self, prefixuri):
        """set api request prefixuri

        :param prefixuri: prefixuri like /stage
        :return:
        """
        self.client.set_prefixuri(prefixuri)

    def set_timeout(self, timeout):
        """set api request timeout

        :param timeout: time in seconds
        :return: 
        """
        self.timeout = timeout
        self.client.set_timeout(timeout)

    def set_task_timeout(self, timeout):
        """set task request timeout

        :param timeout: time in seconds
        """
        self.task_timeout = timeout

    def create_token(self):
        self.client.create_token()

    def get_token(self):
        """get api token

        :return: {'token':.., 'seckey':..}
        """
        return self.client.get_token()

    def set_token(self, token, seckey=None):
        """set api token

        :param token: access token
        :param seckey: keyauth secret key
        """
        self.client.set_token(token, seckey=seckey)

    def set_debug(self, debug):
        """enable or disable extended http request log

        :param debug: True or False
        """
        self.client.set_debug(debug)

    def set_print_curl(self, print_curl):
        """enable or disable print curl in log

        :param print_curl: True or False
        """
        self.client.set_print_curl(print_curl)

    def get_curl_request(self):
        """return request with curl syntax

        :return:
        """
        return self.client.get_curl_request()

    def set_task_trace(self, func):
        """set task trace function. task_status ex: 'SUCCESS', 'FAILURE', 'TIMEOUT'

        :param func: trace function like: def trace(subsystem, task_id, task_status, msg=None): ...
        """
        self.task_trace = func

    def set_save_token(self, save_token):
        """set save token function

        :param save_token: save_token function
        """
        self.client.save_token = save_token

    def api_request(self, subsystem, path, method, data='', headers=None):
        """Make api request using subsystem

        :param subsystem: subsystem
        :param path: request path
        :param method: http method
        :param data: request data
        :param headers: other headers
        :return: request response
        :rtype: dict
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        res = self.client.api_request(subsystem, path, method, data=data, headers=headers)
        return res

    def ping(self):
        """ping all the cmp subsystems

        :return: dict like this {'auth': True, 'event': True, 'ssh': True, 'resource': True, 'service': True}
        """
        subsystems = {
            'auth': self.auth,
            'event': self.event,
            'ssh': self.ssh,
            'resource': self.resource,
            'service': self.business
        }
        res = {'auth': False, 'event': False, 'ssh': False, 'resource': False, 'service': False}
        for subsystem, helper in subsystems.items():
            ping = helper.ping()
            res[subsystem] = ping
        return res


class CmpBaseService(object):
    """Cmp base service
    """
    SUBSYSTEM = None
    PREFIX = None
    VERSION = None

    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.manager = manager
        self.task_key = 'taskid'

    def get_api_version(self, *args, **kwargs):
        """get api version. Set preferred_version if version is not specified. Set VERSION if preferred_version and
        version are not specified.

        :param args: positional params
        :param kwargs: key value params
        :param kwargs.preferred_version: preferred version [optional]
        :param kwargs.version: version [optional]
        :return:
        """
        preferred_version = kwargs.get('preferred_version', None)
        version = kwargs.get('version', None)
        if version is None and preferred_version is None:
            version = self.VERSION
        elif version is None:
            version = preferred_version
        return version

    def get_uri(self, uri, **kwargs):
        version = self.get_api_version(**kwargs)
        return '/%s/%s/%s' % (version, self.PREFIX, uri)

    def is_name(self, oid):
        """Check if id is uuid, id or literal name.

        :param oid:
        :return: True if it is a literal name
        """
        # get obj by uuid
        if match('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', str(oid)):
            self.logger.debug('Param %s is an uuid' % oid)
            return False
        # get obj by id
        elif match('^\d+$', str(oid)):
            self.logger.debug('Param %s is an id' % oid)
            return False
        # get obj by name
        elif match('[\-\w\d]+', oid):
            self.logger.debug('Param %s is a name' % oid)
            return True

    def is_uuid(self, oid):
        """Check if id is uuid

        :param oid:
        :return: True if it is a uuid
        """
        if match('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', str(oid)) is not None:
            return True
        return False

    def wait_task(self, res):
        if isinstance(res, dict):
            taskid = dict_get(res, self.task_key)
            if taskid is not None:
                self.__wait_task(taskid)
            # taskid = res.get('nvl_TaskId', None)
            # if taskid is not None:
            #     self.cmp_api_client.wait_task(taskid, maxtime=task_timeout, delta=delta)
            # taskid = dict_get(res, '%s.nvl-activeTask' % task_key)
            # if taskid is not None:
            #     self.cmp_api_client.wait_task(taskid, maxtime=task_timeout, delta=delta)

    def api_get(self, uri, data='', headers=None):
        res = self.manager.client.api_request(self.SUBSYSTEM, uri, 'GET', data=data, headers=headers)
        return res

    def api_post(self, uri, data='', headers=None):
        res = self.manager.client.api_request(self.SUBSYSTEM, uri, 'POST', data=data, headers=headers)
        self.wait_task(res)
        return res

    def api_put(self, uri, data='', headers=None):
        res = self.manager.client.api_request(self.SUBSYSTEM, uri, 'PUT', data=data, headers=headers)
        self.wait_task(res)
        return res

    def api_patch(self, uri, data='', headers=None):
        res = self.manager.client.api_request(self.SUBSYSTEM, uri, 'PATCH', data=data, headers=headers)
        self.wait_task(res)
        return res

    def api_delete(self, uri, data='', headers=None):
        res = self.manager.client.api_request(self.SUBSYSTEM, uri, 'DELETE', data=data, headers=headers)
        self.wait_task(res)
        return res

    def format_paginated_query(self, kwargs, params, mappings=None, aliases=None):
        params.extend(['page', 'size', 'field', 'order'])
        return self.format_query(kwargs, params, mappings, aliases)

    def format_query(self, kwargs, params, mappings=None, aliases=None):
        if mappings is None:
            mappings = {}
        if aliases is None:
            aliases = {}
        data = {}
        for item in params:
            mapping = mappings.get(item, None)
            value = kwargs.get(item, None)
            if value is not None:
                if mapping is not None:
                    value = mapping(value)
                item = aliases.get(item, item)
                data[item] = value
        data = urlencode(data, doseq=True)
        self.logger.debug('query data: %s' % data)
        return data

    def format_request_data(self, kwargs, param_names):
        """Set params in request data

        :param dict kwargs: input params
        :param list param_names: list of supported param names
        :return: dict with params that are not None
        """
        data = {}
        for key in param_names:
            val = kwargs.get(key, None)
            if val is not None:
                data[key] = val
        return data

    #
    # task
    #
    def __get_task_status(self, taskid):
        """get task status

        :param taskid: task id
        :return: task status
        :raise CmpApiClientError:
        """
        try:
            uri = '/v2.0/%s/worker/tasks/%s/status' % (self.PREFIX, taskid)
            res = self.api_get(uri)
            task = res.get('task_instance')
            status = task.get('status')
            return status
        except:
            return 'FAILURE'

    def __get_task(self, taskid):
        """get task

        :param taskid: task id
        :return: task
        :raise CmpApiClientError:
        """
        uri = '/v2.0/%s/worker/tasks/%s' % (self.PREFIX, taskid)
        res = self.api_get(uri)
        task = res.get('task_instance')
        self.logger.debug('Get task %s: %s' % (taskid, task))
        return task

    def __get_task_trace(self, taskid):
        uri = '/v2.0/%s/worker/tasks/%s/trace' % (self.PREFIX, taskid)
        res = self.api_get(uri)
        trace = res.get('task_trace')[-1]['message']
        self.logger.debug('Get task %s trace: %s' % (taskid, trace))
        return trace

    def __trace_task(self, taskid, status, msg=None):
        """Trace for running task

        :param taskid: task id
        :param status: task status
        :param msg: custom message [optional]
        :return: None
        """
        if self.manager.task_trace is not None:
            self.manager.task_trace(self.SUBSYSTEM, taskid, status, msg=msg)

    def __wait_task(self, taskid, trace=None):
        """Wait for running task

        :param taskid: task id
        :param trace: trace function [optional]
        :param headers: other headers
        :return: None
        """
        self.logger.info('wait for task %s' % taskid)
        status = self.__get_task_status(taskid)
        elapsed = 0
        while status not in ['SUCCESS', 'FAILURE', 'TIMEOUT']:
            self.__trace_task(taskid, status)
            sleep(self.manager.task_delta)
            status = self.__get_task_status(taskid)
            self.logger.debug('%s task %s status: %s' % (self.SUBSYSTEM, taskid, status))
            elapsed += self.manager.task_delta
            if elapsed > self.manager.task_timeout:
                status = 'TIMEOUT'

        # # get task
        # task = self.__get_task(taskid)

        if status == 'TIMEOUT':
            self.__trace_task(taskid, status, msg='timeout')
            msg = '%s task %s timeout' % (self.SUBSYSTEM, taskid)
            self.logger.error(msg)
            raise CmpApiClientError(msg)
        elif status == 'FAILURE':
            trace = self.__get_task_trace(taskid)
            self.__trace_task(taskid, status, msg=trace)

            msg = '%s task %s failure' % (self.SUBSYSTEM, taskid)
            self.logger.error(msg)
            raise CmpApiClientError(msg)
        else:
            self.__trace_task(taskid, status)

        self.logger.info('%s task %s success' % (self.SUBSYSTEM, taskid))

    #
    # common
    #
    def ping(self):
        """ping cmp subsystem

        :return: True if ping ok, False otherwise
        """
        res = True
        try:
            ping = self.api_get(self.get_uri('ping'))
            res = res and ping.get('sql_ping', False) and ping.get('redis_ping', False) \
                  and ping.get('redis_identity_ping', False)
        except:
            res = False
        return res
