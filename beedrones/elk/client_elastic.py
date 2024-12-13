# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte


from logging import getLogger

from requests.exceptions import ConnectionError, ConnectTimeout
from urllib3 import disable_warnings, exceptions
from elasticsearch import Elasticsearch


disable_warnings(exceptions.InsecureRequestWarning)


class ElasticError(Exception):
    def __init__(self, value, code=400):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "ElasticError: %s" % self.value

    def __str__(self):
        return "ElasticError: %s" % self.value


class ElasticEntity(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
        self.manager: ElasticManager = manager
        self.next = None

    @property
    def timeout(self):
        return self.manager.timeout

    def has_next(self):
        if self.next is not None:
            return True
        return False


class ElasticManager(object):
    def __init__(
        self,
        es: Elasticsearch = None,
        host=None,
        hosts=None,
        user=None,
        pwd=None,
        proxy=None,
        timeout=60.0,
    ):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        if es is not None:
            self.logger.debug("+++++ ElasticManager - es not None")
            self.es = es
        else:
            self.logger.debug("+++++ ElasticManager - es is None")
            if host is None and hosts is None:
                raise
            self.user = user
            self.pwd = pwd
            self.timeout = timeout

            elk_hosts = []
            if host is not None:
                self.logger.debug("+++++ ElasticManager - add host %s", host)
                elk_hosts.append("https://" + str(host) + ":9200")
            else:
                for host_item in hosts:
                    self.logger.debug("+++++ ElasticManager - add hosts %s", host_item)
                    elk_hosts.append("https://" + str(host_item) + ":9200")

            if user is not None and pwd is not None:
                http_auth = (user, pwd)
            else:
                http_auth = None

            self.logger.debug("+++++ ElasticManager - before Elasticsearch")
            self.es = Elasticsearch(
                elk_hosts,
                # http_auth
                http_auth=http_auth,
                # turn on SSL
                # use_ssl=True,
                # make sure we verify SSL certificates
                verify_certs=False,
            )
            self.logger.debug("+++++ ElasticManager - FINE")

        from .role_mapping import ElasticRoleMapping
        from .user import ElasticUser

        # initialize proxy objects
        self.role_mapping = ElasticRoleMapping(self)
        self.user = ElasticUser(self)

    def set_timeout(self, timeout):
        self.timeout = timeout

    def ping(self):
        """Ping elastic

        :return: True or False
        """
        res = False
        try:
            self.es.ping()
            res = True
        except ConnectTimeout as ex:
            self.logger.error("elastic connection timeout: %s" % ex)
        except ConnectionError as ex:
            self.logger.error("elastic connection error: %s" % ex)
        except Exception as ex:
            self.logger.error("elastic http %s error: %s" % ("post", False))
        self.logger.debug("Ping elastic server: %s" % res)

        return res
