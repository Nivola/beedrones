# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import jsonDumps

import ujson as json
from logging import getLogger
from time import time
import ssl
import re
from beecell.simple import truncate, check_vault
from six.moves.urllib.parse import urlparse
from six.moves import http_client
from socket import timeout as SocketTimeout


class OpenstackError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return str(self.value)

    def __str__(self):
        return self.value


class OpenstackNotFound(OpenstackError):
    def __init__(self, value):
        OpenstackError.__init__(self, "Openstack entity (%s) was not found" % value, 404)


def setup_client(f):
    def wrapper(*args, **kvargs):
        args[0].setup()
        return f(*args, **kvargs)

    return wrapper


class OpenstackClient(object):
    """
    :param uri: Ex. http://0.0.0.0:5000/v3
    :param proxy: proxy server. Ex. ('proxy.it', 3128) [default=None]
    """

    def __init__(self, uri, proxy=None, timeout=30):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        if uri is not None:
            obj = urlparse(uri)
            self.proto = obj.scheme
            self.path = obj.path
            self.host, self.port = obj.netloc.split(":")
            self.port = int(self.port)
        else:
            self.proto = "http"
            self.path = "/"
            self.host = "localhost"
            self.port = 80

        self.proxy = proxy
        self.timeout = timeout

        self.microversion = None

    def call(
        self,
        path,
        method,
        data="",
        headers=None,
        timeout=None,
        token=None,
        base_path=None,
        resolve_conflicts=None,
        content_type="application/json",
    ):
        """Http client. Usage:

        res = http_client2('https', '/api', 'POST', port=443, data='', headers={})

        :param path: Request path. Ex. /api/
        :param method: Request method. Ex. GET, POST, PUT, DELETE
        :param headers: Request headers. [default={}]. Ex.
            {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        :param data: Request data. [default={}]. Ex.
            {'@number': 12524, '@type': 'issue', '@action': 'show'}
        :param timeout: Request timeout. [optional]
        :param token: Openstack authorization token [optional]
        :param base_path: base path that replace defualt path set initially
        :param resolve_conflicts: [optional] set this function to make some action when 409 error is returned.
            def resolve_conflicts(path, method, data='', headers=None, timeout=30, token=None, base_path=None,
                                  res=None):
                ...
                return res, res_headers, response.status
        :param content_type: request content type [default=application/json]
        :raise OpenstackError:
        :raise OpenstackNotFound: If request return 404
        """
        start = time()

        # set timeout
        if timeout is None:
            timeout = self.timeout

        if base_path is not None:
            path = base_path + path
        else:
            path = self.path + path

        http_headers = {"Content-Type": content_type}
        if token is not None:
            http_headers["X-Auth-Token"] = token
        if self.microversion is not None:
            http_headers.update(self.microversion)
        if headers is not None:
            http_headers.update(headers)

        self.logger.info(
            "Send http %s api request to %s://%s:%s%s with token %s"
            % (method, self.proto, self.host, self.port, path, token)
        )

        if isinstance(data, dict):
            data = jsonDumps(data)
        if isinstance(data, str):
            # todo: manage data as dict in all the client before log and obscure only password
            if data.lower().find("password") < 0:
                self.logger.debug("Send [headers=%s] [data=%s]" % (http_headers, data))
            else:
                self.logger.debug("Send [headers=%s] [data=%s]" % (http_headers, "xxxxxxx"))

        try:
            _host = self.host
            _port = self.port
            _headers = http_headers
            if self.proxy is not None:
                _host = self.proxy[0]
                _port = self.proxy[1]
                _headers = {}
                path = "%s://%s:%s%s" % (self.proto, self.host, self.port, path)

            if self.proto == "http":
                conn = http_client.HTTPConnection(_host, _port, timeout=timeout)
            else:
                ssl._create_default_https_context = ssl._create_unverified_context
                conn = http_client.HTTPSConnection(_host, _port, timeout=timeout)

            if self.proxy is not None:
                conn.set_tunnel(self.host, port=self.port, headers=headers)
                self.logger.debug("set proxy %s" % self.proxy)
                headers = None

            conn.request(method, path, data, _headers)
            response = conn.getresponse()
            content_type = response.getheader("content-type")
            self.logger.info("Response status: %s %s" % (response.status, response.reason))
        except SocketTimeout as ex:
            self.logger.error("timeout")
            raise OpenstackError("timeout after %ss" % timeout, 400)
        except http_client.RemoteDisconnected:
            self.logger.error("Remote end closed connection without response")
            raise OpenstackError("Remote end closed connection without response", 400)
        except Exception as ex:
            self.logger.error(str(ex))
            raise OpenstackError(str(ex), 400)

        # read response
        try:
            res = response.read()
            res_headers = response.getheaders()
            if content_type == "application/octet-stream":
                self.logger.debug("Response [content-type=%s] [headers=%s]" % (content_type, truncate(res_headers)))
            else:
                res1 = res
                self.logger.debug(
                    "Response [content-type=%s] [headers=%s] [data=%s]"
                    % (content_type, truncate(res_headers), truncate(res1))
                )

            if content_type is not None and content_type.find("application/json") >= 0:
                try:
                    res = json.loads(res)
                except Exception as ex:
                    self.logger.warning(ex)
            conn.close()
            elapsed = time() - start
            self.logger.info("Response elapsed: %s" % elapsed)
        except Exception as ex:
            self.logger.error(ex)
            raise OpenstackError(ex.message, 400)

        # get error messages
        # self.logger.debug("+++++ AAA - response.status: %s" % response.status)
        if response.status in [400, 401, 403, 404, 405, 408, 409, 413, 415, 500, 503]:
            try:
                self.logger.debug("+++++ AAA - type str: %s" % type(res))
                if isinstance(res, bytes):
                    res = res.decode()
                elif not isinstance(res, str):
                    excpt = None
                    res_keys = res.keys()
                    if "error" in res_keys:
                        excpt = "error"
                    elif "Error" in res_keys:
                        excpt = "Error"
                    elif "NeutronError" in res_keys:
                        excpt = "NeutronError"
                    elif "badRequest" in res_keys:
                        excpt = "badRequest"
                    elif "conflictingRequest" in res_keys:
                        excpt = "conflictingRequest"
                    elif "Forbidden" in res_keys:
                        excpt = "Forbidden"
                    elif "forbidden" in res_keys:
                        excpt = "forbidden"
                    elif "itemNotFound" in res_keys:
                        excpt = "itemNotFound"
                    elif len(res_keys) > 0:
                        excpt = res_keys[0]

                    if excpt is not None:
                        res = "%s - %s" % (excpt, res[excpt]["message"])
            except Exception as ex_status:
                self.logger.error("+++++ AAA - ex_status: %s" % ex_status)

            self.logger.error("Response [content-type=%s] [data=%s]" % (content_type, truncate(res)))

        # evaluate response status
        status = response.status

        # BAD_REQUEST     400     HTTP/1.1, RFC 2616, Section 10.4.1
        if status == 400:
            raise OpenstackError(f"Bad Request {res}", 400)

        # UNAUTHORIZED           401     HTTP/1.1, RFC 2616, Section 10.4.2
        elif status == 401:
            raise OpenstackError("Unauthorized%s" % res, 401)

        # PAYMENT_REQUIRED       402     HTTP/1.1, RFC 2616, Section 10.4.3

        # FORBIDDEN              403     HTTP/1.1, RFC 2616, Section 10.4.4
        elif status == 403:
            raise OpenstackError("Forbidden%s" % res, 403)

        # NOT_FOUND              404     HTTP/1.1, RFC 2616, Section 10.4.5
        elif status == 404:
            if res == "":
                raise OpenstackNotFound(path)
            else:
                raise OpenstackError(res, 404)

        # METHOD_NOT_ALLOWED     405     HTTP/1.1, RFC 2616, Section 10.4.6
        elif status == 405:
            raise OpenstackError("Method Not Allowed%s" % res, 405)
        # NOT_ACCEPTABLE         406     HTTP/1.1, RFC 2616, Section 10.4.7

        # PROXY_AUTHENTICATION_REQUIRED     407     HTTP/1.1, RFC 2616, Section 10.4.8

        # REQUEST_TIMEOUT        408
        elif status == 408:
            raise OpenstackError("Request timeout%s" % res, 408)

        # CONFLICT               409
        elif status == 409:
            if resolve_conflicts is not None:
                res, res_headers, status = resolve_conflicts(res)
                return res, res_headers, status
            else:
                raise OpenstackError("Conflict%s" % res, 409)

        # Request Entity Too Large          413
        elif status == 413:
            raise OpenstackError("Request Entity Too Large%s" % res, 413)

        # Unsupported Media Type            415
        elif status == 415:
            raise OpenstackError("Unsupported Media Type%s" % res, 415)

        # INTERNAL SERVER ERROR  500
        elif status == 500:
            raise OpenstackError("Server error%s" % res, 500)

        # Service Unavailable  503
        elif status == 503:
            raise OpenstackError("Service Unavailable%s" % res, 503)

        # OK                     200    HTTP/1.1, RFC 2616, Section 10.2.1
        # CREATED                201    HTTP/1.1, RFC 2616, Section 10.2.2
        # ACCEPTED               202    HTTP/1.1, RFC 2616, Section 10.2.3
        # NON_AUTHORITATIVE_INFORMATION    203    HTTP/1.1, RFC 2616, Section 10.2.4
        # NO_CONTENT             204    HTTP/1.1, RFC 2616, Section 10.2.5
        # RESET_CONTENT          205    HTTP/1.1, RFC 2616, Section 10.2.6
        # PARTIAL_CONTENT        206    HTTP/1.1, RFC 2616, Section 10.2.7
        # MULTI_STATUS           207    WEBDAV RFC 2518, Section 10.2
        elif re.match("20[0-9]+", str(status)) or re.match("300", str(status)):
            return res, res_headers, status


