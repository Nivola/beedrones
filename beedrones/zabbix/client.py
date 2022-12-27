# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte

from beecell.simple import jsonDumps
import base64
from logging import getLogger
import requests
from requests import ConnectionError, ConnectTimeout
from beecell.simple import truncate, check_vault
from urllib3 import disable_warnings, exceptions
from six import ensure_binary

disable_warnings(exceptions.InsecureRequestWarning)


class ZabbixError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "ZabbixError: %s" % self.value

    def __str__(self):
        return "ZabbixError: %s" % self.value


class ZabbixEntity(object):
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

    def http_post(self, uri, data={}):
        method = 'post'
        heady = {'content-type': 'application/json'}
        uri = self.manager.base_uri + uri

        try:
            res = requests.post(uri, headers=heady, timeout=self.timeout, data=jsonDumps(data), verify=False)
            output = res.json()
            if 'error' in output:
                error = output['error']['data']
                raise Exception(error)
            self.logger.debug('zabbix http %s response: %s' % (method, truncate(output)))
        except ConnectTimeout as ex:
            self.logger.error('zabbix connection timeout: %s' % ex)
            raise ZabbixError(ex)
        except ConnectionError as ex:
            self.logger.error('zabbix connection error: %s' % ex)
            raise ZabbixError(ex)
        except Exception as ex:
            self.logger.error('zabbix http %s error: %s' % (method, ex))
            raise ZabbixError(ex)

        return output

    def call(self, method, params={}):
        data = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1, 'auth': self.token}
        self.logger.debug('zabbix imput data: %s' % data)
        res = self.http_post('/', data=data)
        return res.get('result')


