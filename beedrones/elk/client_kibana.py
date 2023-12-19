# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import jsonDumps

import requests
import json
from logging import getLogger

from beecell.simple import check_vault, truncate
from requests.exceptions import ConnectionError, ConnectTimeout
from urllib3 import disable_warnings, exceptions
import base64


disable_warnings(exceptions.InsecureRequestWarning)


class KibanaError(Exception):
    def __init__(self, value, code=400):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "KibanaError: %s" % self.value

    def __str__(self):
        return "KibanaError: %s" % self.value


class KibanaEntity(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
        self.manager: KibanaManager = manager
        self.next = None

    @property
    def timeout(self):
        return self.manager.timeout

    def has_next(self):
        if self.next is not None:
            return True
        return False

    def http_get(self, uri, default_result=[], **params):
        method = "get"

        headers = {"Content-Type": "application/json", "kbn-xsrf": "true"}

        user_password_bytes = str.encode(self.manager.user + ":" + self.manager.password)
        encode_bytes = base64.b64encode(user_password_bytes)
        encode_str = encode_bytes.decode("ascii")
        headers["Authorization"] = "Basic %s" % encode_str
        self.logger.debug("kibana headers: %s" % headers)

        uri = self.manager.kibana_base_uri + uri

        try:
            self.logger.debug("kibana http_get uri: %s" % uri)
            res = requests.get(uri, headers=headers, timeout=self.timeout, params=params, verify=False)
            output = res.json()
            if res.status_code in [400, 401, 403, 404, 405]:
                self.logger.error("kibana http %s response: %s" % (method, truncate(output)))
                error = output["error"] + " - " + output["message"]
                raise Exception(error)
            self.logger.debug("kibana http %s response: %s" % (method, truncate(output)))
        except ConnectTimeout as ex:
            self.logger.error("kibana connection timeout: %s" % ex)
            raise KibanaError(ex)
        except ConnectionError as ex:
            self.logger.error("kibana connection error: %s" % ex)
            raise KibanaError(ex)
        except Exception as ex:
            self.logger.error("kibana http %s error: %s" % (method, ex))
            raise KibanaError(ex)

        return output

    def http_list(self, uri, page=1, page_size=20, **params):
        # params.update({'page': page, 'page_size': page_size, 'order_by': '-id'})
        res = self.http_get(uri, **params)
        output = res
        return output

    def http_post(self, uri, data={}, files=None):
        method = "post"

        headers = {"kbn-xsrf": "true"}
        if files is None:
            headers["Content-Type"] = "application/json"

        user_password_bytes = str.encode(self.manager.user + ":" + self.manager.password)
        encode_bytes = base64.b64encode(user_password_bytes)
        encode_str = encode_bytes.decode("ascii")
        headers["Authorization"] = "Basic %s" % encode_str
        self.logger.debug("kibana headers: %s" % headers)

        uri = self.manager.kibana_base_uri + uri

        try:
            self.logger.debug("kibana http_post uri: %s" % uri)
            self.logger.debug("kibana post data %s" % data)
            if files is None:
                res = requests.post(
                    uri,
                    headers=headers,
                    timeout=self.timeout,
                    data=jsonDumps(data),
                    verify=False,
                )
            else:
                res = requests.post(
                    uri,
                    headers=headers,
                    timeout=self.timeout,
                    verify=False,
                    files=files,
                )

            if res.status_code in [400, 401, 403, 404, 405, 409]:
                output = res.json()
                self.logger.error("kibana http %s response: %s" % (method, truncate(output)))
                error = output["error"] + " - " + output["message"]
                if error is None:
                    error = output
                raise Exception(error)
            else:
                try:
                    output = res.json()
                except:
                    output = res.text
            self.logger.debug("kibana http %s response: %s" % (method, truncate(output, size=4000)))
        except ConnectTimeout as ex:
            self.logger.error("kibana connection timeout: %s" % ex)
            raise KibanaError(ex)
        except ConnectionError as ex:
            self.logger.error("kibana connection error: %s" % ex)
            raise KibanaError(ex)
        except Exception as ex:
            self.logger.error("kibana http %s error: %s" % (method, ex), exc_info=True)
            raise KibanaError(ex)

        return output

    def http_put(self, uri, data={}):
        method = "put"

        headers = {"Content-Type": "application/json", "kbn-xsrf": "true"}

        user_password_bytes = str.encode(self.manager.user + ":" + self.manager.password)
        encode_bytes = base64.b64encode(user_password_bytes)
        encode_str = encode_bytes.decode("ascii")
        headers["Authorization"] = "Basic %s" % encode_str
        self.logger.debug("kibana headers: %s" % headers)

        uri = self.manager.kibana_base_uri + uri

        try:
            self.logger.debug("pou data %s to kibana" % data)
            res = requests.put(
                uri,
                headers=headers,
                timeout=self.timeout,
                data=jsonDumps(data),
                verify=False,
            )
            if res.status_code in [400, 401, 403, 404, 405, 409]:
                output = res.json()
                self.logger.error("kibana http %s response: %s" % (method, truncate(output)))
                error = output["error"] + " - " + output["message"]
                if error is None:
                    error = output
                raise Exception(error)
            else:
                try:
                    output = res.json()
                except:
                    output = res.text
            self.logger.debug("kibana http %s response: %s" % (method, truncate(output, size=4000)))
        except ConnectTimeout as ex:
            self.logger.error("kibana connection timeout: %s" % ex)
            raise KibanaError(ex)
        except ConnectionError as ex:
            self.logger.error("kibana connection error: %s" % ex)
            raise KibanaError(ex)
        except Exception as ex:
            self.logger.error("kibana http %s error: %s" % (method, ex), exc_info=True)
            raise KibanaError(ex)

        return output

    def http_delete(self, uri, data=None):
        method = "delete"

        headers = {"Content-Type": "application/json", "kbn-xsrf": "true"}

        user_password_bytes = str.encode(self.manager.user + ":" + self.manager.password)
        encode_bytes = base64.b64encode(user_password_bytes)
        encode_str = encode_bytes.decode("ascii")
        headers["Authorization"] = "Basic %s" % encode_str
        self.logger.debug("kibana headers: %s" % headers)

        uri = self.manager.kibana_base_uri + uri

        try:
            res = requests.delete(uri, headers=headers, timeout=self.timeout, verify=False)
            if res.status_code in [400, 401, 403, 404, 405]:
                output = res.json()
                error = output["error"]
                raise Exception(error)
            self.logger.debug("kibana http %s response: %s" % (method, True))
        except ConnectTimeout as ex:
            self.logger.error("kibana connection timeout: %s" % ex)
            raise KibanaError(ex)
        except ConnectionError as ex:
            self.logger.error("kibana connection error: %s" % ex)
            raise KibanaError(ex)
        except Exception as ex:
            self.logger.error("kibana http %s error: %s" % (method, ex))
            raise KibanaError(ex)


class KibanaManager(object):
    def __init__(self, uri=None, user=None, passwd=None, proxy=None, timeout=60.0):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        self.kibana_base_uri = uri
        self.user = user
        self.password = passwd
        self.timeout = timeout

        from .space import KibanaSpace
        from .role import KibanaRole

        # initialize proxy objects
        self.space = KibanaSpace(self)
        self.role = KibanaRole(self)

    def set_timeout(self, timeout):
        self.timeout = timeout

    def ping(self):
        """Ping kibana

        :return: True or False
        """
        res = False
        try:
            uri = self.kibana_base_uri + "api/"
            requests.get(
                uri,
                headers={"content-type": "application/json"},
                timeout=self.timeout,
                verify=False,
            )
            res = True
        except ConnectTimeout as ex:
            self.logger.error("kibana connection timeout: %s" % ex)
        except ConnectionError as ex:
            self.logger.error("kibana connection error: %s" % ex)
        except Exception as ex:
            self.logger.error("kibana http %s error: %s" % ("get", ex))
        self.logger.debug("Ping kibana server: %s" % res)

        return res

    def version(self):
        """Get kibana version

        :return: kibana version
        """
        method = "get"
        try:
            headers = {"Content-Type": "application/json"}
            user_password_bytes = str.encode(self.user + ":" + self.password)
            encode_bytes = base64.b64encode(user_password_bytes)
            encode_str = encode_bytes.decode("ascii")
            headers["Authorization"] = "Basic %s" % encode_str
            self.logger.debug("kibana headers: %s" % headers)

            uri = self.kibana_base_uri + "api/status"
            res = requests.get(uri, headers=headers, timeout=self.timeout, verify=False)
            self.logger.debug("kibana res: %s" % res)
            output = res.json()

            if res.status_code in [400, 401, 403, 404, 405]:
                self.logger.error("kibana http %s response: %s" % (method, truncate(output)))
                error = output["error"] + " - " + output["message"]
                raise Exception(error)

            version_obj = output.get("version", None)
            number = version_obj["number"]
            version = {"version": number}
            self.logger.debug("Get version: %s" % version)
            return version
        except ConnectTimeout as ex:
            self.logger.error("kibana connection timeout: %s" % ex)
            raise KibanaError(ex)
        except ConnectionError as ex:
            self.logger.error("kibana connection error: %s" % ex)
            raise KibanaError(ex)
        except Exception as ex:
            self.logger.error("get version error: %s" % ex)
            raise KibanaError(ex)
