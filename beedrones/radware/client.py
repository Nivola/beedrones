# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from logging import getLogger
from beecell.perf import watch
import ssl
import base64
import re
from beecell.simple import truncate
from urllib.parse import urlparse
from http import client as httpclient


class RadwareClient(object):
    """ """

    def __init__(self, uri, proxy=None):
        self.logger = getLogger(self.__class__.__module__ + '.'+self.__class__.__name__)

        obj = urlparse(uri)

        self.proto = obj.scheme
        self.path = obj.path
        self.host, self.port = obj.netloc.split(':')
        self.port = int(self.port)
        self.proxy = proxy

    @watch
    def call(self, path, method, data='', headers=None, timeout=30, token=None, base_path=None,
             content_type='application/xml'):
        """Http client. Usage:
            res = http_client2('https', '/api', 'POST', port=443, data='', headers={})
        
        :param path: Request path. Ex. /api/
        :param method: Request method. Ex. GET, POST, PUT, DELETE
        :param headers: Request headers. [default={}]. Ex. 
                        {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        :param data: Request data. [default={}]. Ex. 
                       {'@number': 12524, '@type': 'issue', '@action': 'show'}
        :param timeout: Request timeout. [default=30s]
        :param token: Openstack authorization token [optional]
        :param base_path: base path that replace defualt path set initially
        :param content_type: acepted value 'application/json' o 'application/xml' default = 'application/xml'
        """
        if base_path is not None:
            path = base_path + path
        else:
            path = self.path + path
        
        http_headers = {}
        #http_headers['Content-Type'] = 'application/json'
        # valori possibili : 'application/json' o 'application/xml'
        http_headers['Content-Type']=content_type
            
        
        #http_headers['Content-Type']='application/xml'
        if token is not None:
            http_headers['X-RestSvcSessionId'] = token
        if headers is not None:
            http_headers.update(headers)
        
        self.logger.debug('Send http %s request to %s://%s:%s%s' % 
                          (method, self.proto, self.host, self.port, path))
        self.logger.debug('Send headers: %s' % http_headers)
        if data.lower().find('password') < 0:
            self.logger.debug('Send data: %s' % data)
        else:
            self.logger.debug('Send data: XXXXXXXXX')
            self.logger.debug('Send data: %s' % data)
        try:
            _host = self.host
            _port = self.port
            _headers = http_headers
            if self.proxy is not None:
                _host = self.proxy[0]
                _port = self.proxy[1]
                _headers = {}
                path = "%s://%s:%s%s" % (self.proto, self.host, self.port, path)
            
            if self.proto == 'http':       
                conn = httpclient.HTTPConnection(_host, _port, timeout=timeout)
            else:
                try:
                    ssl._create_default_https_context = ssl._create_unverified_context
                except:
                    pass
                conn = httpclient.HTTPSConnection(_host, _port, timeout=timeout)

            if self.proxy is not None:
                conn.set_tunnel(self.host, port=self.port, headers=headers)
                self.logger.debug("set proxy %s" % self.proxy)
                headers = None

            conn.request(method, path, data, _headers)
            response = conn.getresponse()
            content_type = response.getheader('content-type')
            self.logger.debug('Response status: %s' % response.status)
            self.logger.debug('Response content-type: %s' % content_type)
        except Exception as ex:
            raise RadwareError(ex, 400)
        
        # read response
        try:
            res = response.read()
            res_headers = response.getheaders()
            self.logger.debug('Response data: %s' % truncate(res, 200))
            self.logger.debug('Response headers: %s' % truncate(res_headers, 200))
            if content_type is not None and \
               content_type.find('application/json') >= 0:
                try:
                    res = json.loads(res)
                except Exception as ex:
                    self.logger.warn(ex)
                    res = res
            conn.close()
        except Exception as ex:
            raise RadwareError(ex, 400)

        # get error messages
        if response.status in [400, 401, 403, 404, 405, 408, 409, 413, 415, 500, 503]:
            try:
                excpt = res.keys()[0]
                res = '%s - %s' % (excpt, res[excpt][u'message'])
            except:
                res = ''            
            
        # evaluate response status
        # BAD_REQUEST     400     HTTP/1.1, RFC 2616, Section 10.4.1
        if response.status == 400:
            raise RadwareError('Bad Request%s' % res, 400)
  
        # UNAUTHORIZED           401     HTTP/1.1, RFC 2616, Section 10.4.2
        elif response.status == 401:
            raise RadwareError('Unauthorized%s', 401)
        
        # PAYMENT_REQUIRED       402     HTTP/1.1, RFC 2616, Section 10.4.3
        
        # FORBIDDEN              403     HTTP/1.1, RFC 2616, Section 10.4.4
        elif response.status == 403:
            raise RadwareError('Forbidden%s' % res, 403)
        
        # NOT_FOUND              404     HTTP/1.1, RFC 2616, Section 10.4.5
        elif response.status == 404:
            raise RadwareError('Not Found%s' % res, 404)
        
        # METHOD_NOT_ALLOWED     405     HTTP/1.1, RFC 2616, Section 10.4.6
        elif response.status == 405:
            raise RadwareError('Method Not Allowed%s' % res, 405)
        # NOT_ACCEPTABLE         406     HTTP/1.1, RFC 2616, Section 10.4.7
        
        # PROXY_AUTHENTICATION_REQUIRED     407     HTTP/1.1, RFC 2616, Section 10.4.8
        
        # REQUEST_TIMEOUT        408
        elif response.status == 408:
            raise RadwareError('Request timeout%s' % res, 408)
        
        # CONFLICT               409
        elif response.status == 409:
            raise RadwareError('Conflict%s' % res, 409)
            # raise OpenstackError(' conflict', 409)
        
        # Request Entity Too Large          413
        elif response.status == 413:
            raise RadwareError('Request Entity Too Large%s' % res, 413)
        
        # Unsupported Media Type            415
        elif response.status == 415:
            raise RadwareError('Unsupported Media Type%s' % res, 415)
        
        # INTERNAL SERVER ERROR  500
        elif response.status == 500:
            raise RadwareError('Server error%s' % res, 500)
        
        # Service Unavailable  503
        elif response.status == 503:
            raise RadwareError('Service Unavailable%s' % res, 503)         
        
        # OK                     200    HTTP/1.1, RFC 2616, Section 10.2.1
        # CREATED                201    HTTP/1.1, RFC 2616, Section 10.2.2
        # ACCEPTED               202    HTTP/1.1, RFC 2616, Section 10.2.3
        # NON_AUTHORITATIVE_INFORMATION    203    HTTP/1.1, RFC 2616, Section 10.2.4
        # NO_CONTENT             204    HTTP/1.1, RFC 2616, Section 10.2.5
        # RESET_CONTENT          205    HTTP/1.1, RFC 2616, Section 10.2.6
        # PARTIAL_CONTENT        206    HTTP/1.1, RFC 2616, Section 10.2.7
        # MULTI_STATUS           207    WEBDAV RFC 2518, Section 10.2
        elif re.match('20[0-9]+', str(response.status)):
            return res, res_headers

