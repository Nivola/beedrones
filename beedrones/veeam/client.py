# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from urllib.parse import urlparse
from logging import getLogger
from beecell.perf import watch
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
from http import client as httpclient


class VeeamClient(object):
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
            raise VeeamError(ex, 400)
        
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
            raise VeeamError(ex, 400)

        # get error messages
        if response.status in [400, 401, 403, 404, 405, 408, 409, 413, 415, 
                               500, 503]:
            try:
                excpt = res.keys()[0]
                res = '%s - %s' % (excpt, res[excpt][u'message'])
            except:
                res = ''            
            
            '''
            if u'NeutronError' in res.keys():
                res = u' - %s' % res[u'NeutronError'][u'message']
            elif u'badRequest' in res.keys():
                res = u' - %s' % res[u'badRequest'][u'message']
            elif u'computeFault' in res.keys():
                res = u' - %s' % res[u'computeFault'][u'message']
            else:                        
                try:
                    res = ' - %s' % res[u'error'][u'message']
                except:
                    res = ''
            '''
                    
        # evaluate response status
        # BAD_REQUEST     400     HTTP/1.1, RFC 2616, Section 10.4.1
        if response.status == 400:
            raise VeeamError('Bad Request%s' % res, 400)
  
        # UNAUTHORIZED           401     HTTP/1.1, RFC 2616, Section 10.4.2
        elif response.status == 401:
            raise VeeamError('Unauthorized%s', 401)
        
        # PAYMENT_REQUIRED       402     HTTP/1.1, RFC 2616, Section 10.4.3
        
        # FORBIDDEN              403     HTTP/1.1, RFC 2616, Section 10.4.4
        elif response.status == 403:
            raise VeeamError('Forbidden%s' % res, 403)
        
        # NOT_FOUND              404     HTTP/1.1, RFC 2616, Section 10.4.5
        elif response.status == 404:
            raise VeeamError('Not Found%s' % res, 404)
        
        # METHOD_NOT_ALLOWED     405     HTTP/1.1, RFC 2616, Section 10.4.6
        elif response.status == 405:
            raise VeeamError('Method Not Allowed%s' % res, 405)
        # NOT_ACCEPTABLE         406     HTTP/1.1, RFC 2616, Section 10.4.7
        
        # PROXY_AUTHENTICATION_REQUIRED     407     HTTP/1.1, RFC 2616, Section 10.4.8
        
        # REQUEST_TIMEOUT        408
        elif response.status == 408:
            raise VeeamError('Request timeout%s' % res, 408)
        
        # CONFLICT               409
        elif response.status == 409:
            raise VeeamError('Conflict%s' % res, 409)
            # raise OpenstackError(' conflict', 409)
        
        # Request Entity Too Large          413
        elif response.status == 413:
            raise VeeamError('Request Entity Too Large%s' % res, 413)
        
        # Unsupported Media Type            415
        elif response.status == 415:
            raise VeeamError('Unsupported Media Type%s' % res, 415)
        
        # INTERNAL SERVER ERROR  500
        elif response.status == 500:
            raise VeeamError('Server error%s' % res, 500)
        
        # Service Unavailable  503
        elif response.status == 503:
            raise VeeamError('Service Unavailable%s' % res, 503)         
        
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
    
    @watch  
    def wait_status(self,href,token):
        self.logger.debug("Wait status for :'%s'" % href)
        status=xmltodict(self.call(href,'GET','','',30,token,'')[0])['Task']['State']
        while (status == 'Running'):
            status=xmltodict(self.call(href,'GET','','',30,token,'')[0])['Task']['State']
            self.logger.debug("Task status :'%s'" % status)
            #time.sleep(0.2)
        return status

        
class VeeamError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)
    
    def __repr__(self):
        return "VeeamError: %s" % self.value    
    
    def __str__(self):
        return "VeeamError: %s" % self.value


class VeeamManager(object):
    """
    :param veeam_conn: vcenter connection params {'host':, 'port':, 'user':, 
                                                    'pwd':, 'verified':False}
    """
    @watch
    def __init__(self, veeam_conn=None, key=None):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        # print self.__class__.__module__+ '.'+self.__class__.__name__
        
        if veeam_conn is not None:
            
            method = 'POST'
            path = '/api/sessionMngr/?v=v1_2'
            
            self.client = VeeamClient(veeam_conn['uri'])

            self.veeam_uri = veeam_conn['uri']

            # print (veeam_conn['pwd'])

            # check password is encrypted
            if veeam_conn['pwd'] is not None:
                pwd = check_vault(veeam_conn['pwd'], key)

            # print ("Password :%s" % pwd)
            stringa_utenza = veeam_conn['user'] + ":" + pwd
            auth_base64 = base64.b64encode(stringa_utenza)
            utenza_base64 = "Basic " + auth_base64
            
            headers = {'Authorization': utenza_base64}

            res, heads = self.client.call(path,method,'',headers,30,None,'')
            # self.logger.debug("response :'%s'" % res)
            # self.logger.debug("headers ")
            
            self.veeam_token=heads[0][1]
            self.logger.debug("veeam_Token :'%s'" % self.veeam_token)

            # Since we had to call via winrm the veeam server to execute powershell commands
            # we need the host to connect with
            # obj = urlparse(self.veeam_uri)
            # host, port = obj.netloc.split(':')

            # check password is encrypted
            # print (veeam_conn)
            if veeam_conn['veeamsrvpwd'] is not None:
                veeam_srv_pwd = check_vault(veeam_conn['veeamsrvpwd'], key)

            veeam_srv = veeam_conn['veeamsrv']
            veeam_srv_user = veeam_conn['veeamsrvuser']
            # veeam_srv_pwd = veeam_conn['veeamsrvpwd']
            self.winrm_session = winrm.Session(veeam_srv, auth=(veeam_srv_user, veeam_srv_pwd))


            # 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/sessionMngr/?v=v1_2'
            # by sergio self.client = VeeamClient("http://tst-veeamsrv.tstsddc.csi.it:9399") 
            # by sergio self.job = VeeamJob(self, self.client)
            self.jobs = VeeamJob(self, self.client)
            self.jobobjs = VeeamJobIncludes(self, self.client)
            self.replica = VeeamReplica(self, self.client)



            ''' 
            # Examples: List of backup jobs
            
            powershell_list_vbr_command = """add-pssnapin VeeamPSSnapin;  get-vbrjob | fl name, id, jobtype, 
                                                                                                IsScheduleEnabled"""
            ret = self.winrm_session.run_ps(powershell_list_vbr_command)
            
            if ret.status_code:       
                ERRORE = True  
            else:
                str_ret = ret.std_out.split('\r\n')
                for element in str_ret:
                    print (element)            
            '''

            
    
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
                raise VeeamError("Ping veeam %s : KO"%conn_uri,r.status_code)
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
        except VeeamError as e:
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
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
    
        
    
