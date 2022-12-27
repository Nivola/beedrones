# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

import libvirt
import logging
from time import sleep
from beecell.remote import RemoteClient, RemoteException
from xmltodict import parse as xmltodict
from beedrones.virt.domain import VirtDomain

"""
0    VIR_DOMAIN_NOSTATE    no state
1    VIR_DOMAIN_RUNNING    the domain is running
2    VIR_DOMAIN_BLOCKED    the domain is blocked on resource
3    VIR_DOMAIN_PAUSED     the domain is paused by user
4    VIR_DOMAIN_SHUTDOWN   the domain is being shut down
5    VIR_DOMAIN_SHUTOFF    the domain is shut off
6    VIR_DOMAIN_CRASHED    the domain is crashed
7    VIR_DOMAIN_PMSUSPENDED    the domain is suspended by guest 
                               power management
8    VIR_DOMAIN_LAST        NB: this enum value will increase 
                            over time as new events are added 
                            to the libvirt API. It reflects the 
                            last state supported by this version 
                            of the libvirt API.
"""
vm_state = [
    'NOSTATE',
    'RUNNING',
    'BLOCKED',
    'PAUSED',
    'SHUTDOWN',
    'SHUTOFF',
    'CRASHED',
    'PMSUSPENDED',
    'LAST',
]


class VirtManagerError(Exception):
    pass


class VirtManager(object):
    def __init__(self, hid, host, port=16509, user=None, pwd=None, key=None, asynchronous=False):
        """
        :param api_params: dict with {uri, api_key, sec_key}
        """
        self.logger = logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)
        
        self.id = hid
        # mysql db connection params
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.key = key
        self.asynchronous = asynchronous

    def __str__(self):
        return '<VirtManager id=%s, host=%s, port=%s>' % (self.id, self.host, self.port)
        
    def __repr__(self):
        return '<VirtManager id=%s, host=%s, port=%s>' % (self.id, self.host, self.port)

    def connect(self):
        try:
            if self.user is not None:
                conn_string = 'qemu+ssh://%s@%s/system?no_tty=1&keyfile=%s' % (self.user, self.host, self.key)
                conn = VirtServer(self.id, conn_string, asynchronous=self.asynchronous, user=self.user, pwd=self.pwd)
            else:
                conn_string = 'qemu+tcp://%s:%s/system' % (self.host, self.port)
                conn = VirtServer(self.id, conn_string, asynchronous=self.asynchronous)
            conn.connect()
            self.logger.debug('Get libvirt-qemu server %s:%s connection: %s' % (
                self.host, self.port, conn))
            return conn
        except VirtServerError as e:
            raise VirtManagerError(e)
    
    def release(self, conn):
        conn.disconnect()
        self.logger.debug('Release libvirt-qemu connection: %s' % conn)
        
    def run_ssh_command(self, cmd):
        try:
            remote = RemoteClient(self.host)
            return remote.run_ssh_command(cmd, self.user, self.pwd, 22)
        except RemoteException as e:
            raise VirtManagerError(e)


class VirtServerError(Exception): 
    pass