class RadwareError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)
   
    def __repr__(self):
        return "RadwareError: %s" % self.value
   
    def __str__(self):
        return "RadwareError: %s" % self.value
    
class RadwareManager(object):

    """
    radware_conn :
        radwareTest = {'uriRadware':'https://10.138.176.90:443',
                 'user':'admin',
                 'pwd':'admin',
                 'verified':False}

    """
    @watch
    def __init__(self, radware_conn=None):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        if radware_conn is not None:
            method='GET'
            path='/monitor?prop=agApplyPending,agSavePending,agSyncNeeded,vrrpInfoHAState'

            self.client=RadwareClient(radware_conn['uri'])

            self.radware_uri=radware_conn['uri']

            # check password is encrypted
            stringaUtenza = radware_conn['user'] + ":" + radware_conn['pwd']
            auth_base64=base64.b64encode(stringaUtenza)
            utenza_base64="Basic " + auth_base64

            headers = {'Authorization': utenza_base64}

            self.headers=headers
            res,heads=self.client.call(path,method,'',headers,30,None,'')

class RadwareStatus(object):
    
    def __init__(self, radwaremanager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
              
        self.util=radwaremanager.client
        self.radware_uri=radwaremanager.radware_uri
        self.headers=radwaremanager.headers


    def get_slb(self):
        """Get all radware slb table
            the result will be a DICT 
            
             risultato ={u'SlbOperEnhRealServerTable': [{u'Status': 1, u'Index': u'api-pod1'}, {u'Status': 1, u'Index': u'api-pod2'}, {u'Status': 1, u'Index': u'api-pod3'}, {u'Status': 1, u'Index': u'doc-pod1'}, {u'Status': 1, u'Index': u'doc-pod2'}, {u'Status': 1, u'Index': u'doc-pod3'}, {u'Status': 1, u'Index': u'portal-pod1'}, {u'Status': 1, u'Index': u'portal-pod2'}, {u'Status': 1, u'Index': u'portal-pod3'}]}
        
        :raise RadwareError
        """  
        method='GET'
        path='/config/SlbOperEnhRealServerTable'
        #print self.headers 
        try:   
            risultato, heads=self.util.call(path,method,'',self.headers ,30,None,'')
            self.logger.debug("risultato :'%s'" % risultato)
        except RadwareError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
        
        return (risultato)          




    def get_vrrp(self):
        """Get radware vrrp table
            the result will be a DICT 
            
             risultato = {u'VrrpNewCfgVirtRtrTable': [{u'Ipv6Interval': 100, u'DeleteStatus': 1, u'Addr': u'84.1.2.3', u'xxx': 2, u'TckVlanPort': 2, u'TckHsrv': 2, u'Priority': 101, u'State': 1, u'Version': 1, u'Sharing': 2, u'TckVirtRtr': 2, u'Interval': 1, u'Indx': 1024, u'TckIpIntf': 2, u'TckIslPort': -1, u'ID': 1024, u'Preempt': 1, u'TckRServer': 2, u'TckSwExt': -1, u'OspfCost': 0, u'IfIndex': 1, u'Ipv6Addr': None, u'TckL4Port': 2}]}
        
        :raise RadwareError
        """  
        method='GET'
        path='/config/VrrpNewCfgVirtRtrTable'
        #print self.headers 
        try:   
            risultato, heads=self.util.call(path,method,'',self.headers ,30,None,'')
            self.logger.debug("risultato :'%s'" % risultato)
        except RadwareError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
        
        return (risultato)          




    def get_sync(self):
        """Get radware sync table
            the result will be a DICT 
            
             risultato = {u'AgLastSyncInfoTable': [{u'LastSyncFailReason': None, u'LastSyncPeerIp': u'84.1.2.3', u'LastSyncTime': u'14:51:42 Thu Oct 18, 2018', u'LastSyncType': 2, u'LastSyncStatus': 3, u'LastSyncInfoIdx': 1, u'LastSuccessfulSyncType': 2, u'LastSuccessfulSyncTime': u'14:51:42 Thu Oct 18, 2018'}]}
        
        :raise RadwareError
        """  
        method='GET'
        path='/config/AgLastSyncInfoTable'
        #print self.headers 
        try:   
            risultato, heads=self.util.call(path,method,'',self.headers ,30,None,'')
            self.logger.debug("risultato :'%s'" % risultato)
        except RadwareError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
        
        return (risultato)          

    def get_ha_status(self):
        """Get radware high availability status
            the result will be a DICT 
            
             risultato = {u'vrrpInfoHAState': u'ACTIVE'}
        
        :raise RadwareError
        """  
        method='GET'
        path='/monitor?prop=vrrpInfoHAState'
        #print self.headers 
        try:   
            risultato, heads=self.util.call(path,method,'',self.headers ,30,None,'')
            self.logger.debug("risultato :'%s'" % risultato)
        except RadwareError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
        
        return (risultato)          