class OpenstackObject(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        self.manager = manager
        self.uri = self.manager.uri
        self.client = None

    def setup(self):
        self.uri = "http://localhost"
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)

    def set_nova_microversion(self, version):
        """Set nova api microversion

        :param version: microversion to set
        """
        self.client.microversion = {"X-Openstack-Nova-Api-Version": version}

    def set_cinder_microversion(self, version):
        """Set cinder api microversion

        :param version: microversion to set
        """
        self.client.microversion = {"OpenStack-API-Version": "volume %s" % version}

    def set_manila_microversion(self, version):
        """Set manila api microversion

        :param version: microversion to set
        """
        self.client.microversion = {"X-OpenStack-Manila-API-Version": version}

    def is_token_valid(self):
        """Check if token expired"""
        return self.manager.identity.validate_token(self.manager.identity.token)


class OpenstackManager(object):
    """Openstack platform manager

    :param uri: connection uri
    :param proxy: http proxy [optional]
    :param default_region: default region [optional]
    """

    def __init__(self, uri=None, proxy=None, default_region=None, timeout=30):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        # identity service uri
        self.uri = uri
        # http(s) proxy
        self.proxy = proxy
        # default_region
        self.region = default_region

        # connection timeout
        self.timeout = timeout

        # openstack proxy objects
        self.identity = OpenstackIdentity(self)
        self.system = None
        self.keypair = None
        self.server = None
        self.server_group = None
        self.volume = None
        self.network = None
        self.image = None
        self.flavor = None
        self.project = None
        self.domain = None
        self.heat = None
        self.manila = None
        self.aodh = None
        self.glance = None
        self.gnocchi = None
        self.masakari = None
        self.aggregate = None

        # openstack services endpoint
        self.endpoints = None

        self.__after_init()

    def __repr__(self):
        return "<OpenstackManager id=%s>" % id(self)

    def __after_init(self):
        # import external classes
        from beedrones.openstack.system import OpenstackSystem
        from beedrones.openstack.heat import OpenstackHeat
        from beedrones.openstack.swift import OpenstackSwift
        from beedrones.openstack.manila import OpenstackManila
        from beedrones.openstack.aodh import OpenstackAodh
        from beedrones.openstack.glance import OpenstackGlance
        from beedrones.openstack.gnocchi import OpenstackGnocchi
        from beedrones.openstack.masakari import OpenstackMasakari
        from beedrones.openstack.project import OpenstackProject, OpenstackDomain
        from beedrones.openstack.volume import OpenstackVolume, OpenstackVolumeV3
        from beedrones.openstack.server import (
            OpenstackServer,
            OpenstackKeyPair,
            OpenstackserverGroup,
        )
        from beedrones.openstack.flavor import OpenstackFlavor
        from beedrones.openstack.image import OpenstackImage
        from beedrones.openstack.network import OpenstackNetwork
        from beedrones.openstack.aggragate import OpenstackAggregate

        # initialize proxy objects
        self.system = OpenstackSystem(self)
        self.project = OpenstackProject(self)
        self.domain = OpenstackDomain(self)
        self.keypair = OpenstackKeyPair(self)
        self.server = OpenstackServer(self)
        self.server_group = OpenstackserverGroup(self)
        self.volume = OpenstackVolume(self)
        self.volume_v3 = OpenstackVolumeV3(self)
        self.network = OpenstackNetwork(self)
        self.image = OpenstackImage(self)
        self.flavor = OpenstackFlavor(self)
        self.heat = OpenstackHeat(self)
        self.swift = OpenstackSwift(self)
        self.manila = OpenstackManila(self)
        self.aodh = OpenstackAodh(self)
        self.glance = OpenstackGlance(self)
        self.gnocchi = OpenstackGnocchi(self)
        self.aggregate = OpenstackAggregate(self)
        self.masakari = OpenstackMasakari(self)

    def set_region(self, region):
        self.region = region

    def authorize(
        self,
        user=None,
        pwd=None,
        project=None,
        domain=None,
        version="v3",
        token=None,
        catalog=None,
        key=None,
        project_id=None,
    ):
        """Get token

        :param user: user
        :param pwd: password
        :param project: project
        :param domain: domain
        :param version: keystone api version
        :param token: existing token
        :param catalog: endpoints catalog
        :param key: key used to decrypt data
        :param project_id: project id
        :param key: [optional] fernet key used to decrypt encrypted password
        """
        # check password is encrypted
        if pwd is not None:
            pwd = check_vault(pwd, key)

        # set token
        if token is not None:
            self.identity.set_token(token)
            self.identity.set_catalog(catalog)
        else:
            # get token from identity service
            self.logger.debug(
                "+++++ Get token for user: %s, project: %s, domain: %s, version: %s" % (user, project, domain, version)
            )
            if version == "v3":
                self.identity.get_token(user, pwd, project, domain, project_id=project_id)
            elif version == "v2":
                self.identity.get_token_v2(user, pwd, project)

        # self.system = None
        # self.keypair = None
        # self.server = None
        # self.volume = None
        # self.network = None
        # self.image = None
        # self.flavor = None
        # self.project = None
        # self.domain = None
        # self.heat.setup()
        # self.manila = None
        # self.aodh = None
        # self.glance = None
        # self.gnocchi = None

    def ping(self):
        """Ping openstack

        :return: True if ping ok
        """
        res = self.identity.ping()
        self.logger.info("ping opensatck: %s" % res)
        return res

    def version(self):
        """Get openstack version

        :return: openstack version
        """
        return self.system.version()

    def endpoint(self, service, interface="public"):
        """
        :param service: service name
        :param interface: openstack inerface. Ex. admin, internal, public [default=public]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        # get service endpoints
        endpoints = self.identity.catalog.get(service, {}).get("endpoints", [])
        for endpoint in endpoints:
            if endpoint["region_id"] == self.region and endpoint["interface"] == interface:
                uri = endpoint["url"].rstrip("/")
                uri_parsed = urlparse(uri)
                if service == "keystone" and uri_parsed.path.find("/v3") == -1:
                    uri += "/v3"
                return uri
        raise OpenstackError("Service %s endpoint was not found" % service)

    def get_token(self):
        return self.identity.get_active_token()

    def get_catalog(self):
        return self.identity.catalog

    def validate_token(self, token):
        return self.identity.validate_token(token)


class OpenstackIdentity(object):
    """ """

    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        self.manager = manager
        self.client = OpenstackClient(manager.uri, manager.proxy, timeout=manager.timeout)

        self.token = None
        self.token_expire = None
        # openstack services
        self.catalog = {}

        # openstack identity proxy objects
        self.role = OpenstackIdentityRole(manager)
        self.user = OpenstackIdentityUser(manager)

    def ping(self):
        """ """
        try:
            self.api()
            return True
        except:
            return False

    def api(self):
        """Get identity api versions.

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        res = self.client.call("/", "GET", data="")
        self.logger.debug("Get openstack identity api versions: %s" % truncate(res[0]))
        return res[0]

    def get_active_token(self):
        return {"token": self.token, "expires_at": self.token_expire}

    def get_token(self, user, pwd, project_name, domain, project_id=None):
        """Get token for api v3

        :param user: user
        :param pwd: user password
        :param project_name: project name
        :param domain: domain
        :param project_id: project id [optional]
        :return: token
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        scope = "project"
        credentials = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": user,
                            "domain": {"id": domain},
                            "password": pwd,
                        }
                    },
                },
                "scope": None,
            }
        }
        if scope == "project":
            if project_id is not None:
                credentials["auth"]["scope"] = {"project": {"id": project_id, "domain": {"name": domain}}}
            else:
                credentials["auth"]["scope"] = {"project": {"name": project_name, "domain": {"name": domain}}}
        elif scope == "domain":
            credentials["auth"]["scope"] = {"domain": {"name": domain}}

        data = jsonDumps(credentials)
        self.logger.debug(
            "+++++ Get authorization token v3 - data: %s - project_name: %s - project_id: %s"
            % (data, project_name, project_id)
        )
        res, headers, status = self.client.call("/auth/tokens", "POST", data=data)

        # get token
        self.token = [h[1] for h in headers if h[0].lower() == "x-subject-token"][0]
        self.token_expire = res["token"]["expires_at"]

        # openstack service catalog
        self._parse_catalog(res["token"]["catalog"])

        self.logger.debug(
            "+++++ Get authorization token v3: %s - token_expire: %s - project_name: %s - project_id: %s"
            % (self.token, self.token_expire, project_name, project_id)
        )

        return {"token": self.token, "expires_at": self.token_expire}

    def get_token_v2(self, user, pwd, project):
        """Get token for api v2

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        credentials = {
            "auth": {
                "tenantName": project,
                "passwordCredentials": {"username": user, "password": pwd},
            }
        }

        data = jsonDumps(credentials)
        path = self.manager.uri
        redux_uri = path.rstrip("v3") + "v2.0"

        res, headers, status = self.client.call("/tokens", "POST", data=data, base_path=redux_uri)

        # get token
        self.token = res["access"]["token"]["id"]
        self.token_expire = res["access"]["token"]["expires"]

        # openstack service catalog
        self._parse_catalog_v2(res["access"]["serviceCatalog"])

        self.logger.debug("++++ Get authorization token v2: %s - token_expire: %s" % (self.token, self.token_expire))

        return {"token": self.token, "expires_at": self.token_expire}

    def set_token(self, token):
        """Set token

        :param token: {'token':.., 'expires_at':..}

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        self.token = token["token"]
        self.token_expire = token["expires_at"]

    def set_catalog(self, catalog):
        """Set catalog"""
        self.catalog = catalog

    def _parse_catalog(self, catalog):
        """ """
        for item in catalog:
            name = item["name"]
            self.catalog[name] = {
                "name": name,
                "type": item["type"],
                "id": item["id"],
                "endpoints": item["endpoints"],
            }
            # replace endpoint uri ip with keystone uri ip. Use when you want
            # to connect with native controller ip instead of controllers vip
            if name not in ["TrilioVaultWLM"]:
                for endpoint in item["endpoints"]:
                    url = endpoint["url"].split("//")
                    url2 = url[1].split(":")
                    endpoint["url"] = "%s//%s:%s" % (url[0], self.client.host, url2[1])
        self.logger.debug("Parse openstack service catalog: %s" % truncate(self.catalog))

    def _parse_catalog_v2(self, catalog):
        """ """
        for item in catalog:
            self.catalog[item["name"]] = {
                "name": item["name"],
                "type": item["type"],
                "endpoints": [],
            }
            endpoint = item["endpoints"][0]
            data = {
                "region_id": endpoint["region"],
                "url": endpoint["publicURL"],
                "region": endpoint["region"],
                "interface": "public",
                "id": endpoint["id"],
            }
            self.catalog[item["name"]]["endpoints"].append(data)

            data = {
                "region_id": endpoint["region"],
                "url": endpoint["adminURL"],
                "region": endpoint["region"],
                "interface": "admin",
                "id": endpoint["id"],
            }
            self.catalog[item["name"]]["endpoints"].append(data)

            data = {
                "region_id": endpoint["region"],
                "url": endpoint["internalURL"],
                "region": endpoint["region"],
                "interface": "internal",
                "id": endpoint["id"],
            }
            self.catalog[item["name"]]["endpoints"].append(data)

        self.logger.debug("Parse openstack service catalog: %s" % truncate(self.catalog))

    def validate_token(self, token):
        """
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        try:
            res = self.client.call(
                "/auth/tokens",
                "GET",
                data="",
                headers={"X-Subject-Token": token},
                token=token,
            )
            # self.logger.debug("Validate authorization token: %s - res: %s" % (token, res))
            res_token = res[0]["token"]
            expires_at = res_token["expires_at"]
            self.logger.debug("Validate authorization token: %s - expires_at: %s (UTC)" % (token, expires_at))
        except Exception as ex:
            self.logger.error(ex, exc_info=True)
            return False
        return True

    def release_token(self, token=None):
        """
        :param token: token to release. If not specified release inner token [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if token is None:
            token = self.token
            self.token = None

        self.client.call(
            "/auth/tokens",
            "DELETE",
            data="",
            headers={"X-Subject-Token": token},
            token=token,
        )
        self.logger.debug("Release authorization token: %s" % token)
        return True

    def get_services(self):
        """
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        res = self.client.call("/services", "GET", data="", token=self.token)
        self.logger.debug("Get openstack services: %s" % truncate(res[0]))
        return res[0]["services"]

    def get_endpoints(self):
        """
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        res = self.client.call("/endpoints", "GET", data="", token=self.token)
        self.logger.debug("Get openstack endpoints: %s" % truncate(res[0]))
        return res[0]["endpoints"]

    #
    # credentials
    #
    def get_credentials(self, oid=None):
        """In exchange for a set of authentication credentials that the user
        submits, the Identity service generates and returns a token. A token
        represents the authenticated identity of a user and, optionally, grants
        authorization on a specific project or domain.

        :param oid: credential id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/credentials"
        key = "credentials"
        if oid is not None:
            path = "%s/%s" % (path, oid)
            key = "credential"
        res = self.client.call(path, "GET", data="", token=self.token)
        self.logger.debug("Get openstack credentials: %s" % truncate(res[0]))
        try:
            return res[0][key]
        except:
            raise OpenstackError("No credentials found")

    #
    # groups
    #
    def get_groups(self, oid=None):
        """

        :param oid: group id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/groups"
        key = "groups"
        if oid is not None:
            path = "%s/%s" % (path, oid)
            key = "group"
        res = self.client.call(path, "GET", data="", token=self.token)
        self.logger.debug("Get openstack groups: %s" % truncate(res[0]))
        try:
            return res[0][key]
        except:
            raise OpenstackError("No groups found")

    #
    # policies
    #
    def get_policies(self, oid=None):
        """

        :param oid: policy id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/policies"
        key = "policies"
        if oid is not None:
            path = "%s/%s" % (path, oid)
            key = "policy"
        res = self.client.call(path, "GET", data="", token=self.token)
        self.logger.debug("Get openstack policies: %s" % truncate(res[0]))
        try:
            return res[0][key]
        except Exception:
            raise OpenstackError("No policies found")

    #
    # regions
    #
    def get_regions(self, oid=None):
        """

        :param oid: region id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/regions"
        key = "regions"
        if oid is not None:
            path = "%s/%s" % (path, oid)
            key = "region"
        res = self.client.call(path, "GET", data="", token=self.token)
        self.logger.debug("Get openstack regions: %s" % truncate(res[0]))
        try:
            return res[0][key]
        except Exception:
            raise OpenstackError("No regions found")

    #
    # tenants
    #
    def get_tenants(self):
        """
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        res = self.client.call("/tenants", "GET", data="", token=self.token)
        self.logger.debug("Get openstack tenants: %s" % truncate(res[0]))
        return res[0]["tenants"]

    #
    # projects
    #
    def get_projects(self):  # by miko
        """
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        res = self.client.call("/projects", "GET", data="", token=self.token)
        self.logger.debug("Get openstack projects: %s" % truncate(res[0]))
        return res[0]


class OpenstackIdentityRole(OpenstackObject):
    """ """

    def __init__(self, manager):
        OpenstackObject.__init__(self, manager)

    def setup(self):
        self.uri = self.manager.endpoint("keystone")
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)

    @setup_client
    def list(self, detail=False, name=None):
        """
        :param name:
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/roles?"
        if detail is True:
            path = "/roles/detail?"
        if name is not None:
            path = "%sname=%s" % (path, name)

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack roles: %s" % truncate(res[0]))
        return res[0]["roles"]

    @setup_client
    def get(self, oid):
        """
        :param oid: role id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/roles/%s" % oid
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack role: %s" % truncate(res[0]))
        return res[0]["role"]

    @setup_client
    def create(
        self,
    ):
        """TODO
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {}

        path = "/roles"
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Create openstack role: %s" % truncate(res[0]))
        return res[0]["server"]

    @setup_client
    def update(self, oid):
        """TODO
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/roles/%s" % oid
        res = self.client.call(path, "PUT", data="", token=self.manager.identity.token)
        self.logger.debug("Update openstack role: %s" % truncate(res[0]))
        return res[0]["server"]

    @setup_client
    def delete(self, oid):
        """TODO
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/roles/%s" % oid
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack role: %s" % truncate(res[0]))
        return res[0]["server"]

    @setup_client
    def assignments(self, role=None, group=None, user=None, project=None, domain=None):
        """
        :param role:
        :param group:
        :param user:
        :param project:
        :param domain:
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/role_assignments?"
        if role is not None:
            path = "%srole.id=%s" % (path, role)
        elif group is not None:
            path = "%sgroup.id=%s" % (path, group)
        elif user is not None:
            path = "%suser.id=%s" % (path, user)

        if project is not None:
            path = "%s&scope.project.id=%s&include_subtree=true&effective" % (
                path,
                project,
            )
        elif domain is not None:
            path = "%s&scope.domain.id=%s#effective" % (path, domain)

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack role assignments: %s" % truncate(res[0]))
        return res[0]["role_assignments"]


class OpenstackIdentityUser(OpenstackObject):
    """ """

    def __init__(self, manager):
        OpenstackObject.__init__(self, manager)

    def setup(self):
        self.uri = self.manager.endpoint("keystone")
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)

    @setup_client
    def list(self, detail=False, name=None, domain=None):
        """
        :param name:
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/users?"
        if name is not None:
            path = "%sname=%s" % (path, name)
        if domain is not None:
            path = "%sdomain=%s" % (path, domain)

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack users: %s" % truncate(res[0]))
        return res[0]["users"]

    @setup_client
    def get(self, oid):
        """
        :param oid: role id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/users/%s" % oid
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack user: %s" % truncate(res[0]))
        user = res[0]["user"]

        # get groups
        path = "/users/%s/groups" % oid
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack user %s groups: %s" % (oid, truncate(res[0])))
        user["groups "] = res[0]["groups"]

        # get projects
        path = "/users/%s/projects" % oid
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack user %s projects: %s" % (oid, truncate(res[0])))
        user["projects"] = res[0]["projects"]

        # get roles
        path = "/role_assignments?user.id=%s&effective" % (oid)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack user %s roles: %s" % (oid, truncate(res[0])))
        try:
            user["roles"] = [r["role"] for r in res[0]["role_assignments"]]
        except Exception:
            user["roles"] = []

        return user

    @setup_client
    def create(self, name, email, default_project, domain, password, description=""):
        """TODO
        :param name:
        :param email:
        :param default_project:
        :param domain:
        :param password:
        :param description: [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "user": {
                "default_project_id": default_project,
                "description": description,
                "domain_id": domain,
                "email": email,
                "enabled": True,
                "name": name,
                "password": password,
            }
        }

        path = "/users"
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Create openstack user: %s" % truncate(res[0]))
        return res[0]["user"]

    @setup_client
    def update(
        self,
        oid,
        name=None,
        email=None,
        default_project=None,
        domain=None,
        password=None,
        enabled=None,
        description=None,
    ):
        """Updates the password for or enables or disables a user.

        :param oid: user id
        :param name: [optional]
        :param email: [optional]
        :param default_project: [optional]
        :param domain: [optional]
        :param password: [optional]
        :param enabled: [optional]
        :param description: [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"user": {}}

        if name is not None:
            data["user"]["name"] = name
        if email is not None:
            data["user"]["email"] = email
        if default_project is not None:
            data["user"]["default_project_id"] = default_project
        if domain is not None:
            data["user"]["domain_id"] = domain
        if password is not None:
            data["user"]["password"] = password
        if enabled is not None:
            data["user"]["enabled"] = enabled
        if description is not None:
            data["user"]["description"] = description

        path = "/users/%s" % oid
        res = self.client.call(path, "PATCH", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Update openstack user: %s" % truncate(res[0]))
        return res[0]["user"]

    @setup_client
    def delete(self, oid):
        """Deletes a user.

        :param oid: user id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/users/%s" % oid
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack user: %s" % truncate(res[0]))
        return True

    @setup_client
    def password(self, oid):
        """Changes the password for a user.

        :param oid: user id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/users/%s" % oid
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack user: %s" % truncate(res[0]))
        return res[0]["server"]