class VeeamJob(object):
    
    def __init__(self, veeammanager,veeamclient):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        
        self.token=veeammanager.veeam_token        
        self.util=veeamclient
        self.veeam_uri=veeammanager.veeam_uri

        self.ji = VeeamJobIncludes(veeammanager, veeamclient)
        #self.ji=veeammanager.jobobjs
         
         
          
             
    def get_jobs(self):
        """Get all the jobs configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :raise VeeamError
        """  
        method='GET'
        path='/api/jobs'
        
        try:   
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0],
                          dict_constructor=dict, attr_prefix='')
            jobs=res['EntityReferences']['Ref']
            risultato = {u'status':u'OK',u'status_code':'200',u'data':jobs}
            self.logger.debug("risultato :'%s'" % risultato)
        
            for item in jobs:
                self.logger.info("Nome %s , UID '%s'  , Href '%s' " % (item['Name'],item['UID'],item['Href']))
                
            
            self.logger.debug("--------------------------------------------------keys: %s " % jobs[0].keys())

        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
        
        return (risultato)

    def wait_for_task(self, href, delta=2, maxtime=180):
        """

        :param href:
        :param delta:
        :param maxtime:
        :return:
        """
        method = 'GET'
        try:
            ciclo = True
            elapsed = 0
            while ciclo:
                res = xmltodict(self.util.call(href, method, '', '', 30, self.token, '')[0])
                time.sleep(delta)
                elapsed += delta
                if res['Task']['State'] != 'Running':
                    ciclo = False

                if elapsed > maxtime:
                    self.logger.error(u"Task-id '%s' is still running after %s s" % (res['Task']['TaskId'], maxtime))
                    raise VeeamError(u"Task-id '%s' is still running after %s s" % (res['Task']['TaskId'], maxtime))

        except VeeamError as e:
            risultato = {u'status': u'ERROR', u'status_code': e.code, u'data': e.value}

        risultato = {u'status': u'OK', u'status_code':200, u'data': res}
        self.logger.debug(risultato)
        return risultato

    def search_job(self, jobName):
        """search the jobname in Veeam Enterprise manager server and returns the href of this job
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :raise VeeamError
        """  
        method='GET'
        path='/api/jobs'
        
        href_trovato="false"
        try:   
            res = xmltodict(self.util.call(path, method, '', '', 30, self.token, '')[0])
            jobs = res['EntityReferences']['Ref']
            self.logger.debug("res todo:'%s'" % jobs)
        
            for item in jobs:
                self.logger.info("Nome %s , UID '%s'  , Href '%s' " % (item['@Name'], item['@UID'], item['@Href']))
                if jobName in item['@Name']:
                    # ho torvato l'href
                    href_trovato= item['@Href']     
                    self.logger.info ("trovato !!!!! : %s" % href_trovato)                               

            self.logger.debug("--------------------------------------------------keys: %s " % jobs[0].keys())

        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
        
        if (href_trovato == "false"):
            # non ho torvato l'href
            # print ("not found")
            risultato = {u'status':u'NOTFOUND',u'status_code':'e.code',u'data':u'job not found'}            
        else:
            risultato = {u'status':u'OK',u'status_code':'200',u'data':href_trovato}
        # 
        self.logger.info (risultato)
        return (risultato)          



    def get_job_props(self,href):        
        """Get the properties of a single job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """  
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='GET'        
        path=path+"?format=Entity"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0],
                          dict_constructor=dict, attr_prefix='')
            self.logger.debug("risultato :'%s'" % res)
            # DEVO VERIFICARE SE RICHIEDO LO STATO DEL BACKUP ESEGUITO O LE PROPRIETA' DEL BACKUP

            #print(res.keys())

            if u'Job' in res.keys():
                    # proprieta' del backup
                    risultato = {u'status': u'OK', u'status_code': '202', u'data': res}
            else:

                if u'BackupJobSession' in (res['BackupJobSessions']).keys():
                    ''' SONO stati eseguiti i job di backup '''
                    #print ("e' presente BackupJobSession")
                    # TO DO: se necessario , Gestire la presenza di un unico job
                    risultato = {u'status': u'OK', u'status_code': '202', u'data': res}
                else:
                    ''' NON sono mai stati eseguiti jobs di backup '''
                    self.logger.error (" NOT FOUND ---> no backup jobs found !!!!!")
                    risultato = {u'status': u'NOTFOUND', u'status_code': '404', u'data': 'no backup jobs found'}

        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
    
    def edit_job(self, href, xml):
        """Edit the properties of a job backup configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        :param XML : properties to modify in an xml format
                    Example :
                    
                    XML='<?xml version="1.0" encoding="utf-8"?>
                    <Job Type="Job"  
                    xmlns="http://www.veeam.com/ent/v1.0" 
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        <JobScheduleOptions>
                            <RetryOptions>
                                <RetryTimes>3</RetryTimes>
                                <RetryTimeout>5</RetryTimeout>
                                <RetrySpecified>true</RetrySpecified>
                            </RetryOptions>        
                            <OptionsDaily Enabled="true">
                                <Kind>Everyday</Kind>
                                <Days>Sunday</Days>
                                <Days>Monday</Days>
                                <Days>Tuesday</Days>
                                <Days>Wednesday</Days>
                                <Days>Thursday</Days>
                                <Days>Friday</Days>
                                <Days>Saturday</Days>
                                <Time>22:00:00.0000000</Time>
                            </OptionsDaily>        
                        </JobScheduleOptions>
                    </Job>'
               
        :raise VeeamError
        """  
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method = 'PUT'
        path = path+"?action=edit"
        self.logger.debug("action  %s "%path)
        
        try:
            res = xmltodict(self.util.call(path, method, xml, '', 30, self.token, '')[0])
            self.logger.debug("risultato :'%s'" % res)
            self.wait_for_task(res['Task']['@Href'])
            risultato = {u'status': u'OK', u'status_code':' 202', u'data': res}
        except VeeamError as e:
            risultato = {u'status': u'ERROR', u'status_code': e.code, u'data': e.value}
                    
        return risultato

    def set_job_schedule(self, href, time, schedule='daily', retrytimes=3, retrytimeout=5, retryspecified='true',
                         day_number_in_month=None,
                         day_of_week=None,
                         months="<Months>January</Months> \
                                        <Months>February</Months> \
                                        <Months>March</Months> \
                                        <Months>April</Months> \
                                        <Months>May</Months> \
                                        <Months>June</Months>\
                                        <Months>July</Months>\
                                        <Months>August</Months>\
                                        <Months>September</Months>\
                                        <Months>October</Months>\
                                        <Months>November</Months>\
                                        <Months>December</Months>\
                                        <DayOfMonth>1</DayOfMonth>",
                         days="<Days>Sunday</Days>\
                                        <Days>Monday</Days>\
                                        <Days>Tuesday</Days>\
                                        <Days>Wednesday</Days>\
                                        <Days>Thursday</Days>\
                                        <Days>Friday</Days>\
                                        <Days>Saturday</Days>"):
        """
        Configure the job schedule for the job specified in the href parameter

        :param href: uri of the job to enable
            (Ex: http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312)
        :param time: time to start the job in the format hh:mm:ss
        :param schedule: schedule type ( daily | selecteddays \ weekdays | monthly ), the default is daily
        :param retrytimes: default 3
        :param retrytimeout: default 5
        :param retryspecified: default true
        :param days: day of the week for scheduling
                in xml-like format (<Days>Sunday</Days><Days>Monday</Days>...<Days>Saturday</Days>)
        :param day_number_in_month: the value can be 'First','Second','Third','Fourth' or 'OnDay'
        :param day_of_week: day of the week for monthly schedule; valuea are 'Sunday','Monday',..,'Saturday'
        :param months: month for monthly scheduling
                in xml-like format (<Months>January</Months><Months>February</Months>...<Months>December</Months>)
        :return:


        Examples:


        daily : set_job_schedule(href, '02:00:00', schedule='daily', day_number_in_month='Second',day_of_week='Monday')
        
        weekdays : set_job_schedule(href, '02:00:00', schedule='weekdays',
                                                     day_number_in_month='Second',
                                                     day_of_week='Monday')

        selecteddays : set_job_schedule(href, '02:00:00', schedule='selecteddays',
                                                    days="<Days>Sunday</Days>/
                                                    <Days>Friday</Days>/
                                                    <Days>Friday</Days>")

        monthly :  set_job_schedule(href, '14:00:00', schedule='monthly',
                                                    day_number_in_month="Third", day_of_week="Wednesday")

        monthly (only some months): set_job_schedule(href, '14:00:00', schedule='monthly',
                                                    day_number_in_month="Third", day_of_week="Wednesday",
                                                    months="<Months>April</Months><Months>July</Months><Months>December</Months>")

        """

        if schedule == "daily":
            xml = """<?xml version="1.0" encoding="utf-8"?>
            <Job Type="Job"   
                xmlns="http://www.veeam.com/ent/v1.0" 
                xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <JobScheduleOptions>
                        <Standart>
                            <RetryOptions>
                                    <RetryTimes>{1}</RetryTimes>
                                    <RetryTimeout>{2}</RetryTimeout>
                                    <RetrySpecified>{3}</RetrySpecified>
                            </RetryOptions>        
                            <OptionsDaily Enabled="true">
                                <Kind>Everyday</Kind>
                                {4}
                                <Time>{0}</Time>
                            </OptionsDaily> 
                            <OptionsMonthly Enabled="false">
                            </OptionsMonthly>           
                        </Standart>
                    </JobScheduleOptions>
                </Job>
            """.format(time, retrytimes, retrytimeout, retryspecified, days)

        if schedule == "selecteddays":
            xml = """<?xml version="1.0" encoding="utf-8"?>
             <Job Type="Job"   
                 xmlns="http://www.veeam.com/ent/v1.0" 
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                     <JobScheduleOptions>
                         <Standart>
                             <RetryOptions>
                                     <RetryTimes>{1}</RetryTimes>
                                     <RetryTimeout>{2}</RetryTimeout>
                                     <RetrySpecified>{3}</RetrySpecified>
                             </RetryOptions>        
                             <OptionsDaily Enabled="true">
                                 <Kind>SelectedDays</Kind>
                                 {4}
                             </OptionsDaily>  
                            <OptionsMonthly Enabled="false">
                            </OptionsMonthly>           
                         </Standart>
                     </JobScheduleOptions>
                 </Job>
             """.format(time, retrytimes, retrytimeout, retryspecified, days)

        if schedule == "weekdays":
            xml = """<?xml version="1.0" encoding="utf-8"?>
            <Job Type="Job"   
                xmlns="http://www.veeam.com/ent/v1.0" 
                xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <JobScheduleOptions>
                        <Standart>
                            <RetryOptions>
                                    <RetryTimes>{1}</RetryTimes>
                                    <RetryTimeout>{2}</RetryTimeout>
                                    <RetrySpecified>{3}</RetrySpecified>
                            </RetryOptions>        
                            <OptionsDaily Enabled="true">
                                <Kind>WeekDays</Kind>
                                {4}
                                <Time>{0}</Time>
                            </OptionsDaily>             
                            <OptionsMonthly Enabled="false">
                            </OptionsMonthly>           
                        </Standart>
                    </JobScheduleOptions>
                </Job>
            """.format(time, retrytimes, retrytimeout, retryspecified, days)

        if schedule == "monthly":
            xml = """<?xml version="1.0" encoding="utf-8"?>
            <Job Type="Job"   
                xmlns="http://www.veeam.com/ent/v1.0" 
                xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <JobScheduleOptions>
                        <Standart>
                            <RetryOptions>
                                    <RetryTimes>{1}</RetryTimes>
                                    <RetryTimeout>{2}</RetryTimeout>
                                    <RetrySpecified>{3}</RetrySpecified>
                            </RetryOptions>        
                            <OptionsDaily Enabled="false">
                            </OptionsDaily>             
                            <OptionsMonthly Enabled="true">
                                <Time>{0}</Time>
                                <DayNumberInMonth>{4}</DayNumberInMonth>
                                <DayOfWeek>{5}</DayOfWeek>
                                {6}
                                <DayOfMonth>1</DayOfMonth>
                            </OptionsMonthly>
                        </Standart>
                    </JobScheduleOptions>
                </Job>
            """.format(time, retrytimes, retrytimeout, retryspecified, day_number_in_month, day_of_week,
                       months)

        res = self.edit_job(href, xml)
        # print res['data']['Task']['@Href']
        # print res['data']['Task'].keys()
        # print res['data']['Task']['State']
        # res1 = self.wait_for_task(res['data']['Task']['@Href'])

        return res

    def enable_job_schedule(self, href, enabled='true'):
        """
        Enable job schedule

        :param href: uri of the job to enable
            (Ex: http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312)
        :param enabled: default = True
        :return:
        """

        xml = """<?xml version="1.0" encoding="utf-8"?>
        <Job Type="Job"   
            xmlns="http://www.veeam.com/ent/v1.0" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <ScheduleConfigured>{0}</ScheduleConfigured>
            </Job>""".format(enabled)
        return self.edit_job(href, xml)

    def disable_job_schedule(self, href):
        """
        Disable job schedule

        :param href: uri of the job to disable
            (Ex: http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312)
        :return:
        """
        return self.enable_job_schedule(href, enabled='false')

    def enable_job(self, href, enabled='true'):
        """
        Enable job

        :param href:
        :param enabled:
        :return:
        """

        xml = """<?xml version="1.0" encoding="utf-8"?>
        <Job Type="Job"   
            xmlns="http://www.veeam.com/ent/v1.0" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <ScheduleEnabled>{0}</ScheduleEnabled>
            </Job>""".format(enabled)
        return self.edit_job(href, xml)

    def disable_job(self, href):
        """
        Disable job

        :param href: uri of the job to disable
            (Ex: http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312)
        :return:
        """
        return self.enable_job(href, enabled='false')

    def start_job(self, href):
        """Start the backup job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """  
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s " % proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"?action=start"
        self.logger.debug("action  %s "%path)
        
        try:
            res = xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)

            res = self.wait_for_task(res['Task']['@Href'])

            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
            self.logger.error(risultato)
                    
        return(risultato)

    def stop_job(self,href):
        """Stop the backup job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """
        obj = urlparse(href)
 
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"?action=stop"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)

    def retry_job(self, href):
        """Retry the backup job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """        
        obj = urlparse(href)
 
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"?action=retry"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)

    def remove_job(self):
        pass

    def get_backups_status(self):
        """Get the status of the backups jobs

             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}]


        :raise VeeamError
        """
        res = self.get_jobs()
        jobbi = res['data']
        elementi = {u'data': []}
        elementi2 = {}
        for job in jobbi:
            Data = "2000-01-01T00:00:00"
            i = 0
            indice = 0
            sessionUID = ''
            hrefindice = ''
            Result = ''
            Stato = ''
            differenza = ""
            FineJob = ''
            # print (job.keys())
            uid = job['@UID']
            urn, veeam, jobs, obj32 = uid.split(':')
            '''
            print ("veeam_uri %s " % self.veeam_uri)
            '''
            href = self.veeam_uri + '/api/jobs/' + obj32 + '/backupSessions?format=Entity'
            #print(u'Href = ' + href)

            res2 = self.get_job_props(href)
            #print(res2[u'status'])
            if res2['status'] == 'OK':
                #print (type((res2['data']['BackupJobSessions']['BackupJobSession'])))
                if not isinstance((res2['data']['BackupJobSessions']['BackupJobSession']), list):
                    # NON e' una LISTA
                    ''' [u'@Href', u'@Type', u'@Name', u'@UID', u'Links', u'JobUid', u'JobName', 
                    u'JobType', u'CreationTimeUTC', u'EndTimeUTC', u'State', u'Result', u'Progress', 
                    u'IsRetry']
                    '''

                    Data = res2['data']['BackupJobSessions']['BackupJobSession'][u'CreationTimeUTC']
                    #print ((res2['data']['BackupJobSessions']['BackupJobSession']).keys())
                    if not u'EndTimeUTC' in (res2['data']['BackupJobSessions']['BackupJobSession']).keys():
                        # job in progress
                        FineJob = u' ---- '
                        differenza = u' ---- '
                    else :
                        FineJob = res2['data']['BackupJobSessions']['BackupJobSession'][u'EndTimeUTC']
                        differenza = datetime.datetime.strptime(FineJob, '%Y-%m-%dT%H:%M:%S.%fZ') - \
                                     datetime.datetime.strptime(Data, '%Y-%m-%dT%H:%M:%S.%fZ')

                    sessionUID = res2['data']['BackupJobSessions']['BackupJobSession']['@UID']
                    hrefindice = res2['data']['BackupJobSessions']['BackupJobSession']['@Href']
                    Stato = res2['data']['BackupJobSessions']['BackupJobSession'][u'State']
                    Result = res2['data']['BackupJobSessions']['BackupJobSession'][u'Result']
                    elementi[u'data'].append(
                        {u'JobName': res2['data']['BackupJobSessions']['BackupJobSession']['JobName'],
                         u'@UID': sessionUID,
                         u'@Href': hrefindice,
                         u'Result': Result,
                         u'State': Stato,
                         u'JobType': res2['data']['BackupJobSessions']['BackupJobSession']['JobType'],
                         u'ElapsedTime': str(differenza),
                         u'CreationTimeUTC': Data,
                         u'EndTimeUTC': FineJob})

                else:
                    # print ("E' una lista")
                    for element in res2['data']['BackupJobSessions']['BackupJobSession']:
                        if (element[u'CreationTimeUTC'] > Data):
                            Data = element[u'CreationTimeUTC']
                            if element[u'State'] == 'Stopped':

                                FineJob = element[u'EndTimeUTC']
                                differenza = datetime.datetime.strptime(FineJob, '%Y-%m-%dT%H:%M:%S.%fZ') - \
                                             datetime.datetime.strptime(Data, '%Y-%m-%dT%H:%M:%S.%fZ')
                            else:
                                FineJob = u' ---- '
                                differenza = u' ---- '

                            sessionUID = element['@UID']
                            hrefindice = element['@Href']
                            indice = i
                            Stato = element[u'State']
                            Result = element[u'Result']
                        i = i + 1
                    elemento = res2['data']['BackupJobSessions']['BackupJobSession'][indice]
                    # print(elemento.keys())
                    elementi[u'data'].append({u'JobName': elemento['JobName'],
                                              u'@UID': sessionUID,
                                              u'@Href': hrefindice,
                                              u'Result': Result,
                                              u'State': Stato,
                                              u'JobType': elemento['JobType'],
                                              u'ElapsedTime': str(differenza),
                                              u'CreationTimeUTC': Data,
                                              u'EndTimeUTC': FineJob})
            else:
                # status == ERROR
                # [u'@UID', u'@Name', u'@Href', u'@Type', u'Links']

                elementi[u'data'].append({u'JobName': job['@Name'],
                                          u'@UID': job['@UID'],
                                          u'@Href': job['@Href'],
                                          u'Result': res2['data'],
                                          u'State': Stato,
                                          u'JobType': job['@Type'],
                                          u'ElapsedTime': u' ---- ',
                                          u'CreationTimeUTC': u' ---- ',
                                          u'EndTimeUTC': u' ---- '})
        #print(elementi)
        risultato = {u'status': u'OK', u'status_code': '200', u'data': elementi[u'data']}
        return (risultato)

    def OLD_create_job(self,tmplName,jobName,repositoryUid,hierarchyObjRef,hierarchyObjName):
        """
            
            In Veeam Enterprise manager server non esiste una API per la creazione di un backup job
            questo metodo quindi non e' una vera e propria create ma un clone da un "template" job noto    
        
            CREATE a new backup job 'href' Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param tmplName : name of the template to clone
        :param jobName : name of the new backup job
        :param repositoryUid : Uid of the repository where to create the folder backup
        :param HierarchyObjRef : The HierarchyObjRefType object describes a specific node 
                                    in the virtual infrastructure hierarchy
        :param hierarchyObjName: the logical name of the HierarchyObjRef
             
        :raise VeeamError
        """  
        
        XML="""<?xml version="1.0" encoding="utf-8"?>
        <JobCloneSpec xmlns="http://www.veeam.com/ent/v1.0" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> 
        <BackupJobCloneInfo> <JobName>{0}</JobName> <FolderName>{0}</FolderName> 
        <RepositoryUid>{1}</RepositoryUid> </BackupJobCloneInfo>
        </JobCloneSpec>""".format(jobName,repositoryUid)
        
        XMLOBJ2ADD="""<?xml version="1.0" encoding="utf-8"?>
                    <CreateObjectInJobSpec xmlns="http://www.veeam.com/ent/v1.0"
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <HierarchyObjRef>{0}</HierarchyObjRef>
                    <HierarchyObjName>{1}</HierarchyObjName>
                    </CreateObjectInJobSpec>""".format(hierarchyObjRef,hierarchyObjName)


        cerca=self.search_job(tmplName)
        
        if (cerca['status']=='OK'):
            # Found job to copy
            risultato=self.clone_job(cerca['data'], XML)
            self.logger.debug("risultato Clone :'%s'" % risultato)
            path=risultato['data']['Task']['@Href']
            self.logger.debug("Task id :'%s'" % path)          
            status=xmltodict(self.util.call(path,'GET','','',30,self.token,'')[0])['Task']['State']
            
            while (status == 'Running'):
                status=xmltodict(self.util.call(path,'GET','','',30,self.token,'')[0])['Task']['State']
                self.logger.debug("Task status Clone :'%s'" % status)
            
            # search new href of the new created job 
            cercanewjob=self.search_job(jobName)
            #print (cercanewjob['data'])
            
            hrefji=cercanewjob['data']+'/includes'
            #self.ji.get_includes('http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/69406254-dec6-487a-a113-9ccea73f31ec')
            #VeeamJobIncludes.get_includes_props("http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/69406254-dec6-487a-a113-9ccea73f31ec")
            #self.ji.get_includes_props()
            #self.ji.get_includes('')
            try:
                res=xmltodict(self.util.call(hrefji, 'GET','','', 30, self.token , '')[0])
                self.logger.debug("risultato :'%s'" % res)
                '''
                risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
                print (risultato)
                print (risultato['data']['ObjectsInJob']['ObjectInJob']['HierarchyObjRef'])
                '''
                ObjInJobId2delete=res['ObjectsInJob']['ObjectInJob']['ObjectInJobId']
                href2delete=hrefji+'/'+ObjInJobId2delete
                #print ("Obj n job 2 delete: %s" %href2delete)
                status=xmltodict(self.util.call(hrefji, 'POST',XMLOBJ2ADD,'', 30, self.token , '')[0])['Task']['State']
                while (status == 'Running'):
                    status=xmltodict(self.util.call(path,'GET','','',30,self.token,'')[0])['Task']['State']
                    self.logger.debug("Task obj in job 2 add:'%s'" % status)
                    time.sleep(0.2)     

                status=xmltodict(self.util.call(href2delete, 'DELETE','','', 30, self.token , '')[0])['Task']['State']
                while (status == 'Running'):
                    status=xmltodict(self.util.call(path,'GET','','',30,self.token,'')[0])['Task']['State']
                    self.logger.debug("Task obj in job 2 add:'%s'" % status)
                    time.sleep(0.2)
                
                risultato={u'status':u'OK',u'status_code':'202',u'data':status}
                
            except VeeamError as e:
                risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
       
        else:
            # Job to copy NOT FOUND ( Template NOT FOUND)
            risultato = cerca
        
        return(risultato)
    
    def create_job(self,tmplName,jobName,repositoryUid,hierarchyObjRef,hierarchyObjName):
        """
            
            In Veeam Enterprise manager server non esiste una API per la creazione di un backup job
            questo metodo quindi non e' una vera e propria create ma un clone da un "template" job noto    
        
            CREATE a new backup job 'href' Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param tmplName : name of the template to clone
        :param jobName : name of the new backup job
        :param repositoryUid : Uid of the repository where to create the folder backup
        :param HierarchyObjRef : The HierarchyObjRefType object describes a specific node 
                                    in the virtual infrastructure hierarchy
        :param hierarchyObjName: the logical name of the HierarchyObjRef

        :raise VeeamError
        """  
        
        XML="""<?xml version="1.0" encoding="utf-8"?>
        <JobCloneSpec xmlns="http://www.veeam.com/ent/v1.0" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> 
        <BackupJobCloneInfo> <JobName>{0}</JobName> <FolderName>{0}</FolderName> 
        <RepositoryUid>{1}</RepositoryUid> </BackupJobCloneInfo>
        </JobCloneSpec>""".format(jobName,repositoryUid)
        
        XMLOBJ2ADD="""<?xml version="1.0" encoding="utf-8"?>
                    <CreateObjectInJobSpec xmlns="http://www.veeam.com/ent/v1.0"
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <HierarchyObjRef>{0}</HierarchyObjRef>
                    <HierarchyObjName>{1}</HierarchyObjName>
                    </CreateObjectInJobSpec>""".format(hierarchyObjRef,hierarchyObjName)


        cerca=self.search_job(tmplName)
        
        if (cerca['status']=='OK'):
            # Found job to copy
            risultato=self.clone_job(cerca['data'], XML)
            self.logger.debug("risultato Clone :'%s'" % risultato)
            path=risultato['data']['Task']['@Href']
            self.logger.debug("Task id :'%s'" % path)          
            
            # wait for task to complete
            status=self.util.wait_status(path,self.token)
            
            # search new href of the new created job 
            cercanewjob=self.search_job(jobName)
            
            hrefji=cercanewjob['data']+'/includes'
            print ("hrefji :%s"%hrefji)
            res=self.ji.get_includes(hrefji)
            print ("res: %s"%res)
            #VeeamJobIncludes.get_includes_props("http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/69406254-dec6-487a-a113-9ccea73f31ec")
            #self.ji.get_includes_props()
            #self.ji.get_includes('')
            try:
                res=xmltodict(self.util.call(hrefji, 'GET','','', 30, self.token , '')[0])
                self.logger.debug("risultato :'%s'" % res)
                ObjInJobId2delete=res['ObjectsInJob']['ObjectInJob']['ObjectInJobId']
                self.logger.debug("Obj in JOB to DELETE :'%s'" % ObjInJobId2delete)
                
                href2delete=hrefji+'/'+ObjInJobId2delete
                
                #print ("Obj n job 2 delete: %s" %href2delete)
                #path=risultato['data']['Task']['@Href']
                
                # add the new obj to job
                path=xmltodict(self.util.call(hrefji, 'POST',XMLOBJ2ADD,'', 30, self.token , '')[0])['Task']['@Href']
                status=self.util.wait_status(path,self.token)
                
                # DELETE the ghost obj from job
                path=xmltodict(self.util.call(href2delete, 'DELETE','','', 30, self.token , '')[0])['Task']['@Href']
                status=self.util.wait_status(path,self.token)

                risultato={u'status':u'OK',u'status_code':'202',u'data':status}
                
            except VeeamError as e:
                risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
       
        else:
            # Job to copy NOT FOUND ( Template NOT FOUND)
            risultato = cerca
        
        return(risultato)
    

    
    def clone_job(self,href,XML):
        """CLONE the backup job 'href' in a new job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job to clone in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        :param XML : properties to modify in an xml format
                    Example :
                    
                    XML='<?xml version="1.0" encoding="utf-8"?>
                    <JobCloneSpec xmlns="http://www.veeam.com/ent/v1.0" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> 
                        <BackupJobCloneInfo> 
                            <JobName>Prova Cloned Job</JobName> 
                            <FolderName>Prova Cloned Job</FolderName> 
                            <RepositoryUid>urn:veeam:Repository:b03eb865-79eb-4450-bc52-48a7472314ca</RepositoryUid> 
                        </BackupJobCloneInfo> 
                    </JobCloneSpec>'
               
        :raise VeeamError
        """  
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"?action=clone"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,XML,'', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
        
    def togglescheduleenabled_job(self,href):
        """Enable/disable the backup job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """        
        obj = urlparse(href)
 
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"?action=toggleScheduleEnabled"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)


