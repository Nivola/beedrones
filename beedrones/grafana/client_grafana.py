# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte

from beecell.simple import jsonDumps

import requests
import json
from logging import getLogger
from beecell.simple import check_vault, truncate
from requests.exceptions import ConnectionError, ConnectTimeout
from urllib3 import disable_warnings, exceptions
import base64
from grafana_api import GrafanaFace


disable_warnings(exceptions.InsecureRequestWarning)


class GrafanaError(Exception):
    def __init__(self, value, code=400):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)
   
    def __repr__(self):
        return 'GrafanaError: %s' % self.value
   
    def __str__(self):
        return 'GrafanaError: %s' % self.value


class GrafanaEntity(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)
        self.manager: GrafanaManager = manager
        self.next = None

    # @property
    # def token(self):
    #     return self.manager.token

    @property
    def timeout(self):
        return self.manager.timeout

    def has_next(self):
        if self.next is not None:
            return True
        return False

    #
    # search (esteso con page)
    #
    def search_ext(
        self,
        query=None,
        tag=None,
        type_=None,
        dashboard_ids=None,
        folder_ids=None,
        starred=None,
        limit=None,
        page=None
    ):
        """

        :param query:
        :param tag:
        :param type_:
        :param dashboard_ids:
        :param folder_ids:
        :param starred:
        :param limit:
        :param page:
        :return:
        """
        list_dashboard_path = "/search"
        params = []

        if query:
            params.append("query=%s" % query)

        if tag:
            params.append("tag=%s" % tag)

        if type_:
            params.append("type=%s" % type_)

        if dashboard_ids:
            params.append("dashboardIds=%s" % dashboard_ids)

        if folder_ids:
            params.append("folderIds=%s" % folder_ids)

        if starred:
            params.append("starred=%s" % starred)

        if limit:
            params.append("limit=%s" % limit)

        if page:
            params.append("page=%s" % page)

        list_dashboard_path += "?"
        list_dashboard_path += "&".join(params)

        # r = self.api.GET(list_dashboard_path)
        r = self.manager.grafanaFace.api.GET(list_dashboard_path)
        return r


class GrafanaManager(object):
    def __init__(self, grafanaFace: GrafanaFace = None, host=None, hosts=None, port=None, protocol='http', username=None, pwd=None, timeout=60.0):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.grafanaFace: GrafanaFace

        if grafanaFace is not None:
            self.logger.debug('+++++ GrafanaManager - grafanaFace not None')
            self.grafanaFace = grafanaFace
        else:
            self.logger.debug('+++++ GrafanaManager - grafanaFace is None')
            if host is None and hosts is None:
                raise
            self.username = username
            self.pwd = pwd
            self.timeout = timeout
            self.port = port
            self.protocol = protocol

            grafana_hosts = []
            if host is not None:
                self.logger.debug('+++++ GrafanaManager - add host %s', host)
                grafana_hosts.append(str(host))
            else:
                for host_item in hosts:
                    self.logger.debug('+++++ GrafanaManager - add hosts %s', host_item)
                    grafana_hosts.append(str(host_item))

            self.logger.debug('+++++ GrafanaManager - username: %s' % username)
            self.logger.debug('+++++ GrafanaManager - grafana_hosts: %s' % grafana_hosts[0])
            self.grafanaFace = GrafanaFace(
                auth=(username, pwd),
                host=grafana_hosts[0],
                port=port,
                protocol=protocol,
                verify=False
            )
            self.logger.debug('+++++ GrafanaManager - self.grafanaFace %s: ' % self.grafanaFace)
            self.logger.debug('+++++ GrafanaManager - FINE')

        from .folder import GrafanaFolder
        from .team import GrafanaTeam
        from .user import GrafanaUser
        from .alert_notification import GrafanaAlertNotification
        from .dashboard import GrafanaDashboard

        # initialize proxy objects
        self.folder = GrafanaFolder(self)
        self.team = GrafanaTeam(self)
        self.user = GrafanaUser(self)
        self.alert_notification = GrafanaAlertNotification(self)
        self.dashboard = GrafanaDashboard(self)

    def set_timeout(self, timeout):
        self.timeout = timeout

    def ping(self):
        """Ping grafana

        :return: True or False
        """
        res = False
        try:
            # grafana_base_uri = 'http://' + self.grafanaFace.api.url_host + ":" + str(self.grafanaFace.api.url_port)
            grafana_base_uri = self.grafanaFace.api.url_protocol + '://' + self.grafanaFace.api.url_host + ":" + str(self.grafanaFace.api.url_port)
            self.logger.debug('+++++ GrafanaManager - grafana_base_uri: %s', grafana_base_uri)
            uri = grafana_base_uri + "/api/folders?limit=1"
            response = requests.get(uri, headers={'content-type': 'application/json'}, timeout=self.timeout, verify=False)
            self.logger.debug('grafana response: %s' % response)
            res = True
        except ConnectTimeout as ex:
            self.logger.error('+++++ GrafanaManager - connection timeout: %s' % ex)
            raise GrafanaError(ex)
        except ConnectionError as ex:
            self.logger.error('+++++ GrafanaManager -  connection error: %s' % ex)
            raise GrafanaError(ex)
        except Exception as ex:
            self.logger.error('+++++ GrafanaManager -  error: {}'.format(ex))
            raise GrafanaError(ex)

        self.logger.debug('+++++ GrafanaManager - ping - res: %s' % res)

        return res


    def version(self):
        """Version grafana

        :return: version
        """
        method = 'get'
        try:
            headers = {'Content-Type': 'application/json'}
            username_password_bytes = str.encode(self.username + ':' + self.pwd)
            encode_bytes = base64.b64encode(username_password_bytes)
            encode_str = encode_bytes.decode("ascii")
            headers['Authorization'] = 'Basic %s' % encode_str
            self.logger.debug('grafana headers: %s' % headers)

            # grafana_base_uri = 'http://' + self.grafanaFace.api.url_host + ":" + str(self.grafanaFace.api.url_port)
            grafana_base_uri = self.grafanaFace.api.url_protocol + '://' + self.grafanaFace.api.url_host + ":" + str(self.grafanaFace.api.url_port)
            self.logger.debug('+++++ GrafanaManager - grafana_base_uri: %s', grafana_base_uri)
            uri = grafana_base_uri + "/api/frontend/settings"
            
            res = requests.get(uri, headers=headers, timeout=self.timeout, verify=False)
            self.logger.debug('grafana res: %s' % res)
            output = res.json()

            if res.status_code in [400, 401, 403, 404, 405]:
                self.logger.error('+++++ GrafanaManager - http %s response: %s' % (method, truncate(output)))
                raise Exception(output)

            buildInfo = output.get('buildInfo', None)
            number = buildInfo['version']
            version = {'version': number }
            self.logger.debug('+++++ GrafanaManager - version: %s' % version)
            return version

        except ConnectTimeout as ex:
            self.logger.error('+++++ GrafanaManager - connection timeout: %s' % ex)
            raise GrafanaError(ex)
        except ConnectionError as ex:
            self.logger.error('+++++ GrafanaManager -  connection error: %s' % ex)
            raise GrafanaError(ex)
        except Exception as ex:
            self.logger.error('+++++ GrafanaManager -  error: {}'.format(ex))
            raise GrafanaError(ex)

