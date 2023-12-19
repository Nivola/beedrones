# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import truncate
from beedrones.haproxy.client import HaproxyEntity, HaproxyError


class HaproxyFrontend(HaproxyEntity):
    """HaproxyFrontend"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_uri = "/v2/services/haproxy/configuration"

    def list(self, **filter):
        """Get haproxy frontends

        :return: list of frontends
        :raise HaproxyError:
        """
        data = filter
        res = self.http_get("/frontends", data=data).get("data", [])
        self.logger.debug("list frontends: %s" % truncate(res))
        return res

    def get(self, name):
        """Get haproxy frontend

        :param name: frontend name
        :return: frontend
        :raise HaproxyError:
        """
        res = self.http_get("/frontends/%s" % name, data=None).get("data", [])
        self.logger.debug("get frontend: %s" % truncate(res))
        return res

    def add(
        self,
        name,
        default_backend,
        mode="tcp",
        force_reload=True,
        maxconn=10000,
        client_timeout=1800000,
        http_connection_mode="http-keep-alive",
        http_keep_alive_timeout=10000,
        http_request_timeout=10000,
        log=True,
        *args,
        **kwargs,
    ):
        """add haproxy frontend

        :param name: frontend name
        :param default_backend: default backend
        :param mode: frontend mode. Allowed tcp, http [default=tcp]
        :param maxconn: max connection [default=10000]
        :param client_timeout: client timeout [default=1800000]
        :param log: enable to log request [default=True]
        :param http_connection_mode: http connection mode. Allowed values: httpclose, http-server-close, http-keep-alive
            [default=http-keep-alive]
        :param http_keep_alive_timeout: http keep alive timeout [default=10000]
        :param http_request_timeout: http request timeout [default=10000]
        :param bool force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :return: frontend acl
        :raise HaproxyError:
        """
        params = {
            "force_reload": force_reload,
            "version": self.get_configuration_version,
        }
        data = {
            "default_backend": default_backend,
            "maxconn": maxconn,
            "client_timeout": client_timeout,
            "mode": mode,
            "name": name,
        }
        if mode == "tcp":
            data["tcplog"] = log
        if mode == "http":
            data.update(
                {
                    "httplog": log,
                    "http_connection_mode": http_connection_mode,
                    "http_keep_alive_timeout": http_keep_alive_timeout,
                    "http_request_timeout": http_request_timeout,
                }
            )
        res = self.http_post("/frontends", params=params, data=data).get("data", [])
        self.logger.debug("add frontend %s" % name)
        return res

    def delete(self, name, force_reload=True):
        """delete haproxy frontend

        :param name: frontend name
        :param force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :return: True
        :raise HaproxyError:
        """
        params = {
            "force_reload": force_reload,
            "version": self.get_configuration_version,
        }
        res = self.http_delete("/frontends/%s" % name, params=params)
        self.logger.debug("delete frontend %s" % name)
        return res

    def get_acls(self, frontend):
        """get haproxy frontend acl

        :param frontend: frontend name
        :return: list of frontend acls
        :raise HaproxyError:
        """
        data = {"parent_name": frontend, "parent_type": "frontend"}
        res = self.http_get("/acls", data=data).get("data", [])
        self.logger.debug("list frontend %s acls: %s" % (frontend, truncate(res)))
        return res

    def add_acl(self, frontend, name, value, force_reload=True, criterion="src", index=0):
        """add haproxy frontend acl

        :param frontend: frontend name
        :param force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :param str name: acl name
        :param str criterion: acl criterion. [default=src]
        :param int index: acl index [defaul=0]
        :param str value: acl value
        :return: frontend acl
        :raise HaproxyError:
        """
        params = {
            "parent_name": frontend,
            "parent_type": "frontend",
            "force_reload": force_reload,
            "version": self.get_configuration_version,
        }
        data = {
            "acl_name": name,
            "criterion": criterion,
            "index": index,
            "value": value,
            "version": self.get_configuration_version,
        }
        res = self.http_post("/acls", params=params, data=data).get("data", [])
        self.logger.debug("add frontend %s acl: %s" % (frontend, name))
        return res

    def del_acl(self, frontend, index, force_reload=True):
        """delete haproxy frontend acl

        :param frontend: frontend name
        :param force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :param int index: acl index
        :return: True
        :raise HaproxyError:
        """
        params = {
            "parent_name": frontend,
            "parent_type": "frontend",
            "force_reload": force_reload,
            "version": self.get_configuration_version,
        }
        res = self.http_delete("/acls/%s" % index, params=params)
        self.logger.debug("delete frontend %s acl: %s" % (frontend, index))
        return res

    def get_binds(self, name):
        """get haproxy frontend binds

        :param name: frontend name
        :return: list of frontend acls
        :raise HaproxyError:
        """
        data = {"frontend": name}
        res = self.http_get("/binds", data=data).get("data", [])
        self.logger.debug("list frontend %s binds: %s" % (name, truncate(res)))
        return res

    def add_bind(self, frontend, name, address="*", port=80, force_reload=True):
        """add haproxy frontend bind

        :param frontend: frontend name
        :param force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :param str name: bind name
        :param str address: bind address [default=*]
        :param int port: bind port [defaul=80]
        :return: frontend bind
        :raise HaproxyError:
        """
        params = {
            "frontend": frontend,
            "force_reload": force_reload,
            "version": self.get_configuration_version,
        }
        data = {"address": address, "name": name, "port": port}
        res = self.http_post("/binds", params=params, data=data).get("data", [])
        self.logger.debug("add frontend %s bind: %s" % (frontend, name))
        return res

    def del_bind(self, frontend, name, force_reload=True):
        """delete haproxy frontend bind

        :param frontend: frontend name
        :param force_reload: if True, do a force reload, do not wait for the configured reload-delay [default=True]
        :param str name: bind name
        :return: True
        :raise HaproxyError:
        """
        params = {
            "frontend": frontend,
            "force_reload": force_reload,
            "version": self.get_configuration_version,
        }
        res = self.http_delete("/binds/%s" % name, params=params)
        self.logger.debug("delete frontend %s bind: %s" % (frontend, name))
        return res