class ZabbixManager(object):
    """ZabbixManager

    Definitions:

    host - a networked device that you want to monitor, with IP/DNS.
    host group - a logical grouping of hosts; it may contain hosts and templates. Hosts and templates within a host
        group are not in any way linked to each other. Host groups are used when assigning access rights to hosts for
        different user groups.
    item - a particular piece of data that you want to receive off of a host, a metric of data.
    value preprocessing - a transformation of received metric value before saving it to the database.
    trigger - a logical expression that defines a problem threshold and is used to "evaluate" data received in items.
        When received data are above the threshold, triggers go from 'Ok' into a 'Problem' state. When received data
        are below the threshold, triggers stay in/return to an 'Ok' state.
    event - a single occurrence of something that deserves attention such as a trigger changing state or a
        discovery/agent auto-registration taking place.
    event tag - a pre-defined marker for the event. It may be used in event correlation, permission granulation, etc.
    event correlation - a method of correlating problems to their resolution flexibly and precisely. For example, you
        may define that a problem reported by one trigger may be resolved by another trigger, which may even use a
        different data collection method.
    problem - a trigger that is in "Problem" state.
    problem update - problem management options provided by Zabbix, such as adding comment, acknowledging, changing
        severity or closing manually.
    action - a predefined means of reacting to an event. An action consists of operations (e.g. sending a notification)
        and conditions (when the operation is carried out)
    escalation - a custom scenario for executing operations within an action; a sequence of sending
        notifications/executing remote commands.
    media - a means of delivering notifications; delivery channel.
    notification - a message about some event sent to a user via the chosen media channel.
    remote command - a pre-defined command that is automatically executed on a monitored host upon some condition.
    template - a set of entities (items, triggers, graphs, screens, applications, low-level discovery rules, web
        scenarios) ready to be applied to one or several hosts. The job of templates is to speed up the deployment of
        monitoring tasks on a host; also to make it easier to apply mass changes to monitoring tasks. Templates are
        linked directly to individual hosts.
    application - a grouping of items in a logical group.
    web scenario - one or several HTTP requests to check the availability of a web site.
    frontend - the web interface provided with Zabbix.
    dashboard - customizable section of the web interface displaying summaries and visualisations of important
        information in visual units called widgets.
    widget - visual unit displaying information of a certain kind and source (a summary, a map, a graph, the clock,
        etc), used in the dashboard.
    Zabbix API - Zabbix API allows you to use the JSON RPC protocol to create, update and fetch Zabbix objects
        (like hosts, items, graphs and others) or perform any other custom tasks.
    Zabbix server - a central process of Zabbix software that performs monitoring, interacts with Zabbix proxies and
        agents, calculates triggers, sends notifications; a central repository of data.
    Zabbix agent - a process deployed on monitoring targets to actively monitor local resources and applications.
    Zabbix proxy - a process that may collect data on behalf of Zabbix server, taking some processing load off of the
        server.
    encryption - support of encrypted communications between Zabbix components (server, proxy, agent, zabbix_sender and
        zabbix_get utilities) using Transport Layer Security (TLS) protocol.
    network discovery - automated discovery of network devices.
    low-level discovery - automated discovery of low-level entities on a particular device (e.g. file systems, network
        interfaces, etc).
    low-level discovery rule - set of definitions for automated discovery of low-level entities on a device.
    item prototype - a metric with certain parameters as variables, ready for low-level discovery. After low-level
        discovery the variables are automatically substituted with the real discovered parameters and the metric
        automatically starts gathering data.
    trigger prototype - a trigger with certain parameters as variables, ready for low-level discovery. After low-level
        discovery the variables are automatically substituted with the real discovered parameters and the trigger
        automatically starts evaluating data. Prototypes of some other Zabbix entities are also in use in low-level
        discovery - graph prototypes, host prototypes, host group prototypes, application prototypes.
    agent auto-registration - automated process whereby a Zabbix agent itself is registered as a host and started to
        monitor.
    """
    def __init__(self, uri=None, proxy=None):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.base_uri = uri + '/api_jsonrpc.php'
        self.token = None
        self.timeout = 5.0

        from .proxy import ZabbixProxy
        from .host import ZabbixHost
        from .host_template import ZabbixHostTemplate
        from .host_group import ZabbixHostGroup
        from .host_interface import ZabbixHostInterface
        from .alert import ZabbixAlert
        from .action import ZabbixAction
        from .problem import ZabbixProblem
        from .trigger import ZabbixTrigger
        from .it_service import ZabbixItService

        self.proxy = ZabbixProxy(self)
        self.host = ZabbixHost(self)
        self.template = ZabbixHostTemplate(self)
        self.group = ZabbixHostGroup(self)
        self.interface = ZabbixHostInterface(self)
        self.alert = ZabbixAlert(self)
        self.problem = ZabbixProblem(self)
        self.action = ZabbixAction(self)
        self.trigger = ZabbixTrigger(self)
        self.it_service = ZabbixItService(self)

    def set_timeout(self, timeout):
        self.timeout = timeout

    def ping(self):
        """Ping zabbix

        :return: True or False
        """
        res = False
        try:
            uri = self.base_uri
            requests.get(uri, headers={'content-type': 'application/json'}, timeout=self.timeout, verify=False)
            res = True
        except ConnectTimeout as ex:
            self.logger.error('zabbix connection timeout: %s' % ex)
        except ConnectionError as ex:
            self.logger.error('zabbix connection error: %s' % ex)
        except Exception as ex:
            self.logger.error('zabbix http %s error: %s' % ('post', False))
        self.logger.debug('Ping zabbix server: %s' % res)

        return res

    def version(self):
        """Get zabbix version

        :return: zabbix version
        """
        try:
            headers = {'Content-Type': 'application/json'}
            uri = self.base_uri
            data = {'jsonrpc': '2.0', 'method': 'apiinfo.version', 'params': [], 'id': 1}
            res = requests.post(uri, headers=headers, data=jsonDumps(data), timeout=self.timeout, verify=False)
            output = res.json()
            if 'error' in output:
                error = output['error']['data']
                raise Exception(error)
            version = output['result']
            self.logger.debug('Get version: %s' % version)
            return version
        except ConnectTimeout as ex:
            self.logger.error('zabbix connection timeout: %s' % ex)
            raise ZabbixError(ex)
        except ConnectionError as ex:
            self.logger.error('zabbix connection error: %s' % ex)
            raise ZabbixError(ex)
        except Exception as ex:
            self.logger.error('get version error: %s' % ex)
            raise ZabbixError(ex)

    def authorize(self, user=None, pwd=None, http_user=None, http_pwd=None, token=None, key=None, userData=False):
        """Get token

        :param user: user
        :param pwd: password
        :param http_user: user used to make simple http authentication
        :param http_pwd: password used to make simple http authentication
        :param token: authentication token
        :param key: [optional] fernet key used to decrypt encrypted password
        :param userData: flag to get additional information about the user
        :param timeout: http request timeout [defualt=5.0s]
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

                headers = {'Content-Type': 'application/json'}
                if http_user is not None and http_pwd is not None:
                    headers['Authorization'] = 'Basic %s' % base64.b64encode('%s:%s' % (http_user, http_pwd))

                uri = self.base_uri
                pwd = ensure_binary(pwd)
                pwd = pwd.decode("utf-8")
                params = {'user': user, 'password': pwd}
                if userData:
                    params['userData'] = userData
                data = {'jsonrpc': '2.0', 'method': 'user.login', 'params': params, 'id': 1}
                res = requests.post(uri, headers=headers, data=jsonDumps(data), timeout=self.timeout, verify=False)
                output = res.json()
                # print('output={}'.format(output))  # debugging
                if 'error' in output:
                    error = output['error']['data']
                    raise Exception(error)
                if userData:
                    self.token = output['result'].get('sessionid')
                else:
                    self.token = output['result']
                self.logger.debug('Get token for user %s: %s' % (user, self.token))
                return self.token
            except ConnectTimeout as ex:
                self.logger.error('zabbix connection timeout: %s' % ex)
                raise ZabbixError(ex)
            except ConnectionError as ex:
                self.logger.error('zabbix connection error: %s' % ex)
                raise ZabbixError(ex)
            except Exception as ex:
                self.logger.error('get token error: %s' % ex)
                raise ZabbixError(ex)

    def logout(self, token):
        """Logout from zabbix

        :param token: zabbix token
        :return: True/False
        :raise ZabbixError:
        """
        try:
            # get token from identity service
            self.logger.debug('Try to delete token %s' % token)

            headers = {'Content-Type': 'application/json-rpc'}

            uri = self.base_uri
            data = {'jsonrpc': '2.0', 'method': 'user.logout', 'params': {}, 'auth': token, 'id': 1}
            res = requests.post(uri, headers=headers, data=jsonDumps(data), timeout=self.timeout, verify=False)
            output = res.json()
            if res.status_code in [400]:
                error = output['detail']
                raise Exception(error)
            self.token = output['result']
            self.logger.debug('Delete token %s' % token)
            return self.token
        except ConnectTimeout as ex:
            self.logger.error('zabbix connection timeout: %s' % ex)
            raise ZabbixError(ex)
        except ConnectionError as ex:
            self.logger.error('zabbix connection error: %s' % ex)
            raise ZabbixError(ex)
        except Exception as ex:
            self.logger.error('get token error: %s' % ex)
            raise ZabbixError(ex)
