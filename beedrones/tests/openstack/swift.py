# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

import tests.test_util
import gevent
from pyVim import connect
from beedrones.openstack.client import OpenstackManager
from tests.test_util import run_test, CloudapiTestCase
import ujson as json
import unittest
import random
import time
from beecell.simple import transaction_id_generator
from gibboncloudapi.util.data import container
from beecell.simple import jsonDumps

#uri = "http://172.25.5.60:5000/v3"
uri = "http://172.25.3.51:5000/v3"
test_files_url="http://172.25.5.22/testfiles"

domain = 'default'    
user = 'admin'
project = 'admin'
#project = 'demo'
pwd = 'Opstkcs1'
region = 'RegionOne'

client = OpenstackManager(uri=uri, default_region=region)

sid = 'ce1c69c5-b360-4761-9758-5245c758663a'
vid = '4aaef387-96e8-4f98-91e4-bee36c0787fc'
user_id = None
project_id = None


class OpenstackSwiftTestCase(CloudapiTestCase):
    """To execute this test you need an openstack instance.
    """

        
    def test_info(self):
        res = client.swift.info()
        self.logger.debug('Get openstack swift info: %s' % res)


#---------------Accounts------------------
        

    def test_account_read(self):
        res = client.swift.account_read()
        self.logger.debug('Get openstack swift account container list and details: %s' % jsonDumps(res))

    def test_account_metadata_get(self):
        res = client.swift.account_metadata_get()
        self.logger.debug('Get openstack swift account  metadata: %s'%jsonDumps(res))

    
    def test_account_metadata_post(self):
        res = client.swift.account_metadata_post(x_account_meta_name={'prova':'prova',
                                                                      'prova2':''},
                                                 )
        self.logger.debug('Get openstack swift account metadata creation: %s'%jsonDumps(res))



#---------------Containers------------------

    def test_container_read(self):
        container='prova'
        res = client.swift.container_read(container=container)
        self.logger.debug('Get openstack swift container details: %s' % jsonDumps(res))
        
    def test_container_put(self):
        container='prova'
        res = client.swift.container_put(container=container, x_container_meta_name={'meta1':'','meta2':''})
        self.logger.debug('Create openstack swift container %s: %s' % (container, jsonDumps(res)))        

    def test_container_delete(self):
        container='morbido'
        res = client.swift.container_delete(container=container)
        self.logger.debug('Delete openstack swift container %s: %s' % (container, jsonDumps(res)))

    def test_container_metadata_post(self):
        container='prova'
        res = client.swift.container_metadata_post(container=container, x_container_meta_name={'meta1':'container_metadata_post','meta2':'container_metadata_post'})
        self.logger.debug('Create openstack swift container %s: %s' % (container, jsonDumps(res)))        

    def test_container_metadata_get(self):
        container='morbido'
        res = client.swift.container_metadata_get(container=container)
        self.logger.debug('Get openstack swift container details: %s' % jsonDumps(res))

#---------------Objects------------------

    def test_object_get(self):
        container='signaling'
        c_object='29ceecd5-2332-4a46-ba0c-45b486543bc2 '
        res = client.swift.object_get(container=container,c_object=c_object)
        self.logger.debug('Get openstack swift object details: %s' % res)

    def test_object_put(self):
        container='prova'
        c_object='test3'
        res = client.swift.object_put(container=container,
                                      c_object=c_object
                                      #data="Prova test",
                                      #content_type='text/html; charset=UTF-8'
                                      )
        self.logger.debug('Put openstack swift object: %s' % jsonDumps(res))

    def test_object_copy(self):
        container='prova'
        c_object='test3'
        res = client.swift.object_copy(container=container,c_object=c_object,
                                      destination="prova/test4")
        self.logger.debug('Put openstack swift object: %s' % jsonDumps(res))

    def test_object_delete(self):
        container='prova'
        c_object='test3'
        res = client.swift.object_delete(container=container,c_object=c_object)
        self.logger.debug('Delete openstack swift object: %s' % jsonDumps(res))

    def test_object_metadata_get(self):
        container='signaling'
        c_object='50747727-495d-4b94-a0a0-cc472787361d'
        res = client.swift.object_metadata_get(container=container,c_object=c_object)
        self.logger.debug('Get openstack swift object metadata details: %s' % jsonDumps(res))

    def test_object_metadata_post(self):
        container='prova'
        c_object='test4'
        res = client.swift.object_metadata_post(container=container,c_object=c_object,
                                    x_object_meta_name='Metadata name prova',
                                    content_type='text/html; charset=UTF-8')
        self.logger.debug(u'Modify openstack swift object metadata: %s' % jsonDumps(res))


    def test_generate_key(self):
        res = client.swift.generate_key(key='containerkey',container='signaling')
        self.logger.debug(u'Generate openstack swift temp key: %s' % jsonDumps(res))

        
    def test_generate_temp_url(self):
        timeout='300'
        c_object='test'
        method='GET'
        key='containerkey'
        res = client.swift.generate_temp_url(c_object=c_object,
                    timeout=timeout,method=method, key=key)
        self.logger.debug(u'Generate openstack swift temp urls: %s' % res)

    def test_object_put_temp_url(self):
        container='signaling'
        c_object='test'
        res = client.swift.object_put(container=container,c_object=c_object,
                                      data="Prova test2",
                                      content_type='text/html; charset=UTF-8')
        self.logger.debug(u'Put openstack swift object: %s' % jsonDumps(res))

    def test_object_get_temp_url(self):
        container='signaling'
        c_object='test'
        res = client.swift.object_get(container=container,c_object=c_object)
        self.logger.debug(u'Get openstack swift object details: %s' % res)        

#---------------Other Tests------------------
    
    def test_authorize(self):
        #authorize keystone api v3
        res = client.authorize(user, pwd, project=project, domain=domain)
        #authorize keystone api v2
        #res = client.authorize(user, pwd, project=project, version='v2')
        
    def test_release_token(self):
        client.identity.release_token() 
        
def test_suite():
    tests = [
            'test_authorize',
            
            #'test_info',

#--------------Test swift account-----------------------
            
            #'test_account_read',
            #'test_account_metadata_post',
            #'test_account_metadata_get',

#--------------Test swift containers--------------------            
            
            #'test_container_put',
            #'test_container_read',            
            #'test_container_delete',
            #'test_container_metadata_post',
            #'test_container_metadata_get',

#--------------Test swift object--------------------            
            
            'test_object_put',
            #'test_object_get',
            #'test_object_copy',
            #'test_object_delete',
            #'test_object_metadata_post',
            #'test_object_metadata_get', 
            
            #'test_generate_key'
            #'test_generate_temp_url',           
            #'test_object_put_temp_url',
            #'test_object_get_temp_url',
                                    
            #'test_release_token',
            
            ]
    return unittest.TestSuite(map(OpenstackSwiftTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])                  