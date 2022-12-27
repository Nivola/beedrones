# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import jsonDumps

import requests
from logging import getLogger
from beecell.simple import check_vault, truncate
from requests.exceptions import ConnectionError, ConnectTimeout
from urllib3 import disable_warnings, exceptions

disable_warnings(exceptions.InsecureRequestWarning)


class AwxError(Exception):
    def __init__(self, value, code=400):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)
   
    def __repr__(self):
        return 'AwxError: %s' % self.value
   
    def __str__(self):
        return 'AwxError: %s' % self.value


class AwxEntity(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.manager = manager
        self.next = None

    @property
    def token(self):
        return self.manager.token

    @property
    def timeout(self):
        return self.manager.timeout

    def has_next(self):
        if self.next is not None:
            return True
        return False

    def http_get(self, uri, default_result=[], **params):
        method = 'get'
        header = {'Authorization': 'Bearer ' + self.token}
        uri = self.manager.awx_base_uri + uri

        try:
            res = requests.get(uri, headers=header, timeout=self.timeout, params=params, verify=False)
            output = res.json()
            if res.status_code in [400, 403, 404, 405]:
                error = output['detail']
                raise Exception(error)
            self.logger.debug('awx http %s response: %s' % (method, truncate(output)))
        except ConnectTimeout as ex:
            self.logger.error('awx connection timeout: %s' % ex)
            raise AwxError(ex)
        except ConnectionError as ex:
            self.logger.error('awx connection error: %s' % ex)
            raise AwxError(ex)
        except Exception as ex:
            self.logger.error('awx http %s error: %s' % (method, ex))
            raise AwxError(ex)

        return output

    def http_list(self, uri, page=1, page_size=20, **params):
        params.update({'page': page, 'page_size': page_size, 'order_by': '-id'})
        res = self.http_get(uri, **params)
        output = res.get('results', None)
        self.next = res.get('next', None)
        return output

    def http_post(self, uri, data={}):
        method = 'post'
        header = {'Authorization': 'Bearer ' + self.token, 'content-type': 'application/json'}
        uri = self.manager.awx_base_uri + uri

        try:
            self.logger.debug('post data %s to awx' % data)
            res = requests.post(uri, headers=header, timeout=self.timeout, data=jsonDumps(data), verify=False)
            if res.status_code in [400, 403, 404, 405]:
                output = res.json()
                error = output.get('detail', None)
                if error is None:
                    error = output
                raise Exception(error)
            else:
                try:
                    output = res.json()
                except:
                    output = res.text
            self.logger.debug('awx http %s response: %s' % (method, truncate(output)))
        except ConnectTimeout as ex:
            self.logger.error('awx connection timeout: %s' % ex)
            raise AwxError(ex)
        except ConnectionError as ex:
            self.logger.error('awx connection error: %s' % ex)
            raise AwxError(ex)
        except Exception as ex:
            self.logger.error('awx http %s error: %s' % (method, ex), exc_info=True)
            raise AwxError(ex)

        return output

    def http_delete(self, uri, data=None):
        method = 'delete'
        header = {'Authorization': 'Bearer ' + self.token}
        uri = self.manager.awx_base_uri + uri

        try:
            res = requests.delete(uri, headers=header, timeout=self.timeout, verify=False)
            if res.status_code in [400, 403, 404, 405]:
                output = res.json()
                error = output['detail']
                raise Exception(error)
            self.logger.debug('awx http %s response: %s' % (method, True))
        except ConnectTimeout as ex:
            self.logger.error('awx connection timeout: %s' % ex)
            raise AwxError(ex)
        except ConnectionError as ex:
            self.logger.error('awx connection error: %s' % ex)
            raise AwxError(ex)
        except Exception as ex:
            self.logger.error('awx http %s error: %s' % (method, ex))
            raise AwxError(ex)


class AwxManager(object):
    def __init__(self, uri=None, proxy=None, timeout=60.0):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        if uri is None:
            raise 
        self.awx_base_uri = uri
        self.token = None
        self.token_expire = None
        self.timeout = timeout

        from .user import AwxUser
        from .organization import AwxOrganization
        from .inventory import AwxInventory
        from .inventory_script import AwxInventoryScript
        from .job import AwxJob
        from .project import AwxProject
        from .credential import AwxCredential
        from .template import AwxJobTemplate
        from .host import AwxHost
        from .ad_hoc_command import AwxAdHocCommand

        # initialize proxy objects
        self.user = AwxUser(self)
        self.organization = AwxOrganization(self)
        self.inventory = AwxInventory(self)
        self.inventory_script = AwxInventoryScript(self)
        self.job = AwxJob(self)
        self.project = AwxProject(self)
        self.credential = AwxCredential(self)
        self.job_template = AwxJobTemplate(self)
        self.host = AwxHost(self)
        self.ad_hoc_command = AwxAdHocCommand(self)

    def set_timeout(self, timeout):
        self.timeout = timeout

    def ping(self):
        """Ping awx

        :return: True or False
        """
        res = False
        try:
            uri = self.awx_base_uri
            requests.get(uri, headers={'content-type': 'application/json'}, timeout=self.timeout, verify=False)
            res = True
        except ConnectTimeout as ex:
            self.logger.error('awx connection timeout: %s' % ex)
        except ConnectionError as ex:
            self.logger.error('awx connection error: %s' % ex)
        except Exception as ex:
            self.logger.error('awx http %s error: %s' % ('post', False))
        self.logger.debug('Ping awx server: %s' % res)

        return res

    def version(self):
        """Get awx version

        :return: awx version
        """
        try:
            # get token from identity service
            header = {'Authorization': 'Bearer ' + self.token, 'content-type': 'application/json'}
            uri = self.awx_base_uri + 'config/'
            res = requests.get(uri, headers=header, timeout=self.timeout, verify=False)
            output = res.json()
            if res.status_code in [400]:
                error = output['detail']
                raise Exception(error)
            version = {'version': output.get('version', None), 'ansible_version': output.get('ansible_version', None)}
            self.logger.debug('Get version: %s' % version)
            return version
        except ConnectTimeout as ex:
            self.logger.error('awx connection timeout: %s' % ex)
            raise AwxError(ex)
        except ConnectionError as ex:
            self.logger.error('awx connection error: %s' % ex)
            raise AwxError(ex)
        except Exception as ex:
            self.logger.error('get version error: %s' % ex)
            raise AwxError(ex)

    def authorize(self, user=None, pwd=None, token=None, key=None):
        """Get token

        :param user: user
        :param pwd: password
        :param token: token string
        :param key: [optional] fernet key used to decrypt encrypted password
        """
        # check password is encrypted
        if pwd is not None:
            pwd = check_vault(pwd, key)

        # set token
        if token is not None:
            self.token = token
        else:
            try:
                # get token from identity service
                self.logger.debug('Try to get token for user %s' % user)
                uri = self.awx_base_uri + 'users/2/personal_tokens/'
                res = requests.post(uri, headers={'content-type': 'application/json'}, auth=(user, pwd),
                                    timeout=self.timeout, verify=False)
                output = res.json()
                if res.status_code in [400, 401]:
                    error = output['detail']
                    raise Exception(error)
                self.token = output['token']
                self.token_expire = output['expires']
                self.logger.debug('Get token %s for user %s' % (self.token, user))
                # return self.token
            except ConnectTimeout as ex:
                self.logger.error('awx connection timeout: %s' % ex)
                raise AwxError(ex)
            except ConnectionError as ex:
                self.logger.error('awx connection error: %s' % ex)
                raise AwxError(ex)
            except Exception as ex:
                self.logger.error('get token error: %s' % ex)
                raise AwxError(ex)

    def get_token(self):
        return {'token': self.token, 'expires': self.token_expire}