class VeeamReplica(object):

    def __init__(self, veeammanager, veeamclient):
        self.logger = getLogger(self.__class__.__module__ + \
                                '.' + self.__class__.__name__)

        self.token = veeammanager.veeam_token
        self.winrm_session = veeammanager.winrm_session
        self.util = veeamclient
        self.veeam_uri = veeammanager.veeam_uri

        self.ji = VeeamJobIncludes(veeammanager, veeamclient)
        self.job = VeeamJob(veeammanager, veeamclient)
        # self.ji=veeammanager.jobobjs

    def get_jobs(self):
        """Get all the jobs configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8

             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}]

        :raise VeeamError
        """
        method = 'GET'
        path = '/api/jobs'

        try:
            res = xmltodict(self.util.call(path, method, '', '', 30, self.token, '')[0])
            jobs = res['EntityReferences']['Ref']
            risultato = {u'status': u'OK', u'status_code': '200', u'data': jobs}
            self.logger.debug("risultato :'%s'" % risultato)

            for item in jobs:
                self.logger.info("Nome %s , UID '%s'  , Href '%s' " % (item['@Name'], item['@UID'], item['@Href']))

            self.logger.debug("--------------------------------------------------keys: %s " % jobs[0].keys())

        except VeeamError as e:
            risultato = {u'status': u'ERROR', u'status_code': e.code, u'data': e.value}

        return(risultato)

    def get_esxi_from_vm(self, vm_name):
        """Get all the jobs configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8

             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}]

        :raise VeeamError
        """
        powershell_replica_command = """\

                add-pssnapin VeeamPSSnapin;
                (Find-VBRViEntity -Name {0}).VmHostName
                """.format(vm_name)
        # {0} = vm_name,

        self.logger.debug("powershell_replica_command=%s", powershell_replica_command)

        ret = self.winrm_session.run_ps(powershell_replica_command)
        # print ret

        if not ret.std_out:
            # has_worked = False
            self.logger.error("VM '%s' not FOUND" % vm_name)
            # response = {u'status': False, u'status_code': 400, u'data': ret.std_err}
            raise VeeamError("VM '%s' not FOUND" % vm_name, 400)
        else:
            # has_worked = True
            self.logger.debug("RESP: VM '%s' is connected to ESXi '%s'" % (vm_name, ret.std_out))
            # response = {u'status': True, u'status_code': 200, u'data': ret.std_out}

        return ret.std_out



    def get_vbrjobs_winrm(self):

        # Examples: List of backup jobs

        powershell_list_vbr_command = """add-pssnapin VeeamPSSnapin;  get-vbrjob | fl name, id, jobtype, 
                                                                                            IsScheduleEnabled"""
        ret = self.winrm_session.run_ps(powershell_list_vbr_command)

        if ret.status_code:
            ERRORE = True
        else:
            # str_ret = ret.std_out.split('\r\n')
            # for element in str_ret:
            #     print (element)
            #

            str_VM_Details_split=ret.std_out.split('\r\n')
            self.logger.debug('str_VM_Details_split :  %s', str_VM_Details_split)

            json_returned = "["
            primo_elemento = 1
            for element in str_VM_Details_split:
                str_element=element.replace(" ", "")
                self.logger.debug(str_element)
                if str_element:
                    elemento = str_element.split(':')
                    if 'Name' in str_element:

                        if primo_elemento:
                            json_2_add = "{'Name':'%s'," % elemento[1]
                            primo_elemento = 0

                        else:
                            json_returned = json_returned[:-1]
                            json_2_add = "},{'Name':'%s'," % elemento[1]

                        json_returned = json_returned + json_2_add
                    else:
                        json_2_add = "'%s':'%s'," % (elemento[0], elemento[1])
                        json_returned = json_returned + json_2_add
            json_returned = json_returned[:-1]
            json_returned = json_returned + "}]"
        self.logger.info ("json_returned : %s" % json_returned)

        return json_returned

    def create_replica_job(self, esxiname, dest_datastore, dest_folder, server_name2replicate, replica_job_name,
                           replica_suffix, description):

        """
        Create a new replica job between two host esxi


        :param esxiname:
        :param dest_datastore:
        :param dest_folder:
        :param server_name2replicate:
        :param replica_job_name:
        :param replica_suffix:
        :param description:
        :return:
        """

        '''
        esxiname = "podto2-vsphere01.site02.nivolapiemonte.it"
        dest_datastore = "SITE02-VSPHERE-VMAX-LUN00"
        dest_folder = "demo_tenant_avz710"
        server_name2replicate = "urbackup(tenant demo)"
        replica_name = "replicajob_urbackup(tenant demo)"
        replica_suffix = "_suffix"
        description = "test replica via api"
        '''

        powershell_replica_command_OLD = """\
        
            add-pssnapin VeeamPSSnapin;
            $server = Get-VBRServer -Type ESXi -Name {0};
            $resourcepool = Find-VBRViResourcePool -Server $server;
            $datastore = Find-VBRViDatastore -Server $server -Name "{1}";
            $folder = Find-VBRViFolder -Server $server -Name "{2}";
            
            Find-VBRViEntity -Name "{3}" | Add-VBRViReplicaJob -Name "{4}" -Server $server -Datastore $datastore -ResourcePool $resourcepool -Folder $folder -Suffix "{5}" -Description "{6}"; """.format(esxiname, dest_datastore, dest_folder, server_name2replicate,
                                                        replica_job_name, replica_suffix, description)

        powershell_replica_command = """\

                add-pssnapin VeeamPSSnapin;
                $server = Get-VBRServer -Type ESXi -Name {0};
                $resourcepool = Find-VBRViResourcePool -Server $server;
                $datastore = Find-VBRViDatastore -Server $server -Name "{1}";
                $folder = Find-VBRViFolder -Server $server -Name "{2}";

                Find-VBRViEntity -Name "{3}" | Add-VBRViReplicaJob -Name "{4}" -Server $server -Datastore $datastore\
                 -Folder $folder -Suffix "{5}" -Description "{6}"; """.format(esxiname, dest_datastore, dest_folder,
                                                                              server_name2replicate, replica_job_name,
                                                                              replica_suffix, description)

        self.logger.debug("powershell_replica_command=%s", powershell_replica_command)
        # {0} = esxiname
        # {1} = dest_datastore,
        # {2} = dest_folder
        # {3} = server_name2replicate
        # {4} = replica_job_name
        # {5} = replica_suffix
        # {6} = description

        ret = self.winrm_session.run_ps(powershell_replica_command)

        if ret.status_code:
            ERRORE = True
            self.logger.error("winrm: %s" % ret.std_err)
            self.logger.error("Error code: %s" % ret.status_code)
        else:
            # str_ret = ret.std_out.split('\r\n')
            # for element in str_ret:
            #     print (element)
            #
            self.logger.debug("RESP: %s" % ret.std_out)

        return

    def create_replica_mapping(self, replica_job_name, description, original_vm, replica_vm):

        """
        Create a new replica job between two host esxi using replica mapping.


        :param replica_job_name: Specifies the name you want to assign to the replication job.
        :param description: Specifies the description of the new job.
        :param original_vm: Specifies the production VM you want to replicate using replica mapping.
                            The replication job will map this VM to a selected replica VM on the DR site.
        :param replica_vm: Specifies the VM on the DR site you want to use as the replication target.
                            The replication job will map the production VM to this VM.
        :return:
        """

        powershell_replica_command = """\

                add-pssnapin VeeamPSSnapin;
                $src_vm =  Find-VBRViEntity -Name  {0};
                $dest_vm =  Find-VBRViEntity -Name  {1};
                Add-VBRViReplicaJob -Name "{2}" -Description "{3}" -Server $dest_vm.VmHostName \
                 -Entity $src_vm -OriginalVM $src_vm -ReplicaVM  $dest_vm; """.format(original_vm,
                                                                                       replica_vm, replica_job_name,
                                                                                       description)
        # {0} = original_vm,
        # {1} = replica_vm
        # {2} = replica_job_name
        # {3} = description

        # print powershell_replica_command

        self.logger.debug("powershell_replica_command=%s", powershell_replica_command)

        ret = self.winrm_session.run_ps(powershell_replica_command)

        if ret.status_code:
            has_worked = False
            self.logger.error("winrm: %s" % ret.std_err)
            self.logger.error("Error code: %s" % ret.status_code)
            # response = {u'status': False, u'status_code': 400, u'data': ret.std_err}
            raise VeeamError("winrm_session.run_ps : %s" % ret.std_err, 400)
        else:
            has_worked = True
            self.logger.debug("RESP: %s" % ret.std_out)
            # response = {u'status': True, u'status_code': 200, u'data': ret.std_out}

        return has_worked

    def set_replica_schedule_old(self, href, time, schedule='daily', retrytimes=3, retrytimeout=5, retryspecified='true',
                             day_number_in_month=None,
                             day_of_week=None,
                             months="<Months>January</Months> \
                                        <Months>February</Months> \
                                        <Months>March</Months> \
                                        <Months>April</Months> \
                                        <Months>May</Months> \
                                        <Months>June</Months>\
                                        <Months>July</Months>\
                                        <Months>August</Months>\
                                        <Months>September</Months>\
                                        <Months>October</Months>\
                                        <Months>November</Months>\
                                        <Months>December</Months>\
                                        <DayOfMonth>1</DayOfMonth>",
                             days="<Days>Sunday</Days>\
                                        <Days>Monday</Days>\
                                        <Days>Tuesday</Days>\
                                        <Days>Wednesday</Days>\
                                        <Days>Thursday</Days>\
                                        <Days>Friday</Days>\
                                        <Days>Saturday</Days>"):
        """
        Set job schedule

        :param href:
        :param time:
        :param schedule:
        :param retrytimes:
        :param retrytimeout:
        :param retryspecified:
        :param days:
        :param day_number_in_month:
        :param day_of_week:
        :param months:
        :return:
        """

        if schedule == "daily":
            xml = """<?xml version="1.0" encoding="utf-8"?>
            <Job Type="Job"   
                xmlns="http://www.veeam.com/ent/v1.0" 
                xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <JobScheduleOptions>
                        <Standart>
                            <RetryOptions>
                                    <RetryTimes>{1}</RetryTimes>
                                    <RetryTimeout>{2}</RetryTimeout>
                                    <RetrySpecified>{3}</RetrySpecified>
                            </RetryOptions>        
                            <OptionsDaily Enabled="true">
                                <Kind>Everyday</Kind>
                                {4}
                                <Time>{0}</Time>
                            </OptionsDaily> 
                            <OptionsMonthly Enabled="false">
                            </OptionsMonthly>           
                        </Standart>
                    </JobScheduleOptions>
                </Job>
            """.format(time, retrytimes, retrytimeout, retryspecified, days)

        if schedule == "selecteddays":
            xml = """<?xml version="1.0" encoding="utf-8"?>
             <Job Type="Job"   
                 xmlns="http://www.veeam.com/ent/v1.0" 
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                     <JobScheduleOptions>
                         <Standart>
                             <RetryOptions>
                                     <RetryTimes>{1}</RetryTimes>
                                     <RetryTimeout>{2}</RetryTimeout>
                                     <RetrySpecified>{3}</RetrySpecified>
                             </RetryOptions>        
                             <OptionsDaily Enabled="true">
                                 <Kind>SelectedDays</Kind>
                                 {4}
                             </OptionsDaily>  
                            <OptionsMonthly Enabled="false">
                            </OptionsMonthly>           
                         </Standart>
                     </JobScheduleOptions>
                 </Job>
             """.format(time, retrytimes, retrytimeout, retryspecified, days)

        if schedule == "weekdays":
            xml = """<?xml version="1.0" encoding="utf-8"?>
            <Job Type="Job"   
                xmlns="http://www.veeam.com/ent/v1.0" 
                xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <JobScheduleOptions>
                        <Standart>
                            <RetryOptions>
                                    <RetryTimes>{1}</RetryTimes>
                                    <RetryTimeout>{2}</RetryTimeout>
                                    <RetrySpecified>{3}</RetrySpecified>
                            </RetryOptions>        
                            <OptionsDaily Enabled="true">
                                <Kind>WeekDays</Kind>
                                {4}
                                <Time>{0}</Time>
                            </OptionsDaily>             
                            <OptionsMonthly Enabled="false">
                            </OptionsMonthly>           
                        </Standart>
                    </JobScheduleOptions>
                </Job>
            """.format(time, retrytimes, retrytimeout, retryspecified, days)

        if schedule == "monthly":

            xml = """<?xml version="1.0" encoding="utf-8"?>
            <Job Type="Job"   
                xmlns="http://www.veeam.com/ent/v1.0" 
                xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <JobScheduleOptions>
                        <Standart>
                            <RetryOptions>
                                    <RetryTimes>{1}</RetryTimes>
                                    <RetryTimeout>{2}</RetryTimeout>
                                    <RetrySpecified>{3}</RetrySpecified>
                            </RetryOptions>        
                            <OptionsDaily Enabled="false">
                            </OptionsDaily>             
                            <OptionsMonthly Enabled="true">
                                <Time>{0}</Time>
                                <DayNumberInMonth>{4}</DayNumberInMonth>
                                <DayOfWeek>{5}</DayOfWeek>
                                {6}
                                <DayOfMonth>1</DayOfMonth>
                            </OptionsMonthly>
                        </Standart>
                    </JobScheduleOptions>
                </Job>
            """.format(time, retrytimes, retrytimeout, retryspecified, day_number_in_month, day_of_week, months)

        res = self.job.edit_job(href, xml)

        return res

    def set_replica_schedule(self, href, time, schedule='daily', retrytimes=3, retrytimeout=5, retryspecified='true',
                             day_number_in_month=None,
                             day_of_week=None,
                             months="<Months>January</Months> \
                                        <Months>February</Months> \
                                        <Months>March</Months> \
                                        <Months>April</Months> \
                                        <Months>May</Months> \
                                        <Months>June</Months>\
                                        <Months>July</Months>\
                                        <Months>August</Months>\
                                        <Months>September</Months>\
                                        <Months>October</Months>\
                                        <Months>November</Months>\
                                        <Months>December</Months>\
                                        <DayOfMonth>1</DayOfMonth>",
                             days="<Days>Sunday</Days>\
                                        <Days>Monday</Days>\
                                        <Days>Tuesday</Days>\
                                        <Days>Wednesday</Days>\
                                        <Days>Thursday</Days>\
                                        <Days>Friday</Days>\
                                        <Days>Saturday</Days>"):

        return self.job.set_job_schedule(href, time, schedule, retrytimes, retrytimeout, retryspecified,
                                          day_number_in_month, day_of_week, months, days)

    def enable_replica_schedule(self, href):
        """

        :param href: uri of the job to enable
            (Ex: http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312)
        :return:
        """
        return self.job.enable_job_schedule(href)

    def disable_replica_schedule(self, href):
        """

        :param href: uri of the job to enable
            (Ex: http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312)
        :return:
        """
        return self.job.disable_job_schedule(href)

    def enable_replica(self, href):
        """

        :param href: uri of the job to enable
            (Ex: http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312)
        :return:
        """
        return self.job.enable_job(href)

    def disable_replica(self, href):
        """

        :param href: uri of the job to enable
            (Ex: http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312)
        :return:
        """
        return self.job.disable_job(href)

    def set_notification_email(self, replica_job_name, email, email_notification='False'):
        """
        Set email notification for the job

        :param replica_job_name:
        :param email:
        :param email_notification:
        :return:
        """

        power_shell_command = """\

            add-pssnapin VeeamPSSnapin;
            Get-VBRJob -Name "{0}" | Set-VBRJobAdvancedNotificationOptions -EmailNotification ${1}\
             -EmailNotificationAddresses "{2}";""".format(replica_job_name, email_notification, email)
        self.logger.debug("power_shell_command=%s", power_shell_command)
        # {0} = replica_job_name
        # {1} = email

        ret = self.winrm_session.run_ps(power_shell_command)

        if ret.status_code:
            ERRORE = True
            self.logger.error("winrm: %s" % ret.std_err)
            self.logger.error("Error code: %s" % ret.status_code)
        else:
            # str_ret = ret.std_out.split('\r\n')
            # for element in str_ret:
            #     print (element)
            #
            self.logger.debug("RESP: %s" % ret.std_out)

        return

    def enable_notification_email(self, replica_job_name, email_notification='True'):
        """
        Set email notification for the job

        :param replica_job_name:
        :param email:
        :param email_notification:
        :return:
        """

        power_shell_command = """\

            add-pssnapin VeeamPSSnapin;
            Get-VBRJob -Name "{0}" | Set-VBRJobAdvancedNotificationOptions -EmailNotification ${1};""".format(
            replica_job_name, email_notification)
        self.logger.debug("power_shell_command=%s", power_shell_command)
        # {0} = replica_job_name
        # {1} = email

        ret = self.winrm_session.run_ps(power_shell_command)

        if ret.status_code:
            ERRORE = True
            self.logger.error("winrm: %s" % ret.std_err)
            self.logger.error("Error code: %s" % ret.status_code)
        else:
            # str_ret = ret.std_out.split('\r\n')
            # for element in str_ret:
            #     print (element)
            #
            self.logger.debug("RESP: %s" % ret.std_out)

        return

    def disable_notification_email(self, replica_job_name):
        """
        Disable email notification for the job

        :param replica_job_name:
        :return:
        """
        return self.enable_notification_email(replica_job_name, email_notification='False')

    def add_replica_network_mapping(self, replica_job_name, source_esxi, source_net, target_esxi, target_net):
        """
        Add network mapping to the replica settings

        :param replica_job_name: name of the replica's job
        :param source_esxi: name of the vmware esxi where the vm to replicate resides
        :param source_net: name of the source network
        :param target_esxi: name of the vmware esxi where the vm is replicated
        :param target_net: name of the target network
        :return:
        """

        # Example:
        # # Get-VBRViServerNetworkInfo -Server $source_esxi | ft Networkname
        # # source net =vxw-dvs-74-virtualwire-25-sid-5002-LS-vxlan-TenantDemo
        #
        # $source_esxi = get-vbrserver -name "tst-esx01.tstsddc.csi.it"
        # $source_net = Get-VBRViServerNetworkInfo -Server $source_esxi | Where-Object { $_.NetworkName -eq "vxw-dvs-74-virtualwire-25-sid-5002-LS-vxlan-TenantDemo" }
        #
        # # target net : vxw-dvs-15-virtualwire-7-sid-15006-LS-vxlan1-tenantDEMO
        # $target_esxi = get-vbrserver -name "podvc-vsphere02.site03.nivolapiemonte.it"
        # $target_net = Get-VBRViServerNetworkInfo -Server  $target_esxi | Where-Object { $_.NetworkName -eq "vxw-dvs-15-virtualwire-7-sid-15006-LS-vxlan1-tenantDEMO" }
        #
        #
        # $replica_job =  Get-VBRJob -Name "replica_gui"
        # Set-VBRViReplicaJob -Job $replica_job -EnableNetworkMapping -SourceNetwork $source_net -TargetNetwork $target_net

        # powershell_replica_command = """\
        # $source_esxi = get-vbrserver -name "{0}";
        # $source_net = Get-VBRViServerNetworkInfo -Server $source_esxi | Where-Object { $_.NetworkName -eq "{1}" };
        # $target_esxi = get-vbrserver -name "{2}";
        # $target_net = Get-VBRViServerNetworkInfo -Server $target_esxi | Where-Object { $_.NetworkName -eq "{3}" }
        # $replica_job =  Get-VBRJob -Name "{4}"
        # Set-VBRViReplicaJob -Job $replica_job -EnableNetworkMapping -SourceNetwork $source_net -TargetNetwork \
        # $target_net""".format(source_esxi, source_net, target_esxi, target_net, replica_job_name)
        # # {0} = source_esxi
        # # {1} = source_net
        # # {2} = target_esxi
        # # {3} = target_net
        # # {4} = replica_job_name

        powershell_replica_command = """\
        add-pssnapin VeeamPSSnapin;
        $source_esxi = get-vbrserver -name %s;
        $source_net = Get-VBRViServerNetworkInfo -Server $source_esxi | Where-Object { $_.NetworkName -eq "%s" };
        $target_esxi = get-vbrserver -name %s;
        $target_net = Get-VBRViServerNetworkInfo -Server $target_esxi | Where-Object { $_.NetworkName -eq "%s" };
        $replica_job =  Get-VBRJob -Name "%s";
        Set-VBRViReplicaJob -Job $replica_job -EnableNetworkMapping -SourceNetwork $source_net -TargetNetwork \
        $target_net""" % (source_esxi, source_net, target_esxi, target_net, replica_job_name)
        # {0} = source_esxi
        # {1} = source_net
        # {2} = target_esxi
        # {3} = target_net
        # {4} = replica_job_name

        self.logger.debug("powershell_replica_command=%s", powershell_replica_command)
        # print powershell_replica_command
        ret = self.winrm_session.run_ps(powershell_replica_command)
        # print ret.std_err


        if ret.status_code:
            # ERRORE = True
            self.logger.error("winrm: %s" % ret.std_err)
            self.logger.error("Error code: %s" % ret.status_code)
        else:
            # str_ret = ret.std_out.split('\r\n')
            # for element in str_ret:
            #     print (element)
            #
            self.logger.debug("RESP: %s" % ret.std_out)

        return

    def add_replica_reiprule(self, replica_job_name, source_ip, target_ip, target_gateway, source_mask='255.255.255.0',
                             target_mask='255.255.255.0', dns="10.103.48.1,10.103.48.2"):
        """

        :param replica_job_name:
        :param source_ip:
        :param target_ip:
        :param target_gateway:
        :param source_mask:
        :param target_mask:
        :param dns:
        :return:
        """

        # $reiprule = New-VBRViReplicaReIpRule -SourceIp 172.16.*.* -SourceMask 255.255.0.0 -TargetIp 172.17.*.*
        #                                       -TargetMask 255.255.0.0 -TargetGateway 172.17.0.1
        #

        # $job = Get-VBRJob -Name "Apache Replication"
        #
        # $reiprule = New-VBRViReplicaReIpRule -SourceIp 172.16.*.* -SourceMask 255.255.0.0 -TargetIp 172.17.*.* -TargetMask 255.255.0.0 -TargetGateway 172.17.0.1
        #
        # Set-VBRViReplicaJob -Job $job -EnableReIp -ReIpRule $reiprule

        powershell_replica_command = """\
            add-pssnapin VeeamPSSnapin;
            $job = Get-VBRJob -Name "{0}";
            $dns = "{6}"
            $new_dns = $dns.split(',')
            $reiprule = New-VBRViReplicaReIpRule -SourceIp {1} -SourceMask {2} -TargetIp {3} -TargetMask {4}\
            -TargetGateway {5} -DNS $new_dns ;
            Set-VBRViReplicaJob -Job $job -EnableReIp -ReIpRule $reiprule
        """.format(replica_job_name, source_ip, source_mask, target_ip, target_mask, target_gateway, dns)
        # {0} = replica_job_name
        # {1} = source_ip
        # {2} = source_mask
        # {3} = target_ip
        # {4} = target_mask
        # {5} = target_gateway
        # {6} = dns

        try:
            self.logger.debug("powershell_replica_command=%s", powershell_replica_command)

            ret = self.winrm_session.run_ps(powershell_replica_command)

            if ret.status_code:
                self.logger.error("winrm: %s" % ret.std_err)
                self.logger.error("Error code: %s" % ret.status_code)
                risultato = {u'status': u'ERROR', u'status_code': ret.status_code, u'data': ret.std_err}
            else:
                # str_ret = ret.std_out.split('\r\n')
                # for element in str_ret:
                #     print (element)
                #
                # print ret.status_code
                self.logger.debug("RESP: %s" % ret.std_out)
                risultato = {u'status': u'OK', u'status_code': ret.status_code, u'data': ret.std_out}

        except VeeamError as e:
            risultato = {u'status': u'ERROR', u'status_code': e.code, u'data': e.value}

        return risultato

    def remove_replica_vm(self, replica_job_name):
        """
        Remove the replicated VM from disk

        :param replica_job_name:
        :return:
        """
        powershell_replica_command = """\
        Get-VBRReplica -Name {0} | Remove-VBRReplica -FromDisk
        """.format(replica_job_name)

        ret = self.winrm_session.run_ps(powershell_replica_command)

        if ret.status_code:
            self.logger.error("winrm: %s" % ret.std_err)
            self.logger.error("Error code: %s" % ret.status_code)
        else:
            # str_ret = ret.std_out.split('\r\n')
            # for element in str_ret:
            #     print (element)
            #
            self.logger.debug("RESP: %s" % ret.std_out)

        return

    def remove_replica(self, replica_job_name):
        """
        Remove the replication job

        :param replica_job_name:
        :return:
        """

        # get href of the job to remove
        href = self.job.search_job(replica_job_name)

        return self.job.remove_job(href)

    def start_replica(self, href):
        """

        :param href: uri of the job to enable
            (Ex: http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/801ab7dd-de71-4cce-89af-467de5e48312)
        :return:
        """
        return self.job.start_job(href)