class VirtServer(object):
    def __init__(self, id, uri, asynchronous=False, user=None, pwd=None):
        """Create a virt server instance
        
        :param uri : Example "qemu+tcp://10.102.90.3/system" 
        """
        self.logger = logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)
        
        self.id = id
        self.uri = uri
        self.conn = None
        self.hostname = None
        self.asynchronous = asynchronous
        self.user = user
        self.pwd = pwd
        
        self.datacenter = {'id': 'dc1', 'name': 'dc1'}
        self.cluster = {'id': 'cls1', 'name': 'cls1'}
    
    def switch(self):
        try:
            if self.asynchronous is True:
                sleep(0.01)
        except:
            pass

    # hypervisor
    def connect(self):
        """Connect a virt server

        :return: server connection
        """
        if self.conn is None:
            try:
                self.switch()
                self.conn = libvirt.open(self.uri)
                self.switch()
                self.hostname = self.conn.getHostname()
                self.switch()
            except libvirt.libvirtError as ex:
                raise VirtServerError(ex)

        return self.conn

    def close(self):
        """Disconnect a virt server

        :return:
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None
 
    def is_alive(self):
        """Return status of the hypervisor: alive, dead, error
        """
        state = {1: 'alive', 0: 'dead', -1: 'error'}
        res = None
        if self.conn is not None:
            res = self.conn.isAlive()
            return state[res]
        else:
            raise VirtServerError('No connection to libvirt host found')
 
    def ping(self):
        """Ping a virt server
        """
        if self.conn is not None and self.conn.isAlive() == 1:
            return True
        else:
            return False
 
    def info(self):
        """Return basic hypervisor info: hostname, hypervisor, info, libver, maxvcpux, uri.
        """
        libver = self.conn.getLibVersion()
        self.switch()
        conntype = self.conn.getType()
        self.switch()
        ver = self.conn.getVersion()
        self.switch()
        info = self.conn.getInfo()
        self.switch()
        uri = self.conn.getURI()
        self.switch()
        vm_number = self.conn.numOfDomains()
        self.switch()

        ip_address = uri.split('@')[1].split('/')[0]

        data = {
            'hostname': self.hostname,
            'libver': libver,
            'hypervisor': {
                'type': conntype,
                'version': ver
            },
            'info': info,
            'uri': uri,
            'ip_address': ip_address,
            'type': None,
            'vm_running': vm_number,
        }
        return data

    def get_last_error(self):
        """get last error"""
        err = libvirt.virGetLastError()
        return err

    # def tree(self):
    #     """Return hypervisor tree."""
    #     if self.conn is None:
    #         raise VirtServerError('No connection to libvirt %s host found' % self.id)
    #
    #     tree = []
    #
    #     dc_tree = {
    #         'id': self.datacenter['id'],
    #         'name': self.datacenter['name'],
    #         'clusters': [],
    #         'datastores': [],
    #         'networks': [],
    #         'resource_pools': [],
    #         'vms': []
    #     }
    #     tree.append(dc_tree)
    #
    #     # get clusters
    #     # kvm-libvirt hypervisor correspond to kvm host
    #     # To use the same structure as vShpere vCenter suppose that
    #     # kvm-libvirt hypervisor has a cluster with one only host
    #     # corresponding to itself
    #     cluster_info = {
    #         'id': self.cluster['id'],
    #         'name': self.cluster['name'],
    #         'hosts': self.nodes_list()
    #     }
    #     dc_tree['clusters'].append(cluster_info)
    #
    #     # get datastores
    #     datastores = self.node_datastore_list(None)
    #     for datastore in datastores:
    #         datastore_info = {'id': datastore.id, 'name': datastore.name}
    #         dc_tree['datastores'].append(datastore_info)
    #
    #     # get resource pools
    #
    #     # get networks
    #     dc_tree['networks'] = [{'name': item} for item in self.networks_list().keys()]
    #
    #     # get virtual machines
    #     dc_tree['vms'] = [{'name': dom.name(), 'id': dom.ID(), 'state': vm_state[dom.info()[0]]}
    #                       for dom in self.conn.listAllDomains(1)]
    #     return dc_tree

    def stats(self):
        """ TO-DO """
        pass

    # def nw_filters_list(self):
    #     """ """
    #     if self.conn is None:
    #         raise VirtServerError('No connection to libvirt %s host found' % self.id)
    #     data = []
    #     for item in self.conn.listAllNWFilters(0):
    #         data.append(xmltodict(item.XMLDesc(0), dict_constructor=dict, attr_prefix=''))

    # node
    # def nodes_list(self):
    #     """ """
    #     return [{'id': self.id, 'name': self.hostname}]
    
    def ext_info(self):
        """Return virt node extended info
        """
        info = xmltodict(self.conn.getCapabilities(), dict_constructor=dict, attr_prefix='')

        # main info
        data = info.get('capabilities')
        
        return data

    def get_network_conf(self):
        """ Describe node network configuration
        """
        try:
            resp = {}

            # get physical interface
            # inactive interface
            for item in self.conn.listAllInterfaces(1):
                data = xmltodict(item.XMLDesc(0), dict_constructor=dict, attr_prefix='')
                data = data.get('interface')
                resp[data.get('name')] = data

            # active interface
            for item in self.conn.listAllInterfaces(2):
                data = xmltodict(item.XMLDesc(0), dict_constructor=dict, attr_prefix='')
                data = data.get('interface')
                resp[data.get('name')] = data

            return resp
        except libvirt.libvirtError as ex:
            raise VirtServerError(ex)

    def get_datastores(self):
        """Return virt node storage
        """
        '''
        virStoragePoolState
        VIR_STORAGE_POOL_INACTIVE = 0
        VIR_STORAGE_POOL_BUILDING = 1
        VIR_STORAGE_POOL_RUNNING = 2
        VIR_STORAGE_POOL_DEGRADED = 3
        VIR_STORAGE_POOL_INACCESSIBLE = 4

        virConnectListAllStoragePoolsFlags
        VIR_CONNECT_LIST_STORAGE_POOLS_INACTIVE = 1
        VIR_CONNECT_LIST_STORAGE_POOLS_ACTIVE = 2
        VIR_CONNECT_LIST_STORAGE_POOLS_PERSISTENT = 4
        VIR_CONNECT_LIST_STORAGE_POOLS_TRANSIENT = 8
        VIR_CONNECT_LIST_STORAGE_POOLS_AUTOSTART = 16
        VIR_CONNECT_LIST_STORAGE_POOLS_NO_AUTOSTART = 32
        VIR_CONNECT_LIST_STORAGE_POOLS_DIR = 64
        VIR_CONNECT_LIST_STORAGE_POOLS_FS = 128
        VIR_CONNECT_LIST_STORAGE_POOLS_NETFS = 256
        VIR_CONNECT_LIST_STORAGE_POOLS_LOGICAL = 512
        VIR_CONNECT_LIST_STORAGE_POOLS_DISK = 1024
        VIR_CONNECT_LIST_STORAGE_POOLS_ISCSI = 2048
        VIR_CONNECT_LIST_STORAGE_POOLS_SCSI = 4096
        VIR_CONNECT_LIST_STORAGE_POOLS_MPATH = 8192
        VIR_CONNECT_LIST_STORAGE_POOLS_RBD = 16384
        VIR_CONNECT_LIST_STORAGE_POOLS_SHEEPDOG = 32768           
        '''
        dss = self.conn.listAllStoragePools(2)
        return dss

    # datastore
    def get_datastore_info(self, name=None, id=None):
        """get datastore info

        :param name:
        :param id:
        :return:
        """
        try:
            if name is not None:
                dom = self.conn.storagePoolLookupByName(name)
            elif id is not None:
                dom = self.conn.storagePoolLookupByUUIDString(id)
            data = xmltodict(dom.XMLDesc(1), dict_constructor=dict, attr_prefix='')
            return data
        except libvirt.libvirtError as ex:
            raise VirtServerError(ex)

    def gte_datastore_tree(self, name=None, id=None, path = '/'):
        """Get datastore tree

        :param name:
        :param uuid:
        """
        data = []
        try:
            if name is not None:
                dom = self.conn.storagePoolLookupByName(name)
            elif id is not None:
                dom = self.conn.storagePoolLookupByUUIDString(id)
            storage_path = xmltodict(dom.XMLDesc(1), dict_constructor=dict, attr_prefix='')['target']['path']
            vols = dom.listVolumes()
            
            for vol in vols:
                vol_path = "%s/%s" % (storage_path, vol)
                volobj = self.__volume_info(path=vol_path)
                data.append(volobj)
        except libvirt.libvirtError as ex:
            raise VirtServerError(ex)
        return data

    def __volume_info(self, name=None, path=None):
        """Get volume info

        :param extended: True show more description fields
        """
        data = None
        try:
            if name is not None:
                vol = self.conn.storageVolLookupByName(name)
            elif path is not None:
                vol = self.conn.storageVolLookupByPath(path)
            data = xmltodict(vol.XMLDesc(0), dict_constructor=dict, attr_prefix='')
            data['storage'] = vol.storagePoolLookupByVolume().name()
        except libvirt.libvirtError as ex:
            raise VirtServerError(ex)
        return data

    # domain
    def get_domains(self, status=0):
        """Get virt node domains. Use status to filter the search.

        :param status:
        1     ACTIVE
        2     INACTIVE
        4     PERSISTENT
        8     TRANSIENT
        16    RUNNING
        32    PAUSED
        64    SHUTOFF
        128   OTHER
        256   MANAGEDSAVE
        512   NO_MANAGEDSAVE
        1024  AUTOSTART
        2048  NO_AUTOSTART
        4096  HAS_SNAPSHOT
        8192  NO_SNAPSHOT  
        """
        data = []
        for dom in self.conn.listAllDomains(status):
            data.append(VirtDomain(self, dom))
        return data

    def get_domain(self, name=None, id=None):
        """Get domain info

        :param name: [optional] name of virtual machine
        :param id: [optional] id of virtual machine
        """
        try:
            if name is not None:
                dom = self.conn.lookupByName(name)
            elif id is not None:
                dom = self.conn.lookupByName(id)
            return VirtDomain(self, dom)
        except libvirt.libvirtError as ex:
            raise VirtServerError(ex)

    def get_domain_stats(self, status=0):
        """Query statistics for all domains on a given connection.
        """
        try:
            resp = []
            for s in self.conn.getAllDomainStats(flags=status):
                item = s[1]
                item['name'] = s[0].name()
                resp.append(item)
            return resp
        except libvirt.libvirtError as ex:
            raise VirtServerError(ex)

    def __get_domain_info(self, dom):
        """Get domain info

        XMLDesc flags:
        1 VIR_DOMAIN_XML_SECURE     dump security sensitive information too
        2 VIR_DOMAIN_XML_INACTIVE   dump inactive domain information
        4 VIR_DOMAIN_XML_UPDATE_CPU update guest CPU requirements according to host CPU
        8 VIR_DOMAIN_XML_MIGRATABLE dump XML suitable for migration
        """
        ext_infos = xmltodict(dom.XMLDesc(8), dict_constructor=dict, attr_prefix='')
        resp = ext_infos.get('domain')
            
        return resp

    # device
    def get_devices(self):
        """Get virt node devices
        """
        resp = []
        try:
            for item in self.conn.listAllDevices(0):
                data = xmltodict(item.XMLDesc(0), dict_constructor=dict, attr_prefix='')
                resp.append(data.get('device'))
        except libvirt.libvirtError as ex:
            raise VirtServerError(ex)
        return resp
