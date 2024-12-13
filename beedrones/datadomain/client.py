# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import jsonDumps

from urllib.parse import quote
import requests
import json
from logging import getLogger

from beecell.simple import check_vault, truncate
from requests.exceptions import ConnectionError, ConnectTimeout
from urllib3 import disable_warnings, exceptions

disable_warnings(exceptions.InsecureRequestWarning)


class DataDomainError(Exception):
    def __init__(self, value, code=400):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "DataDomainError: %s" % self.value

    def __str__(self):
        return "DataDomainError: %s" % self.value


class DataDomainEntity(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        self.manager = manager
        self.next = None

    @property
    def token(self):
        return self.manager.token

    @property
    def timeout(self):
        return self.manager.timeout

    @property
    def headers(self):
        headers = self.manager.dd_base_headers
        headers.update({"X-DD-AUTH-TOKEN": self.manager.get_token()})
        return headers

    def get_system_uri(self, oid):
        """get datadomain base system uri

        :param oid: system id. uuid from system api
        :return: formatted uri
        """
        oid = quote(oid)
        return "/dd-systems/%s" % oid

    def http_get(self, uri, **params):
        method = "get"
        uri = self.manager.dd_base_uri + uri

        try:
            res = requests.get(
                uri,
                headers=self.headers,
                timeout=self.timeout,
                params=params,
                verify=False,
            )
            output = res.json()
            if res.status_code in [400, 403, 404, 405]:
                error = output.get("details", "")
                raise Exception(error)
            self.logger.debug("datadomain http %s response: %s" % (method, truncate(output)))
        except ConnectTimeout as ex:
            self.logger.error("datadomain connection timeout: %s" % ex)
            raise DataDomainError(ex)
        except ConnectionError as ex:
            self.logger.error("datadomain connection error: %s" % ex)
            raise DataDomainError(ex)
        except Exception as ex:
            self.logger.error("datadomain http %s error: %s" % (method, ex))
            raise DataDomainError(ex)

        return output

    def http_post(self, uri, data={}):
        method = "post"
        uri = self.manager.dd_base_uri + uri

        try:
            self.logger.debug("post data %s to dd" % data)
            res = requests.post(
                uri,
                headers=self.headers,
                timeout=self.timeout,
                data=jsonDumps(data),
                verify=False,
            )
            output = res.json()
            if res.status_code in [400, 403, 404, 405]:
                error = output.get("detail", None)
                if error is None:
                    error = output
                raise Exception(error)
            self.logger.debug("datadomain http %s response: %s" % (method, truncate(output)))
        except ConnectTimeout as ex:
            self.logger.error("datadomain connection timeout: %s" % ex)
            raise DataDomainError(ex)
        except ConnectionError as ex:
            self.logger.error("datadomain connection error: %s" % ex)
            raise DataDomainError(ex)
        except Exception as ex:
            self.logger.error("datadomain http %s error: %s" % (method, ex))
            raise DataDomainError(ex)

        return output

    def http_put(self, uri, data={}):
        method = "put"
        uri = self.manager.dd_base_uri + uri

        try:
            self.logger.debug("put data %s to dd" % data)
            res = requests.put(
                uri,
                headers=self.headers,
                timeout=self.timeout,
                data=jsonDumps(data),
                verify=False,
            )
            output = res.json()
            if res.status_code in [400, 403, 404, 405]:
                error = output.get("detail", None)
                if error is None:
                    error = output
                raise Exception(error)
            self.logger.debug("datadomain http %s response: %s" % (method, truncate(output)))
        except ConnectTimeout as ex:
            self.logger.error("datadomain connection timeout: %s" % ex)
            raise DataDomainError(ex)
        except ConnectionError as ex:
            self.logger.error("datadomain connection error: %s" % ex)
            raise DataDomainError(ex)
        except Exception as ex:
            self.logger.error("datadomain http %s error: %s" % (method, ex))
            raise DataDomainError(ex)

        return output

    def http_delete(self, uri, data=None):
        method = "delete"
        uri = self.manager.dd_base_uri + uri

        try:
            res = requests.delete(uri, headers=self.headers, timeout=self.timeout, verify=False)
            if res.status_code in [400, 403, 404, 405]:
                output = res.json()
                error = output["detail"]
                raise Exception(error)
            self.logger.debug("datadomain http %s response: %s" % (method, True))
        except ConnectTimeout as ex:
            self.logger.error("datadomain connection timeout: %s" % ex)
            raise DataDomainError(ex)
        except ConnectionError as ex:
            self.logger.error("datadomain connection error: %s" % ex)
            raise DataDomainError(ex)
        except Exception as ex:
            self.logger.error("datadomain http %s error: %s" % (method, ex))
            raise DataDomainError(ex)


class DataDomainManager(object):
    def __init__(self, uri=None, proxy=None, timeout=60.0):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        if uri is None:
            raise
        self.dd_base_uri = uri
        self.dd_base_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.token = None
        self.token_expire = None
        self.timeout = timeout

        from .system import DataDomainSystem
        from .network import DataDomainNetwork
        from .mtree import DataDomainMtree
        from .protocol import DataDomainProtocol
        from .user import DataDomainUser
        from .trust import DataDomainTrust
        from .tenant import DataDomainTenant

        # initialize proxy objects
        self.system = DataDomainSystem(self)
        self.network = DataDomainNetwork(self)
        self.mtree = DataDomainMtree(self)
        self.protocol = DataDomainProtocol(self)
        self.user = DataDomainUser(self)
        self.trust = DataDomainTrust(self)
        self.tenant = DataDomainTenant(self)

    @property
    def headers(self):
        headers = self.dd_base_headers
        headers.update({"X-DD-AUTH-TOKEN": self.get_token()})
        return headers

    def set_timeout(self, timeout):
        self.timeout = timeout

    def ping(self):
        """Ping dd

        :return: True or False
        """
        res = False
        try:
            uri = self.dd_base_uri
            requests.get(uri, headers=self.dd_base_headers, timeout=self.timeout, verify=False)
            res = True
        except ConnectTimeout as ex:
            self.logger.error("datadomain connection timeout: %s" % ex)
        except ConnectionError as ex:
            self.logger.error("datadomain connection error: %s" % ex)
        except Exception as ex:
            self.logger.error("datadomain http %s error: %s" % ("post", False))
        self.logger.debug("Ping dd server: %s" % res)

        return res

    def version(self):
        """Get dd version

        :return: dd version
        """
        try:
            # get token from identity service
            header = self.dd_base_headers
            uri = self.dd_base_uri + "config/"
            res = requests.get(uri, headers=header, timeout=self.timeout, verify=False)
            output = res.json()
            if res.status_code in [400]:
                error = output["detail"]
                raise Exception(error)
            version = {
                "version": output.get("version", None),
                "ansible_version": output.get("ansible_version", None),
            }
            self.logger.debug("Get version: %s" % version)
            return version
        except ConnectTimeout as ex:
            self.logger.error("datadomain connection timeout: %s" % ex)
            raise DataDomainError(ex)
        except ConnectionError as ex:
            self.logger.error("datadomain connection error: %s" % ex)
            raise DataDomainError(ex)
        except Exception as ex:
            self.logger.error("get version error: %s" % ex)
            raise DataDomainError(ex)

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
                self.logger.debug("Try to get token for user %s" % user)
                data = {"auth_info": {"username": user, "password": pwd}}
                uri = self.dd_base_uri + "/auth"
                res = requests.post(
                    uri,
                    headers=self.dd_base_headers,
                    data=jsonDumps(data),
                    timeout=self.timeout,
                    verify=False,
                )
                if res.status_code in [400, 401]:
                    raise Exception("")
                self.token = res.headers["X-DD-AUTH-TOKEN"]
                self.logger.debug("Get token %s for user %s" % (self.token, user))
            except ConnectTimeout as ex:
                self.logger.error("datadomain connection timeout: %s" % ex)
                raise DataDomainError(ex)
            except ConnectionError as ex:
                self.logger.error("datadomain connection error: %s" % ex)
                raise DataDomainError(ex)
            except Exception as ex:
                self.logger.error("get token error: %s" % ex)
                raise DataDomainError(ex)

    def delete_token(self):
        try:
            uri = self.dd_base_uri + "/auth"
            res = requests.delete(uri, headers=self.headers, timeout=self.timeout, verify=False)
            if res.status_code != 200:
                return False
        except ConnectTimeout as ex:
            self.logger.error("datadomain connection timeout: %s" % ex)
            raise DataDomainError(ex)
        except ConnectionError as ex:
            self.logger.error("datadomain connection error: %s" % ex)
            raise DataDomainError(ex)
        except Exception as ex:
            self.logger.error("delete token error: %s" % ex)
            raise DataDomainError(ex)
        return True

    def get_token(self):
        return self.token