class VeeamJobIncludes(object):
    """Manage the objects of a backup jobs """        
    
    def __init__(self, veeammanager,veeamclient):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        
        self.token = veeammanager.veeam_token
        self.util = veeamclient
           
    def get_includes(self,href):
        """Get all the includes of the backup job 'href' configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """        
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='GET'        
        path=path+"/includes"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)

    def get_includes_props(self,href):
        """Get the properties of the include 'href' configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """        

        method='GET'        
        path=href
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)

         
    def add_includes(self,href,XML):
        """add a new 'XML' include the backup job 'href' configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job to clone in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        :param XML : properties to modify in an xml format
                    Example :
                    
                XML='<?xml version="1.0" encoding="utf-8"?>
                    <CreateObjectInJobSpec xmlns="http://www.veeam.com/ent/v1.0"
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <HierarchyObjRef>urn:VMware:Vm:7f6b6270-1f3b-4dc6-872f-2d1dfc519c00.vm-1401</HierarchyObjRef>
                    <HierarchyObjName>tst-calamari</HierarchyObjName>
                    </CreateObjectInJobSpec>
                    '
               
        :raise VeeamError
        """  
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"/includes"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,XML,'', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
        
    def delete_includes(self,href):
        """DELETE the include 'href' configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """        

        method='DELETE'        
        path=href
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
        
    

