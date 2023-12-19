# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte

"""

"""

from __future__ import unicode_literals
from __future__ import print_function
import re
import requests
from logging import getLogger


class GuacamoleError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "GuacamoleError: %s" % self.value

    def __str__(self):
        return "GacamoleError: %s" % self.value


class GuacamoleClient(object):
    def __init__(
        self,
        hostname,
        username,
        password,
        method="https",
        url_path="/",
        default_datasource=None,
        verify=True,
    ):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
        if method.lower() not in ["https", "http"]:
            self.logger.error("Only http and https methods are valid.")
            raise GuacamoleError("Only http and https methods are valid.")
        self.REST_API = "{}://{}{}/api".format(method, hostname, url_path)
        self.logger.info("REST_API %s " % self.REST_API)

        self.username = username
        self.password = password
        self.verify = verify
        auth = self.__authenticate()
        self.logger.debug("AUTH :%s" % auth)

        if "authToken" not in auth:
            self.logger.error("Failed to retrieve auth token")
            raise GuacamoleError("Failed to retrieve auth token")

        if "dataSource" not in auth:
            self.logger.error("Failed to retrieve primary data source")
            raise GuacamoleError("Failed to retrieve primary data source")

        if "availableDataSources" not in auth:
            self.logger.error("Failed to retrieve data sources")
            raise GuacamoleError("Failed to retrieve data sources")

        self.datasources = auth["availableDataSources"]
        if default_datasource:
            if default_datasource not in self.datasources:
                self.logger.error(
                    "Datasource {} does not exist. Possible values: {}".format(default_datasource, self.datasources)
                )
                raise GuacamoleError(
                    "Datasource {} does not exist. Possible values: {}".format(default_datasource, self.datasources)
                )

            self.primary_datasource = default_datasource
        else:
            self.primary_datasource = auth["dataSource"]
        self.logger.debug("primary_datasource: %s" % self.primary_datasource)

        self.token = auth["authToken"]
        self.logger.debug("TOKEN: %s " % self.token)

    def __authenticate(self):
        r = requests.post(
            url=self.REST_API + "/tokens",
            data={"username": self.username, "password": self.password},
            verify=self.verify,
            allow_redirects=True,
        )
        self.logger.debug(
            """requests.post( url=%s/tokens,data={'username': %s, 'password': %s},verify=%s,
            allow_redirects=True)"""
            % (self.REST_API, self.username, self.password, self.verify)
        )
        r.raise_for_status()
        self.logger.debug(r.json)
        return r.json()

    def __auth_request(self, method, url, payload=None, url_params=None, json_response=True):
        params = [("token", self.token)]
        if url_params:
            params += url_params
        self.logger.debug(
            "{method} {url} - Params: {params}- Payload: {payload}".format(
                method=method, url=url, params=params, payload=payload
            )
        )
        self.logger.debug(
            "requests.request(method={}, url={}, params={}, json={}, verify={}, allow_redirects=True".format(
                method, url, params, payload, self.verify
            )
        )

        r = requests.request(
            method=method,
            url=url,
            params=params,
            json=payload,
            verify=self.verify,
            allow_redirects=True,
        )
        # print(r)
        r.raise_for_status()

        if not r.ok:
            self.logger.error(r.content)
        r.raise_for_status()
        if json_response:
            try:
                return r.json()
            except:
                self.logger.error("Could not decode JSON response")
                return r
        else:
            return r

    def get_connections(self, datasource=None):
        if not datasource:
            datasource = self.primary_datasource
        params = [
            ("permission", "UPDATE"),
            ("permission", "DELETE"),
        ]
        return self.__auth_request(
            method="GET",
            url="{}/session/data/{}/connectionGroups/ROOT/tree".format(self.REST_API, datasource),
            url_params=params,
        )

    def get_connections_groups(self, datasource=None):
        """
        Edit an exiting connection group
        """
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="GET",
            url="{}/session/data/{}/connectionGroups/".format(self.REST_API, datasource),
        )

    def get_active_connections(self, datasource=None):
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="GET",
            url="{}/session/data/{}/activeConnections".format(self.REST_API, datasource),
        )

    def get_connection(self, connection_id, datasource=None):
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="GET",
            url="{}/session/data/{}/connections/{}".format(self.REST_API, datasource, connection_id),
        )

    def get_connection_parameters(self, connection_id, datasource=None):
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="GET",
            url="{}/session/data/{}/connections/{}/parameters".format(self.REST_API, datasource, connection_id),
        )

    def get_connection_full(self, connection_id, datasource=None):
        c = self.get_connection(connection_id, datasource)
        c["parameters"] = self.get_connection_parameters(connection_id, datasource)
        return c

    def __get_connection_by_name(self, cons, name, regex=False):
        # FIXME This need refactoring (DRY)
        if "childConnections" not in cons:
            if "childConnectionGroups" in cons:
                for c in cons["childConnectionGroups"]:
                    res = self.__get_connection_by_name(c, name, regex)
                    if res:
                        return res
        else:
            children = cons["childConnections"]
            if regex:
                res = [x for x in children if re.search(name, x["name"])]
            else:
                res = [x for x in children if x["name"] == name]
            if not res:
                if "childConnectionGroups" in cons:
                    for c in cons["childConnectionGroups"]:
                        res = self.__get_connection_by_name(c, name, regex)
                        if res:
                            return res
            else:
                return res[0]

    def get_connection_by_name(self, name, regex=False, datasource=None):
        """
        Get a connection group by its name
        """
        cons = self.get_connections(datasource)
        res = self.__get_connection_by_name(cons, name, regex)
        if not res:
            self.logger.error("Could not find connection named {}".format(name))
        return res

    def add_connection(self, payload, datasource=None):
        """
        Add a new connection

        Example payload:
        {"name":"iaas-067-mgt01 (Admin)",
        "parentIdentifier":"4",
        "protocol":"rdp",
        "attributes":{"max-connections":"","max-connections-per-user":""},
        "activeConnections":0,
        "parameters":{
            "port":"3389",
            "enable-menu-animations":"true",
            "enable-desktop-composition":"true",
            "hostname":"iaas-067-mgt01.vcloud",
            "color-depth":"32",
            "enable-font-smoothing":"true",
            "ignore-cert":"true",
            "enable-drive":"true",
            "enable-full-window-drag":"true",
            "security":"any",
            "password":"XXX",
            "enable-wallpaper":"true",
            "create-drive-path":"true",
            "enable-theming":"true",
            "username":"Administrator",
            "console":"true",
            "disable-audio":"true",
            "domain":"iaas-067-mgt01.vcloud",
            "drive-path":"/var/tmp",
            "disable-auth":"",
            "server-layout":"",
            "width":"",
            "height":"",
            "dpi":"",
            "console-audio":"",
            "enable-printing":"",
            "preconnection-id":"",
            "enable-sftp":"",
            "sftp-port":""}}
        """
        if not datasource:
            datasource = self.primary_datasource
        if self.get_connection_by_name(payload["name"]):
            self.logger.error("Cannot create connection '%s': already exists" % payload["name"])
            raise GuacamoleError("Cannot create connection '%s': already exists" % payload["name"])

        return self.__auth_request(
            method="POST",
            url="{}/session/data/{}/connections".format(self.REST_API, datasource),
            payload=payload,
        )

    def edit_connection(self, connection_id, payload, datasource=None):
        """
        Edit an existing connection

        Example payload:
        {"name":"test",
        "identifier":"7",
        "parentIdentifier":"ROOT",
        "protocol":"rdp",
        "attributes":{"max-connections":"","max-connections-per-user":""},
        "activeConnections":0,
        "parameters":{
            "disable-audio":"true",
            "server-layout":"fr-fr-azerty",
            "domain":"dt",
            "hostname":"127.0.0.1",
            "enable-font-smoothing":"true",
            "security":"rdp",
            "port":"3389",
            "disable-auth":"",
            "ignore-cert":"",
            "console":"",
            "width":"",
            "height":"",
            "dpi":"",
            "color-depth":"",
            "console-audio":"",
            "enable-printing":"",
            "enable-drive":"",
            "create-drive-path":"",
            "enable-wallpaper":"",
            "enable-theming":"",
            "enable-full-window-drag":"",
            "enable-desktop-composition":"",
            "enable-menu-animations":"",
            "preconnection-id":"",
            "enable-sftp":"",
            "sftp-port":""}}
        """
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="PUT",
            url="{}/session/data/{}/connections/{}".format(self.REST_API, datasource, connection_id),
            payload=payload,
        )

    def delete_connection(self, connection_id, datasource=None):
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="DELETE",
            url="{}/session/data/{}/connections/{}".format(self.REST_API, datasource, connection_id),
        )

    def get_history(self, datasource=None):
        if not datasource:
            datasource = self.primary_datasource

        raise NotImplementedError()

    def __get_connection_group_by_name(self, cons, name, regex=False):
        if "childConnectionGroups" in cons:
            children = cons["childConnectionGroups"]
            if regex:
                res = [x for x in children if re.search(name, x["name"])]
            else:
                res = [x for x in children if x["name"] == name]
            if res:
                return res[0]
            for c in cons["childConnectionGroups"]:
                res = self.__get_connection_group_by_name(c, name, regex)
                if res:
                    return res

    def get_connection_group_by_name(self, name, regex=False, datasource=None):
        """
        Get a connection group by its name
        """
        if not datasource:
            datasource = self.primary_datasource
        cons = self.get_connections(datasource)
        return self.__get_connection_group_by_name(cons, name, regex)

    def add_connection_group(self, payload, datasource=None):
        """
        Create a new connection group

        Example payload:
        {"parentIdentifier":"ROOT",
        "name":"iaas-099 (Test)",
        "type":"ORGANIZATIONAL",
        "attributes":{"max-connections":"","max-connections-per-user":""}}
        """
        if not datasource:
            datasource = self.primary_datasource
        if self.get_connection_group_by_name(payload["name"]):
            self.logger.error("Cannot create group '%s': already exists" % payload["name"])
            raise GuacamoleError("Cannot create group '%s': already exists" % payload["name"])
        return self.__auth_request(
            method="POST",
            url="{}/session/data/{}/connectionGroups".format(self.REST_API, datasource),
            payload=payload,
        )

    def edit_connection_group(self, connection_group_id, payload, datasource=None):
        """
        Edit an exiting connection group

        Example payload:
        {"parentIdentifier":"ROOT",
        "name":"iaas-099 (Test)",
        "type":"ORGANIZATIONAL",
        "attributes":{"max-connections":"","max-connections-per-user":""}}
        """
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="PUT",
            url="{}/session/data/{}/connectionGroups/{}".format(
                self.REST_API,
                datasource,
                connection_group_id,
            ),
            payload=payload,
        )

    def delete_connection_group(self, connection_group_id, datasource=None):
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="DELETE",
            url="{}/session/data/{}/connectionGroups/{}".format(self.REST_API, datasource, connection_group_id),
        )

    def get_users(self, datasource=None):
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="GET",
            url="{}/session/data/{}/users".format(
                self.REST_API,
                datasource,
            ),
        )

    def add_user(self, payload, datasource=None):
        """
        Add/enable a user

        Example payload:
        {"username":"test"
         "password":"testpwd",
         "attributes":{
                "disabled":"",
                "expired":"",
                "access-window-start":"",
                "access-window-end":"",
                "valid-from":"",
                "valid-until":"",
                "timezone":null}}
        """
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="POST",
            url="{}/session/data/{}/users".format(self.REST_API, datasource),
            payload=payload,
        )

    def get_user(self, username, datasource=None):
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="GET",
            url="{}/session/data/{}/users/{}".format(self.REST_API, datasource, username),
        )

    def delete_user(self, username, datasource=None):
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="DELETE",
            url="{}/session/data/{}/users/{}".format(self.REST_API, datasource, username),
        )

    def get_permissions(self, username, datasource=None):
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="GET",
            url="{}/session/data/{}/users/{}/permissions".format(self.REST_API, datasource, username),
        )

    def grant_permission(self, username, payload, datasource=None):
        """
        Example payload:
        [{"op":"add","path":"/systemPermissions","value":"ADMINISTER"}]
        """
        if not datasource:
            datasource = self.primary_datasource
        return self.__auth_request(
            method="PATCH",
            url="{}/session/data/{}/users/{}/permissions".format(self.REST_API, datasource, username),
            payload=payload,
            json_response=False,
        )
