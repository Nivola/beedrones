# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte


import json
from logging import getLogger
import requests

from requests.exceptions import ConnectionError, ConnectTimeout
from urllib3 import disable_warnings, exceptions
from beecell.simple import check_vault, truncate, jsonDumps


disable_warnings(exceptions.InsecureRequestWarning)
BEARER = "Bearer "
VEEAM_API_VERSION = "1.0-rev1"
# VEEAM_API_VERSION = "1.1-rev0"


class VeeamError(Exception):
    def __init__(self, value, code=400):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "VeeamError: %s" % self.value

    def __str__(self):
        return "VeeamError: %s" % self.value


class VeeamEntity(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
        self.manager: VeeamManager = manager
        self.next = None

    @property
    def timeout(self):
        return self.manager.timeout

    def has_next(self):
        if self.next is not None:
            return True
        return False

    @property
    def token(self):
        return self.manager.token

    def http_get(self, uri, default_result=[], **params):
        method = "get"
        headers = {
            "Authorization": BEARER + self.token,
            "Content-Type": "application/json",
            "x-api-version": VEEAM_API_VERSION,
        }
        self.logger.debug("veeam headers: %s" % headers)
        self.logger.debug("veeam params: %s" % params)

        uri = self.manager.veeam_base_uri + uri

        try:
            self.logger.debug("veeam http_get uri: %s" % uri)
            res = requests.get(uri, headers=headers, timeout=self.timeout, params=params, verify=False)
            output = res.json()
            if res.status_code in [400, 401, 403, 404, 405, 500]:
                self.logger.error("veeam http %s response: %s" % (method, truncate(output)))
                error = "%s - %s" % (output["errorCode"], output["message"])
                raise Exception(error)
            self.logger.debug("veeam http %s response: %s" % (method, truncate(output)))
        except ConnectTimeout as ex:
            self.logger.error("veeam connection timeout: %s" % ex)
            raise VeeamError(ex)
        except ConnectionError as ex:
            self.logger.error("veeam connection error: %s" % ex)
            raise VeeamError(ex)
        except json.decoder.JSONDecodeError as ex:
            self.logger.error("veeam http %s error: %s - res: %s" % (method, ex, res))
            raise VeeamError(ex)
        except Exception as ex:
            self.logger.error("veeam http %s error: %s" % (method, ex))
            raise VeeamError(ex)

        return output

    def http_list(self, uri, page=1, page_size=10, **params):
        skip: int = (int(page) - 1) * int(page_size)
        params.update({"skip": skip, "limit": page_size})
        res = self.http_get(uri, **params)
        output = res
        return output

    def http_post(self, uri, data={}, files=None):
        method = "post"
        headers = {"Authorization": BEARER + self.token, "x-api-version": VEEAM_API_VERSION}
        if files is None:
            headers["Content-Type"] = "application/json"
        self.logger.debug("veeam headers: %s" % headers)

        uri = self.manager.veeam_base_uri + uri

        try:
            self.logger.debug("veeam http_post uri: %s" % uri)
            self.logger.debug("veeam post data %s" % data)
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
                self.logger.error("veeam http %s response: %s" % (method, truncate(output)))
                error = output["error"] + " - " + output["message"]
                if error is None:
                    error = output
                raise Exception(error)
            else:
                try:
                    output = res.json()
                except:
                    output = res.text
            self.logger.debug("veeam http %s response: %s" % (method, truncate(output, size=4000)))
        except ConnectTimeout as ex:
            self.logger.error("veeam connection timeout: %s" % ex)
            raise VeeamError(ex)
        except ConnectionError as ex:
            self.logger.error("veeam connection error: %s" % ex)
            raise VeeamError(ex)
        except Exception as ex:
            self.logger.error("veeam http %s error: %s" % (method, ex), exc_info=True)
            raise VeeamError(ex)

        return output

    def http_put(self, uri, data={}):
        method = "put"

        headers = {
            "Authorization": BEARER + self.token,
            "Content-Type": "application/json",
            "x-api-version": VEEAM_API_VERSION,
        }
        self.logger.debug("veeam headers: %s" % headers)

        uri = self.manager.veeam_base_uri + uri

        try:
            self.logger.debug("put data %s to veeam" % data)
            res = requests.put(
                uri,
                headers=headers,
                timeout=self.timeout,
                data=jsonDumps(data),
                verify=False,
            )
            if res.status_code in [400, 401, 403, 404, 405, 409]:
                output = res.json()
                self.logger.error("veeam http %s response: %s" % (method, truncate(output)))
                error = output["error"] + " - " + output["message"]
                if error is None:
                    error = output
                raise Exception(error)
            else:
                try:
                    output = res.json()
                except:
                    output = res.text
            self.logger.debug("veeam http %s response: %s" % (method, truncate(output, size=4000)))
        except ConnectTimeout as ex:
            self.logger.error("veeam connection timeout: %s" % ex)
            raise VeeamError(ex)
        except ConnectionError as ex:
            self.logger.error("veeam connection error: %s" % ex)
            raise VeeamError(ex)
        except Exception as ex:
            self.logger.error("veeam http %s error: %s" % (method, ex), exc_info=True)
            raise VeeamError(ex)

        return output

    def http_delete(self, uri, data=None):
        method = "delete"

        headers = {
            "Authorization": BEARER + self.token,
            "Content-Type": "application/json",
            "x-api-version": VEEAM_API_VERSION,
        }
        self.logger.debug("veeam headers: %s" % headers)

        uri = self.manager.veeam_base_uri + uri

        try:
            res = requests.delete(uri, headers=headers, timeout=self.timeout, verify=False)
            if res.status_code in [400, 401, 403, 404, 405]:
                output = res.json()
                error = output["error"]
                raise Exception(error)
            self.logger.debug("veeam http %s response: %s" % (method, True))
        except ConnectTimeout as ex:
            self.logger.error("veeam connection timeout: %s" % ex)
            raise VeeamError(ex)
        except ConnectionError as ex:
            self.logger.error("veeam connection error: %s" % ex)
            raise VeeamError(ex)
        except Exception as ex:
            self.logger.error("veeam http %s error: %s" % (method, ex))
            raise VeeamError(ex)


class VeeamManager(object):
    def __init__(self, uri=None, timeout=60.0):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        self.veeam_base_uri = uri
        self.timeout = timeout

        # self.user = user
        # self.password = passwd

        self.token = None
        self.token_expire = None

        from .job import VeeamJob
        from .backup import VeeamBackup
        from .restore_point import VeeamRestorePoint

        # initialize proxy objects
        self.job = VeeamJob(self)
        self.backup = VeeamBackup(self)
        self.restorepoint = VeeamRestorePoint(self)

    def set_timeout(self, timeout):
        self.timeout = timeout

    def ping(self):
        """Ping veeam

        :return: True or False
        """
        res = False
        try:
            uri = self.veeam_base_uri  # + "api/"
            requests.get(
                uri,
                headers={"content-type": "application/json"},
                timeout=self.timeout,
                verify=False,
            )
            res = True
        except ConnectTimeout as ex:
            self.logger.error("veeam connection timeout: %s" % ex)
        except ConnectionError as ex:
            self.logger.error("veeam connection error: %s" % ex)
        except Exception as ex:
            self.logger.error("veeam http %s error: %s" % ("get", ex))
        self.logger.debug("Ping veeam server: %s" % res)

        return res

    def version(self):
        """Get veeam version

        :return: veeam version
        """
        method = "get"
        try:
            headers = {
                "Authorization": BEARER + self.token,
                "Content-Type": "application/json",
                "x-api-version": VEEAM_API_VERSION,
            }
            self.logger.debug("veeam headers: %s" % headers)

            uri = self.veeam_base_uri + "v1/serverInfo"
            res: requests.models.Response = requests.get(uri, headers=headers, timeout=self.timeout, verify=False)

            self.logger.debug("veeam res.status_code: %s" % res.status_code)
            self.logger.debug("veeam res: %s" % res)

            if res.status_code in [404]:
                return {"version": "unknown - version number only from Veeam Backup & Replication 12.0"}
            else:
                output = res.json()
                self.logger.debug("veeam output: %s" % output)

                buildVersion = output.get("buildVersion", None)
                version = {"version": buildVersion}
                self.logger.debug("Get version: %s" % version)
                return version
        except ConnectTimeout as ex:
            self.logger.error("veeam connection timeout: %s" % ex)
            raise VeeamError(ex)
        except ConnectionError as ex:
            self.logger.error("veeam connection error: %s" % ex)
            raise VeeamError(ex)
        except Exception as ex:
            self.logger.error("get version error: %s" % ex)
            raise VeeamError(ex)

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
                data = {
                    "grant_type": "password",
                    "username": user,
                    "password": pwd,
                    "use_short_term_refresh": "true",
                }
                # get token from identity service
                self.logger.debug("Try to get token for user %s" % user)
                uri = self.veeam_base_uri + "oauth2/token"

                res = requests.post(
                    uri,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "x-api-version": VEEAM_API_VERSION,
                    },
                    data=data,
                    timeout=self.timeout,
                    verify=False,
                )

                self.logger.debug("res: %s" % res)
                try:
                    output = res.json()
                except:
                    raise Exception(f"code: {res.status_code} - res: {res}")

                if res.status_code in [400, 401]:
                    # error = output["detail"]
                    raise Exception(output)

                self.token = output["access_token"]
                self.token_expire = output["expires_in"]
                self.logger.debug("Get token %s for user %s" % (self.token, user))
            except ConnectTimeout as ex:
                self.logger.error("awx connection timeout: %s" % ex)
                raise VeeamError(ex)
            except ConnectionError as ex:
                self.logger.error("awx connection error: %s" % ex)
                raise VeeamError(ex)
            except Exception as ex:
                self.logger.error("get token error: %s" % ex)
                raise VeeamError(ex)

    def get_token(self):
        return {"token": self.token, "expires": self.token_expire}
