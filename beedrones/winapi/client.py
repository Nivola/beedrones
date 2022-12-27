# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from urllib.parse import urlparse
from logging import getLogger
from beecell.perf import watch
# from beecell.beecell.perf import watch
import ssl
import requests
import base64
from xmltodict import parse as xmltodict
import json
import re
import datetime
import winrm
import time
from beecell.simple import truncate, check_vault
# from beecell.beecell.simple import truncate, check_vault
from http import client as httpclient
from beecell.simple import jsonDumps


class WinapiClient(object):
    """ """
    def __init__(self, uri, proxy=None):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        obj = urlparse(uri)
        self.proto = obj.scheme
        self.path = obj.path
        self.host, self.port = obj.netloc.split(':')
        self.port = int(self.port)
        self.proxy = proxy

    @watch
    def call(self, path, method, data='', headers=None, timeout=30, 
             token=None, base_path=None, content_type='application/xml'):
        """Http client. Usage:
            res = http_client2('https', '/api', 'POST',
                                port=443, data='', headers={})        
        
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
        :raise OpenstackError:
        """
        if base_path is not None:
            path = base_path + path
        else:
            path = self.path + path

        http_headers = {}
        # http_headers['Content-Type'] = 'application/json'
        # valori possibili : 'application/json' o 'application/xml'
        http_headers['Content-Type'] = content_type

        # http_headers['Content-Type']='application/xml'
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
            raise WinapiError(ex, 400)
        
        # read response
        try:
            res = response.read()
            res_headers = response.getheaders()
            self.logger.debug('Response data: %s' % truncate(res, 200))
            self.logger.debug('Response headers: %s' % truncate(res_headers, 200))

            if content_type is not None and \
               content_type.find('application/json') >= 0:
                try:
                    print("Sono in call: " + res) #by miko
                    res = json.loads(res)
                except Exception as ex:
                    self.logger.warning(ex)
                    res = res
            conn.close()
        except Exception as ex:
            raise WinapiError(ex, 400)

        # get error messages
        if response.status in [400, 401, 403, 404, 405, 408, 409, 413, 415, 
                               500, 503]:
            try:
                excpt = res.keys()[0]
                res = '%s - %s' % (excpt, res[excpt][u'message'])
            except:
                res = ''            

        # evaluate response status
        # BAD_REQUEST     400     HTTP/1.1, RFC 2616, Section 10.4.1
        if response.status == 400:
            raise WinapiError('Bad Request%s' % res, 400)
  
        # UNAUTHORIZED           401     HTTP/1.1, RFC 2616, Section 10.4.2
        elif response.status == 401:
            raise WinapiError('Unauthorized%s', 401)
        
        # PAYMENT_REQUIRED       402     HTTP/1.1, RFC 2616, Section 10.4.3
        
        # FORBIDDEN              403     HTTP/1.1, RFC 2616, Section 10.4.4
        elif response.status == 403:
            raise WinapiError('Forbidden%s' % res, 403)
        
        # NOT_FOUND              404     HTTP/1.1, RFC 2616, Section 10.4.5
        elif response.status == 404:
            raise WinapiError('Not Found%s' % res, 404)
        
        # METHOD_NOT_ALLOWED     405     HTTP/1.1, RFC 2616, Section 10.4.6
        elif response.status == 405:
            raise WinapiError('Method Not Allowed%s' % res, 405)
        # NOT_ACCEPTABLE         406     HTTP/1.1, RFC 2616, Section 10.4.7
        
        # PROXY_AUTHENTICATION_REQUIRED     407     HTTP/1.1, RFC 2616, Section 10.4.8
        
        # REQUEST_TIMEOUT        408
        elif response.status == 408:
            raise WinapiError('Request timeout%s' % res, 408)
        
        # CONFLICT               409
        elif response.status == 409:
            raise WinapiError('Conflict%s' % res, 409)
            # raise OpenstackError(' conflict', 409)
        
        # Request Entity Too Large          413
        elif response.status == 413:
            raise WinapiError('Request Entity Too Large%s' % res, 413)
        
        # Unsupported Media Type            415
        elif response.status == 415:
            raise WinapiError('Unsupported Media Type%s' % res, 415)
        
        # INTERNAL SERVER ERROR  500
        elif response.status == 500:
            raise WinapiError('Server error%s' % res, 500)
        
        # Service Unavailable  503
        elif response.status == 503:
            raise WinapiError('Service Unavailable%s' % res, 503)
        
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

    def call2(self, path, method, data='', headers=None, timeout=30,
             token=None, base_path=None, content_type='application/xml'):
        """Http client. Usage:
            res = http_client2('https', '/api', 'POST',
                                port=443, data='', headers={})

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
        :raise OpenstackError:
        """
        if base_path is not None:
            path = base_path + path
        else:
            path = self.path + path

        http_headers = {}
        # http_headers['Content-Type'] = 'application/json'
        # valori possibili : 'application/json' o 'application/xml'
        http_headers['Content-Type'] = content_type

        # http_headers['Content-Type']='application/xml'
        if token is not None:
            http_headers['X-RestSvcSessionId'] = token
        if headers is not None:
            http_headers.update(headers)

        self.logger.debug('Send http %s request to %s://%s:%s%s' %
                          (method, self.proto, self.host, self.port, path))

        url = '%s://%s:%s%s' % (self.proto, self.host, self.port, path)
        self.logger.debug('Send headers: %s' % http_headers)
        if data.lower().find('password') < 0:
            self.logger.debug('Send data: %s' % data)
        else:
            self.logger.debug('Send data: XXXXXXXXX')
            self.logger.debug('Send data: %s' % data)
        try:
            # resp=requests.get(f'https://tst-winapi.tstsddc.csi.it:9443/api/v1.0/jobs/status',headers=HEADERS, verify=False)
            # request(method, url, params=None, data=None, headers=None, cookies=None, files=None, auth=None,
            # timeout=None, allow_redirects=True, proxies=None, hooks=None, stream=None, verify=None, cert=None, json=None

            _host = self.host
            _port = self.port
            _headers = http_headers
            proxyDict = None
            if self.proxy is not None:
                _host = self.proxy[0]
                _port = self.proxy[1]
                _headers = {}
                path = "%s://%s:%s%s" % (self.proto, self.host, self.port, path)

                proxyDict = {
                    self.proto: path
                }

                """
                http_proxy  = "http://10.10.1.10:3128"
                https_proxy = "https://10.10.1.11:1080"
                ftp_proxy   = "ftp://10.10.1.10:3128"

                proxyDict = { 
                              "http"  : http_proxy, 
                              "https" : https_proxy, 
                              "ftp"   : ftp_proxy
                            }

                r = requests.get(url, headers=headers, proxies=proxyDict)
                """
            self.logger.debug('Send http %s request to %s' %
                              (method, path))
            self.logger.debug('URL : %s' % url)
            self.logger.debug('HEADERS : %s' % _headers)
            self.logger.debug('Proxies : %s' % proxyDict)
            response = requests.request(method, url, headers=_headers, proxies=proxyDict, verify=False)

            """
            HEADERS = {'Accept': 'application/json'}
            method= 'GET'
            path = 'https://tst-winapi.tstsddc.csi.it:9443/api/v1.0/jobs/status'
            proxies = Null
            esp=requests.get(f'https://tst-winapi.tstsddc.csi.it:9443/api/v1.0/jobs/status',headers=HEADERS, verify=False)
            
            
            """
            content_type = response.headers['Content-Type']
            self.logger.debug('Response status: %s' % response)
            self.logger.debug('Response content-type: %s' % content_type)

        except Exception as ex:
            raise WinapiError(ex, 400)

        # read response
        try:
            res = response.text
            res_headers = response.headers
            self.logger.debug('Response data: %s' % truncate(res, 200))
            self.logger.debug('Response headers: %s' % truncate(res_headers, 200))

            if content_type is not None and \
                    content_type.find('application/json') >= 0:
                try:
                    res = response.json()
                except Exception as ex:
                    self.logger.warning(ex)
                    res = res

        except Exception as ex:
            raise WinapiError(ex, 400)

        # get error messages
        if response.status_code in [400, 401, 403, 404, 405, 408, 409, 413, 415,
                               500, 503]:
            try:
                excpt = res.keys()[0]
                res = '%s - %s' % (excpt, res[excpt][u'message'])
            except:
                res = ''

                # evaluate response status
        # BAD_REQUEST     400     HTTP/1.1, RFC 2616, Section 10.4.1
        if response.status_code == 400:
            raise WinapiError('Bad Request%s' % res, 400)

        # UNAUTHORIZED           401     HTTP/1.1, RFC 2616, Section 10.4.2
        elif response.status_code == 401:
            raise WinapiError('Unauthorized%s', 401)

        # PAYMENT_REQUIRED       402     HTTP/1.1, RFC 2616, Section 10.4.3

        # FORBIDDEN              403     HTTP/1.1, RFC 2616, Section 10.4.4
        elif response.status_code == 403:
            raise WinapiError('Forbidden%s' % res, 403)

        # NOT_FOUND              404     HTTP/1.1, RFC 2616, Section 10.4.5
        elif response.status_code == 404:
            raise WinapiError('Not Found%s' % res, 404)

        # METHOD_NOT_ALLOWED     405     HTTP/1.1, RFC 2616, Section 10.4.6
        elif response.status_code == 405:
            raise WinapiError('Method Not Allowed%s' % res, 405)
        # NOT_ACCEPTABLE         406     HTTP/1.1, RFC 2616, Section 10.4.7

        # PROXY_AUTHENTICATION_REQUIRED     407     HTTP/1.1, RFC 2616, Section 10.4.8

        # REQUEST_TIMEOUT        408
        elif response.status_code == 408:
            raise WinapiError('Request timeout%s' % res, 408)

        # CONFLICT               409
        elif response.status_code == 409:
            raise WinapiError('Conflict%s' % res, 409)
            # raise OpenstackError(' conflict', 409)

        # Request Entity Too Large          413
        elif response.status_code == 413:
            raise WinapiError('Request Entity Too Large%s' % res, 413)

        # Unsupported Media Type            415
        elif response.status_code == 415:
            raise WinapiError('Unsupported Media Type%s' % res, 415)

        # INTERNAL SERVER ERROR  500
        elif response.status_code == 500:
            raise WinapiError('Server error%s' % res, 500)

        # Service Unavailable  503
        elif response.status_code == 503:
            raise WinapiError('Service Unavailable%s' % res, 503)

        # OK                     200    HTTP/1.1, RFC 2616, Section 10.2.1
        # CREATED                201    HTTP/1.1, RFC 2616, Section 10.2.2
        # ACCEPTED               202    HTTP/1.1, RFC 2616, Section 10.2.3
        # NON_AUTHORITATIVE_INFORMATION    203    HTTP/1.1, RFC 2616, Section 10.2.4
        # NO_CONTENT             204    HTTP/1.1, RFC 2616, Section 10.2.5
        # RESET_CONTENT          205    HTTP/1.1, RFC 2616, Section 10.2.6
        # PARTIAL_CONTENT        206    HTTP/1.1, RFC 2616, Section 10.2.7
        # MULTI_STATUS           207    WEBDAV RFC 2518, Section 10.2
        elif re.match('20[0-9]+', str(response.status_code)):
            return res, res_headers

    @watch
    def wait_status(self, href, token):
        self.logger.debug("Wait status for :'%s'" % href)
        status = xmltodict(self.call(href, 'GET', '', '', 30, token, '')[0])['Task']['State']
        while status == 'Running':
            status = xmltodict(self.call(href, 'GET', '', '', 30, token, '')[0])['Task']['State']
            self.logger.debug("Task status :'%s'" % status)
            # time.sleep(0.2)
        return status

        
