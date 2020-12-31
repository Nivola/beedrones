# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

import socket
from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim
from logging import getLogger
import time
import base64
import ssl
import re
from urllib3.util.ssl_ import create_urllib3_context
import ujson as json
from beecell.simple import get_class_props, truncate, check_vault, bool2str
from xmltodict import parse as xmltodict
from six.moves import http_client
from six import b
import xml.etree.ElementTree as et


class VsphereError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)
    
    def __repr__(self):
        return 'VsphereError: %s' % self.value    
    
    def __str__(self):
        return 'VsphereError: %s' % self.value


class VsphereNotFound(VsphereError):
    def __init__(self):
        VsphereError.__init__(self, 'NOT_FOUND', 404)


class VsphereManager(object):
    """
    :param vcenter_conn: vcenter connection params 
        {'host':, 'port':, 'user':, 'pwd':, 'verified':False}
    :param nsx_manager_conn: nsx manager connection params 
        {'host':, 'port':443, 'user':'admin', 'pwd':, verified':False, 'timeout':5}
    :param key: [optional] fernet key used to decrypt encrypted password
    """
    TASK_SUCCESS = vim.TaskInfo.State.success
    TASK_ERROR = vim.TaskInfo.State.error
    
    def __init__(self, vcenter_conn=None, nsx_manager_conn=None, key=None):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)
        
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
            pwd = check_vault(vcenter_conn['pwd'], key)

            self.vsphere_id = '%s:%s' % (vcenter_conn['host'], vcenter_conn['port'])
            self._get_vcenter_connection(vcenter_conn['host'],  vcenter_conn['port'], vcenter_conn['user'], pwd,
                                         verified=vcenter_conn['verified'], timeout=vcenter_conn.get('timeout', 30))
        if nsx_manager_conn is not None:
            # check password is encrypted
            pwd = check_vault(nsx_manager_conn['pwd'], key)
            nsx_manager_conn['pwd'] = pwd

            self.nsx_id = '%s:%s' % (nsx_manager_conn['host'], nsx_manager_conn['port'])
            self._get_nsx_manager_connection(nsx_manager_conn['host'], nsx_manager_conn['user'], pwd,
                                             port=nsx_manager_conn['port'], verified=nsx_manager_conn['verified'],
                                             timeout=nsx_manager_conn['timeout'])

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
            'name', 'parent', 'overallStatus',
            'config.hardware.numCPU',
            'config.hardware.memoryMB',
            # 'guest.disk',
            'guest.guestState', 'guest.hostName',
            'guest.ipAddress',
            'guest.net',
            'config.guestFullName', 'config.guestId',
            'config.template',
            'runtime.powerState',
            'layoutEx.file'
        ]
    
    def _get_vcenter_connection(self, host, port, user, pwd, verified=False, timeout=30):
        """"""
        try:
            ctx = None
            socket.setdefaulttimeout(timeout/2)
            try:
                try:
                    ssl._https_verify_certificates(enable=False)
                except:
                    ctx = create_urllib3_context(cert_reqs=ssl.CERT_NONE)
                self.si = connect.SmartConnect(host=host, user=user, pwd=pwd, port=int(port), sslContext=ctx,
                                               connectionPoolTimeout=timeout)
            except:               
                self.si = connect.SmartConnectNoSSL(host=host, user=user, pwd=pwd, port=int(port),
                                                    connectionPoolTimeout=timeout)

            self.vcenter_session = self.si.content.sessionManager.currentSession
            self.logger.info('Connect vcenter %s. Current session id: %s' % ( host, self.vcenter_session.key))
        except vim.fault.NotAuthenticated as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg, code=0)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg, code=0)
        except socket.timeout:
            error = 'timeout after %ss' % timeout
            self.logger.error(error, exc_info=False)
            raise VsphereError(error, code=0)
        except Exception as error:
            self.logger.error(error, exc_info=False)
            raise VsphereError(error, code=0)
        
    def _get_nsx_manager_connection(self, host, user, pwd, port=443, verified=False, timeout=60):
        """Configure nsx https client
        
        :param host: Request host. Ex. 10.102.90.30
        :param port: Request port. [default=80]
        :param timeout: Request timeout. [default=30s]
        :raise VsphereError:
        """
        self.logger.debug('Configure http client for https://%s:%s' %(host, port))

        try:
            if verified is False:
                try:
                    ssl._create_default_https_context = ssl._create_unverified_context
                except: 
                    pass
            
            self.nsx = {'host': host, 'port': port, 'timeout': timeout, 'user': user, 'pwd': pwd, 'etag': None}
        except Exception as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error, code=0)
    
    def disconnect(self):
        """Disconnect vcenter and reset nsx connection"""
        try:
            connect.Disconnect(self.si)
            self.si = None
            self.nsx = None
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg, code=0)
        except Exception as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error, code=0)
        return None

    def get_vcenter_session(self):
        """Get current vcenter session
        """
        self.vcenter_session = None
        try:
            self.vcenter_session = self.si.content.sessionManager.currentSession
            self.logger.info('Current session id: %s' % self.vcenter_session.key)
        except vim.fault.NotAuthenticated as error:
            self.logger.warning(error)
        except vmodl.MethodFault as error:
            self.logger.warning(error)
            # raise VsphereError(error.msg, code=0)
        except Exception as error:
            self.logger.warning(error)
            # raise VsphereError(error, code=0)
        return self.vcenter_session

    def nsx_call(self, path, method, data, headers={}, parse=True, timeout=None):
        """Run nsx https request
        
        :param path: Request path. Ex. /api/
        :param method: Request method. Ex. GET, POST, PUT, DELETE
        :param headers: Request headers. [default={}]. Ex. 
                        {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        :param data: Request data. [default={}]. Ex. {'@number': 12524, '@type': 'issue', '@action': 'show'}
        :param timeout: [defualt=None] optional request timeout
        :raise VsphereError:
        """
        try:
            if timeout is None:
                timeout = self.nsx['timeout']
            
            conn = http_client.HTTPSConnection(self.nsx['host'], self.nsx['port'], timeout=timeout)
            
            # set simple authentication
            auth = base64.encodestring(b'%s:%s' % (b(self.nsx['user']), b(self.nsx['pwd']))).replace(b'\n', b'')
            headers['Authorization'] = 'Basic %s' % auth.decode('utf-8')

            self.logger.info('Send %s request to %s' % (method, path))
            if data.lower().find('password') < 0:
                self.logger.debug('Send [headers=%s] [data=%s]' % (headers, data))
            else:
                self.logger.debug('Send [headers=%s] [data=%s]' % (headers, 'xxxxxxx'))
            
            data = str(data)
            conn.request(method, path, data, headers)
            response = conn.getresponse()
            content_type = response.getheader('content-type')
            self.logger.info('Response status: %s %s' % (response.status, response.reason))
        except Exception as error:
            self.logger.error(error, exc_info=True)
            raise VsphereError(error, code=400)
        
        # evaluate response status
        # BAD_REQUEST     400     HTTP/1.1, RFC 2616, Section 10.4.1
        if response.status == 400:
            res = response.read()
            self.logger.debug('Response [content-type=%s] [data=%s]' % (content_type, res))
            if parse is True and (content_type.find('text/xml') >= 0 or content_type.find('application/xml') >= 0):
                res = xmltodict(res, dict_constructor=dict, attr_prefix='')
                msg = res
                if 'error' in res.keys():
                    res = res.get('error')
                    msg = res
                if 'details' in res.keys():
                    msg = res.get('details')
                if 'rootCauseString' in res.keys():
                    msg += res.get('rootCauseString')
            else:
                msg = ''
                
            self.logger.error('BAD_REQUEST - %s' % msg, exc_info=False)
            raise VsphereError('BAD_REQUEST - %s' % msg, code=400)
  
        # UNAUTHORIZED           401     HTTP/1.1, RFC 2616, Section 10.4.2
        elif response.status == 401:
            self.logger.error('UNAUTHORIZED', exc_info=False)
            raise VsphereError('UNAUTHORIZED', code=401)
        
        # PAYMENT_REQUIRED       402     HTTP/1.1, RFC 2616, Section 10.4.3
        
        # FORBIDDEN              403     HTTP/1.1, RFC 2616, Section 10.4.4
        elif response.status == 403:
            self.logger.error('FORBIDDEN', exc_info=False)
            raise VsphereError('FORBIDDEN', code=403)
        
        # NOT_FOUND              404     HTTP/1.1, RFC 2616, Section 10.4.5
        elif response.status == 404:
            self.logger.error('NOT_FOUND', exc_info=False)
            raise VsphereNotFound()
        
        # METHOD_NOT_ALLOWED     405     HTTP/1.1, RFC 2616, Section 10.4.6
        elif response.status == 405:
            self.logger.error('METHOD_NOT_ALLOWED', exc_info=False)
            raise VsphereError('METHOD_NOT_ALLOWED', code=405)
        # NOT_ACCEPTABLE         406     HTTP/1.1, RFC 2616, Section 10.4.7
        
        # PROXY_AUTHENTICATION_REQUIRED     407     HTTP/1.1, RFC 2616, Section 10.4.8
        
        # REQUEST_TIMEOUT        408
        elif response.status == 408:
            self.logger.error('REQUEST_TIMEOUT', exc_info=False)
            raise VsphereError('REQUEST_TIMEOUT', code=408)

        # CONFLICT        409
        elif response.status == 409:
            res = response.read()
            self.logger.debug('Response [content-type=%s] [data=%s]' % (content_type, res))
            if parse is True and (content_type.find('text/xml') >= 0 or content_type.find('application/xml') >= 0):
                res = xmltodict(res, dict_constructor=dict, attr_prefix='')
                msg = res
                if 'error' in res.keys():
                    res = res.get('error')
                    msg = res
                if 'details' in res.keys():
                    msg = res.get('details')
            else:
                msg = ''

            self.logger.error('CONFLICT - %s' % msg, exc_info=False)
            raise VsphereError('CONFLICT - %s' % msg, code=409)

        # PRECONDITION_FAILED     412
        elif response.status == 412:
            self.logger.error('PRECONDITION_FAILED', exc_info=False)
            raise VsphereError('PRECONDITION_FAILED', code=412)

        # INTERNAL SERVER ERROR  500
        elif response.status == 500:
            self.logger.error('CLOUDAPI_SERVER_ERROR', exc_info=False)
            raise VsphereError('CLOUDAPI_SERVER_ERROR', code=500)        
        
        # OK                     200    HTTP/1.1, RFC 2616, Section 10.2.1
        # CREATED                201    HTTP/1.1, RFC 2616, Section 10.2.2
        # ACCEPTED               202    HTTP/1.1, RFC 2616, Section 10.2.3
        # NON_AUTHORITATIVE_INFORMATION    203    HTTP/1.1, RFC 2616, Section 10.2.4
        # NO_CONTENT             204    HTTP/1.1, RFC 2616, Section 10.2.5
        # RESET_CONTENT          205    HTTP/1.1, RFC 2616, Section 10.2.6
        # PARTIAL_CONTENT        206    HTTP/1.1, RFC 2616, Section 10.2.7
        # MULTI_STATUS           207    WEBDAV RFC 2518, Section 10.2
        elif re.match('20[0-9]+', str(response.status)):
            try:
                res = response.read()
                res_headers = response.getheaders()
                
                # get etag
                self.nsx['etag'] = response.getheader('etag', 0)
                self.nsx['location'] = response.getheader('Location', None)
                
                self.logger.debug('Response [content-type=%s] [headers=%s] [data=%s]' %
                                  (content_type, truncate(res_headers), truncate(res)))
                
                if content_type is not None:
                    # json reqeust
                    if parse is True and content_type.find('application/json') >= 0:
                        res = json.loads(res)
                    elif parse is True and content_type.find('text/xml') >= 0 or \
                         parse is True and content_type.find('application/xml') >= 0:
                        res = xmltodict(res, dict_constructor=dict, attr_prefix='')
                    conn.close()
                else:
                    conn.close()
                return res
            except Exception as error:
                self.logger.error(error, exc_info=False)
                raise VsphereError(error, code=0)
        return None        
    
    # Shamelessly borrowed from:
    # https://github.com/dnaeon/py-vconnector/blob/master/src/vconnector/core.py
    def collect_properties(self, view_ref, obj_type, path_set=None, include_mors=False):
        """Collect properties for managed objects from a view ref.
    
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
        traversal_spec.name = 'traverseEntities'
        traversal_spec.path = 'view'
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
                properties['obj'] = obj.obj
    
            data.append(properties)
        return data
    
    def get_container_view(self, obj_type, container=None):
        """Get a vSphere Container View reference to all objects of type 'obj_type'.
        It is up to the caller to take care of destroying the View when no longer needed.
    
        :param list obj_type: A list of managed object types
        :return: A container view ref to the discovered managed objects
        """
        if not container:
            container = self.si.content.rootFolder

        view_ref = self.si.content.viewManager.CreateContainerView(
            container=container,
            type=obj_type,
            recursive=True
        )
        return view_ref
    
    def get_object(self, morid, obj_type, container=None):
        cont = self.get_container_view(obj_type, container=container)
    
        obj = None
        for view in cont.view:
            if view._moId == morid:
                obj = view
                break
        cont.Destroy()
        return obj
    
    def get_object_by_name(self, name, obj_type, container=None):
        cont = self.get_container_view(obj_type, container=container)
    
        obj = None
        for view in cont.view:
            if view.name == name:
                obj = view
                break
        cont.Destroy()
        return obj

    def get_objects_by_name(self, name, obj_type, container=None):
        cont = self.get_container_view(obj_type, container=container)

        objs = []
        for view in cont.view:
            if view.name.find(name) >= 0:
                objs.append(view)
        cont.Destroy()
        return objs

    def query_nsx_job(self, jobid):
        """Query nsx job
        
        :param jobid: job id
        """
        res = self.nsx_call('/api/2.0/services/taskservice/job/%s' %(jobid), 'GET', '')
        return res

    def wait_task(self, task, delta=1, trace=None):
        self.logger.debug('Monitor task: %s' % task)
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            if trace:
                trace()
            time.sleep(delta)
        
        if task.info.state in [vim.TaskInfo.State.error]:
            self.logger.error('Error: %s' % task.info.error.msg)
        if task.info.state in [vim.TaskInfo.State.success]:
            self.logger.debug('Completed')
    
    def query_task(self, task, wait=None):
        """Query vsphere task.
        
        :param task: vsphere task
        :param wait: wait function to execute in each step of the loop
        :return: vsphere entity instance
        :raises ApiManagerError: raise :class:`.ApiManagerError`
        """
        try:
            # loop until job has finished
            self.logger.debug('Query vsphere task %s - START' % task.info.key)
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                
                # update job status
                self.logger.debug('Query vsphere task %s - RUN: %s' %(task.info.key, task.info.progress))
                if wait is not None:
                    wait()
                
            # vsphere task error
            if task.info.state in [vim.TaskInfo.State.error]:
                self.logger.error('Query vsphere task %s - ERROR - %s' %(task.info.key, task.info.error.msg))
                raise VsphereError('Vsphere task %s failed. Error %s' %(task.info.key, task.info.error.msg))
                                       
            # vsphere task completed
            elif task.info.state in [vim.TaskInfo.State.success]:
                self.logger.debug('Query vsphere task  %s - STOP' % (task.info.key))
                return task.info.result
        except vmodl.MethodFault as ex:
            self.logger.error(ex.msg, exc_info=False)
            raise VsphereError(ex.msg)    
    
    @staticmethod
    def wait_for_tasks(service_instance, tasks):
        """Given the service instance si and tasks, it returns after all the
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
                            if change.name == 'info':
                                state = change.val.state
                            elif change.name == 'info.state':
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


