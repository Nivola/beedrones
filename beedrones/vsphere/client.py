# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2026 CSI-Piemonte

import time
import ssl
from typing import TYPE_CHECKING, List, Dict
from logging import getLogger
import socket
import base64
import xml.etree.ElementTree as et
import http.client as http_client
from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim
from urllib3.util.ssl_ import create_urllib3_context
import ujson as json
from xmltodict import parse as xmltodict
from beecell.simple import get_class_props, check_vault, bool2str
from beecell.util import b, ensure_text
if TYPE_CHECKING:
    from .network import VsphereNetwork

class VsphereError(Exception):
    def __init__(self, value, *args, code=0):
        if value is None or not isinstance(value, str) or "%" not in value:
            self.value = value
        else:
            self.value = value % args

        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return f"VsphereError: {self.value}"

    def __str__(self):
        return f"VsphereError: {self.value}"


class VsphereNotFound(VsphereError):
    def __init__(self):
        VsphereError.__init__(self, "NOT_FOUND", code=404)


class VsphereManager():
    """
    :param vcenter_conn: vcenter connection params
        {'host':, 'port':, 'user':, 'pwd':, 'verified':False}
    :param nsx_manager_conn: nsx manager connection params
        {'host':, 'port':443, 'user':'admin', 'pwd':, verified':False, 'timeout':5}
    :param key: [optional] fernet key used to decrypt encrypted password
    """

    TASK_SUCCESS = vim.TaskInfo.State.success
    TASK_ERROR = vim.TaskInfo.State.error

    network: 'VsphereNetwork'

    def __init__(self, vcenter_conn: dict = None, nsx_manager_conn: dict = None, key: str = None):
        self.logger = getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        # vcenter connection service instance
        self.vsphere_id = None
        self.si = None
        self.vcenter_session = None
        self.os_list = get_class_props(vim.vm.GuestOsDescriptor.GuestOsIdentifier)
        self.vcenter_conn = vcenter_conn

        # nsx manager connection
        self.nsx_id = None
        self.nsx = None
        self.nsx_user = None
        self.nsx_pwd = None
        self.nsx_manager_conn = nsx_manager_conn

        # encryption key
        self.key = key

        if vcenter_conn is not None:
            # check password is encrypted
            pwd = check_vault(vcenter_conn["pwd"], key)

            self.vsphere_id = f"{vcenter_conn['host']}:{vcenter_conn['port']}"
            self._get_vcenter_connection(
                vcenter_conn["host"],
                vcenter_conn["port"],
                vcenter_conn["user"],
                pwd,
                verified=vcenter_conn["verified"],
                timeout=vcenter_conn.get("timeout", 30),
            )
        if nsx_manager_conn is not None:
            # check password is encrypted
            pwd = check_vault(nsx_manager_conn["pwd"], key)
            nsx_manager_conn["pwd"] = pwd

            self.nsx_id = f"{nsx_manager_conn['host']}:{nsx_manager_conn['port']}"
            self._get_nsx_manager_connection(
                nsx_manager_conn["host"],
                nsx_manager_conn["user"],
                pwd,
                port=nsx_manager_conn["port"],
                verified=nsx_manager_conn["verified"],
                timeout=nsx_manager_conn.get("timeout", 30),
            )

        from .system import VsphereSystem
        from .datacenter import VsphereDatacenter
        from .folder import VsphereFolder
        from .server import VsphereServer
        from .vapp import VsphereVApp
        from .datastore import VsphereDatastore
        from .network import VsphereNetwork
        from .cluster import VsphereCluster

        # vsphere proxy objects
        self.system = VsphereSystem(self)
        self.datacenter = VsphereDatacenter(self)
        self.folder = VsphereFolder(self)
        self.server = VsphereServer(self)
        self.vapp = VsphereVApp(self)
        self.datastore = VsphereDatastore(self)
        self.network = VsphereNetwork(self)
        self.cluster = VsphereCluster(self)

        self.server_props = [
            "name",
            "parent",
            "overallStatus",
            "config.hardware.numCPU",
            "config.hardware.memoryMB",
            # 'guest.disk',
            "guest.guestState",
            "guest.hostName",
            "guest.ipAddress",
            "guest.net",
            "config.guestFullName",
            "config.guestId",
            "config.template",
            "runtime.powerState",
            "layoutEx.file",
        ]

    def _get_vcenter_connection(self, host, port, user, pwd, verified=False, timeout=30):
        """
        Get vcenter connection.
        """
        try:
            ctx = None
            socket.setdefaulttimeout(timeout / 2)
            try:
                ctx = create_urllib3_context(cert_reqs=ssl.CERT_NONE)
                self.si = connect.SmartConnect(
                    host=host,
                    user=user,
                    pwd=pwd,
                    port=int(port),
                    sslContext=ctx,
                    connectionPoolTimeout=timeout,
                )
            except Exception:
                # NB: does not exist anymore
                # in current version of the library
                self.si = connect.SmartConnectNoSSL(
                    host=host,
                    user=user,
                    pwd=pwd,
                    port=int(port),
                    connectionPoolTimeout=timeout,
                )

            self.vcenter_session = self.si.content.sessionManager.currentSession
            self.logger.info("Connect vcenter %s. Current session id: %s", host, self.vcenter_session.key)
        except vim.fault.NotAuthenticated as error:
            self.logger.error(str(error), exc_info=False)
            raise VsphereError(str(error), code=0) from error
        except vmodl.MethodFault as error:
            self.logger.error(str(error), exc_info=False)
            raise VsphereError(str(error), code=0) from error
        except socket.timeout as error:
            error_str = f"timeout after {timeout}s"
            self.logger.error(error_str, exc_info=False)
            raise VsphereError(error_str, code=0) from error
        except Exception as error:
            self.logger.error(error, exc_info=False)
            raise VsphereError(str(error), code=0) from error

    def _get_nsx_manager_connection(self, host, user, pwd, port=443, verified=False, timeout=60):
        """
        Configure nsx https client

        :param host: Request host. Ex. 10.102.90.30
        :param port: Request port. [default=80]
        :param timeout: Request timeout. [default=30s]
        :raise VsphereError:
        """
        self.logger.debug("Configure http client for https://%s:%s", host, port)

        try:
            if not verified:
                ssl._create_default_https_context = ssl._create_unverified_context

            self.nsx = {
                "host": host,
                "port": port,
                "timeout": timeout,
                "user": user,
                "pwd": pwd,
                "etag": None,
            }
        except Exception as error:
            self.logger.error(str(error), exc_info=False)
            raise VsphereError(error, code=0) from error

    def _destroy_filter(self, pc_filter, task_key):
        """Destroy existing filter """
        if pc_filter:
            try:
                pc_filter.Destroy()
            except Exception as ex:
                self.logger.debug(
                    "Failed to destroy filter for task %s: %s", task_key, ex
                )

    def _cleanup_property_collector(self, pc, pc_filter, task_key):
        """Safe cleanup of PropertyCollector and filter."""
        self._destroy_filter(pc_filter, task_key)
        if pc:
            try:
                pc.Destroy()
            except Exception as ex:
                self.logger.debug(
                    "Failed to destroy PropertyCollector for task %s: %s",
                    task_key, ex
                )

    def _evaluate_task_state(self, state, task, task_key):
        """Evaluate task state """
        if state == vim.TaskInfo.State.success:
            self.logger.debug("Query vsphere task %s - STOP", task_key)
            return True, task.info.result

        if state == vim.TaskInfo.State.error:
            err = task.info.error
            msg = err.msg if err else "Unknown error"
            raise VsphereError(f"Task {task_key} failed: {msg}")

        return False, None

    def _iter_state_changes(self, update):
        """Extract task state changes from deeply nested VMware update objects."""
        for fs in getattr(update, "filterSet", []) or []:
            for obj_set in getattr(fs, "objectSet", []) or []:
                for change in getattr(obj_set, "changeSet", []) or []:
                    if getattr(change, "name", "") == "info.state":
                        yield change.val

    def disconnect(self):
        """Disconnect vcenter and reset nsx connection"""
        try:
            connect.Disconnect(self.si)
            self.si = None
            self.nsx = None
        except vmodl.MethodFault as error:
            self.logger.error(str(error), exc_info=False)
            raise VsphereError(error, code=0) from error
        except Exception as error:
            self.logger.error(str(error), exc_info=False)
            raise VsphereError(error, code=0) from error

    def get_vcenter_session(self):
        """Get current vcenter session"""
        # if self.vcenter_session is not None:
        #     return self.vcenter_session
        self.vcenter_session = None
        try:
            self.vcenter_session = self.si.content.sessionManager.currentSession
            self.logger.debug("vsphere - Current session id: %s", self.vcenter_session.key)
        except vim.fault.NotAuthenticated as error:
            self.logger.warning(error)
            return None
        except vmodl.MethodFault as error:
            self.logger.warning(error)
            return None
        except Exception as error:
            self.logger.warning(error)
            return None

        return self.vcenter_session

    def nsx_call(self, path, method, data, headers=None, parse=True, timeout=None):
        """
        Run nsx https request

        :param path: Request path. Ex. /api/
        :param method: Request method. Ex. GET, POST, PUT, DELETE
        :param headers: Request headers. [default={}]. Ex.
                        {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        :param data: Request data. [default={}]. Ex. {'@number': 12524, '@type': 'issue', '@action': 'show'}
        :param timeout: [defualt=None] optional request timeout
        :raise VsphereError:
        """
        try:
            headers = {} if headers is None else headers
            if timeout is None:
                timeout = self.nsx["timeout"]

            conn = http_client.HTTPSConnection(self.nsx["host"], self.nsx["port"], timeout=timeout)

            # set simple authentication
            auth = base64.b64encode(b"%s:%s" % (b(self.nsx["user"]), b(self.nsx["pwd"]))).replace(b"\n", b"")
            headers["Authorization"] = f"Basic {auth.decode('utf-8')}"

            self.logger.debug("Send %s request to %s", method, path)
            data = str(data)
            if "password" not in data.lower():
                self.logger.debug("Send [headers=%s] [data=%s]", headers, data)
            else:
                self.logger.debug("Send [headers=%s] [data=%s]", headers, "xxxxxxx")

            conn.request(method, path, data, headers)
            response = conn.getresponse()
            content_type = response.getheader("content-type")
            self.logger.debug("Response status: %s %s", response.status, response.reason)
        except Exception as error:
            self.logger.error(error, exc_info=True)
            raise VsphereError(error, code=400) from error

        # evaluate response status
        # BAD_REQUEST     400     HTTP/1.1, RFC 2616, Section 10.4.1
        if response.status == 400:
            res = response.read()
            self.logger.debug("Response [content-type=%s] [data=%s]", content_type, res)
            if parse is True and (content_type.find("text/xml") >= 0 or content_type.find("application/xml") >= 0):
                res = xmltodict(res, dict_constructor=dict, attr_prefix="")
                msg = res
                if "error" in res.keys():
                    res = res.get("error")
                    msg = res
                if "details" in res.keys():
                    msg = res.get("details")
                if "rootCauseString" in res.keys() and res.get("rootCauseString") is not None:
                    msg += res.get("rootCauseString")
            elif parse is True and (content_type.find("application/json") >= 0):
                res = ensure_text(res)
                res = json.loads(res)
                msg = res
                if "error" in res.keys():
                    res = res.get("error")
                    msg = res
                if "details" in res.keys():
                    msg = res.get("details")
                if "rootCauseString" in res.keys() and res.get("rootCauseString") is not None:
                    msg += res.get("rootCauseString")
            else:
                msg = ""

            self.logger.error("BAD_REQUEST - %s", msg, exc_info=False)
            raise VsphereError(f"BAD_REQUEST - {msg}", code=400)

        # UNAUTHORIZED           401     HTTP/1.1, RFC 2616, Section 10.4.2
        if response.status == 401:
            self.logger.error("UNAUTHORIZED", exc_info=False)
            raise VsphereError("UNAUTHORIZED", code=401)

        # PAYMENT_REQUIRED       402     HTTP/1.1, RFC 2616, Section 10.4.3

        # FORBIDDEN              403     HTTP/1.1, RFC 2616, Section 10.4.4
        if response.status == 403:
            self.logger.error("FORBIDDEN", exc_info=False)
            raise VsphereError("FORBIDDEN", code=403)

        # NOT_FOUND              404     HTTP/1.1, RFC 2616, Section 10.4.5
        if response.status == 404:
            self.logger.error("NOT_FOUND", exc_info=False)
            raise VsphereNotFound()

        # METHOD_NOT_ALLOWED     405     HTTP/1.1, RFC 2616, Section 10.4.6
        if response.status == 405:
            self.logger.error("METHOD_NOT_ALLOWED", exc_info=False)
            raise VsphereError("METHOD_NOT_ALLOWED", code=405)
        # NOT_ACCEPTABLE         406     HTTP/1.1, RFC 2616, Section 10.4.7

        # PROXY_AUTHENTICATION_REQUIRED     407     HTTP/1.1, RFC 2616, Section 10.4.8

        # REQUEST_TIMEOUT        408
        if response.status == 408:
            self.logger.error("REQUEST_TIMEOUT", exc_info=False)
            raise VsphereError("REQUEST_TIMEOUT", code=408)

        # CONFLICT        409
        if response.status == 409:
            res = response.read()
            self.logger.debug("Response [content-type=%s] [data=%s]", content_type, res)
            if parse is True and (content_type.find("text/xml") >= 0 or content_type.find("application/xml") >= 0):
                res = xmltodict(res, dict_constructor=dict, attr_prefix="")
                msg = res
                if "error" in res.keys():
                    res = res.get("error")
                    msg = res
                if "details" in res.keys():
                    msg = res.get("details")
            else:
                msg = ""

            self.logger.error("CONFLICT - %s", msg, exc_info=False)
            raise VsphereError(f"CONFLICT - {msg}", code=409)

        # PRECONDITION_FAILED     412
        if response.status == 412:
            self.logger.error("PRECONDITION_FAILED", exc_info=False)

            body = response.read()
            self.logger.error("+++++ Response body: %s", body)
            self.logger.error("+++++ Request headers: %s", headers)

            raise VsphereError("PRECONDITION_FAILED", code=412)

        # INTERNAL SERVER ERROR  500
        if response.status == 500:
            self.logger.error("CLOUDAPI_SERVER_ERROR", exc_info=False)
            raise VsphereError("CLOUDAPI_SERVER_ERROR", code=500)

        # OK                     200    HTTP/1.1, RFC 2616, Section 10.2.1
        # CREATED                201    HTTP/1.1, RFC 2616, Section 10.2.2
        # ACCEPTED               202    HTTP/1.1, RFC 2616, Section 10.2.3
        # NON_AUTHORITATIVE_INFORMATION    203    HTTP/1.1, RFC 2616, Section 10.2.4
        # NO_CONTENT             204    HTTP/1.1, RFC 2616, Section 10.2.5
        # RESET_CONTENT          205    HTTP/1.1, RFC 2616, Section 10.2.6
        # PARTIAL_CONTENT        206    HTTP/1.1, RFC 2616, Section 10.2.7
        # MULTI_STATUS           207    WEBDAV RFC 2518, Section 10.2
        if 200 <= response.status < 300:
            try:
                res = response.read()
                res_headers = response.getheaders()

                # get etag
                etag = response.getheader("etag", 0)
                # self.logger.debug("nsx_call - etag: %s" % etag)
                self.nsx["etag"] = etag
                res_etag = etag
                if isinstance(etag, str):
                    self.nsx["etag"] = etag.strip('"')
                    res_etag = etag.strip('"')
                # self.logger.debug("+++++ nsx_call - res_etag: %s" % res_etag)

                location = response.getheader("Location", None)
                self.nsx["location"] = location
                ext_id = None
                if location is not None:
                    ext_id = location.rsplit("/", 1)[-1]

                self.logger.debug(
                    "Response [content-type=%s] [headers=%s] [data=%s]",
                    content_type, res_headers, res
                )

                if content_type is not None:
                    # json request
                    if parse is True and content_type.find("application/json") >= 0:
                        res = json.loads(res)
                    elif (
                        parse is True
                        and content_type.find("text/xml") >= 0
                        or parse is True
                        and content_type.find("application/xml") >= 0
                    ):
                        res = xmltodict(res, dict_constructor=dict, attr_prefix="")
                    conn.close()
                else:
                    conn.close()

                if res == b"":
                    res = {"ext_id": ext_id}

                return res, res_etag
            except Exception as error:
                self.logger.error(error, exc_info=False)
                raise VsphereError(error, code=0) from error
        return None

    # Shamelessly borrowed from:
    # https://github.com/dnaeon/py-vconnector/blob/master/src/vconnector/core.py
    def collect_properties(self, view_ref, obj_type, path_set=None, include_mors=False):
        """
        Collect properties for managed objects from a view ref.

        Check the vSphere API documentation for example on retrieving object properties:

            - http://goo.gl/erbFDz

        :param pyVmomi.vim.view.* view_ref: Starting point of inventory navigation
        :param pyVmomi.vim.* obj_type: Type of managed object
        :param list path_set: List of properties to retrieve
        :param bool include_mors: If True include the managed objects refs in the result
        :return: A list of properties for the managed objects

        """
        collector = self.si.content.propertyCollector

        # Create object specification to define the starting point of
        # inventory navigation
        obj_spec = vmodl.query.PropertyCollector.ObjectSpec()
        obj_spec.obj = view_ref
        obj_spec.skip = True

        # Create a traversal specification to identify the path for collection
        traversal_spec = vmodl.query.PropertyCollector.TraversalSpec()
        traversal_spec.name = "traverseEntities"
        traversal_spec.path = "view"
        traversal_spec.skip = False
        traversal_spec.type = view_ref.__class__
        obj_spec.selectSet = [traversal_spec]

        # Add the object and property specification to the
        # property filter specification
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = [obj_spec]

        # Identify the properties to the retrieved
        property_spec = vmodl.query.PropertyCollector.PropertySpec()
        property_spec.type = obj_type

        if not path_set:
            property_spec.all = True

        property_spec.pathSet = path_set
        property_specs = [property_spec]

        filter_spec.propSet = property_specs

        # Retrieve properties
        props = collector.RetrieveContents([filter_spec])

        view_ref.Destroy()

        data = []
        for obj in props:
            properties = {}
            for prop in obj.propSet:
                properties[prop.name] = prop.val

            if include_mors:
                properties["obj"] = obj.obj

            data.append(properties)
        return data

    def get_container_view(self, obj_type, container=None, recursive=True):
        """
        Get a vSphere Container View reference to all objects of type 'obj_type'.
        It is up to the caller to take care of destroying the View when no longer needed.

        :param list obj_type: A list of managed object types
        :return: A container view ref to the discovered managed objects
        """
        content = self.si.content
        if container is None:
            container = content.rootFolder
        return content.viewManager.CreateContainerView(container=container, type=obj_type, recursive=recursive)

    def get_object(self, morid, obj_type, container=None, recursive=True):
        """
        Retrieve a vSphere object by its Managed Object Reference ID (moId).
        Creates a temporary ContainerView and ensures its destruction to 
        prevent vCenter memory leaks.
        """
        cont = self.get_container_view(obj_type, container=container, recursive=recursive)
        obj = None
        try:
            obj = next((obj for obj in cont.view if obj._moId == morid), None)
        finally:
            cont.Destroy()
        return obj

    def get_object_by_name(self, name, obj_type, container=None):
        """
        Retrieve a single vSphere object by its exact name.
        Returns the first exact match found, or None.
        """
        cont = self.get_container_view(obj_type, container=container)
        obj = None
        try:
            obj = next((obj for obj in cont.view if obj.name == name), None)
        finally:
            cont.Destroy()
        return obj

    def get_objects_by_name(self, name, obj_type, container=None):
        """
        Retrieve a list of vSphere objects using a partial name match (substring).
        Returns an empty list if no matches are found.
        """
        cont = self.get_container_view(obj_type, container=container)
        objs = []
        try:
            for view in cont.view:
                if name in view.name:
                    objs.append(view)
        finally:
            cont.Destroy()
        return objs

    def get_vm_object(self, morid):
        """
        Retrieve VM object directly from vCenter (stateless).
        Returns None if VM does not exist or connection fails.
        """
        try:
            # Instantiate local proxy object
            vm = vim.VirtualMachine(morid, self.si._stub)

            # lightweight check to verify robustness
            if vm._moId == morid:
                return vm

        except Exception as e:
            self.logger.error("Error fetching VM %s: %s", morid, e, exc_info=True)
            return None

        # Returns None if VM does not exist
        return None

    def query_nsx_job(self, jobid):
        """
        Query nsx job

        :param jobid: job id
        """
        res, __ = self.nsx_call(f"/api/2.0/services/taskservice/job/{jobid}", "GET", "")
        return res

    def wait_task(self, task, delta=1, trace=None, raise_on_error=False):
        self.logger.debug("Monitor task: %s", task)
        while task.info.state not in [
            vim.TaskInfo.State.success,
            vim.TaskInfo.State.error,
        ]:
            if trace:
                trace()
            time.sleep(delta)

        if task.info.state in [vim.TaskInfo.State.error]:
            self.logger.error("Error: %s", task.info.error.msg)
            if raise_on_error:
                raise Exception(task.info.error.msg)
        if task.info.state in [vim.TaskInfo.State.success]:
            self.logger.debug("Completed")
        return task.info.state

    def query_task(self, task, wait=None, timeout=7200):
        """
        Wait for a vSphere task to complete using an isolated PropertyCollector.
        Automatically recovers from socket/SSL timeouts by recreating the filter.

        :param task: vSphere task object
        :param wait: wait function to execute in each step of the loop
        :param timeout: maximum seconds to wait [default=7200 (2 hours)]
        :return: task.info.result (may be None for some task types)
        :raises VsphereError: on task failure or timeout
        """
        task_key = getattr(task.info, "key", "<unknown>")
        is_done, result = self._evaluate_task_state(getattr(task.info, "state", None), task, task_key)
        if is_done:
            return result

        start_time = time.time()
        # Setup isolated PropertyCollector (thread-safe)
        pc = self.si.content.propertyCollector.CreatePropertyCollector()
        pc_filter = None

        obj_spec = vmodl.query.PropertyCollector.ObjectSpec(obj=task, skip=False)
        path_set = ["info.state", "info.error", "info.result"]
        prop_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task, pathSet=path_set)
        filter_spec = vmodl.query.PropertyCollector.FilterSpec(objectSet=[obj_spec], propSet=[prop_spec])

        try:
            pc_filter = pc.CreateFilter(filter_spec, partialUpdates=False)
            version = ""

            while True:
                # Check overall timeout
                if time.time() - start_time > timeout:
                    raise VsphereError(f"Timeout ({timeout}s) waiting for task {task_key}")

                try:
                    wait_option = vmodl.query.PropertyCollector.WaitOptions(maxWaitSeconds=10)
                    update = pc.WaitForUpdatesEx(version, wait_option)
                except Exception as ex:
                    is_net_timeout = isinstance(ex, (socket.timeout, TimeoutError, ssl.SSLError, OSError))
                    err_type = "Network timeout" if is_net_timeout else "Unexpected error"
                    self.logger.warning(
                        "Query vsphere task error %s: %s - Recreate filter and retry; %s", err_type, task_key, ex
                    )
                    self._destroy_filter(pc_filter, task_key)
                    pc_filter = pc.CreateFilter(filter_spec, partialUpdates=False)
                    version = ""
                    if wait is not None:
                        wait()
                    continue

                if not update:
                    continue

                version = getattr(update, "version", "") or ""
                for new_state in self._iter_state_changes(update):
                    is_done, result = self._evaluate_task_state(new_state, task, task_key)
                    if is_done:
                        return result

        finally:
            self._cleanup_property_collector(pc, pc_filter, task_key)

    @staticmethod
    def wait_for_tasks(service_instance, tasks):
        """
        Given the service instance si and tasks, it returns after all the
        tasks are complete
        """
        property_collector = service_instance.content.propertyCollector
        task_list = [str(task) for task in tasks]
        # Create filter
        obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task) for task in tasks]
        property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task, pathSet=[], all=True)
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = obj_specs
        filter_spec.propSet = [property_spec]
        pcfilter = property_collector.CreateFilter(filter_spec, True)
        try:
            version, state = None, None
            # Loop looking for updates till the state moves to a completed state.
            while len(task_list):
                update = property_collector.WaitForUpdates(version)
                for filter_set in update.filterSet:
                    for obj_set in filter_set.objectSet:
                        task = obj_set.obj
                        for change in obj_set.changeSet:
                            if change.name == "info":
                                state = change.val.state
                            elif change.name == "info.state":
                                state = change.val
                            else:
                                continue

                            if not str(task) in task_list:
                                continue

                            if state == vim.TaskInfo.State.success:
                                # Remove task from taskList
                                task_list.remove(str(task))
                            elif state == vim.TaskInfo.State.error:
                                raise task.info.error
                # Move to next version
                version = update.version
        finally:
            if pcfilter:
                pcfilter.Destroy()

    def ping(self):
        return self.system.ping()

    def version(self):
        return self.system.version()

    def get_custom_fields(self) -> List[Dict]:
        cfm = self.si.content.customFieldsManager
        custom_fields = []
        for f in cfm.field:
            field_i = {
                "key": f.key,
                "name": f.name
            }
            tmp_managed_object_type = getattr(f, "managedObjectType", None)
            if tmp_managed_object_type:
                field_i["managedObjectType"] = tmp_managed_object_type
            custom_fields.append(field_i)

        return custom_fields

    def create_custom_field(self, field_name: str, managedObjectType=None):
        cfm = self.si.content.customFieldsManager
        # check if custom field already exists
        existing_field = next(
            (f for f in cfm.field if f.name == field_name),
            None
        )
        if existing_field:
            self.logger.warning("Field %s already exists", field_name)
            return existing_field
        # create the field
        try:
            new_field = cfm.AddCustomFieldDef(name=field_name, moType=managedObjectType)
            self.logger.info("Created custom field '%s' for moType '%s'", field_name, managedObjectType)
            return new_field
        except Exception as e:
            self.logger.error("Failed to create custom field '%s': %s", field_name, e)
            raise


