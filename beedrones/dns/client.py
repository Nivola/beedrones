# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte

from copy import deepcopy
from logging import getLogger
import dns.query
import dns.resolver
import dns.tsigkeyring
import dns.update
from dns.tsig import HMAC_MD5

from beecell.simple import check_vault


class DnsError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "DnsError: %s" % self.value

    def __str__(self):
        return "DnsError: %s" % self.value


class DnsNotFound(DnsError):
    def __init__(self):
        DnsError.__init__(self, "NOT_FOUND", 404)


class DnsManager(object):
    """
    :param nameservers: list of nameservers
    :param dnskey: key user for dynamic dns update
    :param key: [optional] fernet key used to decrypt encrypted password
    """

    def __init__(self, nameservers, zones=[], dnskey=None, key=None):
        self.logger = getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        self.nameservers = nameservers
        self.zones = zones
        self.key = None
        if dnskey is not None and isinstance(dnskey, dict):
            for k, v in dnskey.items():
                dnskey[k] = check_vault(v, key)
        self.key = deepcopy(dnskey)

        keyname = next(iter(self.key))
        self.key[keyname] = (HMAC_MD5, self.key[keyname])

    def get_managed_zones(self):
        """Get managed zones

        :return:
        """
        return self.zones

    def add_record_A(self, ip_addr, host_name, domain, ttl=300):
        """Add new record A to a zone

        :return:
        """
        res = {}
        for nameserver in self.nameservers.get("update"):
            try:
                keyring = dns.tsigkeyring.from_text(self.key)
                update = dns.update.Update(domain, keyring=keyring, keyalgorithm=HMAC_MD5)
                update.add(host_name, ttl, "A", ip_addr)
                self.logger.warn(update)
                response = dns.query.tcp(update, nameserver, timeout=30)
                self.logger.debug(
                    "Add record A (%s, %s, %s) to nameserver %s" % (ip_addr, host_name, domain, nameserver)
                )
                res[nameserver] = response.to_text()
            except Exception:
                err = "Record A (%s, %s, %s) can not be added to nameserver %s" % (
                    ip_addr,
                    host_name,
                    domain,
                    nameserver,
                )
                self.logger.error(err, exc_info=True)
                raise DnsError(err)
        return res

    def del_record_A(self, host_name, domain):
        """Delete existing record A from a zone

        :return:
        """
        res = {}
        for nameserver in self.nameservers.get("update"):
            try:
                keyring = dns.tsigkeyring.from_text(self.key)
                update = dns.update.Update(domain, keyring=keyring, keyalgorithm=HMAC_MD5)
                update.delete(host_name, "A")

                response = dns.query.tcp(update, nameserver, timeout=30)
                self.logger.debug("Delete record A (%s, %s) from nameserver %s" % (host_name, domain, nameserver))
                res[nameserver] = response.to_text()
            except Exception:
                err = "Record A (%s, %s) can not be deleted from nameserver %s" % (
                    host_name,
                    domain,
                    nameserver,
                )
                self.logger.error(err, exc_info=True)
                raise DnsError(err)
        return res

    def replace_record_A(self, ip_addr, host_name, domain, ttl=300):
        """Add new record A to a zone

        :return:
        """
        res = {}
        for nameserver in self.nameservers.get("update"):
            try:
                keyring = dns.tsigkeyring.from_text(self.key)
                update = dns.update.Update(domain, keyring=keyring, keyalgorithm=HMAC_MD5)
                update.replace(host_name, ttl, "A", ip_addr)

                response = dns.query.tcp(update, nameserver, timeout=30)
                self.logger.debug(
                    "Replace record A (%s, %s, %s) to nameserver %s" % (ip_addr, host_name, domain, nameserver)
                )
                res[nameserver] = response.to_text()
            except Exception:
                err = "Record A (%s, %s, %s) can not be replaced to nameserver %s" % (
                    ip_addr,
                    host_name,
                    domain,
                    nameserver,
                )
                self.logger.error(err, exc_info=True)
                raise DnsError(err)
        return res

    def query_record_A(self, host_name, timeout=30.0, group="resolver"):
        """Get record A from a zone

        :return:
        """
        res = {}
        for nameserver in self.nameservers.get(group):
            try:
                resolver = dns.resolver.Resolver(configure=False)
                resolver.nameservers = [nameserver]
                resolver.timeout = timeout
                resolver.lifetime = timeout
                data = resolver.resolve(host_name, "A")
                if data:
                    ip_addr = data[0].to_text()
                res[nameserver] = ip_addr
                self.logger.debug("Get record A (%s, %s) by nameserver %s" % (ip_addr, host_name, nameserver))
            except Exception:
                err = "Record A (%s) can not be retrieved by nameserver %s" % (
                    host_name,
                    nameserver,
                )
                self.logger.error(err, exc_info=True)
                res[nameserver] = None
        return res

    def add_record_CNAME(self, host_name, alias, domain, ttl=300):
        """Add new record CNAME to a zone

        :return:
        """
        res = {}
        for nameserver in self.nameservers.get("update"):
            try:
                keyring = dns.tsigkeyring.from_text(self.key)
                update = dns.update.Update(domain, keyring=keyring, keyalgorithm=HMAC_MD5)
                update.add(alias, ttl, "CNAME", host_name)

                response = dns.query.tcp(update, nameserver, timeout=30)
                self.logger.debug(
                    "Add record CNAME (%s, %s, %s) to nameserver %s" % (host_name, alias, domain, nameserver)
                )
                res[nameserver] = response.to_text()
            except Exception:
                err = "Record CNAME (%s, %s, %s) can not be added to nameserver %s" % (
                    host_name,
                    alias,
                    domain,
                    nameserver,
                )
                self.logger.error(err, exc_info=True)
                raise DnsError(err)
        return res

    def del_record_CNAME(self, alias, domain):
        """Delete existing record CNAME from a zone

        :return:
        """
        res = {}
        for nameserver in self.nameservers.get("update"):
            try:
                keyring = dns.tsigkeyring.from_text(self.key)
                update = dns.update.Update(domain, keyring=keyring, keyalgorithm=HMAC_MD5)
                update.delete(alias, "CNAME")

                response = dns.query.tcp(update, nameserver, timeout=30)
                self.logger.debug("Delete record CNAME (%s, %s) from nameserver %s" % (alias, domain, nameserver))
                res[nameserver] = response.to_text()
            except Exception:
                err = "Record CNAME (%s, %s) can not be deleted from nameserver %s" % (
                    alias,
                    domain,
                    nameserver,
                )
                self.logger.error(err, exc_info=True)
                raise DnsError(err)
        return res

    def replace_record_CNAME(self, host_name, alias, domain):
        """Repalce record CNAME in a zone

        :return:
        """
        res = {}
        for nameserver in self.nameservers.get("update"):
            try:
                keyring = dns.tsigkeyring.from_text(self.key)

                update = dns.update.Update(domain, keyring=keyring, keyalgorithm=HMAC_MD5)
                update.replace(host_name, 300, "CNAME", alias)

                response = dns.query.tcp(update, nameserver, timeout=30)
                self.logger.debug(
                    "Replace record CNAME (%s, %s, %s) to nameserver %s" % (host_name, alias, domain, nameserver)
                )
                res[nameserver] = response.to_text()
            except Exception:
                err = "Record CNAME (%s, %s, %s) can not be replaced to nameserver %s" % (
                    host_name,
                    alias,
                    domain,
                    nameserver,
                )
                self.logger.error(err, exc_info=True)
                raise DnsError(err)
        return res

    def query_record_CNAME(self, host_name, timeout=30.0, group="resolver"):
        """Get record CNAME from a zone

        :return:
        """
        res = {}
        for nameserver in self.nameservers.get(group):
            try:
                resolver = dns.resolver.Resolver(configure=False)
                resolver.nameservers = [nameserver]
                resolver.timeout = timeout
                resolver.lifetime = timeout
                data = resolver.resolve(host_name, "CNAME")
                if data:
                    ip_addr = data[0].to_text()
                res[nameserver] = ip_addr
                self.logger.debug("Get record CNAME (%s, %s) by nameserver %s" % (ip_addr, host_name, nameserver))
            except Exception:
                err = "Record CNAME (%s) can not be retrieved by nameserver %s" % (
                    host_name,
                    nameserver,
                )
                self.logger.error(err, exc_info=True)
                res[nameserver] = None
        return res

    def query_nameservers(self, domain, timeout=30.0, group="resolver"):
        """Query nameservers

        :return:
        """
        res = {}
        for nameserver in self.nameservers.get(group):
            try:
                resolver = dns.resolver.Resolver(configure=False)
                resolver.nameservers = [nameserver]
                resolver.timeout = timeout
                resolver.lifetime = timeout
                answer = resolver.resolve(domain, "NS")
                data = []
                for rr in answer:
                    try:
                        ip_addr = resolver.resolve(rr.to_text(), "A")[0].to_text()
                    except Exception:
                        ip_addr = None
                    data.append((ip_addr, rr.to_text()))
                res[nameserver] = data
                self.logger.debug("Get record NS for domain %s by nameserver %s" % (domain, nameserver))
            except:
                err = "Record NS for domain %s can not be retrieved by nameserver %s" % (domain, nameserver)
                self.logger.error(err, exc_info=True)
                res[nameserver] = None
        return res

    def query_authority(self, domain, timeout=30.0, group="resolver"):
        """Query authority

        :return:
        """
        res = {}
        for nameserver in self.nameservers.get(group):
            try:
                resolver = dns.resolver.Resolver(configure=False)
                resolver.nameservers = [nameserver]
                resolver.timeout = timeout
                resolver.lifetime = timeout
                answer = resolver.resolve(domain, "SOA")
                data = []
                for rr in answer:
                    data.append(
                        {
                            "expire": rr.expire,
                            "minimum": rr.minimum,
                            "mname": rr.mname.to_text(),
                            "refresh": rr.refresh,
                            "retry": rr.retry,
                            "rname": rr.rname.to_text(),
                            "serial": rr.serial,
                        }
                    )
                res[nameserver] = data[0]
                self.logger.debug("Get record SOA for domain %s by nameserver %s" % (domain, nameserver))
            except Exception:
                err = "Record SOA for domain %s can not be retrieved by nameserver %s" % (domain, nameserver)
                self.logger.error(err, exc_info=True)
                res[nameserver] = None
        return res
