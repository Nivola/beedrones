# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beedrones.tests.test_util import runtest, BeedronesTestCase
import unittest
from beedrones.graphite.client import GraphiteManager

tests = [
    'test_get_vsphere_vm_metrics',
    'test_get_vsphere_host_metrics',
    'test_get_kvm_vm_metrics',
    'test_get_kvm_host_metrics',
    'test_get_vsphere_nodes',
    'test_get_kvm_nodes',
    'test_get_kvm_redhat_nodes',
]


class GraphiteClientTestCase(BeedronesTestCase):
    """
    """
    def setUp(self):
        BeedronesTestCase.setUp(self)
        
        env = 'test'
        config = self.platform.get('graphite').get(env)
        host = config.get('host')
        self.graphite_client = GraphiteManager(host, env)
        
        self.vpshere_host_id = config.get('vpshere_host_id')
        self.vpshere_vm_id = config.get('vpshere_vm_id')
        self.kvm_host_id = config.get('kvm_host_id')
        self.kvm_vm_id = config.get('kvm_vm_id')
        self.minutes = 15
        
    def tearDown(self):
        BeedronesTestCase.tearDown(self)
        
    def test_get_vsphere_vm_metrics(self):
        self.graphite_client.set_search_path('test.vmware.tst-open-graphite')
        res = self.graphite_client.get_virtual_node_metrics('vsphere', self.vpshere_vm_id, self.minutes)
        res = self.graphite_client.format_metrics(self.vpshere_vm_id, res, 'vsphere')
        self.logger.info(self.pp.pformat(res))
        
    def test_get_vsphere_host_metrics(self):
        self.graphite_client.set_search_path('test.vmware.tst-open-graphite')
        res = self.graphite_client.get_physical_node_metrics('vsphere', self.vpshere_host_id, self.minutes)
        res = self.graphite_client.format_metrics(self.vpshere_host_id, res, 'vsphere')
        self.logger.info(self.pp.pformat(res))        
        
    def test_get_kvm_vm_metrics(self):
        self.graphite_client.set_search_path('test.kvm')
        res = self.graphite_client.get_virtual_node_metrics(
            'kvm', self.kvm_vm_id, self.minutes)
        res = self.graphite_client.format_metrics(self.kvm_vm_id, res, 'kvm')
        self.logger.info(self.pp.pformat(res))
        
    def test_get_kvm_host_metrics(self):
        self.graphite_client.set_search_path('test.kvm')
        res = self.graphite_client.get_physical_node_metrics(
            'kvm', self.kvm_host_id, self.minutes)
        res = self.graphite_client.format_metrics(self.kvm_host_id, res, 'kvm')
        self.logger.info(self.pp.pformat(res)) 
        
    def test_get_vsphere_nodes(self):
        self.graphite_client.set_search_path('test.vmware.tst-open-graphite')
        res = self.graphite_client.get_nodes('vsphere')
        self.logger.info(self.pp.pformat(res))
        
    def test_get_kvm_nodes(self):
        self.graphite_client.set_search_path('test.kvm')
        res = self.graphite_client.get_nodes('kvm')
        self.logger.info(self.pp.pformat(res))
        
    def test_get_kvm_redhat_nodes(self):
        self.graphite_client.set_search_path('test.redhat')
        res = self.graphite_client.get_nodes('kvm')
        self.logger.info(self.pp.pformat(res))
        
def test_suite():
    tests = [
        #'test_get_vsphere_vm_metrics',
        #'test_get_vsphere_host_metrics',
        #'test_get_kvm_vm_metrics',
        'test_get_kvm_host_metrics',
        
        #'test_get_vsphere_nodes',
        #'test_get_kvm_nodes',
        #'test_get_kvm_redhat_nodes',
    ]
    return unittest.TestSuite(map(GraphiteClientTestCase, tests))


if __name__ == '__main__':
    runtest(GraphiteClientTestCase, tests)