class VsphereObject(object):
    """
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ '.' + self.__class__.__name__)
        
        self.manager = manager
        
    def call(self, path, method, data, headers={}, parse=True, timeout=None):
        if self.manager.nsx is None:
            raise VsphereError('Nsx is not configured')
        else:
            return self.manager.nsx_call(path, method, data, headers=headers, parse=parse, timeout=timeout)

    def get_tags(self, entity):
        """
        """
        try:
            res = [t.key for t in entity.tag]
        except Exception as error:
            self.logger.error(error, exc_info=False)
            res = []
        
        return res

    def assign_tag(self, entity, tag):
        """
        """
        try:
            tag_obj = vim.Tag()
            tag_obj.key = tag
            entity.tag.append(tag_obj)
        except Exception as error:
            self.logger.error(error, exc_info=False)
    
    def remove_tag(self):
        """
        """
        pass
    
    def permissions(self, entity):
        """
        """
        try:
            res = [{'group': p.Group,
                    'principal': p.principal,
                    'propagate': p.propagate,
                    'role': p.roleId
                    } for p in entity.permission]
        except Exception as error:
            self.logger.error(error, exc_info=False)
            res = []
        
        return res
    
    def scheduled_tasks(self):
        """
        """
        pass
    
    def info(self, obj):
        """Get info

        :param server: object obtained from api request
        :return: dict like {'id':.., 'name':..}
        """
        data = {
            'id': obj.get('obj')._moId,
            'parent': obj.get('parent')._moId,
            'name': obj.get('name'),
            'overallStatus': obj.get('overallStatus'),
        }

        return data

    def detail(self, obj):
        """Get detail

        :param obj: object obtained from api request
        :return: dict like {'id':.., 'name':..}
        """
        try:
            info = {
                'id': obj._moId,
                'parent': obj.parent._moId,
                'name': obj.name,
                'overallStatus': obj.overallStatus,
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
            raise VsphereError('key %s is required and can not be None' % key)
        return res

    def xml_set_key(self, parent, kvargs, key, default=None, required=True):
        if required is True:
            et.SubElement(parent, key).text = self.xml_get_kvargs(kvargs, key, default=default, required=required)
        elif required is False and default is not None:
            et.SubElement(parent, key).text = self.xml_get_kvargs(kvargs, key, default=default, required=required)