class WinapiError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)
    
    def __repr__(self):
        return "WinAPI error: %s" % self.value
    
    def __str__(self):
        return "WinAPI error: %s" % self.value


class WinapiManager(object):
    """
    :param winapi_conn: winapi connection params {'host':, 'port':, 'user':,
                                                    'pwd':, 'verified':False}
    """
    @watch
    def __init__(self, winapi_conn=None, key=None):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)

        if winapi_conn is not None:
            """
            host: tst-winapi.tstsddc.csi.it
            proto: https
            port: 9443

            """

            method = 'POST'
            path = '/auth/login'

            self.winapi_uri = winapi_conn['proto'] + '://' + winapi_conn['host'] + ':' + str(winapi_conn['port'])
            self.client = WinapiClient(self.winapi_uri)

            pwd = ''
            # check password is encrypted
            if winapi_conn['pwd'] is not None:
                pwd = check_vault(winapi_conn['pwd'], key)

            stringa_utenza = winapi_conn['user'] + ":" + pwd
            # print("stringa_utenza :%s" % stringa_utenza)
            auth_base64 = base64.b64encode(stringa_utenza.encode('utf8'))
            utenza_base64 = "Basic " + auth_base64.decode('utf8')
            
            headers = {'Authorization': utenza_base64}
            res, heads = self.client.call(path, method, '', headers, 30, None, '')
            # self.logger.debug("response :'%s'" % res)
            # self.logger.debug("headers ")
            # ## by miko
            dict_heads = dict(heads)
            self.winapi_token = dict_heads['X-Restsvctokenid']
            # # self.winapi_token = heads[7][1]
            self.logger.debug("winapi_token :'%s'" % self.winapi_token)

            self.job = WinapiJob(self, self.client)
            self.restore = WinapiRestore(self, self.client)

    @watch
    def ping_veeam(self):
        """Ping veeam server.
        
        :return: True if ping ok, False otherwise
        
        
        """

        try:
            headers = {'X-RestSvcSessionId': self.veeam_token}
            self.logger.debug("Header to send :'%s'" % headers)
            
            conn_uri=self.veeamservice + 'logonSessions'
            self.logger.debug("URI to connect :'%s'" % (conn_uri))
            
            r = requests.get(conn_uri, headers=headers)
            
            if r.status_code == 200:
                self.logger.info("Ping veeam %s : OK"%conn_uri)
                #self.logger.debug("Body : %s"%r.text)
            else:
                self.logger.error("Ping veeam %s : KO ; status_code = %s "%(conn_uri,r.status_code))
                raise WinapiError("Ping veeam %s : KO"%conn_uri,r.status_code)
                return False                             
        except Exception as error:
            return False
        return True

    def get_tasks(self):
        method='GET'        
        path='/api/tasks'
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.client.call(path, method,'','', 30, self.veeam_token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except WinapiError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
    
    def get_task_props(self,taskId):

        method='GET'        
        path='/api/tasks/'+taskId
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.client.call(path, method,'','', 30, self.veeam_token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except WinapiError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
    

class WinapiJob(object):
    
    def __init__(self, winapimanager, winapiclient):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        
        self.token = winapimanager.winapi_token
        self.util = winapiclient
        self.winapi_uri = winapimanager.winapi_uri

    def get_jobs(self):
        """Get all the jobs configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 



        :raise WinapiError
        """
        method = 'GET'
        path = '/api/v1.0/jobs'

        headers = {'Authorization': "Bearer " + self.token}

        try:
            res = self.util.call(path, method, '', headers, 30, self.token, '')
            result = {'status': 'OK', 'status_code': '200', 'data': res[0]}
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, 'data': e.value}

        return result['data']

    def get_jobs_status(self):
        """Get all the jobs configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8



        :raise WinapiError
        """
        method = 'GET'
        path = '/api/v1.0/jobs/status'

        # headers = {'Authorization': "Bearer " + self.token, 'content_type': 'application/json',
        #            'User-Agent': 'python-beedrones'}

        headers = {'Authorization': "Bearer " + self.token}


        try:
            res = self.util.call2(path, method, '', headers, 30, self.token, '')
            result = {'status': 'OK', 'status_code': '200', 'data': '%s' % res[0]}
            # print("Result: %s" % result)
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, 'data': e.value}

        return result['data']

    def get_jobs_id(self, job_id):
        """

        :raise WinapiError
        """
        method = 'GET'
        path = '/api/v1.0/jobs/' + job_id

        headers = {'Authorization': "Bearer " + self.token}

        try:
            res = self.util.call(path, method, '', headers, 30, self.token, '')
            result = {'status': 'OK', 'status_code': '200', 'data': res[0]}
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, u'data': e.value}

        return result['data']

    def get_jobs_id_include(self, job_id):
        """

        :raise WinapiError
        """
        method = 'GET'
        path = '/api/v1.0/jobs/' + job_id + '/includes'

        headers = {'Authorization': "Bearer " + self.token}

        try:
            res = self.util.call(path, method, '', headers, 30, self.token, '')
            result = {'status': 'OK', 'status_code': '200', 'data': res[0]}
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, u'data': e.value}

        return result['data']

    def add_jobs_id_include(self, job_id, json_data):
        """

        :raise WinapiError
        """
        method = 'POST'
        path = '/api/v1.0/jobs/' + job_id + '/includes'

        # headers = {'Authorization': "Bearer " + self.token}
        headers = {'Authorization': "Bearer " + self.token, 'content_type': 'application/json',
                   'User-Agent': 'python-beedrones'}

        try:
            # res = self.util.call(path, method, '', headers, 30, self.token, '')
            res = self.util.call(path, method, jsonDumps(json_data), headers, 30, self.token, '')
            result = {'status': 'OK', 'status_code': '200', 'data': res[0]}
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, u'data': e.value}

        return result['data']

    def start_job(self, job_id):
        """

        :raise WinapiError
        """
        method = 'POST'
        path = '/api/v1.0/jobs/' + job_id + '/start'

        headers = {'Authorization': "Bearer " + self.token}

        try:
            res = self.util.call(path, method, '', headers, 30, self.token, '')
            result = {'status': 'OK', 'status_code': '200', 'data': res[0]}
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, u'data': e.value}

        return result['data']

    def stop_job(self, job_id):
        """

        :raise WinapiError
        """
        method = 'POST'
        path = '/api/v1.0/jobs/' + job_id + '/stop'

        headers = {'Authorization': "Bearer " + self.token}

        try:
            res = self.util.call(path, method, '', headers, 30, self.token, '')
            result = {'status': 'OK', 'status_code': '200', 'data': res[0]}
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, u'data': e.value}

        return result['data']

    def enable_job(self, job_id):
        """

        :raise WinapiError
        """
        method = 'POST'
        path = '/api/v1.0/jobs/' + job_id + '/enable'

        headers = {'Authorization': "Bearer " + self.token}

        try:
            res = self.util.call(path, method, '', headers, 30, self.token, '')
            result = {'status': 'OK', 'status_code': '200', 'data': res[0]}
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, u'data': e.value}

        return result['data']

    def disable_job(self, job_id):
        """

        :raise WinapiError
        """
        method = 'POST'
        path = '/api/v1.0/jobs/' + job_id + '/disable'

        headers = {'Authorization': "Bearer " + self.token}

        try:
            res = self.util.call(path, method, '', headers, 30, self.token, '')
            result = {'status': 'OK', 'status_code': '200', 'data': res[0]}
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, u'data': e.value}

        return result['data']

    def create_job(self, json_data):
        """

        :raise WinapiError
        """
        method = 'POST'
        path = '/api/v1.0/jobs'

        headers = {'Authorization': "Bearer " + self.token, 'content_type': 'application/json'}
        try:
            res = self.util.call(path, method, jsonDumps(json_data), headers, 30, self.token, '')
            # self.logger.debug('BAD_REQUEST ', exc_info=False)
            result = {'status': 'OK', 'status_code': '200', 'data': res[0]}
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, u'data': e.value}

        return result['data']


