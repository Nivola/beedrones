# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
import datetime
import pickle
from logging import getLogger
from beecell.db.manager import parse_redis_uri, RedisManager
from uuid import UUID
from paramiko import DSSKey, ECDSAKey, RSAKey
from paramiko.ssh_exception import SSHException
from base64 import b64encode, b64decode
from six import StringIO, ensure_binary

from typing import Optional, List, Mapping, Union, Dict, Tuple


def time_bound(method):
    def inner(ref, *args, **kwargs):
        from gevent import Timeout
        res = None
        timeout = Timeout(getattr(ref, 'gw_timeout', 30))
        timeout.start()
        try:
            res = method(ref, *args, **kwargs)
        finally:
            timeout.close()
        return res

    return inner


class SshGwError(Exception):
    def __init__(self, value, code=400):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return 'SshGwError: %s' % self.value

    def __str__(self):
        return '%s' % self.value


class SshGwEntity(object):

    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)
        self.manager = manager
        self.next = None


class SshGwUtils(object):

    @staticmethod
    def is_valid_uuid(uuid_to_test, version=4) -> bool:
        """Check if uuid_to_test is a valid UUID.
        :params:
        uuid_to_test : str
        version : {1, 2, 3, 4}
        :return `True` if uuid_to_test is a valid UUID, otherwise `False`.
        """
        try:
            uuid_obj = UUID(uuid_to_test, version=version)
        except ValueError:
            return False
        return str(uuid_obj) == uuid_to_test

    @staticmethod
    def generate_keys(alg_type='rsa', bits=2048) -> Tuple[bytes, bytes]:
        """Create key pair
        :param alg_type: For new key specify type like rsa, dsa. Use for new key when priv_key is None [default=rsa]
        :param bits: For new key specify bits like 2048. Use with type [default=2096]
        :return: keys as tuple
        """
        # create new private e public key pair
        key_dispatch_table = {'dsa': DSSKey, 'rsa': RSAKey, 'ECDSA': ECDSAKey}

        if alg_type not in key_dispatch_table:
            raise SSHException('Unknown %s algorithm to generate keys pair' % alg_type)

        # generating private key
        prv = key_dispatch_table[alg_type].generate(bits=bits)
        file_obj = StringIO()
        prv.write_private_key(file_obj)
        priv_key = b64encode(ensure_binary(file_obj.getvalue()))
        file_obj.close()

        # get public key
        ssh_key = '%s %s' % (prv.get_name(), prv.get_base64())
        pub_key = b64encode(ensure_binary(ssh_key))

        #print(b64decode(priv_key).decode('utf-8')) # str
        #import binascii
        #print(binascii.a2b_base64(priv_key).decode('utf-8')) # str ?
        return pub_key, priv_key # base64 bytes