'''


        veeam = {'host':'veeambackup.csi.it', 'port':'9399',
                 'user':'160610555',
                 'pwd':'aaa', 'verified':False}

        
        self.util=VeeamManager(veeam)




'''

# prod 
'''             
veeam = {'host':'veeambackup.csi.it', 'port':'9399',
                 'user':'160610555',
                 'pwd':'aaa', 'verified':False}
   



prova= VeeamManager(veeam)
print(prova.veeam_token)

#get_class_props(VeeamManager)     
'''

# test 
'''
veeamTest = {'host':'tst-veeamsrv.tstsddc.csi.it', 'port':'9399',
                 'user':'Administrator',
                 'pwd':'ccc', 'verified':False}
'''

'''             
veeam = {'host':'veeambackup.csi.it', 'port':'9399',
                 'user':'160610555',
                 'pwd':'aaa', 'verified':False}
'''
veeamProd = {'host':'veeambackup.csi.it', 'port':'9399',
                 'user':'160610555',
                 'pwd':'aaa', 'verified':False}


veeamTest = {'host':'tst-veeamsrv.tstsddc.csi.it', 'port':'9399',
                 'user':'Administrator',
                 'pwd':'ccc', 'verified':False}


#mieijobs=VeeamJob(VeeamManager(veeamTest)).get_jobs()
'''
if mieijobs['status']=='OK' :
    
    print mieijobs['data']['jobs']
else:
    print mieijobs['data']
#print mieijobs.token

#print mieijobs.get_jobs()
'''