class WinapiRestore(object):

    def __init__(self, winapimanager, winapiclient):
        self.logger = getLogger(self.__class__.__module__ + \
                                '.' + self.__class__.__name__)

        self.token = winapimanager.winapi_token
        self.util = winapiclient
        self.winapi_uri = winapimanager.winapi_uri

    def vm_restore(self, restore_point_id, json_data):
        """

        :raise WinapiError
        """
        method = 'POST'
        path = '/api/v1.0/vmrestore/' + restore_point_id

        # print("JSON DATA: ", json_data)
        # print(jsonDumps(json_data))

        headers = {'Authorization': "Bearer " + self.token, 'content_type': 'application/json',
                   'User-Agent': 'python-beedrones'}
        try:
            res = self.util.call(path, method, jsonDumps(json_data), headers, 30, self.token, '')
            result = {'status': 'OK', 'status_code': '200', 'data': res[0]}
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, u'data': e.value}

        return result['data']

    def get_vm_restore_points(self, vm_name):
        """

        :raise WinapiError
        """
        method = 'GET'
        path = '/api/v1.0/vmrestorepoints/search/' + vm_name

        # print("JSON DATA: ", json_data)
        # print(jsonDumps(json_data))

        headers = {'Authorization': "Bearer " + self.token, 'content_type': 'application/json',
                   'User-Agent': 'python-beedrones'}
        try:
            res = self.util.call(path, method, '', headers, 30, self.token, '')
            result = {'status': 'OK', 'status_code': '200', 'data': res[0]}
        except WinapiError as e:
            result = {'status': 'ERROR', 'status_code': e.code, u'data': e.value}

        return result['data']


