# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from logging import getLogger
from urllib3 import disable_warnings, exceptions
from netapp_ontap import HostConnection, utils
from netapp_ontap.resources import Cluster

from beecell.crypto import check_vault

disable_warnings(exceptions.InsecureRequestWarning)


class OntapError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "OntapError: %s" % self.value

    def __str__(self):
        return "OntapError: %s" % self.value


def make_request(method):
    def inner(ref, *args, **kwargs):
        try:
            if ref.client is None:
                raise OntapError('you must first authenticate')
            res = method(ref, *args, **kwargs)
        except OntapError as ex:
            ref.logger.error(ex, exc_info=True)
            raise
        except Exception as ex:
            ref.logger.error(ex, exc_info=True)
            raise OntapError(str(ex))
        return res
    return inner


class OntapEntity(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.manager = manager

    @property
    def client(self):
        return self.manager.client

    @property
    def timeout(self):
        return self.manager.timeout


class OntapManager(object):
    """OntapManager

    :param key: [optional] fernet key used to decrypt encrypted password
    """
    def __init__(self, host, user, pwd, port=80, proto='http', timeout=5.0, key=None):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.host = host
        self.port = port
        self.proto = proto
        self.user = user
        self.pwd = pwd
        self.timeout = timeout
        self.key = key
        
        # ontap client instance
        self.client = None

        from .svm import OntapSvm
        from .cluster import OntapCluster
        from .volume import OntapVolume
        from .snapmirror import OntapSnapMirror
        from .protocol import OntapProtocol

        self.cluster = OntapCluster(self)
        self.svm = OntapSvm(self)
        self.volume = OntapVolume(self)
        self.snapmirror = OntapSnapMirror(self)
        self.protocol = OntapProtocol(self)

    def set_timeout(self, timeout):
        self.timeout = timeout

    @make_request
    def ping(self):
        """Ping ontap engine

        :return: True or False
        """
        try:
            cluster = Cluster()
            cluster.set_connection(connection=self.client)
            cluster.get()
            return True
        except:
            return False

    def version(self):
        """Get ontap engine version

        :return: zabbix version
        """
        pass

    def authorize(self):
        """Authenticate on server
        """
        # check password is encrypted
        pwd = check_vault(self.pwd, self.key)

        utils.DEBUG = 1
        conn = HostConnection(self.host, username=self.user, password=pwd, verify=False)
        conn.scheme = self.proto
        conn.port = self.port
        self.client = conn
