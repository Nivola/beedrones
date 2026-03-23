# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2026 CSI-Piemonte

"""
ontap platform client module
"""

from os import getenv

from itertools import islice
from logging import getLogger
from typing import Dict, List, Optional, Tuple, Type, TYPE_CHECKING, Union
from netapp_ontap import HostConnection, utils
from netapp_ontap.host_connection import LoggingAdapter
from netapp_ontap import __version__ as client_version
from netapp_ontap.resources import Cluster
import requests
from urllib3 import disable_warnings, exceptions
from beecell.crypto import check_vault
from beecell.simple import import_class_safe
from beecell.types.type_class import get_class_fullname_safe
from beecell.types.type_string import truncate
if TYPE_CHECKING:
    from netapp_ontap.response import NetAppResponse
    from netapp_ontap.resource import Resource

disable_warnings(exceptions.InsecureRequestWarning)


class NivolaOntapHostConnection(HostConnection):
    """extends HostConnection with ontap proxy management
    """

    def __init__(
        self,
        host,
        username: Optional[str] = None,
        password: Optional[str] = None,
        cert: Optional[str] = None,
        key: Optional[str] = None,
        verify: bool = True,
        poll_timeout: int = 30,
        poll_interval: int = 5,
        headers: Optional[Dict] = None,
    ):
        super().__init__(
            host, username, password, cert, key, # type: ignore
            verify, poll_timeout, poll_interval, headers # type: ignore
        )

    @property
    def session(self) -> requests.Session:
        """adds to HostConnection session property logic to handle proxy

        :return: the session
        :rtype: requests.Session
        """
        current_session: Optional[requests.Session] = getattr(self, "_request_session", None)
        if not current_session:
            current_session = requests.Session()

        # set proxy if configured
        _dev_env = "lab" in getenv("API_ENV","")
        _stage_env_DEBUG = "stage" in getenv("API_ENV","")
        if _dev_env or _stage_env_DEBUG:
            ontap_proxy = getenv("ontap_proxy",None)
            if ontap_proxy:
                current_session.proxies.update({
                    "http":  ontap_proxy,
                    "https": ontap_proxy,
                })
        #

        if self.origin not in current_session.adapters:
            current_session.mount(self.origin, LoggingAdapter(self, max_retries=0, timeout=20))
        if self.basic_auth:
            current_session.auth = self.basic_auth # type: ignore
        else:
            current_session.cert = self.cert_auth # type: ignore
        if self.request_headers:
            current_session.headers.update(self.request_headers)
        current_session.verify = self.verify

        import netapp_ontap  # pylint: disable=cyclic-import

        current_session.headers.update({"X-Dot-Client-App": "netapp-ontap-python-%s" % netapp_ontap.__version__})

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

    def inner(ref: 'OntapEntity', *args, **kwargs):
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

    def __init__(self, manager: 'OntapManager'):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        self.manager = manager

    @property
    def client(self):
        return self.manager.client

    @property
    def timeout(self):
        return self.manager.timeout

    @make_request
    def list_entities(
        self, resclass: Type['Resource'], fields, **kwargs
    ) -> Union[Dict,List[Dict]]:
        """list ontap entities

        :param kwargs:
        :return:
        """
        # NB: get_collection returns a generator.
        # max_records controls when to make the actual call to ontap
        # e.g. max_records = 100 but total is 1000, if you iterate over all,
        # this would result in 10 platform calls to ontap.
        # here we use it also to limit the number of queried records.
        max_records = kwargs.pop("max_records", None)

        class_name = get_class_fullname_safe(resclass)
        ontap_resource_class: Type['Resource'] = import_class_safe(class_name)

        if max_records:
            # if given, it means we want paginated
            page = kwargs.pop("page", 0)
            # if offset given, use it, otherwise calculate it
            offset = kwargs.pop("offset", None)
            if not offset:
                offset = page * max_records
            total = ontap_resource_class.count_collection(connection=self.client, **kwargs) # type: ignore
            res: List['Resource'] = ontap_resource_class.get_collection( # type: ignore
                connection=self.client, offset=offset, max_records=max_records,
                fields=fields, **kwargs
            )
            res = islice(res, max_records) # type: ignore
            records: List[Dict] = [item.to_dict() for item in res]
            count = len(records)
            resp = {"total": total, "page": page, "count": count, "records": records} # type: ignore
            resp["order_by"] = kwargs.get("order_by", "N/A N/A") # type: ignore
        else:
            total = ontap_resource_class.count_collection(connection=self.client, **kwargs) # type: ignore
            # list all (without pagination, for compatibility with past implementations)
            res: List['Resource'] = ontap_resource_class.get_collection( # type: ignore
                connection=self.client, fields=fields, **kwargs
            )
            resp: List[Dict] = [item.to_dict() for item in res]
        self.logger.debug(
            "list %s - found %s - total %s: %s",
            resclass.__name__, len(resp), total, truncate(resp)
        )
        return resp

    def handle_response(self, response: 'NetAppResponse', timeout=600, interval=10) -> 'NetAppResponse':
        """if it contains a task id, it waits for task completion,
        otherwise it returns immediately

        :param response: response to a netapp api call
        :type response: NetAppResponse
        :param timeout: if job, poll timeout, defaults to 600
        :type timeout: int, optional
        :param interval: if job, poll interval, defaults to 10
        :type interval: int, optional
        :raises RuntimeError: if error, json error representation
        :return: received final response
        :rtype: NetAppResponse
        """
        self.logger.debug("handle_response. is_err: %s - is_job: %s", response.is_err, response.is_job)
        if response.is_job:
            response = response.poll(connection=self.client, timeout=timeout, interval=interval)
            self.logger.debug("handle_response. is_err: %s - is_job: %s", response.is_err, response.is_job)

        if response.is_err:
            try:
                err = response.http_response.json()
            except ValueError:
                err = response.http_response.text
            raise RuntimeError(f"NetApp API error: {err}")
        else:
            return response

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
        from .snapshot_policy import OntapSnapshotPolicy
        from .snapmirror_policy import OntapSnapmirrorPolicy

        self.cluster = OntapCluster(self)
        self.svm = OntapSvm(self)
        self.volume = OntapVolume(self)
        self.snapmirror = OntapSnapMirror(self)
        self.protocol = OntapProtocol(self)
        self.qtree = OntapQtree(self)
        self.usage = OntapUsage(self)
        self.aggregate = OntapAggregate(self)
        self.snapshot_policy = OntapSnapshotPolicy(self)
        self.snapmirror_policy = OntapSnapmirrorPolicy(self)

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

    # utility functions #

    def get_svm_emptiest_aggregate(self,svm_id=None,svm_name=None,disk_class=None) -> Tuple[str, int]:
        """
        finds the em
        """
        if svm_name is None and svm_id is None:
           raise OntapError("Provide at least svm name or svm id")

        if disk_class and disk_class not in ["capacity", "solid_state"]:
            raise ValueError(
                f"Invalid disk_class value: {disk_class}. "
                "Allowed values for disk_class are 'capacity' or 'solid_state'"
            )

        if svm_id is None:
            # search by name
            svms = self.svm.list(name=svm_name)
            if len(svms)!=1:
                raise OntapError("Error while searching for svm. Expected 1, but %d were found" % len(svms))
            svm_id = svms[0].get("uuid")

        svm = self.svm.get(svm_id)
        svm_aggregates = svm.get("aggregates",[])
        if len(svm_aggregates)==0:
            raise OntapError("No aggregates found for the specified svm: %s" % svm_id)

        # initial values
        emptiest_aggregate_name: Optional[str] = None
        max_space_available: int = -1

        for aggregate in svm_aggregates:
            # for each aggregate, get detail info
            aggregate_detail = self.aggregate.get(aggregate.get("uuid"))
            if disk_class:
                # if disk class specified, verify disk class
                aggregate_disk_class = aggregate_detail.get("block_storage",{}).get("primary",{}).get("disk_class")
                if aggregate_disk_class!=disk_class:
                    # wrong disk class
                    continue
            # get space available and emptiest aggregate
            space_available = aggregate_detail.get("space",{}).get("block_storage",{}).get("available",-1)
            if space_available > max_space_available:
                emptiest_aggregate_name = aggregate_detail.get("name")
                max_space_available = space_available

        if emptiest_aggregate_name is None:
            error_msg = f"Error while determining emptiest aggregate for svm {svm_id}"
            if disk_class:
                error_msg += f" with disk class {disk_class}"
            raise OntapError(error_msg)

        return (emptiest_aggregate_name,max_space_available)
