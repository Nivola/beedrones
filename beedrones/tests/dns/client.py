# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte

from beedrones.dns.client import DnsManager
from beedrones.tests.test_util import BeedronesTestCase, runtest
import dns.resolver


tests = [
    'test_query_google',
    'test_query_nameservers',
    'test_query_authority',
    'test_add_A',
    'test_query_A',
    'test_add_CNAME',
    'test_query_CNAME',
    'test_delete_CNAME',
    'test_query_CNAME_fail',
    'test_delete_A',
    'test_query_A_fail',
]


class DnsManagerTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()

        env = 'test'
        cls.params = cls.platform.get('dns').get(env)
        cls.client = DnsManager(cls.params.get('serverdns'), zones=[], dnskey=cls.params.get('key'))
        cls.zone = cls.params.get('zones').get('test')

    def tearDown(self):
        BeedronesTestCase.tearDown(self)

    def test_query_google(self):
        answer = dns.resolver.query("google.com", "A")
        for data in answer:
            self.logger.info(data.address)

        answers = dns.resolver.query('google.com', 'TXT')
        self.logger.info(' query qname: %s %s %s' % (answers.qname, ' num ans.', len(answers)))
        for rdata in answers:
            for txt_string in rdata.strings:
                self.logger.info(' TXT: %s' % txt_string)

        answers = dns.resolver.query('mail.google.com', 'CNAME')
        self.logger.info(' query qname: %s %s %s' % (answers.qname, ' num ans.', len(answers)))
        for rdata in answers:
            self.logger.info(' cname target address: %s' % rdata.target)

        answers = dns.resolver.query('google.com', 'SOA')
        self.logger.info('query qname: %s %s %s' % (answers.qname, ' num ans.', len(answers)))
        for rdata in answers:
            self.logger.info(' serial: %s  tech: %s' % (rdata.serial, rdata.rname))
            self.logger.info(' refresh: %s  retry: %s' % (rdata.refresh, rdata.retry))
            self.logger.info(' expire: %s  minimum: %s' % (rdata.expire, rdata.minimum))
            self.logger.info(' mname: %s' % rdata.mname)

    def test_query_nameservers(self):
        zone = 'test.nivolapiemonte.it'
        res = self.client.query_nameservers(zone)
        self.logger.info(res)

    def test_query_authority(self):
        zone = 'test.nivolapiemonte.it'
        res = self.client.query_authority(zone)
        self.logger.info(res)

    def test_add_A(self):
        ip_addr = '10.109.89.78'
        host_name = 'prova'
        res = self.client.add_record_A(ip_addr, host_name, self.zone, ttl=30)
        self.logger.info(res)

    def test_delete_A(self):
        host_name = 'prova'
        res = self.client.del_record_A(host_name, self.zone)
        self.logger.info(res)

    def test_query_A(self):
        host_name = 'prova.' + self.zone
        res = self.client.query_record_A(host_name)
        self.logger.info(res)
        self.assertIsNotNone(list(res.values())[0])

    def test_query_A_fail(self):
        host_name = 'prova.' + self.zone
        res = self.client.query_record_A(host_name)
        self.logger.info(res)
        self.assertIsNone(list(res.values())[0])

    def test_add_CNAME(self):
        host_name = 'prova'
        alias = 'prova2'
        res = self.client.add_record_CNAME(host_name, alias, self.zone, ttl=30)
        self.logger.info(res)

    def test_delete_CNAME(self):
        alias = 'prova2'
        res = self.client.del_record_CNAME(alias, self.zone)
        self.logger.info(res)

    def test_query_CNAME(self):
        alias = 'prova2.' + self.zone
        res = self.client.query_record_CNAME(alias)
        self.logger.info(res)
        self.assertIsNotNone(list(res.values())[0])

    def test_query_CNAME_fail(self):
        alias = 'prova2.' + self.zone
        res = self.client.query_record_CNAME(alias)
        self.logger.info(res)
        self.assertIsNone(list(res.values())[0])


if __name__ == '__main__':
    runtest(DnsManagerTestCase, tests)
