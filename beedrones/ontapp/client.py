# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

"""
ontap platform client module
"""

from logging import getLogger
from urllib3 import disable_warnings, exceptions
import requests
from netapp_ontap import HostConnection, utils
from netapp_ontap.host_connection import LoggingAdapter
from netapp_ontap import __version__ as client_version
from netapp_ontap.resources import Cluster

from beecell.crypto import check_vault

disable_warnings(exceptions.InsecureRequestWarning)


class NivolaOntapHostConnection(HostConnection):
    def __init__(
        self,
        host,
        username: str = None,
        password: str = None,
        cert: str = None,
        key: str = None,
        verify: bool = True,
        poll_timeout: int = 30,
        poll_interval: int = 5,
        headers: dict = None,
    ):
        super().__init__(host, username, password, cert, key, verify, poll_timeout, poll_interval, headers)

    @property
    def session(self) -> requests.Session:
        current_session = getattr(self, "_request_session", None)
        if not current_session:
            current_session = requests.Session()

        if self.origin not in current_session.adapters:
            current_session.mount(self.origin, LoggingAdapter(self, max_retries=0, timeout=5))
        if self.basic_auth:
            current_session.auth = self.basic_auth
        else:
            current_session.cert = self.cert_auth
        if self.request_headers:
            current_session.headers.update(self.request_headers)
        current_session.verify = self.verify

        import netapp_ontap  # pylint: disable=cyclic-import

        current_session.headers.update({"X-Dot-Client-App": "netapp-ontap-python-%s" % netapp_ontap.__version__})

        # current_session.verify = False
        self._request_session = current_session
        return current_session


class OntapError(Exception):
    """
    ontap error wrapper
    """

    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return f"OntapError: {self.value}"

    def __str__(self):
        return f"OntapError: {self.value}"


def make_request(method):
    """
    request decorator
    """

    def inner(ref, *args, **kwargs):
        if ref.client is None:
            raise OntapError("you must first authenticate")
        try:
            res = method(ref, *args, **kwargs)
        except (OntapError, Exception) as ex:
            ref.logger.error(ex, exc_info=True)
            raise OntapError(str(ex)) from ex
        return res

    return inner


class OntapEntity:
    """
    base class for ontap entities
    """

    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        self.manager = manager

    @property
    def client(self):
        return self.manager.client

    @property
    def timeout(self):
        return self.manager.timeout


class OntapManager:
    """OntapManager

    :param key: [optional] fernet key used to decrypt encrypted password
    """

    def __init__(self, host, user, pwd, port=80, proto="http", timeout=30.0, key=None):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

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
        from .qtree import OntapQtree
        from .quota import OntapUsage
        from .aggregate import OntapAggregate

        self.cluster = OntapCluster(self)
        self.svm = OntapSvm(self)
        self.volume = OntapVolume(self)
        self.snapmirror = OntapSnapMirror(self)
        self.protocol = OntapProtocol(self)
        self.qtree = OntapQtree(self)
        self.usage = OntapUsage(self)
        self.aggregate = OntapAggregate(self)

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
        except Exception:
            return False

    def version(self):
        """Get ontap version from cluster

        :return: ontap version
        """
        version = {"client": client_version}
        cluster = Cluster()
        cluster.set_connection(connection=self.client)
        cluster.get()
        clu_ver = cluster.version
        version["cluster"] = f"{clu_ver.generation}.{clu_ver.major}.{clu_ver.minor} ({clu_ver.full})"
        return version

    def authorize(self):
        """Authenticate on server"""
        # check password is encrypted
        pwd = check_vault(self.pwd, self.key)

        utils.DEBUG = 1
        conn = NivolaOntapHostConnection(self.host, username=self.user, password=pwd, verify=False)
        conn.scheme = self.proto
        conn.port = self.port
        self.client = conn