class VsphereObject():
    """ """

    def __init__(self, manager: 'VsphereManager'):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
        self.manager: VsphereManager = manager
        self.hw_version_to_scsi_devs_per_bus = [(14, 64), (0, 16)]

    @staticmethod
    def get_mo_id(vsphere_obj):
        return vsphere_obj._moId

    def call(self, path, method, data, headers=None, parse=True, timeout=None):
        headers = {} if headers is None else headers
        if self.manager.nsx is None:
            raise VsphereError("Nsx is not configured")
        res, __ = self.manager.nsx_call(path, method, data, headers=headers, parse=parse, timeout=timeout)
        return res

    def call_and_get_etag(self, path, method, data, headers=None, parse=True, timeout=None):
        headers = {} if headers is None else headers
        if self.manager.nsx is None:
            raise VsphereError("Nsx is not configured")
        res, res_etag = self.manager.nsx_call(path, method, data, headers=headers, parse=parse, timeout=timeout)
        return res, res_etag

    def get_tags(self, entity):
        """ """
        try:
            res = [t.key for t in entity.tag]
        except Exception as error:
            self.logger.error(error, exc_info=False)
            res = []

        return res

    def assign_tag(self, entity, tag):
        """ """
        try:
            tag_obj = vim.Tag()
            tag_obj.key = tag
            entity.tag.append(tag_obj)
        except Exception as error:
            self.logger.error(error, exc_info=False)

    def remove_tag(self):
        """ """
        pass

    def permissions(self, entity):
        """ """
        try:
            res = [
                {
                    "group": p.Group,
                    "principal": p.principal,
                    "propagate": p.propagate,
                    "role": p.roleId,
                }
                for p in entity.permission
            ]
        except Exception as error:
            self.logger.error(error, exc_info=False)
            res = []

        return res

    def scheduled_tasks(self):
        """ """
        pass

    def info(self, obj):
        """
        Get info

        :param server: object obtained from api request
        :return: dict like {'id':.., 'name':..}
        """
        data = {
            "id": obj.get("obj")._moId,
            "parent": obj.get("parent")._moId,
            "name": obj.get("name"),
            "overallStatus": obj.get("overallStatus"),
        }

        return data

    def detail(self, obj):
        """
        Get detail

        :param obj: object obtained from api request
        :return: dict like {'id':.., 'name':..}
        """
        try:
            info = {
                "id": obj._moId,
                "parent": obj.parent._moId,
                "name": obj.name,
                "overallStatus": obj.overallStatus,
            }
        except Exception as error:
            self.logger.error(error, exc_info=False)
            info = {}

        return info

    def xml_get_kvargs(self, kvargs, key, default=None, required=True):
        res = kvargs.get(key, default)
        if res is None:
            res = default
        if isinstance(res, bool):
            res = bool2str(res)
        if isinstance(res, int):
            res = str(res)
        if required is True and res is None:
            raise VsphereError(f"key {key} is required and can not be None")
        return res

    def xml_set_key(self, parent, kvargs, key, default=None, required=True):
        if required is True:
            et.SubElement(parent, key).text = self.xml_get_kvargs(kvargs, key, default=default, required=required)
        elif required is False and default is not None:
            et.SubElement(parent, key).text = self.xml_get_kvargs(kvargs, key, default=default, required=required)