class SshGwManager(object):

    def __init__(self, gw_hosts: List[str], gw_port: int, gw_user: str, gw_pwd: str,
                 redis_manager: Optional[RedisManager], redis_uri: Optional[str], redis_timeout: int = 5,
                 gw_timeout=30.0):
        """Initialize ssh gateway manager
        :param gw_hosts: list of host ip addresses
        :param gw_port: ssh gw service port
        :param gw_user: ssh gw management user
        :param gw_pwd: ssh gw management user password
        :param redis_manager: optional already existing RedisManager instance
        :param redis_uri: optional redis uri
        :param redis_timeout: redis timeout
        :param gw_timeout: ssh gw manager timeout for requests
        """
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.gw_hosts = []
        self.gw_port = gw_port
        self.gw_user = gw_user
        self.gw_pwd = gw_pwd
        self.gw_timeout = gw_timeout
        self.redis_manager: Optional[RedisManager] = None

        try:
            if gw_hosts:
                self.gw_hosts.append(*gw_hosts)
            else:
                raise SshGwError('No hosts supplied')
        except TypeError:
            self.logger.error('__init__ - Invalid type for parameter gw_hosts: expected List[str], found %s',
                              type(gw_hosts))
            raise
        except Exception as ex:
            self.logger.exception('__init__ - %s' % ex)

        if redis_manager:
            self.redis_manager = redis_manager
        else:
            self.__configure_redis(redis_uri, redis_timeout)

    def __configure_redis(self, redis_uri: str, redis_timeout: int = 5):
        # parse redis uri
        try:
            parsed = parse_redis_uri(redis_uri)
        except Exception as ex:
            raise SshGwError(ex)

        if parsed['type'] == 'single':
            self.redis_manager = RedisManager(redis_uri=redis_uri, timeout=redis_timeout)
        elif parsed['type'] == 'sentinel':
            port = parsed['port']
            pwd = parsed['pwd']
            self.redis_manager = RedisManager(redis_uri=None, timeout=redis_timeout,
                                              sentinels=[(host, port) for host in parsed['hosts']],
                                              sentinel_name=parsed['group'],
                                              sentinel_pwd=pwd,
                                              pwd=pwd)
        else:
            raise Exception('Unsupported redis type: %s' % parsed.get('type', None))

        self.prefix_ssh_gw = 'sshgw:'
        self.prefix_ssh_gw_index = 'sshgw:index:'
        self.prefix = 'identity:'
        self.prefix_index = 'identity:index:'

    @time_bound
    def ping_db(self):
        """Ping redis db
        :return: True or False
        """
        self.logger.debug(self.ping_db.__name__ + ' - info: %s', self.redis_manager.info())
        res = self.redis_manager.ping()
        self.logger.debug(self.ping_db.__name__ + ': %s' % ('OK' if res else 'KO'))
        return res

    def ping_hosts(self):
        """Ping ssh gw hosts
        :return: True or False"""
        from requests import get, ConnectionError, ConnectTimeout
        valid = []
        for host in self.gw_hosts:
            try:
                uri = 'http://' + host + ":" + str(self.gw_port)
                get(uri, headers={'content-type': 'application/json'}, timeout=self.gw_timeout, verify=False)
            except ConnectTimeout as ex:
                self.logger.error('connection timeout: %s' % ex)
            except ConnectionError as ex:
                self.logger.error('connection error: %s' % ex)
            except Exception as ex:
                self.logger.error('error: {}'.format(ex))
            else:
                # found valid host
                valid.append(host)
        if len(valid) > 0:
            return True
        else:
            return False

    @time_bound
    def redis_get_uuid(self, user: str) -> str:
        """Get uuid from username
        :param user: username (e.g. matricola@domnt.csi.it)
        :return: uid
        :raises: SshGwError: if data not present
        """
        try:
            res = self.redis_manager.conn.lindex(self.prefix_index + user, 0)
        except Exception as ex:
            self.logger.error('No uuid found for username %s.', user)
            raise SshGwError('No uuid found for username %s: %s' % (user, ex))
        if not res:
            raise SshGwError('No uuid found for username %s.' % user)
        return res

    @time_bound
    def redis_get_identity(self, uid: str) -> Dict:
        """Get identity
        :param uid: identity id
        :return: {'uid':..., 'user':..., timestamp':..., 'ip':..., 'roles':[...], 'perms':...,'pubkey':..., ...}
        """
        identity = self.redis_manager.conn.get(self.prefix + uid)
        if identity is not None:
            data = pickle.loads(identity)
            data['ttl'] = self.redis_manager.conn.ttl(self.prefix + uid)
            self.logger.debug('Get identity %s from redis: %s' % (uid, str(data)))
            return data
        else:
            self.logger.error("Identity %s doesn't exist or has expired." % uid)
            raise SshGwError("Identity %s doesn't exist or has expired." % uid, code=401)

    @time_bound
    def redis_get_identities(self) -> List[Mapping[str, Union[str, datetime.datetime]]]:
        """Get identities
        :return: [{'uid':..., 'user':..., timestamp':..., 'ttl':..., 'ip':...}, ..]
        """
        #from itertools import zip_longest

        #def batcher(iterable, n):
        #    # iterate a list in batches of size n
        #    args = [iter(iterable)] * n
        #    return zip_longest(*args)

        try:
            res = []
            # for key in self.redis_manager.conn.keys(self.prefix + '*'):
            # query in batches of 500. NB: not atomic, can fail midway
            #for key in batcher(self.redis_manager.conn.scan_iter(self.prefix + '*'), 500):
            for key in self.redis_manager.conn.scan_iter(self.prefix + '*'):
                if b'index' in key:
                    continue
                identity = self.redis_manager.conn.get(key)
                data = pickle.loads(identity)
                ttl = self.redis_manager.conn.ttl(key)
                res.append({'uid': data['uid'], 'user': data['user']['name'], 'timestamp': data['timestamp'],
                            'ttl': ttl, 'ip': data['ip']})
        except Exception as ex:
            self.logger.error('No identities found: %s' % ex)
            raise SshGwError('No identities found')

        self.logger.debug('Get identities from redis: %s' % res)
        return res

    @time_bound
    def redis_update_ssh_gw_entry(self, user: str, host: str) -> bytes:
        """update ssh gw entry for user.
        Fails if user identity entry not already present.
        :raises: SshGwError
        :returns: private key, base 64 encoded
        """
        if not SshGwUtils.is_valid_uuid(user):
            # check if it's username
            uuid = self.redis_get_uuid(user)
            uuid = uuid.decode()
            if not SshGwUtils.is_valid_uuid(uuid):
                raise SshGwError("Stored uuid is invalid")
        else:
            uuid = user

        # entry_found = self.redis_manager.conn.exists(self.prefix+uuid)
        identity = self.redis_get_identity(uuid)  # raises SshGwError if not found
        try:
            actual_user_id = identity['user']['id']
        except Exception as ex:
            raise SshGwError('Invalid stored user id: %s' % ex)

        try:
            pub, pri = SshGwUtils.generate_keys()
        except Exception as ex:
            raise SshGwError('Error generating keys: %s' % ex)

        key_index = self.prefix_ssh_gw_index+actual_user_id
        try:
            # check expire old key
            old = self.redis_manager.conn.get(key_index)
            if old:
                self.logger.debug('Old entry found. deleting old values...')
                self.redis_manager.conn.delete(key_index)
                self.redis_manager.conn.delete(old)

            self.redis_manager.conn.set(self.prefix_ssh_gw_index+actual_user_id, pub)
            self.redis_manager.conn.set(pub, host)
            self.redis_manager.conn.expire(pub, 3600)
            self.redis_manager.conn.expire(self.prefix_ssh_gw_index+actual_user_id, 3600)
        except Exception as ex:
            raise SshGwError('Error updating entry for id %s: %s' % (actual_user_id, ex))

        self.logger.debug('Entry updated.')
        return pri
