# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

import json
from urllib.parse import urlencode

import requests
from requests.exceptions import ConnectionError, ConnectTimeout
from beecell.simple import check_vault, truncate
from logging import getLogger


class RancherError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "RancherError: %s" % self.value

    def __str__(self):
        return "RancherError: %s" % self.value


class RancherObject(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
        self.manager = manager
        self.base_uri = "/v3"

    @property
    def token(self):
        return self.manager.token

    @property
    def timeout(self):
        return self.manager.timeout

    def get_uri(self, path):
        res = "%s%s%s" % (self.manager.base_uri, self.base_uri, path)
        self.logger.debug("uri: %s" % res)
        return res

    def format_paginated_query(self, kwargs, params, mappings=None, aliases=None):
        params.extend(["page", "size", "field", "order"])
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
        self.logger.debug("query data: %s" % data)
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

    def http_get(self, uri, **params):
        method = "get"
        header = {"Authorization": "Bearer " + self.token}
        uri = self.get_uri(uri)
        try:
            res = requests.get(uri, headers=header, params=params, timeout=self.timeout, verify=False)
            output = res.json()
            if res.status_code in [400, 403, 404, 405]:
                error = output["message"]
                raise RancherError(error, res.status_code)
            self.logger.debug("Rancher http %s response: %s" % (method, truncate(output)))
            return output
        except ConnectTimeout as ex:
            self.logger.error("Rancher connection timeout: %s" % ex)
            raise RancherError(ex)
        except ConnectionError as ex:
            self.logger.error("Rancher connection error: %s" % ex)
            raise RancherError(ex)
        except Exception as ex:
            self.logger.error("Rancher http %s error: %s" % (method, ex))
            raise RancherError(ex)

    def http_get_provisioning(self, uri, **param):
        saved_base_uri = self.base_uri
        self.base_uri = "/v1"
        output = self.http_get(uri, **param)
        self.base_uri = saved_base_uri
        return output

    def http_list(self, uri, page=1, page_size=20, **params):
        params.update({"page": page, "page_size": page_size, "order_by": "-id"})
        res = self.http_get(uri, **params)
        output = res.get("data")
        return output

    def http_post(self, uri, **data):
        method = "post"
        headers = {
            "Authorization": "Bearer " + self.token,
            "content-type": "application/json",
        }
        uri = self.get_uri(uri)
        try:
            res = requests.post(
                uri,
                headers=headers,
                data=json.dumps(data),
                timeout=self.timeout,
                verify=False,
            )
            if res.status_code in [400, 403, 404, 405, 500]:
                output = res.json()
                error = output.get("message")
                if error is None:
                    error = output
                raise Exception(error)
            elif res.status_code in [409, 422]:
                output = res.json()
                error = "%s: %s" % (output.get("code"), output.get("message"))
                if error is None:
                    error = output
                raise Exception(error)
            else:
                try:
                    output = res.json()
                except:
                    output = res.text
            self.logger.debug("Rancher http %s response: %s" % (method, truncate(output)))
        except ConnectTimeout as ex:
            self.logger.error("Rancher connection timeout: %s" % ex)
            raise RancherError(ex)
        except ConnectionError as ex:
            self.logger.error("Rancher connection error: %s" % ex)
            raise RancherError(ex)
        except Exception as ex:
            self.logger.error("Rancher http %s error: %s" % (method, ex), exc_info=True)
            raise RancherError(ex)
        return output

    def http_post_provisioning(self, uri, **data):
        saved_base_uri = self.base_uri
        self.base_uri = "/v1"
        output = self.http_post(uri, **data)
        self.base_uri = saved_base_uri
        return output

    def http_delete(self, uri, data=None):
        method = "delete"
        headers = {"Authorization": "Bearer " + self.token}
        uri = self.get_uri(uri)
        try:
            res = requests.delete(uri, headers=headers, timeout=self.timeout, verify=False)
            if res.status_code in [400, 403, 404, 405]:
                output = res.json()
                error = output["message"]
                raise Exception(error)
            self.logger.debug("Rancher http %s response: %s" % (method, True))
        except ConnectTimeout as ex:
            self.logger.error("Rancher connection timeout: %s" % ex)
            raise RancherError(ex)
        except ConnectionError as ex:
            self.logger.error("Rancher connection error: %s" % ex)
            raise RancherError(ex)
        except Exception as ex:
            self.logger.error("Rancher http %s error: %s" % (method, ex))
            raise RancherError(ex)


class RancherManager(object):
    def __init__(self, uri=None, proxy=None, timeout=60.0):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        if uri is None:
            raise RancherError("Rancher uri cannot be null")
        self.base_uri = uri
        self.token = None
        self.timeout = timeout

        from .user import RancherUser
        from .role import RancherGlobalRole, RancherTemplateRole
        from .cluster import RancherCluster
        from .project import RancherProject

        # initialize rancher objects
        self.user = RancherUser(self)
        self.role_global = RancherGlobalRole(self)
        self.role_template = RancherTemplateRole(self)
        self.cluster = RancherCluster(self)
        self.project = RancherProject(self)

    def set_timeout(self, timeout):
        self.timeout = timeout

    def authorize(self, user=None, pwd=None, token=None, key=None):
        """Get token

        :param user: user
        :param pwd: password
        :param token: token string
        :param key: [optional] fernet key to decrypt encrypted password
        """
        # check password is encrypted
        if pwd is not None:
            pwd = check_vault(pwd, key)
        # set token
        if token is not None:
            self.token = token
        else:
            try:
                # get login token from identity service
                self.logger.debug("Try to get token for user %s" % user)
                uri = self.base_uri + "/v3-public/localProviders/local?action=login"
                res = requests.post(
                    uri,
                    headers={"content-type": "application/json"},
                    data=json.dumps(
                        {
                            "username": user,
                            "password": pwd,
                            "description": "login-token",
                        }
                    ),
                    timeout=self.timeout,
                    verify=False,
                )
                output = res.json()
                if res.status_code in [400, 401]:
                    error = output["message"]
                    raise RancherError(error, res.status_code)
                self.token = output["token"]
                self.logger.debug("Got token %s for user %s" % (self.token, user))
            except ConnectTimeout as ex:
                self.logger.error("Rancher connection timeout: %s" % ex)
                raise RancherError(ex)
            except ConnectionError as ex:
                self.logger.error("Rancher connection error: %s" % ex)
                raise RancherError(ex)
            except Exception as ex:
                self.logger.error("Rancher token error: %s" % ex, exc_info=True)
                raise RancherError(ex)

    def ping(self):
        """Ping rancher

        :return: True or False
        """
        res = False
        try:
            uri = self.base_uri
            requests.get(
                uri,
                headers={"content-type": "application/json"},
                timeout=self.timeout,
                verify=False,
            )
            res = True
        except ConnectTimeout as ex:
            self.logger.error("Rancher connection timeout: %s" % ex)
        except ConnectionError as ex:
            self.logger.error("Rancher connection error: %s" % ex)
        except Exception as ex:
            self.logger.error("Rancher http %s error: %s" % ("post", False))

        self.logger.debug("Ping server: %s" % res)
        return res

    def version(self):
        """Get server version

        :return: server version
        """
        try:
            header = {
                "Authorization": "Bearer " + self.token,
                "content-type": "application/json",
            }
            uri = self.base_uri + "/v3/settings/server-version"
            res = requests.get(uri, headers=header, timeout=self.timeout, verify=False)
            output = res.json()
            if res.status_code in [400]:
                error = output["message"]
                raise RancherError(error, res.status_code)
            version = output.get("value")
            self.logger.debug("Got version: %s" % version)
            return {"server-version": version}
        except ConnectTimeout as ex:
            self.logger.error("Rancher connection timeout: %s" % ex)
            raise RancherError(ex)
        except ConnectionError as ex:
            self.logger.error("Rancher connection error: %s" % ex)
            raise RancherError(ex)
        except Exception as ex:
            self.logger.error("Get error: %s" % ex)
            raise RancherError(ex)