# # Inizio Prove


### winapiConnTest = {'host': 'tst-winapi.tstsddc.csi.it', 'port': '9443',  "proto": "https",
##                  'user': 'xxx@localhost', 'pwd': 'xxx', 'verified': False}
#
#
### conn = WinapiManager(winapiConnTest)
# print(conn.job.get_jobs())
# # print(conn.job.get_jobs_id('6dcb4630-abac-430d-8bc1-090c458cdcc9'))
# # print(conn.job.get_jobs_id_include('6dcb4630-abac-430d-8bc1-090c458cdcc9'))
# #

###json_file = \
###    {"jobname":"_TST_BCK-miko-from-beedronesz",
###     "repositoryName":"NFS-Linux",
###     "entities":[{"ConnHostId": "c1ce2c97-c076-46ab-87ee-04494841e291", "Reference": "vm-96"},
###                 {"ConnHostId": "c1ce2c97-c076-46ab-87ee-04494841e291", "Reference": "vm-2110"}],
###     "description":"prova da postman"
###}
#
###print(conn.job.create_job(json_file))
# json_restore = {"dest_esxi_name":"tst-esx02.tstsddc.csi.it",
#                 "datastore_name":"Datastore_NFS_10.102.189.180",
#                 "folder_name":"admin-tenant-avz714",
#                 "restored_vm_name":"testborg-rst-winapi2",
#                 "source_network_name":"PG_563_DCCTP-tst-mgt",
#                 "target_network_name" : "CP-dvpg-568_tst-FE-internet",
#                 "source_esxi_name" : "tst-mgmt02.tstsddc.csi.it"
#                 }
#
# p = {"dest_esxi_name": "tst-esx02.tstsddc.csi.it",
#      "datastore_name": "Datastore_NFS_10.102.189.180",
#      "folder_name": "admin-tenant-avz714",
#      "restored_vm_name": "testborg-rst-4-3-21",
#      "source_network_name": "PG_563_DCCTP-tst-mgt",
#      "target_network_name": "CP-dvpg-568_tst-FE-internet",
#      "source_esxi_name": "tst-mgmt02.tstsddc.csi.it"}
#
#
# prova = {"dest_esxi_name":"tst-esx02.tstsddc.csi.it",
#             "datastore_name":"Datastore_NFS_10.102.189.180",
#             "folder_name":"admin-tenant-avz714",
#             "restored_vm_name":"testborg-rst-winapi-2230"
#         }
#
# # print(conn.restore.vm_restore('6d42d895-5103-4a33-a3d9-4b75af3c32e4', prova))




