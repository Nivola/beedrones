# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from ujson import dumps
import base64
from logging import getLogger
import requests
from requests import ConnectionError, ConnectTimeout
from beecell.simple import truncate, check_vault
from urllib3 import disable_warnings, exceptions
from six import ensure_binary

from beecell.types.type_dict import dict_get

disable_warnings(exceptions.InsecureRequestWarning)


class HaproxyError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "HaproxyError: %s" % self.value

    def __str__(self):
        return "HaproxyError: %s" % self.value


def api_request(method):
    def inner(ref, *args, **kwargs):
        try:
            res = method(ref, *args, **kwargs)
            if res.status_code in [200, 201]:
                res = res.json()
            elif res.status_code in [204]:
                res = True
            else:
                res = res.json()
                raise Exception("response error (code={code}): {message}".format(**res))
            return res
        except ConnectTimeout as ex:
            ref.logger.error("haproxy connection timeout: %s" % ex)
            raise HaproxyError(ex)
        except ConnectionError as ex:
            ref.logger.error("haproxy connection error: %s" % ex)
            raise HaproxyError(ex)
        except Exception as ex:
            ref.logger.error("haproxy http error: %s" % ex)
            raise HaproxyError(ex)

    return inner


class HaproxyEntity(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        self.manager = manager
        self.base_uri = "/v2"

    @property
    def token(self):
        return self.manager.token

    @property
    def timeout(self):
        return self.manager.timeout

    @property
    def get_configuration_version(self):
        return self.manager.get_configuration_version()

    def base_http_params(self):
        return self.manager.base_http_params()

    def get_uri(self, path):
        res = "%s://%s:%s%s%s" % (
            self.manager.proto,
            self.manager.host,
            self.manager.port,
            self.base_uri,
            path,
        )
        self.logger.debug("uri: %s" % res)
        return res

    @api_request
    def http_get(self, uri, data=None):
        res = requests.get(self.get_uri(uri), params=data, **self.base_http_params())
        self.logger.debug("haproxy http get response: %s" % truncate(res))
        return res

    @api_request
    def http_post(self, uri, params=None, data=None):
        if data is not None:
            data = dumps(data)
        res = requests.post(self.get_uri(uri), params=params, data=data, **self.base_http_params())
        self.logger.debug("haproxy http post response: %s" % truncate(res))
        return res

    @api_request
    def http_delete(self, uri, params=None, data=None):
        if data is not None:
            data = dumps(data)
        res = requests.delete(self.get_uri(uri), params=params, data=data, **self.base_http_params())
        self.logger.debug("haproxy http delete response: %s" % truncate(res))
        return res


class HaproxyManager(object):
    """HaproxyManager"""

    def __init__(self, host, pwd, port=5555, proto="http", user="admin"):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        self.base_uri = "/v2"
        self.host = host
        self.port = port
        self.proto = proto
        self.user = user
        self.pwd = pwd
        self.timeout = 30.0

        from .frontend import HaproxyFrontend
        from .backend import HaproxyBackend

        self.frontend = HaproxyFrontend(self)
        self.backend = HaproxyBackend(self)

    def set_timeout(self, timeout):
        self.timeout = timeout

    def get_uri(self, path):
        res = "%s://%s:%s%s%s" % (self.proto, self.host, self.port, self.base_uri, path)
        self.logger.debug("uri: %s" % res)
        return res

    def base_http_params(self):
        params = {
            "timeout": self.timeout,
            "verify": False,
            "headers": {"content-type": "application/json"},
            "auth": (self.user, self.pwd),
        }
        return params

    @api_request
    def http_get(self, uri, data=None):
        res = requests.get(self.get_uri(uri), data=data, **self.base_http_params())
        if "error" in res:
            error = res.get("error")
            raise Exception(error["data"])
        self.logger.debug("haproxy http get response: %s" % truncate(res))
        return res

    def ping(self):
        """Ping haproxy

        :return: True or False
        """
        try:
            uri = self.get_uri("/info")
            res = requests.get(
                uri,
                headers={"content-type": "application/json"},
                timeout=self.timeout,
                verify=False,
                auth=(self.user, self.pwd),
            )
            if res.status_code == 200:
                res = True
            else:
                res = False
            self.logger.debug("ping haproxy server: %s" % res)
        except ConnectTimeout as ex:
            self.logger.error("haproxy connection timeout: %s" % ex)
            res = False
        except ConnectionError as ex:
            self.logger.error("haproxy connection error: %s" % ex)
            res = False
        except Exception as ex:
            self.logger.error("haproxy http error: %s" % ex)
            res = False

        return res

    def version(self):
        """get haproxy version

        :return: version info
        """
        res = self.http_get("/info")
        res = dict_get(res, "api.version")
        self.logger.debug("get haproxy server version: %s" % res)
        return res

    def runtime(self):
        """get haproxy runtime

        :return: runtime info
        """
        res = self.http_get("/services/haproxy/runtime/info")
        res = res[0]
        self.logger.debug("get haproxy server runtime: %s" % res)
        return res

    def reloads(self):
        """get haproxy reloads

        :return: reloads info
        """
        res = self.http_get("/services/haproxy/reloads")
        self.logger.debug("get haproxy reloads: %s" % res)
        return res

    def apispec(self, openapi_v3=True):
        """get haproxy api specification

        :param openapi_v3: if True get specification for openapi v3 [default=True]
        :return: reloads info
        """
        if openapi_v3 is True:
            path = "/specification_openapiv3"
        else:
            path = "/specification"
        res = self.http_get(path)
        self.logger.debug("get haproxy api specification: %s" % res)
        return res

    def stats(self):
        """get haproxy stats

        :return: reloads info
        """
        path = "/services/haproxy/stats/native"
        res = self.http_get(path)
        res = res[0].get("stats", [])
        self.logger.debug("get haproxy api stats: %s" % res)
        return res

    def get_configuration_version(self):
        """get haproxy configuration version

        :return: configuration version
        """
        path = "/services/haproxy/configuration/version"
        res = self.http_get(path)
        self.logger.debug("get haproxy configuration version: %s" % res)
        return res

    def get_configuration(self):
        """get haproxy configuration

        :return: configuration
        """
        path = "/services/haproxy/configuration/raw"
        res = self.http_get(path)
        res["data"] = res["data"].split("\n")
        self.logger.debug("get haproxy configuration: %s" % res)
        return res

    def get_root_enpoints(self):
        """get haproxy list of root endpoints.

        :return: list of endpoints
        """
        path = "/"
        res = self.http_get(path)
        self.logger.debug("get haproxy root enpoints: %s" % res)
        return res

    def get_cluster(self):
        """get haproxy cluster data

        :return: configuration
        """
        path = "/cluster"
        res = self.http_get(path)
        self.logger.debug("get haproxy cluster data: %s" % res)
        return res
