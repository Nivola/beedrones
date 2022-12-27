# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from six import ensure_str
from beecell.simple import bool2str, truncate, str2bool
from beecell.types.type_dict import dict_get
from beedrones.vsphere.client import VsphereObject, VsphereError
from six.moves.urllib.parse import urlencode
from xml.etree import ElementTree
from xml.etree.ElementTree import tostring
import xml.etree.ElementTree as et
####from dict2xml import dict2xml


class VsphereNetworkEdge(VsphereObject):
    """
    """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

        self.lb = VsphereNetworkLoadBalancer(self.manager)

    def list(self, datacenter=None, portgroup=None):
        """List edges

        :param datacenter: Retrieve Edges by datacenter
        :param portgroup: Retrieve Edges with one interface on specified port group
        """
        params = {}
        if datacenter is not None:
            params['datacenter'] = datacenter
        if portgroup is not None:
            params['portgroup'] = portgroup
        params = urlencode(params)
        items = self.call('/api/4.0/edges?%s' % params, 'GET', '')
        items = items['pagedEdgeList']['edgePage']
        if 'edgeSummary' in items.keys():
            items = items.get('edgeSummary')
            if isinstance(items, dict):
                items = [items]
            res = [i for i in items if i.get('edgeType', None) == 'gatewayServices']
        else:
            res = []

        return res

    def get(self, oid):
        """Get edge

        :param oid: edge id
        """
        res = self.call('/api/4.0/edges/%s' % oid, 'GET', '')
        return res['edge']

    def list_jobs(self):
        """List edge job

        """
        res = self.call('/api/4.0/edges/jobs/', 'GET', '')
        return [j['edgeJob'] for j in res['edgeJobs']]

    def get_job(self, jobid):
        """Get edge job

        :param jobid: job id
        """
        res = self.call('/api/4.0/edges/jobs/%s' % jobid, 'GET', '')
        return res['edgeJob']

    def __get_kvargs(self, kvargs, key, default=None, required=True):
        res = kvargs.get(key, default)
        if isinstance(res, bool):
            res = bool2str(res)
        if isinstance(res, int):
            res = str(res)
        if required is True and res is None:
            raise VsphereError('key %s is required and can not be None' % key)
        return res

    def __set_key(self, parent, kvargs, key, default=None, required=True):
        if required is True:
            et.SubElement(parent, key).text = self.__get_kvargs(kvargs, key, default=default, required=required)
        elif required is False and default is not None:
            et.SubElement(parent, key).text = self.__get_kvargs(kvargs, key, default=default, required=required)

    def add(self, kvargs):
        """Create new edge

        :param kvargs: positional parameters
        :param kvargs.datacenterMoid: datacenter id
        :param kvargs.name: name
        :param kvargs.description: description [optional]
        :param kvargs.tenant: tenant
        :param kvargs.fqdn: fqdn
        :param kvargs.vseLogLevel: [default='info']
        :param kvargs.enableAesni: [default=False]
        :param kvargs.enableFips: [default=False]
        :param kvargs.applianceSize: Choice of: compact, large, quadlarge, xlarge. [default='compact']
        :param kvargs.enableCoreDump: [default=True]
        :param kvargs.appliances.x.resourcePoolId: resource pool id
        :param kvargs.appliances.x.datastoreId: datastore id
        :param kvargs.appliances.x.hostId: host id [optional]
        :param kvargs.vnics.x.type: vnic type. Can be Uplink or Internal
        :param kvargs.vnics.x.portgroupId: id of the dvpg
        :param kvargs.vnics.x.addressGroups: list of addressgroup
        :param kvargs.vnics.x.addressGroups.y.primaryAddress: primary address. ex. 192.168.3.1
        :param kvargs.vnics.x.addressGroups.y.subnetPrefixLength: subnet prefix length. ex. 24
        :param kvargs.vnics.x.addressGroups.y.secondaryAddresses: list of secondary ip [optional]
        :param kvargs.vnics.x.addressGroups.y.secondaryAddresses.z.ipAddress: ip address. Ex. 192.168.3.2
        :param kvargs.userName: user name [default='admin']
        :param kvargs.password: user password
        :param kvargs.remoteAccess: remote access [default=True]
        :param kvargs.primaryDns: primary dns
        :param kvargs.secondaryDns: secondary dns [optional]
        :param kvargs.domainName: domain name
        :param kvargs.queryDaemon.enabled: query daemon enabled [default=True]
        :param kvargs.queryDaemon.port: query daemon port [default=5666]
        :param kvargs.autoConfiguration.enabled: auto configuration enabled [default=True]
        :param kvargs.autoConfiguration.rulePriority: auto configuration rule priority [default='high']
        :return: dictionary with detail
        """
        edge = et.Element('edge')
        self.__set_key(edge, kvargs, 'datacenterMoid')
        self.__set_key(edge, kvargs, 'name')
        self.__set_key(edge, kvargs, 'description', default=None, required=False)
        self.__set_key(edge, kvargs, 'type', default='gatewayServices', required=False)
        self.__set_key(edge, kvargs, 'tenant')
        self.__set_key(edge, kvargs, 'fqdn')
        self.__set_key(edge, kvargs, 'vseLogLevel', default='info', required=False)
        self.__set_key(edge, kvargs, 'enableAesni', default=False, required=False)
        self.__set_key(edge, kvargs, 'enableFips', default=False, required=False)

        # appliances
        appliances = et.SubElement(edge, 'appliances')
        self.__set_key(appliances, kvargs, 'applianceSize', default='compact', required=False)
        self.__set_key(appliances, kvargs, 'enableCoreDump', default=True, required=False)

        servers = kvargs.get('appliances', [])
        if len(servers) == 0 or len(servers) > 2:
            raise VsphereError('you must specify one or two edge appliance')
        for a in servers:
            appliance = et.SubElement(appliances, 'appliance')
            self.__set_key(appliance, a, 'resourcePoolId')
            self.__set_key(appliance, a, 'datastoreId')
            self.__set_key(appliance, a, 'hostId', default=None, required=False)
            self.__set_key(appliance, a, 'vmFolderId', default=None, required=False)
            # <customField>
            #     <key> system.service.vmware.vsla.main01 </key>
            #     <value> string </value>
            # </customField>
            # <cpuReservation>
            #     <limit>2399</limit>
            #     <reservation>500</reservation>
            #     <shares>500</shares>
            # </cpuReservation>
            #     <memoryReservation>
            #     <limit>5000</limit>
            #     <reservation>500</reservation>
            #     <shares>20480</shares>
            # </memoryReservation>

        # <vnic>
        #     <macAddress>
        #         <edgeVmHaIndex>0</edgeVmHaIndex>
        #         <value>00:50:56:01:03:23</value>
        #     </macAddress>
        #     <fenceParameter>
        #         <key>ethernet0.filter1.param1</key>
        #         <value>1</value>
        #     </fenceParameter>
        #     <mtu>1500</mtu>
        #     <enableProxyArp>false</enableProxyArp>
        #     <enableSendRedirects>true</enableSendRedirects>
        #     <isConnected>true</isConnected>
        #     <inShapingPolicy>
        #         <averageBandwidth>200000000</averageBandwidth>
        #         <peakBandwidth>200000000</peakBandwidth>
        #         <burstSize>0</burstSize>
        #         <enabled>true</enabled>
        #         <inherited>false</inherited>
        #     </inShapingPolicy>
        #     <outShapingPolicy>
        #         <averageBandwidth>400000000</averageBandwidth>
        #         <peakBandwidth>400000000</peakBandwidth>
        #         <burstSize>0</burstSize>
        #         <enabled>true</enabled>
        #         <inherited>false</inherited>
        #     </outShapingPolicy>
        # </vnic>
        # vnics
        vnics = et.SubElement(edge, 'vnics')
        ports = kvargs.get('vnics', [])
        # if len(ports) == 0 or len(ports) > 2:
        #     raise VsphereError('you must specify one edge vnic')
        index = 0
        for p in ports:
            vnic = et.SubElement(vnics, 'vnic')
            self.__set_key(vnic, p, 'index', default=index, required=False)
            self.__set_key(vnic, p, 'type')
            self.__set_key(vnic, p, 'portgroupId')
            self.__set_key(vnic, p, 'isConnected', default=True, required=False)
            addressgroups = et.SubElement(vnic, 'addressGroups')
            for a in p['addressGroups']:
                addressgroup = et.SubElement(addressgroups, 'addressGroup')
                self.__set_key(addressgroup, a, 'primaryAddress')
                self.__set_key(addressgroup, a, 'subnetPrefixLength')
                # secondaryaddresses = et.SubElement(addressgroup, 'secondaryAddresses')
                # for s in a.get('secondaryAddresses', []):
                #     self.__set_key(secondaryaddresses, s, 'ipAddress')
            index += 1

        # cli settings
        cli_settings = et.SubElement(edge, 'cliSettings')
        self.__set_key(cli_settings, kvargs, 'userName', default='admin', required=False)
        self.__set_key(cli_settings, kvargs, 'password')
        self.__set_key(cli_settings, kvargs, 'remoteAccess', default=True, required=False)
        # auto configuration
        cli_settings = et.SubElement(edge, 'autoConfiguration')
        data = {'enabled': kvargs.get('autoConfiguration.enabled', True),
                'port': kvargs.get('autoConfiguration.rulePriority', 'high')}
        self.__set_key(cli_settings, data, 'enabled', default=True, required=False)
        self.__set_key(cli_settings, data, 'rulePriority', default='high', required=False)
        # dns client
        dns_client = et.SubElement(edge, 'dnsClient')
        self.__set_key(dns_client, kvargs, 'primaryDns')
        self.__set_key(dns_client, kvargs, 'secondaryDns', default=None, required=False)
        self.__set_key(dns_client, kvargs, 'domainName')
        # query daemon
        dns_client = et.SubElement(edge, 'queryDaemon')
        data = {'enabled': kvargs.get('queryDaemon.enabled', True), 'port': kvargs.get('queryDaemon.port', 5666)}
        self.__set_key(dns_client, data, 'enabled', default=True, required=False)
        self.__set_key(dns_client, data, 'port', default=5666, required=False)

        data = ensure_str(et.tostring(edge))

        res = self.call('/api/4.0/edges?async=True', 'POST', data, headers={'Content-Type': 'application/xml'})
        self.logger.debug('create new edge with job: %s' % self.manager.nsx['location'])
        return self.manager.nsx['location'].split('/')[-1]

    def update(self, edge, data):
        """update an edge

        :param edge: edge id
        :return:
        """
        res = self.call('/api/4.0/edges/%s?async=True' % edge, 'PUT', data,
                        headers={'Content-Type': 'application/xml'})
        self.logger.debug('delete edge with job: %s' % self.manager.nsx['location'])
        return self.manager.nsx['location'].split('/')[-1]

    def delete(self, edge):
        """Delete an edge

        :param edge: edge id
        :return:
        """
        res = self.call('/api/4.0/edges/%s?async=True' % edge, 'DELETE', '',
                        headers={'Content-Type': 'application/xml'})
        self.logger.debug('delete edge with job: %s' % self.manager.nsx['location'])
        return self.manager.nsx['location'].split('/')[-1]

    def info(self, edge):
        """Get network edge info

        :param edge: edge instance
        :return: dictionary with info
        """
        # edge.pop('id')
        res = edge
        return res

    def detail(self, edge):
        """Get network edge detail

        :param edge: edge instance
        :return: dictionary with detail
        """
        # edge.pop('id')
        appliances = edge.get('appliances', {}).pop('appliance', [])
        edge['appliances'] = appliances
        vnics = edge.get('vnics', {}).get('vnic', [])
        edge['vnics'] = vnics
        features = edge.pop('features', {})
        edge['features'] = [
            {
                'feature': 'routing',
                'enabled': features.get('routing').get('enabled'),
                'version': features.get('routing').get('version')
            },
            {
                'feature': 'nat',
                'enabled': features.get('nat').get('enabled'),
                'version': features.get('nat').get('version')
            },
            {
                'feature': 'bridges',
                'enabled': features.get('bridges').get('enabled'),
                'version': features.get('bridges').get('version')
            },
            {
                'feature': 'firewall',
                'enabled': features.get('firewall').get('enabled'),
                'version': features.get('firewall').get('version')
            },
            {
                'feature': 'l2Vpn',
                'enabled': features.get('l2Vpn').get('enabled'),
                'version': features.get('l2Vpn').get('version')
            },
            {
                'feature': 'sslvpnConfig',
                'enabled': features.get('sslvpnConfig').get('enabled'),
                'version': features.get('sslvpnConfig').get('version')
            },
            {
                'feature': 'syslog',
                'enabled': features.get('syslog').get('enabled'),
                'version': features.get('syslog').get('version')
            },
            {
                'feature': 'dns',
                'enabled': features.get('dns').get('enabled'),
                'version': features.get('dns').get('version')
            },
            {
                'feature': 'dhcp',
                'enabled': features.get('dhcp').get('enabled'),
                'version': features.get('dhcp').get('version')
            },
            {
                'feature': 'ipsec',
                'enabled': features.get('ipsec').get('enabled'),
                'version': features.get('ipsec').get('version')
            },
            {
                'feature': 'gslb',
                'enabled': features.get('gslb').get('enabled'),
                'version': features.get('gslb').get('version')
            },
            {
                'feature': 'loadBalancer',
                'enabled': features.get('loadBalancer').get('enabled'),
                'version': features.get('loadBalancer').get('version')
            },
            {
                'feature': 'highAvailability',
                'enabled': features.get('highAvailability').get('enabled'),
                'version': features.get('highAvailability').get('version')
            }
        ]
        return edge

    def appliances(self, edge):
        """Get network edge appliances

        :param edge: edge instance
        :return: dictionary with detail
        """
        return edge.get('appliances', {}).get('appliance', [])

    #
    # cli settings
    #
    def reset_password(self, edge, pwd):
        """Reset admin password

        :params pwd: new password
        """
        cli_settings = et.Element('cliSettings')
        et.SubElement(cli_settings, 'userName').text = 'admin'
        et.SubElement(cli_settings, 'remoteAccess').text = 'true'
        et.SubElement(cli_settings, 'password').text = pwd
        data = ensure_str(et.tostring(cli_settings))
        self.call('/api/4.0/edges/%s/clisettings' % edge, 'PUT', data, headers={'Content-Type': 'application/xml'},
                  parse=False)
        self.logger.debug('set edge %s admin password' % edge)
        return True

    #
    # vnics
    #
    def vnics(self, edge):
        """Get network edge vnics

        :param edge: edge instance
        :return: dictionary with detail
        """
        return edge.get('vnics', {}).get('vnic', [])

    def vnic_add(self, edge, kvargs):
        """Create new vnic

        :param edge: edge id
        :param kvargs: vnic params
        :param kvargs.index: vnic index
        :param kvargs.type: vnic type. Can be Uplink or Internal
        :param kvargs.portgroupId: id of the dvpg
        :param kvargs.addressGroups: list of addregroup
        :param kvargs.addressGroups.y.primaryAddress: primary address. ex. 192.168.3.1
        :param kvargs.addressGroups.y.subnetPrefixLength: subnet prefix length. ex. 24
        :param kvargs.addressGroups.y.secondaryAddresses: list of secondary ip [optional]
        :param kvargs.addressGroups.y.secondaryAddresses.z.ipAddress: ip address. Ex. 192.168.3.2
        :return: dictionary with detail
        """
        vnics = et.Element('vnics')
        # <vnic>
        #     <macAddress>
        #         <edgeVmHaIndex>0</edgeVmHaIndex>
        #         <value>00:50:56:01:03:23</value>
        #     </macAddress>
        #     <fenceParameter>
        #         <key>ethernet0.filter1.param1</key>
        #         <value>1</value>
        #     </fenceParameter>
        #     <mtu>1500</mtu>
        #     <enableProxyArp>false</enableProxyArp>
        #     <enableSendRedirects>true</enableSendRedirects>
        #     <inShapingPolicy>
        #         <averageBandwidth>200000000</averageBandwidth>
        #         <peakBandwidth>200000000</peakBandwidth>
        #         <burstSize>0</burstSize>
        #         <enabled>true</enabled>
        #         <inherited>false</inherited>
        #     </inShapingPolicy>
        #     <outShapingPolicy>
        #         <averageBandwidth>400000000</averageBandwidth>
        #         <peakBandwidth>400000000</peakBandwidth>
        #         <burstSize>0</burstSize>
        #         <enabled>true</enabled>
        #         <inherited>false</inherited>
        #     </outShapingPolicy>
        # </vnic>
        # vnics
        vnic = et.SubElement(vnics, 'vnic')
        self.__set_key(vnic, kvargs, 'index')
        self.__set_key(vnic, kvargs, 'type')
        self.__set_key(vnic, kvargs, 'portgroupId')
        self.__set_key(vnic, kvargs, 'isConnected', default=True, required=False)
        addressgroups = et.SubElement(vnic, 'addressGroups')
        for a in kvargs['addressGroups']:
            addressgroup = et.SubElement(addressgroups, 'addressGroup')
            self.__set_key(addressgroup, a, 'primaryAddress')
            self.__set_key(addressgroup, a, 'subnetPrefixLength', default=24, required=False)
            if kvargs.get('secondaryAddresses', None) is not None:
                secondaryaddresses = et.SubElement(addressgroup, 'secondaryAddresses')
                for s in a.get('secondaryAddresses', []):
                    self.__set_key(secondaryaddresses, s, 'ipAddress')

        data = ensure_str(et.tostring(vnics))

        res = self.call('/api/4.0/edges/%s/vnics?action=patch' % edge, 'POST', data,
                        headers={'Content-Type': 'application/xml'})
        self.logger.debug('create new edge with job: %s' % self.manager.nsx['location'])
        return True

    def vnic_update(self, edge, vnic, **kvargs):
        """

        :param edge: edge id
        :param vnic: vnic id
        :return:
        """
        action = kvargs.get('action')

        # get current vnic configuration
        xml_res = self.call('/api/4.0/edges/%s/vnics/%s' % (edge, vnic), 'GET', '',
                            headers={'Content-Type': 'application/xml'}, parse=False)

        root = et.fromstring(xml_res)

        # - update sub-interface
        secondary_ip = kvargs.get('secondary_ip')
        secondary_ips = []

        a = root.find('addressGroups')
        b = a.find('addressGroup')
        c = b.find('secondaryAddresses')
        d = c.findall('ipAddress')
        for item in d:
            secondary_ips.append(item.text)
        update = False
        if action == 'add' and secondary_ip not in secondary_ips:
            et.SubElement(c, 'ipAddress').text = secondary_ip
            update = True
        elif action == 'delete' and secondary_ip in secondary_ips:
            for item in d:
                if item.text == secondary_ip:
                    c.remove(item)
                    update = True
                    break

        # - other vnic updates...

        if update:
            # reload configuration
            xml_req = ensure_str(et.tostring(root))
            res = self.call('/api/4.0/edges/%s/vnics/%s' % (edge, vnic), 'PUT', xml_req,
                            headers={'Content-Type': 'application/xml'})
            self.logger.debug('update edge %s vnic %s' % (edge, vnic))

        return True

    def vnic_del(self, edge, vnic):
        """Create new vnic

        :param edge: edge id
        :param vnic: vnic index
        :return: True
        """
        res = self.call('/api/4.0/edges/%s/vnics/%s' % (edge, vnic), 'DELETE', '',
                        headers={'Content-Type': 'application/xml'})
        self.logger.debug('delete edge %s vnic %s' % (edge, vnic))
        return True

    #
    # firewall
    #
    def route(self, edge):
        """Get network edge routing info

        :param edge: edge instance
        :return: dictionary with detail
        """
        features = edge.pop('features', {})
        return features.get('routing', {})

    def route_static_get(self, edge):
        """Get static routing configuration

        :param edge: edge instance
        :return: dictionary with detail
        """
        res = self.call('/api/4.0/edges/%s/routing/config/static' % edge, 'GET', '')
        data = res.get('staticRouting', {})
        data1 = []
        static_routes = data.get('staticRoutes', [])
        if static_routes is not None:
            if isinstance(static_routes, dict):
                static_routes = [static_routes]
            for static_route in static_routes:
                static_route = static_route.get('route')
                if isinstance(static_route, dict):
                    static_route = [static_route]
                for item in static_route:
                    item['type'] = 'static'
                    data1.append(item)
        item = data.get('defaultRoute', {})
        item['type'] = 'default'
        item['gateway'] = item.pop('gatewayAddress', None)
        data1.append(item)
        self.logger.debug('Get static routing configuration: %s' % data1)
        return data1

    def route_default_add(self, edge, gateway, mtu=1500, vnic=0):
        """Create new default route

        :param edge: edge id
        :param gateway: network
        :param mtu: mtu [default=1500]
        :param vnic: vnic [default=0]
        :return: dictionary with detail
        """
        # get base config
        res = self.call('/api/4.0/edges/%s/routing/config/static' % edge, 'GET', '').get('staticRouting', {})
        # old_static_routes = res.get('staticRoutes', {})
        old_default_routes = res.get('defaultRoute', {})

        routes = et.Element('staticRouting')
        default_routes = et.SubElement(routes, 'defaultRoute')

        # set old default route
        et.SubElement(default_routes, 'description').text = old_default_routes.get('description', '')
        et.SubElement(default_routes, 'gatewayAddress').text = gateway
        if vnic is None:
            vnic = old_default_routes['vnic']
        et.SubElement(default_routes, 'vnic').text = str(vnic)
        if mtu is None:
            mtu = old_default_routes['mtu']
        et.SubElement(default_routes, 'mtu').text = str(mtu)

        data = ensure_str(et.tostring(routes))
        self.call('/api/4.0/edges/%s/routing/config/static' % edge, 'PUT', data,
                  headers={'Content-Type': 'application/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('Create new default route')
        return True

    def __get_actual_routes(self, edge):
        # get base config
        res = self.call('/api/4.0/edges/%s/routing/config/static' % edge, 'GET', '').get('staticRouting', {})
        old_static_routes = res.get('staticRoutes', {})
        old_default_routes = res.get('defaultRoute', {})

        try:
            old_static_routes = old_static_routes.get('route', None)
            if old_static_routes is not None and isinstance(old_static_routes, dict):
                old_static_routes = [old_static_routes]
        except:
            old_static_routes = []

        return old_static_routes, old_default_routes

    def route_static_add(self, edge, desc, network, next_hop, mtu=1500, vnic=None):
        """Create new static route

        :param edge: edge id
        :param desc: rule name
        :param network: network
        :param next_hop: nextHop
        :param mtu: mtu [default=1500]
        :param vnic: vnic [optional]
        :return: dictionary with detail
        """
        old_static_routes, old_default_routes = self.__get_actual_routes(edge)

        routes = et.Element('staticRouting')
        static_routes = et.SubElement(routes, 'staticRoutes')
        default_routes = et.SubElement(routes, 'defaultRoute')

        # set old default route
        et.SubElement(default_routes, 'description').text = old_default_routes.get('description', '')
        et.SubElement(default_routes, 'vnic').text = old_default_routes.get('vnic', None)
        et.SubElement(default_routes, 'gatewayAddress').text = old_default_routes.get('gatewayAddress', '')
        et.SubElement(default_routes, 'mtu').text = str(old_default_routes.get('mtu', 1500))

        # set old routes
        for sr in old_static_routes:
            route = et.SubElement(static_routes, 'route')
            et.SubElement(route, 'description').text = sr.get('description', '')
            if sr.get('vnic', None) is not None:
                et.SubElement(route, 'vnic').text = sr.get('vnic', None)
            if sr.get('network', None) is not None:
                et.SubElement(route, 'network').text = sr.get('network', None)
            if sr.get('nextHop', None) is not None:
                et.SubElement(route, 'nextHop').text = sr.get('nextHop', None)
            et.SubElement(route, 'mtu').text = str(sr.get('mtu', 1500))

        # add new route
        route = et.SubElement(static_routes, 'route')
        et.SubElement(route, 'description').text = desc
        et.SubElement(route, 'network').text = network
        et.SubElement(route, 'nextHop').text = next_hop
        et.SubElement(route, 'mtu').text = str(mtu)
        if vnic is not None:
            et.SubElement(route, 'vnic').text = vnic

        data = ensure_str(et.tostring(routes))
        self.call('/api/4.0/edges/%s/routing/config/static' % edge, 'PUT', data,
                  headers={'Content-Type': 'application/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('create new static route: %s' % desc)
        return True

    def route_static_del(self, edge, network, next_hop):
        """Delete existing static route

        :param edge: edge id
        :param network: network
        :param next_hop: nextHop
        :param mtu: mtu [default=1500]
        :param vnic: vnic [optional]
        :return: dictionary with detail
        """
        old_static_routes, old_default_routes = self.__get_actual_routes(edge)

        routes = et.Element('staticRouting')
        static_routes = et.SubElement(routes, 'staticRoutes')
        default_routes = et.SubElement(routes, 'defaultRoute')

        # set old default route
        et.SubElement(default_routes, 'description').text = old_default_routes.get('description', '')
        et.SubElement(default_routes, 'vnic').text = old_default_routes.get('vnic', None)
        et.SubElement(default_routes, 'gatewayAddress').text = old_default_routes.get('gatewayAddress', '')
        et.SubElement(default_routes, 'mtu').text = str(old_default_routes.get('mtu', 1500))

        # set old routes
        for sr in old_static_routes:
            # bypass route to remove
            if sr.get('network', None) == network and sr.get('nextHop', None) == next_hop:
                continue

            # add existing ruote
            route = et.SubElement(static_routes, 'route')

            et.SubElement(route, 'description').text = sr.get('description', '')
            if sr.get('vnic', None) is not None:
                et.SubElement(route, 'vnic').text = sr.get('vnic', None)
            if sr.get('network', None) is not None:
                et.SubElement(route, 'network').text = sr.get('network', None)
            if sr.get('nextHop', None) is not None:
                et.SubElement(route, 'nextHop').text = sr.get('nextHop', None)
            et.SubElement(route, 'mtu').text = str(sr.get('mtu', 1500))

        data = ensure_str(et.tostring(routes))
        self.call('/api/4.0/edges/%s/routing/config/static' % edge, 'PUT', data,
                  headers={'Content-Type': 'application/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('delete existing static route: %s %s' % (network, next_hop))
        return True

    def __route_exist(self, routes, route_to_check):
        network = route_to_check.get('network', None)
        next_hop = route_to_check.get('nextHop', None)
        route = {'destination': network, 'nexthop': next_hop}
        if route in routes:
            return True
        return False

    def route_static_adds(self, edge, new_routes, mtu=1500, vnic=None):
        """Create new static routes

        :param edge: edge id
        :param new_routes: list of (network, next_hop)
        :param mtu: mtu [default=1500]
        :param vnic: vnic [optional]
        :return: dictionary with detail
        """
        old_static_routes, old_default_routes = self.__get_actual_routes(edge)

        routes = et.Element('staticRouting')
        static_routes = et.SubElement(routes, 'staticRoutes')
        default_routes = et.SubElement(routes, 'defaultRoute')

        # set old default route
        et.SubElement(default_routes, 'description').text = old_default_routes.get('description', '')
        et.SubElement(default_routes, 'vnic').text = old_default_routes.get('vnic', None)
        et.SubElement(default_routes, 'gatewayAddress').text = old_default_routes.get('gatewayAddress', '')
        et.SubElement(default_routes, 'mtu').text = str(old_default_routes.get('mtu', 1500))

        # add new route
        for new_route in new_routes:
            route = et.SubElement(static_routes, 'route')
            network = new_route['destination']
            next_hop = new_route['nexthop']
            et.SubElement(route, 'description').text = 'route-to-%s-by-%s' % (network, next_hop)
            et.SubElement(route, 'network').text = network
            et.SubElement(route, 'nextHop').text = next_hop
            et.SubElement(route, 'mtu').text = str(mtu)
            if vnic is not None:
                et.SubElement(route, 'vnic').text = vnic

        # set old routes
        for sr in old_static_routes:
            if self.__route_exist(new_routes, sr):
                continue

            route = et.SubElement(static_routes, 'route')
            et.SubElement(route, 'description').text = sr.get('description', '')
            if sr.get('vnic', None) is not None:
                et.SubElement(route, 'vnic').text = sr.get('vnic', None)
            if sr.get('network', None) is not None:
                et.SubElement(route, 'network').text = sr.get('network', None)
            if sr.get('nextHop', None) is not None:
                et.SubElement(route, 'nextHop').text = sr.get('nextHop', None)
            et.SubElement(route, 'mtu').text = str(sr.get('mtu', 1500))

        data = ensure_str(et.tostring(routes))
        self.call('/api/4.0/edges/%s/routing/config/static' % edge, 'PUT', data,
                  headers={'Content-Type': 'application/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('create new static routes: %s' % new_routes)
        return True

    def route_static_dels(self, edge, del_routes):
        """Delete existing static routes

        :param edge: edge id
        :param del_routes: list of (network, next_hop)
        :return: dictionary with detail
        """
        old_static_routes, old_default_routes = self.__get_actual_routes(edge)

        routes = et.Element('staticRouting')
        static_routes = et.SubElement(routes, 'staticRoutes')
        default_routes = et.SubElement(routes, 'defaultRoute')

        # set old default route
        et.SubElement(default_routes, 'description').text = old_default_routes.get('description', '')
        et.SubElement(default_routes, 'vnic').text = old_default_routes.get('vnic', None)
        et.SubElement(default_routes, 'gatewayAddress').text = old_default_routes.get('gatewayAddress', '')
        et.SubElement(default_routes, 'mtu').text = str(old_default_routes.get('mtu', 1500))

        # set old routes
        for sr in old_static_routes:
            if self.__route_exist(del_routes, sr):
                continue

            # add existing ruote
            route = et.SubElement(static_routes, 'route')

            et.SubElement(route, 'description').text = sr.get('description', '')
            if sr.get('vnic', None) is not None:
                et.SubElement(route, 'vnic').text = sr.get('vnic', None)
            if sr.get('network', None) is not None:
                et.SubElement(route, 'network').text = sr.get('network', None)
            if sr.get('nextHop', None) is not None:
                et.SubElement(route, 'nextHop').text = sr.get('nextHop', None)
            et.SubElement(route, 'mtu').text = str(sr.get('mtu', 1500))

        data = ensure_str(et.tostring(routes))
        self.call('/api/4.0/edges/%s/routing/config/static' % edge, 'PUT', data,
                  headers={'Content-Type': 'application/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('remove existing static routes: %s' % del_routes)
        return True

    def route_static_del_all(self, edge):
        """Delete static and default routes

        :param edge: edge id
        :return: None
        """
        self.call('/api/4.0/edges/%s/routing/config/static' % edge, 'DELETE', '', parse=False,
                  headers={'Content-Type': 'application/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('delete edge %s static and default route' % edge)
        return None

    #
    # nat
    #
    def nat(self, edge):
        """Get network edge nat info

        :param edge: edge instance
        :return: dictionary with detail
        """
        natrule = []
        features = edge.pop('features', {})
        nat = features.get('nat', {})
        natrules = nat.pop('natRules', {})
        if natrules is not None:
            natrule = natrules.get('natRule', {})
            if not isinstance(natrule, list):
                natrule = [natrule]
            nat['rules'] = natrule
        return natrule

    def nat_rule_add(self, edge, desc, action, original_address, translated_address, logged=True, enabled=True,
                     protocol=None, translated_port=None, original_port=None, vnic=0, dnat_match_source_address=None,
                     dnat_match_source_port=None, snat_match_destination_address=None,
                     snat_match_destination_port=None):
        """Create network edge nat rule

        :param edge: edge id
        :param desc: rule name
        :param action: can be dnat, snat
        :param original_address: original address
        :param translated_address: translated address
        :param logged: if True enable logging [default=True]
        :param enabled: if True enable nat [default=True]
        :param original_port: original port [optional]
        :param translated_port: translated port [optional]
        :param protocol: protocol [optional]
        :param vnic: vnic [default=0]
        :param dnat_match_source_address: dnat match source address [optional]
        :param dnat_match_source_port: dnat match source port [optional]
        :param snat_match_destination_address: snat match destination address [optional]
        :param snat_match_destination_port: snat match destination port [optional]
        :return: dictionary with detail
        """
        rules = et.Element('natRules')
        rule = et.SubElement(rules, 'natRule')
        et.SubElement(rule, 'description').text = desc
        et.SubElement(rule, 'vnic').text = str(vnic)
        et.SubElement(rule, 'originalAddress').text = original_address
        et.SubElement(rule, 'translatedAddress').text = translated_address
        et.SubElement(rule, 'action').text = action
        et.SubElement(rule, 'loggingEnabled').text = bool2str(logged)
        et.SubElement(rule, 'enabled').text = bool2str(enabled)
        if protocol:
            et.SubElement(rule, 'protocol').text = protocol
        if translated_port:
            et.SubElement(rule, 'translatedPort').text = str(translated_port)
        if original_port:
            et.SubElement(rule, 'originalPort').text = str(original_port)

        if dnat_match_source_address:
            et.SubElement(rule, 'dnatMatchSourceAddress').text = str(dnat_match_source_address)
        if dnat_match_source_port:
            et.SubElement(rule, 'dnatMatchSourcePort').text = str(dnat_match_source_port)
        if snat_match_destination_address:
            et.SubElement(rule, 'dnatMatchDestinationAddress').text = str(snat_match_destination_address)
        if snat_match_destination_port:
            et.SubElement(rule, 'dnatMatchDestinationPort').text = str(snat_match_destination_port)

        data = ensure_str(et.tostring(rules))
        self.call('/api/4.0/edges/%s/nat/config/rules' % edge, 'POST', data,
                  headers={'Content-Type': 'application/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('Create nat rule: %s' % desc)
        return True

    def nat_rule_update(self, edge, rule_id):
        """Update network edge nat rule TODO:

        :param edge: edge instance
        :param rule_id: rule id
        :return: dictionary with detail
        """
        data = None
        self.call('/api/4.0/edges/%s/nat/config/rules/%s' % (edge['id'], rule_id), 'PUT', data,
                  headers={'Content-Type': 'application/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('Update nat rule: %s' % rule_id)
        return None

    def nat_rule_delete(self, edge, rule_id):
        """Delete network edge nat rule

        :param edge: edge id
        :param rule_id: rule id
        :return: dictionary with detail
        """
        self.call('/api/4.0/edges/%s/nat/config/rules/%s' % (edge, rule_id), 'DELETE', '',
                  headers={'Content-Type': 'application/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('Delete nat rule: %s' % rule_id)
        return None

    #
    # firewall
    #
    def firewall(self, edge):
        """Get network edge firewall config

        :param edge: edge instance
        :return: dictionary with detail
        """
        features = edge.pop('features', {})
        firewall = features.get('firewall', {})
        rules = firewall.pop('firewallRules', {}).get('firewallRule', {})
        if isinstance(rules, dict):
            rules = [rules]
        firewall['rules'] = rules
        self.logger.debug('get firewall config: %s' % truncate(firewall))
        return firewall

    def firewall_rules(self, edge):
        """Get network edge firewall rules

        :param edge: edge instance
        :param rule_id: rule id
        :return: dictionary with detail
        """
        features = edge.get('features', {})
        firewall = features.get('firewall', {})
        rules = firewall.get('firewallRules', {}).get('firewallRule', {})
        self.logger.debug('get firewall rules: %s' % truncate(rules))
        return rules

    def firewall_rule(self, edge, rule_id):
        """Get network edge firewall rule

        :param edge: edge instance
        :param rule_id: rule id
        :return: dictionary with detail
        """
        features = edge.get('features', {})
        firewall = features.get('firewall', {})
        rules = firewall.get('firewallRules', {}).get('firewallRule', {})
        for rule in rules:
            if rule['id'] == rule_id:
                return rule
        return None

    def firewall_rule_add(self, edge, name, action, logged=True, desc=None, enabled=True, source=None,
                          dest=None, application=None, direction=None):
        """Create network edge firewall rule

        :param edge: edge id
        :param name: rule name
        :param desc: rule desc [optional]
        :param action: new action value. Ie: accept, deny
        :param logged: if True rule is logged [default=True]
        :param enabled: if True rule is enabled [default=True]
        :param direction: rule direction: in, out. If not specified is any [optional]
        :param source: list of item like: ip:<ipAddress>, grp:<groupingObjectId>, vnic:<vnicGroupId>
        :param dest: list of item like: ip:<ipAddress>, grp:<groupingObjectId>, vnic:<vnicGroupId>
        :param application: list of item like: app:<applicationId>, ser:proto+port+source_port
        :return: dictionary with detail
        """
        if desc is None:
            desc = name

        rules = et.Element('firewallRules')
        rule = et.SubElement(rules, 'firewallRule')
        # et.SubElement(rule, 'ruleTag')
        et.SubElement(rule, 'name').text = name
        et_source = et.SubElement(rule, 'source')
        et_destination = et.SubElement(rule, 'destination')
        et_application = et.SubElement(rule, 'application')
        # et.SubElement(rule, 'matchTranslated')
        et.SubElement(rule, 'action').text = action
        et.SubElement(rule, 'enabled').text = bool2str(enabled)
        et.SubElement(rule, 'loggingEnabled').text = bool2str(logged)
        et.SubElement(rule, 'description').text = desc

        if direction is not None:
            et.SubElement(rule, 'direction').text = direction

        mapping = {'ip': 'ipAddress', 'grp': 'groupingObjectId', 'vnic': 'vnicGroupId'}

        if source:
            for item in source:
                name, value = item.split(':')
                et.SubElement(et_source, mapping[name]).text = value
        if dest:
            for item in dest:
                name, value = item.split(':')
                et.SubElement(et_destination, mapping[name]).text = value
        if application:
            for item in application:
                name, value = item.split(':')
                if name == 'app':
                    et.SubElement(et_application, 'applicationId').text = value
                elif name == 'ser':
                    proto, port, source_port = value.split('+')
                    et_service = et.SubElement(et_application, 'service')
                    et.SubElement(et_service, 'protocol').text = proto
                    et.SubElement(et_service, 'port').text = port
                    et.SubElement(et_service, 'sourcePort').text = source_port

        data = ensure_str(et.tostring(rules))
        res = self.call('/api/4.0/edges/%s/firewall/config/rules' % edge, 'POST', data,
                        headers={'Content-Type': 'application/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('Create edge firewall rule: %s' % name)
        return res

    def firewall_rule_update(self, edge, rule_id, name=None, desc=None, action=None, direction=None, enabled=None,
                             source_add=None, source_del=None, dest_add=None, dest_del=None, appl=None, logged=None):
        """Update network edge firewall rule

        :param edge: edge id
        :param rule_id: rule id
        :param name:
        :param desc:
        :param action:
        :param direction:
        :param enabled:
        :param source_add:
        :param source_del:
        :param dest_add:
        :param dest_del:
        :param appl:
        :param logged:
        :return: True
        """
        # get and parse current configuration
        res = self.call('/api/4.0/edges/%s/firewall/config/rules/%s' % (edge, rule_id), 'GET', '',
                        headers={'Content-Type': 'application/xml'}, parse=False)
        root = et.fromstring(res)

        mapping = {
            'ip': 'ipAddress',
            'grp': 'groupingObjectId',
            'vnic': 'vnicGroupId'
        }

        # update configuration
        # - update name
        if name:
            root.find('name').text = name
        # - update description
        if desc:
            root.find('description').text = desc
        # - update description with name
        elif name and not desc:
            root.find('description').text = name
        # - enable/disable rule
        if enabled:
            root.find('enabled').text = enabled
        # - update action
        if action:
            root.find('action').text = action
        # - add source items
        if source_add:
            source_tag = root.findall('source')
            source_tag = source_tag[0]
            for item in source_add:
                name, value = item.split(':')
                et.SubElement(source_tag, mapping[name]).text = value
        # - remove source items
        if source_del:
            source_tag = root.findall('source')
            source_tag = source_tag[0]
            for item in source_del:
                name, value = item.split(':')
                for item in source_tag.iter(mapping[name]):
                    if item.text == value:
                        source_tag.remove(item)
        # - add destination items
        if dest_add:
            destination_tag = root.findall('destination')
            destination_tag = destination_tag[0]
            for item in dest_add:
                name, value = item.split(':')
                et.SubElement(destination_tag, mapping[name]).text = value
        # - remove destination items
        if dest_del:
            destination_tag = root.findall('destination')
            destination_tag = destination_tag[0]
            for item in dest_del:
                name, value = item.split(':')
                for item in destination_tag.iter(mapping[name]):
                    if item.text == value:
                        destination_tag.remove(item)
        # - update application
        if appl:
            application_tag = root.findall('application')
            for item in appl:
                name, value = item.split(':')
                if name == 'app':
                    et.SubElement(application_tag, 'applicationId').text = value
                elif name == 'ser':
                    proto, port, source_port = value.split('+')
                    service_tag = et.SubElement(application_tag, 'service')
                    et.SubElement(service_tag, 'protocol').text = proto
                    et.SubElement(service_tag, 'port').text = port
                    et.SubElement(service_tag, 'sourcePort').text = source_port

        # reload configuration
        xml_req = ensure_str(et.tostring(root))
        self.call('/api/4.0/edges/%s/firewall/config/rules/%s' % (edge, rule_id), 'PUT', xml_req,
                  headers={'Content-Type': 'text/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('Update edge firewall rule: %s' % rule_id)
        return True

    def firewall_rule_delete(self, edge, rule_id):
        """Delete network edge firewall rule

        :param edge: edge id
        :param rule_id: rule id
        :return: dictionary with detail
        """
        self.call('/api/4.0/edges/%s/firewall/config/rules/%s' % (edge, rule_id), 'DELETE', '',
                  headers={'Content-Type': 'application/xml', 'If-Match': self.manager.nsx['etag']})
        self.logger.debug('Delete edge firewall rule: %s' % rule_id)
        return True

    #
    # syslog
    #
    def syslog(self, edge):
        """Get syslog config

        :param edge: edge instance
        :return: dictionary with detail
        """
        res = self.call('/api/4.0/edges/%s/syslog/config' % edge, 'GET', '').get('syslog')
        self.logger.debug('get edge syslog config: %s' % res)
        return res

    def syslog_add(self, edge, servers):
        """add syslog servers to edge

        :param edge: edge id
        :param servers: list of rsyslog server ip address
        :return: True
        """
        data = et.Element('syslog')
        et.SubElement(data, 'protocol').text = 'udp'
        adresses = et.SubElement(data, 'serverAddresses')
        for server in servers:
            et.SubElement(adresses, 'ipAddress').text = server

        data = ensure_str(et.tostring(data))
        self.call('/api/4.0/edges/%s/syslog/config' % edge, 'PUT', data, headers={'Content-Type': 'application/xml'})
        self.logger.debug('configure edge %s syslog servers: %s' % (edge, servers))
        return True

    def syslog_del(self, edge):
        """Delete syslog servers from edge

        :param edge: edge id
        :return: None
        """
        self.call('/api/4.0/edges/%s/syslog/config' % edge, 'DELETE', '', headers={'Content-Type': 'application/xml'})
        self.logger.debug('unconfigure edge %s syslog servers' % edge)
        return None

    #
    # l2vpn
    #
    def l2vpn(self, edge):
        """Get network edge l2Vpn config

        :param edge: edge instance
        :return: dictionary with detail
        """
        features = edge.pop('features', {})
        l2vpn = features.get('l2Vpn', {})
        return l2vpn

    #
    # sslvpn
    #
    def sslvpn(self, edge):
        """Get network edge sslVpn config

        :param edge: edge id
        :return: dictionary with detail
        """
        res = self.call('/api/4.0/edges/%s/sslvpn/config' % edge, 'GET', '').get('sslvpnConfig')
        self.logger.debug('get edge sslvpn config: %s' % res)
        return res

    def sslvpn_session_get(self, edge):
        """Get network edge sslVpn active sessions

        :param edge: edge id
        :return: dictionary with detail
        """
        res = self.call('/api/4.0/edges/%s/sslvpn/activesessions' % edge, 'GET', '').get('activeSessions')
        self.logger.debug('get edge %s sslvpn active sessions: %s' % (edge, res))
        return res

    def sslvpn_session_delete(self, edge, session):
        """delete network edge sslVpn active session

        :param edge: edge id
        :param session: session id
        :return: dictionary with detail
        """
        self.call('/api/4.0/edges/%s/sslvpn/activesessions/%s' % (edge, session), 'DELETE', '')
        self.logger.debug('delete edge %s sslvpn active session %s' % (edge, session))
        return True

    def sslvpn_enable(self, edge):
        """enable network edge sslVpn service

        :param edge: edge id
        :return: dictionary with detail
        """
        res = self.call('/api/4.0/edges/%s/sslvpn/config?enableService=true' % edge, 'POST', '')
        self.logger.debug('enable edge sslvpn service: %s' % res)
        return res

    def sslvpn_disable(self, edge):
        """disable network edge sslVpn service

        :param edge: edge id
        :return: dictionary with detail
        """
        res = self.call('/api/4.0/edges/%s/sslvpn/config?enableService=false' % edge, 'POST', '')
        self.logger.debug('disable edge sslvpn service: %s' % res)
        return res

    def sslvpn_delete(self, edge):
        """delete network edge sslVpn service

        :param edge: edge id
        :return: dictionary with detail
        """
        res = self.call('/api/4.0/edges/%s/sslvpn/config' % edge, 'DELETE', '')
        self.logger.debug('delete edge sslvpn service: %s' % res)
        return res

    def sslvpn_server_config_add(self, edge, server_address, port, ciphers=None, cert=None):
        """add network edge sslVpn server config

        :param edge: edge id
        :param server_address: vpn service endpoint server address
        :param port: vpn service endpoint port
        :param ciphers: ciphers list. Ex. AES128-SHA [optional]
        :param cert: certificate id [optional]
        :return: dictionary with detail
        """
        data = et.Element('serverSettings')
        server_addresses = et.SubElement(data, 'serverAddresses')
        et.SubElement(server_addresses, 'ipAddress').text = server_address
        et.SubElement(data, 'port').text = str(port)
        if cert is not None:
            et.SubElement(data, 'certificateId').text = cert
        ciphers_et = et.SubElement(data, 'cipherList')
        if ciphers is None:
            ciphers = [
                'AES128-SHA',
                'AES256-SHA',
                'AES128-GCM-SHA256',
                'ECDHE-RSA-AES128-GCM-SHA256',
                'ECDHE-RSA-AES256-GCM-SHA384'
            ]
        for cipher in ciphers:
            et.SubElement(ciphers_et, 'cipher').text = cipher

        data = ensure_str(et.tostring(data))
        self.call('/api/4.0/edges/%s/sslvpn/config/server' % edge, 'PUT', data,
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('add edge %s sslvpn server config' % edge)
        return True

    def sslvpn_private_network_add(self, edge, network, enabled=True, optimize=True, ports=None, description=''):
        """add network edge sslVpn private network

        :param edge: edge id
        :param description: description [optional]
        :param network: network cidr
        :param enabled: enabled [optional]
        :param ports: tunnel optimize [optional]
        :param optimize: tunnel ports [optional]
        :param cert: certificate id [optional]
        :return: dictionary with detail
        """
        data = et.Element('privateNetwork')
        et.SubElement(data, 'description').text = description
        et.SubElement(data, 'network').text = network
        tunnel = et.SubElement(data, 'sendOverTunnel')
        et.SubElement(tunnel, 'optimize').text = bool2str(optimize)
        if ports is not None:
            et.SubElement(tunnel, 'ports').text = ports
        et.SubElement(data, 'enabled').text = bool2str(enabled)

        data = ensure_str(et.tostring(data))
        self.call('/api/4.0/edges/%s/sslvpn/config/client/networkextension/privatenetworks' % edge, 'POST', data,
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('add edge %s sslvpn private network %s' % (edge, network))
        return True

    def sslvpn_private_network_modify(self, edge, network_cidr, enabled=None, optimize=None,
                                      ports=None, description=None):
        """Modify network edge sslVpn private network

        :param edge: edge id
        :param description: description [optional]
        :param network_cidr: network cidr
        :param enabled: enabled [optional] [True / False]
        :param optimize: tunnel optimize [optional] [True / False]
        :param ports: tunnel ports [optional] or 'delete' if you want to delete the port
        :return: True
        """

        # since the put call need all the private networks configured on the system
        # get private networks list configured in the edge
        res = self.call('//api/4.0/edges/%s/sslvpn/config/client/networkextension/privatenetworks' % edge, 'GET', '')

        privateNetworks = et.fromstring(dict2xml(res))

        # Rimuovo dalla lista tutti gli oggetti di tipo <objectId>privatenetwork-xxx</objectId>
        for network in privateNetworks.findall('.//objectId/..'):
            for element in network.findall('objectId'):
                network.remove(element)

        # Cerco la privateNetwork da modificare
        for network in privateNetworks.findall('privateNetwork'):
            if network.find('network').text == network_cidr:
                if ports is not None and ports != 'delete':
                    tunnel = network.find('sendOverTunnel')
                    elementExist = False
                    for item in tunnel:
                        # print(item.tag, item.text)
                        if item.tag == 'ports':
                            elementExist = True

                    if elementExist:
                        tunnel.find('ports').text = ports
                    else:
                        et.SubElement(tunnel, 'ports').text = ports
                if ports == 'delete':
                    tunnel = network.find('sendOverTunnel')
                    for element in tunnel.findall('ports'):
                        tunnel.remove(element)

                if description is not None:
                    network.find('description').text = description
                if optimize is not None:
                    tunnel = network.find('sendOverTunnel')
                    tunnel.find('optimize').text = bool2str(optimize)
                if enabled is not None:
                    network.find('enabled').text = bool2str(enabled)

        self.call('/api/4.0/edges/%s/sslvpn/config/client/networkextension/privatenetworks' % edge, 'PUT',
                  ensure_str(et.tostring(privateNetworks)), headers={'Content-Type': 'application/xml'})
        self.logger.debug('modified edge %s sslvpn user %s' % (edge, network_cidr))

        return True

    def sslvpn_private_network_delete(self, edge, network):
        """delete all the network edge sslVpn private network

        :param edge: edge id
        :param network: network id
        :return: dictionary with detail
        """
        self.call('/api/4.0/edges/%s/sslvpn/config/client/networkextension/privatenetworks/%s' % (edge, network),
                  'DELETE', '', headers={'Content-Type': 'application/xml'})
        self.logger.debug('delete the edge %s sslvpn private network %s' % (edge, network))
        return True

    def sslvpn_private_network_delete_all(self, edge):
        """delete all the network edge sslVpn private network

        :param edge: edge id
        :return: dictionary with detail
        """
        self.call('/api/4.0/edges/%s/sslvpn/config/client/networkextension/privatenetworks' % edge, 'DELETE', '',
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('delete all the edge %s sslvpn private network' % edge)
        return True

    def sslvpn_ip_pool_add(self, edge, ip_range, netmask, gateway, primary_dns, secondary_dns, dns_suffix=None,
                           wins_server=None, enabled=True, description=''):
        """add network edge sslVpn ippool

        :param edge: edge id
        :param description: description [optional]
        :param ip_range: ip range. Ex. 172.30.0.10-172.30.0.99
        :param netmask: netmask. Ex. 255.255.255.0
        :param gateway: gateway. Ex. 172.30.0.1
        :param primary_dns: primary dns. Ex. 10.103.48.1
        :param secondary_dns: secondary dns. Ex. 10.103.48.2
        :param dns_suffix: dns suffix. [optional]
        :param wins_server: wins server. [optional]
        :param enabled: enabled [optional]
        :return: True
        """
        data = et.Element('ipAddressPool')
        et.SubElement(data, 'description').text = description
        et.SubElement(data, 'ipRange').text = ip_range
        et.SubElement(data, 'netmask').text = netmask
        et.SubElement(data, 'gateway').text = gateway
        et.SubElement(data, 'primaryDns').text = primary_dns
        et.SubElement(data, 'secondaryDns').text = secondary_dns
        if dns_suffix is not None:
            et.SubElement(data, 'dnsSuffix').text = dns_suffix
        if wins_server is not None:
            et.SubElement(data, 'winsServer').text = wins_server
        et.SubElement(data, 'enabled').text = bool2str(enabled)

        data = ensure_str(et.tostring(data))
        self.call('/api/4.0/edges/%s/sslvpn/config/client/networkextension/ippools' % edge, 'POST', data,
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('add edge %s sslvpn ippool %s' % (edge, ip_range))
        return True

    def sslvpn_ip_pool_delete(self, edge, ippool):
        """delete all the network edge sslVpn ippool

        :param edge: edge id
        :param ippool: ippool id
        :return: True
        """
        self.call('/api/4.0/edges/%s/sslvpn/config/client/networkextension/ippools/%s' % (edge, ippool),
                  'DELETE', '', headers={'Content-Type': 'application/xml'})
        self.logger.debug('delete the edge %s sslvpn ippool %s' % (edge, ippool))
        return True

    def sslvpn_ip_pool_delete_all(self, edge):
        """delete all the network edge sslVpn ippool

        :param edge: edge id
        :return: True
        """
        self.call('/api/4.0/edges/%s/sslvpn/config/client/networkextension/ippools' % edge, 'DELETE', '',
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('delete all the edge %s sslvpn ippool' % edge)
        return True

    def sslvpn_install_pkg_add(self, edge, name, gateways, enabled=True, start_client_on_logon=False,
                               hide_systray_icon=False, remember_password=False, silent_mode_operation=False,
                               silent_mode_installation=False, create_desktop_icon=True, create_linux_client=True,
                               enforce_server_Security_cert_validation=False, create_mac_client=True):
        """add network edge sslVpn install packages

        :param edge: edge id
        :param name: name [optional]
        :param gateways: list of gateways (ip, port)
        :param start_client_on_logon: start client on logon [optional]
        :param hide_systray_icon: hide systray icon [optional]
        :param remember_password: remember password [optional]
        :param silent_mode_operation: silent mode operation [optional]
        :param silent_mode_installation: silent mode installation [optional]
        :param create_desktop_icon: create desktop icon [optional]
        :param enforce_server_Security_cert_validation: enforce server Security cert validation [optional]
        :param create_linux_client: create linux client [optional]
        :param create_mac_client: create mac client [optional]
        :param enabled: enabled [optional]
        :return: True
        """
        data = et.Element('clientInstallPackage')
        et.SubElement(data, 'profileName').text = name
        et.SubElement(data, 'description').text = name
        et.SubElement(data, 'enabled').text = bool2str(enabled)
        gateways_et = et.SubElement(data, 'gatewayList')
        for gateway in gateways:
            gateway_et = et.SubElement(gateways_et, 'gateway')
            et.SubElement(gateway_et, 'hostName').text = gateway[0]
            et.SubElement(gateway_et, 'port').text = gateway[1]

        et.SubElement(data, 'startClientOnLogon').text = bool2str(start_client_on_logon)
        et.SubElement(data, 'hideSystrayIcon').text = bool2str(hide_systray_icon)
        et.SubElement(data, 'rememberPassword').text = bool2str(remember_password)
        et.SubElement(data, 'silentModeOperation').text = bool2str(silent_mode_operation)
        et.SubElement(data, 'silentModeInstallation').text = bool2str(silent_mode_installation)
        et.SubElement(data, 'createDesktopIcon').text = bool2str(create_desktop_icon)
        et.SubElement(data, 'enforceServerSecurityCertValidation').text = \
            bool2str(enforce_server_Security_cert_validation)
        et.SubElement(data, 'createLinuxClient').text = bool2str(create_linux_client)
        et.SubElement(data, 'createMacClient').text = bool2str(create_mac_client)

        data = ensure_str(et.tostring(data))
        self.call('/api/4.0/edges/%s/sslvpn/config/client/networkextension/installpackages' % edge, 'POST', data,
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('add edge %s sslvpn install packages' % edge)
        return True

    def sslvpn_install_pkg_delete(self, edge, installpackage):
        """delete all the network edge sslVpn install packages

        :param edge: edge id
        :param installpackage: installpackage id
        :return: True
        """
        self.call('/api/4.0/edges/%s/sslvpn/config/client/networkextension/installpackages/%s' %
                  (edge, installpackage), 'DELETE', '', headers={'Content-Type': 'application/xml'})
        self.logger.debug('delete the edge %s sslvpn install packages %s' % (edge, installpackage))
        return True

    def sslvpn_install_pkg_delete_all(self, edge):
        """delete all the network edge sslVpn install packages

        :param edge: edge id
        :return: True
        """
        self.call('/api/4.0/edges/%s/sslvpn/config/client/networkextension/installpackages' % edge, 'DELETE', '',
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('delete all the edge %s sslvpn install packages' % edge)
        return True

    def sslvpn_user_get(self, edge):
        """Get network edge sslVpn config

        :param edge: edge id
        :param parse : False /True
        :return: dictionary with detail
        """
        # res = self.call('/api/4.0/edges/%s/sslvpn/config' % edge, 'GET', '').get('sslvpnConfig')
        res = self.call('//api/4.0/edges/%s/sslvpn/config/auth/localserver/users' % edge, 'GET', '').get('usersInfo')
        self.logger.debug('get edge sslvpn config: %s' % res)
        return res

    def sslvpn_user_add(self, edge, user_id, password, first_name, last_name, description, disable=False,
                        password_expires=False, change_password_on_next_login=True):
        """add network edge sslVpn user

        :param edge: edge id
        :param user_id: user id
        :param password: user password
        :param first_name: first name
        :param last_name: last name
        :param description: description
        :param disable: disable user account
        :param password_expires: password never expires
        :param change_password_on_next_login: change password on next login
        :return: True
        """
        data = et.Element('user')
        et.SubElement(data, 'userId').text = user_id
        et.SubElement(data, 'password').text = password
        et.SubElement(data, 'firstName').text = first_name
        et.SubElement(data, 'lastName').text = last_name
        et.SubElement(data, 'description').text = description
        et.SubElement(data, 'disableUserAccount').text = bool2str(disable)
        et.SubElement(data, 'passwordNeverExpires').text = bool2str(password_expires)
        allow_change_password_et = et.SubElement(data, 'allowChangePassword')
        et.SubElement(allow_change_password_et, 'changePasswordOnNextLogin').text = \
            bool2str(change_password_on_next_login)

        data = ensure_str(et.tostring(data))
        self.call('/api/4.0/edges/%s/sslvpn/config/auth/localserver/users' % edge, 'POST', data,
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('add edge %s sslvpn user %s' % (edge, user_id))
        return True

    def sslvpn_user_modify_old(self, edge, user_id, password, first_name, last_name, description, disable=False,
                        password_expires=False, change_password_on_next_login=True):
        """modify network edge sslVpn user

        :param edge: edge id
        :param user_id: user id
        :param password: user password
        :param first_name: first name
        :param last_name: last name
        :param description: description
        :param disable: disable user account
        :param password_expires: password never expires
        :param change_password_on_next_login: change password on next login
        :return: True
        """
        data = et.Element('user')
        et.SubElement(data, 'userId').text = user_id
        et.SubElement(data, 'password').text = password
        et.SubElement(data, 'firstName').text = first_name
        et.SubElement(data, 'lastName').text = last_name
        et.SubElement(data, 'description').text = description
        et.SubElement(data, 'disableUserAccount').text = bool2str(disable)
        et.SubElement(data, 'passwordNeverExpires').text = bool2str(password_expires)
        allow_change_password_et = et.SubElement(data, 'allowChangePassword')
        et.SubElement(allow_change_password_et, 'changePasswordOnNextLogin').text = \
            bool2str(change_password_on_next_login)

        data = ensure_str(et.tostring(data))
        data2 = """<usersInfo>%s</usersInfo>""" % data
        # TODO: leggere utenti, ricercare l'utente da modificare tra quelli letti
        #  e modificare quello voluto inviando l'intera list in PUT

        # self.logger.debug('Data : %s' % data2)
        self.call('/api/4.0/edges/%s/sslvpn/config/auth/localserver/users' % edge, 'PUT', data2,
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('modified edge %s sslvpn user %s' % (edge, user_id))
        return True

    def sslvpn_user_modify(self, edge, user_id, password=None, first_name=None, last_name=None, description=None,
                           disable=None, password_expires=None, change_password_on_next_login=None):

        """modify network edge sslVpn user

        :param edge: edge id
        :param user_id: user id
        :param password: user password (if I have not specified the param 'change_password_on_next_login'then i'll force
                                            the user to change pwd at next login)

        :param first_name: first name
        :param last_name: last name
        :param description: description
        :param disable: disable user account (True / False)
        :param password_expires: password never expires (True / False)
        :param change_password_on_next_login: change password on next login (True / False)
        :return: True
        """

        # since the put call need all the users configured on the system
        # get users list configured in the edge
        res = self.call('//api/4.0/edges/%s/sslvpn/config/auth/localserver/users' % edge, 'GET', '', parse=False)

        userInfo = et.fromstring(res)

        # Rimuovo dalla lista tutti gli oggetti di tipo <objectId>user-xxx</objectId>
        for user in userInfo.findall('.//objectId/..'):
            for element in user.findall('objectId'):
                user.remove(element)

        # Cerco l'utenza da modificare
        for user in userInfo.findall('user'):
            if user.find('userId').text == user_id:
                if password is not None:
                    et.SubElement(user, 'password').text = password
                    # se non dico nulla rispetto al cambio pwd next login --> lo forzo a cambiarla
                    if change_password_on_next_login is None:
                        change_password_on_next_login = True
                        user.find('allowChangePassword')[0].text = bool2str(change_password_on_next_login)
                if first_name is not None:
                    user.find('firstName').text = first_name
                if last_name is not None:
                    user.find('lastName').text = last_name
                if description is not None:
                    user.find('description').text = description
                if password_expires is not None:
                    user.find('passwordNeverExpires').text = bool2str(password_expires)
                if disable is not None:
                    user.find('disableUserAccount').text = bool2str(disable)
                if change_password_on_next_login is not None:
                    user.find('allowChangePassword')[0].text = bool2str(change_password_on_next_login)
        # print(ensure_str(et.tostring(userInfo)))

        self.call('/api/4.0/edges/%s/sslvpn/config/auth/localserver/users' % edge, 'PUT',
                  ensure_str(et.tostring(userInfo)), headers={'Content-Type': 'application/xml'})
        self.logger.debug('modified edge %s sslvpn user %s' % (edge, user_id))
        return True

    def sslvpn_user_delete(self, edge, user):
        """delete all the network edge sslVpn user

        :param edge: edge id
        :param user: user id
        :return: True
        """
        self.call('/api/4.0/edges/%s/sslvpn/config/auth/localserver/users/%s' % (edge, user),
                  'DELETE', '', headers={'Content-Type': 'application/xml'})
        self.logger.debug('delete the edge %s sslvpn user %s' % (edge, user))
        return True

    def sslvpn_user_delete_all(self, edge):
        """delete all the network edge sslVpn user

        :param edge: edge id
        :return: True
        """
        self.call('/api/4.0/edges/%s/sslvpn/config/auth/localserver/users' % edge, 'DELETE', '',
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('delete all the edge %s sslvpn user' % edge)
        return True

    def sslvpn_advanced_config(self, edge, enable_compression=False, prevent_multiple_logon=False,
                               randomize_virtualkeys=False, client_notification=False, enable_logging=False,
                               forced_timeout=0, session_idle_timeout=10):
        """set network edge sslVpn advanced configuration

        :param edge: edge id
        :param enable_compression:
        :param prevent_multiple_logon:
        :param randomize_virtualkeys:
        :param client_notification:
        :param enable_logging:
        :param forced_timeout:
        :param session_idle_timeout:
        :return:
        """
        data = et.Element('advancedConfig')
        et.SubElement(data, 'enableCompression').text = bool2str(enable_compression)
        et.SubElement(data, 'forceVirtualKeyboard').text = bool2str(enable_compression)
        et.SubElement(data, 'preventMultipleLogon').text = bool2str(prevent_multiple_logon)
        et.SubElement(data, 'randomizeVirtualkeys').text = bool2str(randomize_virtualkeys)
        timeout_et = et.SubElement(data, 'timeout')
        et.SubElement(timeout_et, 'forcedTimeout').text = forced_timeout
        et.SubElement(timeout_et, 'sessionIdleTimeout').text = session_idle_timeout
        et.SubElement(data, 'clientNotification').text = bool2str(client_notification)
        et.SubElement(data, 'enableLogging').text = bool2str(enable_logging)

        data = ensure_str(et.tostring(data))
        self.call('/api/4.0/edges/%s/sslvpn/config/advancedconfig' % edge, 'PUT', data,
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('add edge %s sslvpn advancedconfig' % edge)
        return True

    def sslvpn_auth_config(self, edge, authentication_timeout=1):
        """set network edge sslVpn auth configuration. Supportati i sistemi: LocalAuthServerDto

        todo: sviluppare supporto per LdapAuthServerDto, RadiusAuthServerDto, RsaAuthServerDto, AdAuthServerDto

        :param edge: edge id
        :param authentication_timeout: authentication timeout [default=1]
        :return:
        """

        '''
        <authenticationConfig>
            <passwordAuthentication>
                <authenticationTimeout></authenticationTimeout>
                <primaryAuthServers>
                    <com.vmware.vshield.edge.sslvpn.dto.LdapAuthServerDto>
                        <ip></ip>
                        <port></port>
                        <timeOut></timeOut>
                        <enableSsl></enableSsl>
                        <searchBase></searchBase>
                        <bindDomainName></bindDomainName>
                        <bindPassword></bindPassword>
                        <loginAttributeName></loginAttributeName>
                        <searchFilter></searchFilter>
                        <enabled></enabled>
                    </com.vmware.vshield.edge.sslvpn.dto.LdapAuthServerDto>
                    <com.vmware.vshield.edge.sslvpn.dto.RadiusAuthServerDto>
                        <ip></ip>
                        <port></port>
                        <timeOut></timeOut>
                        <secret></secret>
                        <nasIp></nasIp>
                        <retryCount></retryCount>
                    </com.vmware.vshield.edge.sslvpn.dto.RadiusAuthServerDto>
                    <com.vmware.vshield.edge.sslvpn.dto.LocalAuthServerDto>
                        <enabled></enabled>
                        <passwordPolicy>
                            <minLength></minLength>
                            <maxLength></maxLength>
                            <minAlphabets></minAlphabets>
                            <minDigits></minDigits>
                            <minSpecialChar></minSpecialChar>
                            <allowUserIdWithinPassword></allowUserIdWithinPassword>
                            <passwordLifeTime></passwordLifeTime>
                            <expiryNotification></expiryNotification>
                        </passwordPolicy>
                        <accountLockoutPolicy>
                            <retryCount></retryCount>
                            <retryDuration></retryDuration>
                            <lockoutDuration></lockoutDuration>
                        </accountLockoutPolicy>
                    </com.vmware.vshield.edge.sslvpn.dto.LocalAuthServerDto>
                    <com.vmware.vshield.edge.sslvpn.dto.RsaAuthServerDto>
                        <timeOut></timeOut>
                        <sourceIp></sourceIp>
                    </com.vmware.vshield.edge.sslvpn.dto.RsaAuthServerDto>
                </primaryAuthServers>
                <secondaryAuthServer>
                    <com.vmware.vshield.edge.sslvpn.dto.AdAuthServerDto>
                        <ip>1.1.1.1</ip>
                        <port>90</port>
                        <timeOut>20</timeOut>
                        <enableSsl>false</enableSsl>
                        <searchBase>searchbasevalue</searchBase>
                        <bindDomainName>binddnvalue</bindDomainName>
                        <bindPassword>password</bindPassword>
                        <loginAttributeName>cain</loginAttributeName>
                        <searchFilter>found</searchFilter>
                        <terminateSessionOnAuthFails>false</terminateSessionOnAuthFails>
                        <enabled>true</enabled>
                    </com.vmware.vshield.edge.sslvpn.dto.AdAuthServerDto>
                </secondaryAuthServer>
            </passwordAuthentication>
        </authenticationConfig>        
        '''

        data = et.Element('authenticationConfig')
        auth = et.SubElement(data, 'passwordAuthentication')
        et.SubElement(auth, 'authenticationTimeout').text = str(authentication_timeout)

        data = ensure_str(et.tostring(data))
        self.call('/api/4.0/edges/%s/sslvpn/config/auth/settings' % edge, 'PUT', data,
                  headers={'Content-Type': 'application/xml'})
        self.logger.debug('add edge %s sslvpn auth config' % edge)
        return True

    #
    # high_availability
    #
    def high_availability(self, edge):
        """Get network edge highAvailability config

        :param edge: edge instance
        :return: dictionary with detail
        """
        features = edge.pop('highAvailability', {})
        high_availability = features.get('highAvailability', {})
        return high_availability

    def dns(self, edge):
        """Get network edge dns config

        :param edge: edge instance
        :return: dictionary with detail
        """
        features = edge.pop('dns', {})
        dns = features.get('dns', {})
        return dns

    def dhcp(self, edge):
        """Get network edge dhcp config

        :param edge: edge instance
        :return: dictionary with detail
        """
        features = edge.pop('dhcp', {})
        dhcp = features.get('dhcp', {})
        return dhcp

    def ipsec(self, edge):
        """Get network edge ipsec config

        :param edge: edge instance
        :return: dictionary with detail
        """
        features = edge.pop('ipsec', {})
        ipsec = features.get('ipsec', {})
        return ipsec

    def gslb(self, edge):
        """Get network edge gslb config

        :param edge: edge instance
        :return: dictionary with detail
        """
        features = edge.pop('gslb', {})
        gslb = features.get('gslb', {})
        return gslb


class VsphereNetworkLoadBalancer(VsphereObject):
    """Class implementing the NSX Edge load balancer functionality.

    The NSX Edge load balancer enables high-availability service and distributes the network traffic
    load among multiple servers.
    It distributes incoming service requests evenly among multiple servers in such a way that
    the load distribution is transparent to users.
    """

    cipher_suites = [
        'DEFAULT',
        'ECDHE-RSA-AES128-GCM-SHA256',
        'ECDHE-RSA-AES256-GCM-SHA384',
        'ECDHE-RSA-AES256-SHA',
        'ECDHE-ECDSA-AES256-SHA',
        'ECDH-ECDSA-AES256-SHA',
        'ECDH-RSA-AES256-SHA',
        'AES256-SHA',
        'AES128-SHA',
        'DES-CBC3-SHA'
    ]

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def config_get(self, edge_id):
        """Get network edge load balancer configuration

        :param edge_id:
        :return:
        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/config' % edge_id, 'GET', '').get('loadBalancer', {})
        for item in ['monitor', 'applicationRule', 'applicationProfile', 'virtualServer', 'pool']:
            data = res.get(item, None)

            if data is None:
                res[item] = []
            elif not isinstance(data, list):
                res[item] = [data]

            if item == 'pool':
                for item2 in res[item]:
                    if not isinstance(item2.get('member', None), list):
                        item2['member'] = [item2['member']]
        return res

    def config_update(self, edge_id, **kvargs):
        """Update load balancer general parameters, including whether load balancer is enable or disable.

        :param edge_id: edge id
        :param kvargs.enabled: enable (True) or disable (False) load balancer configuration
        :param kvargs.logging : enable (True) or disable (False) load balancer logging
        :param kvargs.log_level: Valid log levels are: EMERGENCY|ALERT|CRITICAL|ERROR|WARNING|NOTICE|INFO|DEBUG.
        :param acceleration_enabled: force load balancer to use L4 engine which is faster and more efficient than L7
               engine, True to enable, False to disable
        :return: load balancer configuration

        TODO: service insertion section
        """
        # since during the API call for enabling/disabling the object, the LB will delete the original global config
        # for the edge, we have to read the actual configuration and save the result in XML format (parse=False)
        xml_res = self.call('/api/4.0/edges/%s/loadbalancer/config' % edge_id, 'GET', '', parse=False)

        root = et.fromstring(xml_res)

        enabled = kvargs.get('enabled')
        if enabled is not None and enabled in [True, False]:
            # update the enabled load balancer parameter
            root_enabled = root.find('enabled')
            root_enabled.text = bool2str(enabled)

        acceleration_enabled = kvargs.get('acceleration_enabled')
        if acceleration_enabled is not None and acceleration_enabled in [True, False]:
            # update the accelerationEnabled parameter
            root_accelerationEnabled = root.find('accelerationEnabled')
            root_accelerationEnabled.text = bool2str(acceleration_enabled)

        root_logging = root.find('logging')
        logging = kvargs.get('logging')
        if logging is not None and logging in [True, False]:
            # update enable parameter in logging section
            loggingEnable = root_logging.find('enable')
            loggingEnable.text = bool2str(logging)
        log_level = kvargs.get('log_level')
        if log_level is not None and log_level in ['emergency', 'alert', 'critical', 'error', 'warning', 'notice',
                                                   'info', 'debug']:
            # update logLevel parameter in logging section
            logLevel = root_logging.find('logLevel')
            logLevel.text = log_level

        # TODO: service insertion section parameter with third party appliances

        # reload configuration
        xml_req = ''.join(et.tostring(root, encoding='unicode'))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config' % edge_id, 'PUT', xml_req,
                        headers={'Content-Type': 'text/xml'}, parse=False)

        return res

    def statistics_get(self, edge_id):
        """Retrieves load balancer statistics.

        :param edge_id: id of the edge acting as load balancer
        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/statistics' % edge_id, 'GET', '').\
            get('loadBalancerStatusAndStats', {})
        self.logger.info('get edge %s load balancer statistics: %s' % (edge_id, truncate(res)))
        return res

    """
    Working With Application Profiles

    You create an application profile to define the behavior of a particular type of network traffic. After configuring 
    a profile, you associate the profile with a virtual server. The virtual server then processes traffic according to 
    the values specified in the profile. Using profiles enhances your control over managing network traffic, and makes 
    traffic-management tasks easier and more efficient.
    """

    def app_profile_list(self, edge_id):
        """List application profiles.

        :param edge_id: id of the edge acting as load balancer
        :return: list of app profile configurations
        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles' % edge_id, 'GET', '')
        if res.get('loadBalancer') is None:
            return []
        return res.get('loadBalancer').get('applicationProfile', [])

    def app_profile_get(self, edge_id, app_profile_id):
        """Get application profile details.

        :param edge_id: id of the edge acting as load balancer
        :param app_profile_id: id of the app profile to get info
        :return: app profile configuration
        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles/%s' % (edge_id, app_profile_id),
                        'GET', '')
        res = res.get('applicationProfile')
        self.logger.info('get edge %s app profile %s: %s' % (edge_id, app_profile_id, res))
        return res

    def app_profile_add(self, edge_id, name, template, **kvargs):
        """Create a new application profile.

        :param edge_id: id of the edge acting as load balancer
        :param name: name of the new application profile
        :param template: application profile template, permitted  values: [TCP | UDP | HTTP | HTTPS]
        :param kvargs.http_redirect_url: HTTP redirect URL
        :param kvargs.persistence: persistence method, options are: [None | sourceip | msrdp | cookie]
        :param kvargs.expire: persistence expire time in seconds [Default=1800]
        :param kvargs.cookie_name: cookie name
        :param kvargs.cookie_mode: cookie mode, permitted values: [insert | prefix | app ]
        :param kvargs.insert_x_forwarded_for: insert X-Forwarded-for HTTP header [Default=False]
        :param kvargs.ssl_passthrough : enable SSL passthrough [Default=False]
        :param kvargs.client_ssl_cipher: cipher suites. Options are: DEFAULT, ECDHE-RSA-AES128-GCM-SHA256,
            ECDHE-RSA-AES256-GCM-SHA384, ECDHE-RSA-AES256-SHA, ECDHE-ECDSA-AES256-SHA, ECDH-ECDSA-AES256-SHA,
            ECDH-RSA-AES256-SHA, AES256-SHA AES128-SHA, DES-CBC3-SHA [Default is DEFAULT]
        :param client_auth: whether peer certificate should be verified. Options are: Required, Ignore [Default=Ignore]
        :param kvargsclient_ssl_service_certificate: service certificate identifier list. Only one certificate is supported.
            Required when client_ssl=True
        :param kvargs.server_ssl_enabled: enable pool side SSL [Default=False]
        :return: app profile configuration
        :raise VsphereError(error, code=500)
        """
        if template not in ['TCP', 'UDP', 'HTTP', 'HTTPS']:
            raise VsphereError('Permitted values for application profile template are: TCP, UDP, HTTP, HTTPS')

        insert_x_forwarded_for = kvargs.get('insert_x_forwarded_for') or False
        ssl_passthrough = kvargs.get('ssl_passthrough') or False
        server_ssl_enabled = kvargs.get('server_ssl_enabled') or False

        root = et.Element('applicationProfile')
        et.SubElement(root, 'name').text = name
        et.SubElement(root, 'template').text = template
        et.SubElement(root, 'insertXForwardedFor').text = bool2str(insert_x_forwarded_for)
        et.SubElement(root, 'sslPassthrough').text = bool2str(ssl_passthrough)
        et.SubElement(root, 'serverSslEnabled').text = bool2str(server_ssl_enabled)

        http_redirect_url = kvargs.get('http_redirect_url')
        if http_redirect_url is not None:
            item = et.SubElement(root, 'httpRedirect')
            et.SubElement(item, 'to').text = http_redirect_url

        persistence = kvargs.get('persistence')
        if persistence is not None:
            method = persistence.get('method')
            if template in ['HTTP', 'HTTPS']:
                if method not in ['sourceip', 'cookie']:
                    raise VsphereError('Permitted persistence methods for HTTP/HTTPS templates are: sourceip, cookie')
            elif template in ['TCP']:
                if method not in ['sourceip', 'msrdp']:
                    raise VsphereError('Permitted persistence methods for TCP template are: sourceip, msrdp')
            elif template in ['UDP']:
                if method not in ['sourceip']:
                    raise VsphereError('Permitted persistence method for UDP template is: sourceip')

            item = et.SubElement(root, 'persistence')
            et.SubElement(item, 'method').text = method
            et.SubElement(item, 'expire').text = str(persistence.get('expire') or 300)

            if method == 'cookie':
                cookie_name = persistence.get('cookie_name')
                if cookie_name is None:
                    raise VsphereError('Cookie name is mandatory when persistence is set to cookie')
                cookie_mode = persistence.get('cookie_mode') or 'insert'
                if cookie_mode not in ['insert', 'prefix', 'app']:
                    raise VsphereError('Permitted cookie modes are: insert, prefix, app')
                et.SubElement(item, 'cookieName').text = cookie_name
                et.SubElement(item, 'cookieMode').text = cookie_mode

        if template == 'HTTPS':
            if ssl_passthrough or server_ssl_enabled:
                client_ssl_service_certificate = kvargs.get('client_ssl_service_certificate')
                if client_ssl_service_certificate is None:
                    raise VsphereError('Client ssl service certificate is mandatory')
                client_ssl_ca_certificate = kvargs.get('client_ssl_ca_certificate')
                client_ssl_cipher = kvargs.get('client_ssl_cipher') or VsphereNetworkLoadBalancer.cipher_suites[0]
                if client_ssl_cipher not in VsphereNetworkLoadBalancer.cipher_suites:
                    raise VsphereError('Permitted client ssl ciphers are: %s' % ', '.join(
                        cipher_suite for cipher_suite in VsphereNetworkLoadBalancer.cipher_suites))
                client_auth = kvargs.get('client_auth') or 'Ignore'
                if client_auth not in ['Required', 'Ignore']:
                    raise VsphereError('Permitted values for client auth are: Required, Ignore')

                item = et.SubElement(root, 'clientSsl')
                et.SubElement(item, 'serviceCertificate ').text = client_ssl_service_certificate
                if client_ssl_ca_certificate is not None:
                    et.SubElement(item, 'caCertificate ').text = client_ssl_ca_certificate
                et.SubElement(item, 'ciphers ').text = client_ssl_cipher
                et.SubElement(item, 'clientAuth ').text = client_auth

            if server_ssl_enabled:
                server_ssl_service_certificate = kvargs.get('server_ssl_service_certificate')
                server_auth = kvargs.get('server_auth') or 'Ignore'
                if server_auth not in ['Required', 'Ignore']:
                    raise VsphereError('Permitted values for server auth are: Required, Ignore')
                server_ssl_ca_certificate = kvargs.get('client_ssl_ca_certificate')
                if server_ssl_ca_certificate is None and server_auth == 'Required':
                    raise VsphereError('Server ssl ca is mandatory with server auth set to required')
                server_ssl_cipher = kvargs.get('server_ssl_cipher') or VsphereNetworkLoadBalancer.cipher_suites[0]
                if server_ssl_cipher not in VsphereNetworkLoadBalancer.cipher_suites:
                    raise VsphereError('Permitted server ssl ciphers are: %s' % ', '.join(
                        cipher_suite for cipher_suite in VsphereNetworkLoadBalancer.cipher_suites))

                item = et.SubElement(root, 'serverSsl')
                if server_ssl_service_certificate is not None:
                    et.SubElement(item, 'serviceCertificate ').text = server_ssl_service_certificate
                if server_ssl_ca_certificate is not None:
                    et.SubElement(item, 'caCertificate ').text = server_ssl_ca_certificate
                et.SubElement(item, 'ciphers ').text = server_ssl_cipher
                et.SubElement(item, 'serverAuth ').text = server_auth

        xml_req = et.tostring(root, encoding='unicode')
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles' % edge_id,
                        'POST', xml_req, headers={'Content-Type': 'text/xml'}, parse=False)
        return res

    def app_profile_update(self, edge_id, app_profile_id, **kvargs):
        """Modify an existing application profile.

        :param edge_id: id of the edge acting as load balancer
        :param app_profile_id: id of the app profile to update
        :param kvargs: app profile parameters
        :return: updated app profile configuration
        """
        # get and parse current configuration
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles/%s' % (edge_id, app_profile_id),
                        'GET', '', headers={'Content-Type': 'text/xml'}, parse=False)
        root = et.fromstring(res)

        # update configuration
        http_redirect_url = kvargs.pop('http_redirect_url', None)
        if http_redirect_url is not None:
            item = et.SubElement(root, 'httpRedirect')
            et.SubElement(item, 'to').text = http_redirect_url
        for k, v in kvargs.items():
            if v is not None:
                root.find(k).text = str(v)

        # reload configuration
        xml_req = ensure_str(et.tostring(root))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles/%s' % (edge_id, app_profile_id),
                        'PUT', xml_req, headers={'Content-Type': 'text/xml'}, parse=False)
        return res

    def app_profile_del(self, edge_id, app_profile_id):
        """Delete application profile.

        :param edge_id: edge identifier
        :param app_profile_id: application profile identifier
        :return: True
        """
        self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles/%s' % (edge_id, app_profile_id),
                  'DELETE', '', timeout=600)
        return True

    def app_profile_del_all(self, edge_id):
        """Delete all application profiles in the edge.

        :param edge_id: edge identifier
        :return: True
        """
        self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles' % edge_id, 'DELETE', '', timeout=600)
        return True

    """
    Working With Application Rules

    You can write an application rule to directly manipulate and manage IP application traffic.
    """

    def app_rule_list(self, edge_id):
        """An application profile is used to define the behavior of a particular type of network traffic.
         List all application profiles for the edge identified by edge_id.

        :param edge_id: id of the edge acting as load balancer
        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationrules' % edge_id, 'GET', '')
        res = res.get('loadBalancer')
        if res is None:
            return []
        return res.get('applicationRule', [])

    def app_rule_get(self, edge_id, rule_id):
        """An application profile is use to define the behavior of a particular type of network traffic.
        Get the details of a single application profile identified by 'rule_id'

        :param edge_id :id of the edge acting as load balancer
        :param rule_id: id of the application profiles to list

        TO DO: implementing  https profiles without SSL passthrough

        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationrules/%s' % (edge_id, rule_id), 'GET', '')
        return res.get('applicationRule')

    def app_rule_add(self, edge_id, name, script):
        """An application profile is use to define the behavior of a particular type of network traffic.
        Add a new application rule to LB configuration of the edge identified by edgeid

        :param edge_id : mor-id of the edge acting as load balancer
        :param name : name of the new rule
        :param script : rule script
        :raise VsphereError(error, code=500)
        """
        root = et.Element('applicationRule')
        et.SubElement(root, 'name').text = name
        et.SubElement(root, 'script').text = script

        xml_req = et.tostring(root)
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationrules' % edge_id,
                        'POST', xml_req, headers={'Content-Type': 'text/xml'}, parse=False)
        return res

    def app_rule_update(self, edge_id, rule_id):
        """An application profile is use to define the behavior of a particular type of network traffic.
        Modify an application rule.

        todo:

        :param edge_id: id of the edge acting as load balancer
        :param rule_id: id of the application profiles to delete
        """

        rule = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationrules/%s' % (edge_id, rule_id), 'GET', '',
                         parse=False)

        # xml_req = et.tostring(root)
        # print xml_req
        # res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationrules' % edge_id,
        #                 'POST', xml_req, headers={'Content-Type': 'text/xml'}, parse=False)
        # return res

    def app_rule_del(self, edge_id, rule_id):
        """An application profile is use to define the behavior of a particular type of network traffic.
        Delete a single application profile identified by 'rule_id'

        :param edge_id: id of the edge acting as load balancer
        :param rule_id: id of the application profiles to delete
        """
        self.call('/api/4.0/edges/%s/loadbalancer/config/applicationrules/%s' % (edge_id, rule_id), 'DELETE', '',
                  timeout=600)
        return True

    def app_rule_del_all(self, edge_id):
        """An application profile is use to define the behavior of a particular type of network traffic.
        Delete all the application profiles identified by edge_id

        :param edge_id: id of the edge acting as load balancer
        """
        self.call('/api/4.0/edges/%s/loadbalancer/config/applicationrules' % edge_id, 'DELETE', '', timeout=600)
        return True

    """
    Working With Load Balancer Monitors

    You create a service monitor to define health check parameters for a particular type of network traffic. When you 
    associate a service monitor with a pool, the pool members are monitored according to the service monitor parameters.
    """

    def monitor_list(self, edge_id):
        """List monitors.

        :param edge_id: id of the edge acting as load balancer
        :return: list of monitor configurations
        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/monitors' % edge_id, 'GET', '')
        if res.get('loadBalancer') is None:
            return []
        return res.get('loadBalancer').get('monitor', [])

    def monitor_get(self, edge_id, monitor_id):
        """Get monitor details.

        :param edge_id: id of the edge acting as load balancer
        :param monitor_id: id of the monitor to get info
        :return: monitor configuration
        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/monitors/%s' % (edge_id, monitor_id), 'GET', '')
        res = res.get('monitor')
        self.logger.info('get edge %s monitor %s: %s' % (edge_id, monitor_id, res))
        return res

    def monitor_add(self, edge_id, name, monitor_type, interval=5, timeout=15, max_retries=3, method='GET',
                    url='/', expected=None, send=None, receive=None, extension=None):
        """Create a new monitor.

        :param edge_id: id of the edge acting as load balancer
        :param name: Name of the monitor.
        :param monitor_type: Monitor type. Options are : HTTP, HTTPS, TCP, UDP, ICMP.
        :param interval: Interval in seconds in which a server is to be tested [default=5]
        :param timeout: Timeout value is the maximum time in seconds within which a response from the server must be
            received [default=15]
        :param max_retries: Maximum number of times the server is tested before it is declared DOWN. [default=3]
        :param method: Method to send the health check request to the server. Options are: OPTIONS, GET, HEAD, POST,
            PUT, DELETE, TRACE, CONNECT. Default is GET for HTTP monitor.
        :param url: URL to GET or POST. Default is "/" for HTTP monitor.
        :param expected: Expected string. [Optional] Default is "HTTP/1" for HTTP/HTTPS protocol.
        :param send: String to be sent to the backend server after a connection is established. [Optional] URL encoded
            HTTP POST data for HTTP/HTTPS protocol.
        :param receive: String to be received from the backend server for HTTP/HTTPS protocol. [Optional]
        :param extension: Advanced monitor configuration. [optional]
        :raise VsphereError(error, code=500)
        :return: monitor configuration
        """
        if monitor_type not in ['HTTP', 'HTTPS', 'TCP', 'UDP', 'ICMP']:
            raise VsphereError('Permitted monitor types are HTTP, HTTPS, TCP, UDP, ICMP')

        root = et.Element('monitor')
        et.SubElement(root, 'name').text = name
        et.SubElement(root, 'type').text = monitor_type
        et.SubElement(root, 'interval').text = str(interval)
        et.SubElement(root, 'timeout').text = str(timeout)
        et.SubElement(root, 'maxRetries').text = str(max_retries)

        if monitor_type in ['HTTP', 'HTTPS']:
            if method not in ['OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT']:
                raise VsphereError('Permitted monitor methods for HTTP/HTTPS protocol are: OPTIONS, GET, HEAD, POST, '
                                   'PUT, DELETE, TRACE, CONNECT')

            et.SubElement(root, 'method').text = method
            et.SubElement(root, 'url').text = url
            if expected is not None:
                et.SubElement(root, 'expected').text = expected

        if monitor_type in ['HTTP', 'HTTPS', 'TCP', 'UDP']:
            if send is not None:
                et.SubElement(root, 'send').text = send
            if receive is not None:
                et.SubElement(root, 'receive').text = receive

        if extension is not None:
            et.SubElement(root, 'extension').text = extension

        xml_req = et.tostring(root, encoding='unicode')
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/monitors' % edge_id,
                        'POST', xml_req, headers={'Content-Type': 'text/xml'}, parse=False)
        return res

    def monitor_update(self, edge_id, monitor_id, **kvargs):
        """Modify an existing monitor.

        :param edge_id: id of the edge acting as load balancer
        :param monitor_id: id of the monitor to update
        :param kvargs: monitor parameters
        :return: updated monitor configuration
        """
        # get and parse current configuration
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/monitors/%s' % (edge_id, monitor_id), 'GET', '',
                        headers={'Content-Type': 'text/xml'}, parse=False)
        root = et.fromstring(res)

        # update configuration
        for k, v in kvargs.items():
            if v is not None:
                root.find(k).text = str(v)

        # reload configuration
        xml_req = ensure_str(et.tostring(root))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/monitors/%s' % (edge_id, monitor_id),
                        'PUT', xml_req, headers={'Content-Type': 'text/xml'}, parse=False)
        return True

    def monitor_del(self, edge_id, monitor_id):
        """Delete monitor.

        :param edge_id: id of the edge acting as load balancer
        :param monitor_id: id of the monitor to delete
        :return: True
        """
        self.call('/api/4.0/edges/%s/loadbalancer/config/monitors/%s' % (edge_id, monitor_id), 'DELETE', '',
                  timeout=600)
        return True

    def monitor_del_all(self, edge_id):
        """Delete all monitors in the edge.

        :param edge_id: id of the edge acting as load balancer
        :return: True
        """
        self.call('/api/4.0/edges/%s/loadbalancer/config/monitors' % edge_id, 'DELETE', '', timeout=600)
        return True

    """
    Working With Load Balancer Server Pools
    
    You can add a server pool to manage and share backend servers flexibly and efficiently. A pool manages load
    balancer distribution methods and has a service monitor attached to it for health check parameters.
    """

    def pool_list(self, edge_id):
        """List pools.

        :param edge_id: id of the edge acting as load balancer
        :return: list of pool configurations
        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/pools' % edge_id, 'GET', '')
        if res.get('loadBalancer') is None:
            return []
        return res.get('loadBalancer').get('pool', [])

    def pool_get(self, edge_id, pool_id):
        """Get pool details.

        :param edge_id: id of the edge acting as load balancer
        :param pool_id: id of the pool to get info
        :return: pool configuration
        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edge_id, pool_id), 'GET', '')
        res = res.get('pool')
        self.logger.info('get edge %s pool %s: %s' % (edge_id, pool_id, res))
        return res

    def pool_add(self, edge_id, name, algorithm, algorithm_params='', description='', transparent=False,
                 monitor_id='', ip_version='IPV4'):
        """Create a new pool.

        :param edge_id: the id of the edge acting as load balancer
        :param name: name of the new pool
        :param algorithm: valid algorithms are: ip-hash|round-robin|uri|leastconn|url|httpheader.
        :param algorithm_params:
                    if algorithm = url
                        valid algorithm_params are: urlParam=<url> where 1<=len(url)<=256
                    if algorithm = uri
                        valid algorithm_params are : uriLength=<length> uriDepth=<depth>
                        where 1<=<length><=256 AND 1<=<depth><=10
                    if algorith = httpheader
                        valid algorithm_params are headerName=<name> where 1<=len(name)<=256
        :param description: description [optional]
        :param transparent: [optional, default = false]
        :param monitor_id: [optional]
        :param ip_version: ipv4 or ipv6
        :return: pool configuration
        """
        if algorithm.lower() in ['ip-hash', 'round-robin', 'least-conn']:
            algorithm_params = ''

        root = et.Element('pool')
        et.SubElement(root, 'name').text = name
        et.SubElement(root, 'description').text = description
        et.SubElement(root, 'algorithm').text = algorithm
        et.SubElement(root, 'algorithmParameters').text = algorithm_params
        et.SubElement(root, 'transparent').text = bool2str(transparent)
        et.SubElement(root, 'monitorId').text = monitor_id
        et.SubElement(root, 'ipVersionFilter').text = ip_version

        xml_req = et.tostring(root, encoding='unicode')
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/pools' % edge_id, 'POST', xml_req,
                        headers={'Content-Type': 'text/xml'}, parse=False)
        return res

    def pool_members_add(self, edge_id, pool_id, members, **kvargs):
        """Add members to the pool.

        :param edge_id: edge identifier
        :param pool_id: pool identifier
        :param members: list of member definitions
        :return: pool configuration

        NOTE 1:
        It is necessary to update the full pool configuration to add a new backend member

        NOTE 2:
        If the new member is an IP ADDRESS, the XML must be in this format:
        <member>
            <ipAddress>10.102.189.17</ipAddress>
            <weight>1</weight>
            <port>80</port>
            <monitorPort>80</monitorPort>
            <maxConn>0</maxConn>
            <minConn>0</minConn>
            <condition>enabled</condition>
            <name>server_by_ip</name>
        </member>

        If the member is a VC CONTAINER, the XML must be:
        <member>
            <groupingObjectId>domain-c54</groupingObjectId>
            <weight>1</weight>
            <monitorPort>80</monitorPort>
            <port>80</port>
            <maxConn>0</maxConn>
            <minConn>0</minConn>
            <condition>enabled</condition>
            <name>cluster</name>
        </member>
        """
        # get actual configuration and save result in XML format (parse=False)
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edge_id, pool_id), 'GET', '', parse=False)

        root = et.fromstring(res)
        for member in members:
            ip_address = member.get('ip_addr')
            grouping_obj_id = member.get('ext_id')

            if ip_address is None and grouping_obj_id is None:
                raise Exception('Ip address and grouping object id cannot both be null')

            member_tag = ElementTree.SubElement(root, 'member')
            et.SubElement(member_tag, 'name').text = member.get('name')
            if ip_address is not None:
                et.SubElement(member_tag, 'ipAddress').text = ip_address
            else:
                et.SubElement(member_tag, 'groupingObjectId').text = grouping_obj_id
            et.SubElement(member_tag, 'port').text = str(member.get('lb_port') or 80)
            et.SubElement(member_tag, 'monitorPort').text = str(member.get('hm_port') or 80)
            et.SubElement(member_tag, 'weight').text = str(member.get('weight') or 1)
            et.SubElement(member_tag, 'maxConn').text = str(member.get('max_conn') or 0)
            et.SubElement(member_tag, 'minConn').text = str(member.get('min_conn') or 0)
            et.SubElement(member_tag, 'condition').text = member.get('cond') or 'enabled'

        # reload the modified configuration
        xml_req = ensure_str(et.tostring(root))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edge_id, pool_id), 'PUT', xml_req,
                        headers={'Content-Type': 'text/xml'}, parse=False)
        return res

    def pool_members_del(self, edge_id, pool_id, member_ids):
        """Remove members from the pool.

        :param edge_id: edge identifier
        :param pool_id: pool identifier
        :param member_ids: member identifiers
        :return: pool configuration

        NOTE 1:
        It is necessary to update the full pool configuration to add a new backend member
        """
        # get actual configuration and save result in XML format (parse=False)
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edge_id, pool_id), 'GET', '', parse=False)

        root = et.fromstring(res)
        for member_id in member_ids:
            for member in root.iter('member'):
                if member.find('memberId').text == member_id:
                    root.remove(member)
                    break

        # reload the modified configuration
        xml_req = ensure_str(et.tostring(root))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edge_id, pool_id), 'PUT', xml_req,
                        headers={'Content-Type': 'text/xml'}, parse=False)
        return res

    def pool_update(self, edge_id, pool_id, **kvargs):
        """Update an existing pool.

        :param edge_id: edge identifier
        :param pool_id: pool identifier
        :param kvargs: key-value pool parameters
        :return: updated pool configuration
        """
        # get and parse current configuration
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edge_id, pool_id), 'GET', '',
                        headers={'Content-Type': 'text/xml'}, parse=False)
        root = et.fromstring(res)

        # update configuration
        for k, v in kvargs.items():
            if v is not None:
                root.find(k).text = str(v)

        # reload configuration
        xml_req = ensure_str(et.tostring(root))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edge_id, pool_id),
                        'PUT', xml_req, headers={'Content-Type': 'text/xml'}, parse=False)
        return True

    def pool_del(self, edge_id, pool_id):
        """Delete pool

        :param edge_id: edge identifier
        :param pool_id: pool identifier
        :return: True
        """
        self.call('/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edge_id, pool_id), 'DELETE', '', timeout=600)
        return True

    def pool_del_all(self, edge_id):
        """Delete all pools in the edge.

        :param edge_id: edge identifier
        :return: True
        """
        self.call('/api/4.0/edges/%s/loadbalancer/config/pools' % edge_id, 'DELETE', '', timeout=600)
        return True

    #
    # virtual server
    #
    def virt_server_list(self, edge_id):
        """List virtual servers.

        :param edge_id: id of the edge acting as load balancer
        :return: list of virtual server configurations
        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/virtualservers' % edge_id, 'GET', '')
        if res.get('loadBalancer') is None:
            return []
        return res.get('loadBalancer').get('virtualServer', [])

    def virt_server_get(self, edge_id, virt_srv_id):
        """Get virtual server details.

        :param edge_id: id of the edge acting as load balancer
        :param virt_srv_id: id of the virtual server to get info
        :return: virtual server configuration
        """
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/virtualservers/%s' % (edge_id, virt_srv_id), 'GET', '')
        res = res.get('virtualServer')
        self.logger.info('get edge %s virtual server %s: %s' % (edge_id, virt_srv_id, res))
        return res

    def virt_server_add(self, edge_id, name, ip_address, protocol, port, app_profile, pool, **kvargs):
        """Create a new virtual server.

        :param edge_id: the id of the edge acting as load balancer
        :param name: name of the new virtual server
        :param ip_address: ip address that the load balancer is listening on
        :param protocol: virtual server protocol
        :param port: port number
        :param app_profile: application profile id
        :param pool: pool id
        :param kvargs.enabled: whether the virtual server is enabled [Default=True]
        :param kvargs.max_conn: maximum concurrent connections [Default=0]
        :param kvargs.max_conn_rate: Maximum incoming new connection requests per second [Default=0 i.e. unlimited]
        :param kvargs.acceleration_enabled: use faster L4 load balancer engine rather than L7 engine [Default=False]
        :return: virtual server configuration
        """
        enabled = kvargs.get('enabled') or True
        if enabled not in [True, False]:
            raise VsphereError('Permitted values for enabled are: True, False')
        acceleration_enabled = kvargs.get('acceleration_enabled') or False
        if acceleration_enabled not in [True, False]:
            raise VsphereError('Permitted values for acceleration_enabled are: True, False')
        description = kvargs.get('desc') or name
        max_conn = kvargs.get('max_conn') or 0
        if not isinstance(max_conn, int):
            raise VsphereError('max_conn value must be an integer')
        max_conn_rate = kvargs.get('max_conn_rate') or 0
        if not isinstance(max_conn_rate, int):
            raise VsphereError('max_conn_rate value must be an integer')

        root = et.Element('virtualServer')
        et.SubElement(root, 'enabled').text = bool2str(enabled)
        et.SubElement(root, 'name').text = name
        et.SubElement(root, 'description').text = description
        et.SubElement(root, 'ipAddress').text = ip_address
        et.SubElement(root, 'protocol').text = protocol
        et.SubElement(root, 'port').text = str(port)
        et.SubElement(root, 'applicationProfileId').text = app_profile
        et.SubElement(root, 'defaultPoolId').text = pool
        et.SubElement(root, 'connectionLimit').text = str(max_conn)
        et.SubElement(root, 'connectionRateLimit').text = str(max_conn_rate)
        et.SubElement(root, 'accelerationEnabled').text = bool2str(acceleration_enabled)

        xml_req = et.tostring(root, encoding='unicode')
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/virtualservers' % edge_id, 'POST', xml_req,
                        headers={'Content-Type': 'text/xml'}, parse=False)

        return res

    def virt_server_update(self, edge_id, virt_srv_id, **kvargs):
        """Modify an existing virtual server.

        :param edge_id: id of the edge acting as load balancer
        :param virt_srv_id: id of the virtual server to update
        :param kvargs: virtual server parameters
        :return: updated virtual server configuration
        """
        # read params
        protocol = kvargs.get('protocol')
        port = kvargs.get('port')

        # validate params
        # - protocol
        protocol = protocol.lower()
        if protocol not in ['http', 'https']:
            raise VsphereError('Options for protocol are: %s' % ['http', 'https'])
        # - port
        if not isinstance(port, int) and 1 <= port <= 65535:
            raise VsphereError('Invalid port number')

        # get and parse current configuration
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/virtualservers/%s' % (edge_id, virt_srv_id), 'GET', '',
                        headers={'Content-Type': 'text/xml'}, parse=False)
        root = et.fromstring(res)

        # update configuration
        for k, v in kvargs.items():
            if v is not None:
                root.find(k).text = str(v)

        # reload configuration
        xml_req = ensure_str(et.tostring(root))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/virtualservers/%s' % (edge_id, virt_srv_id),
                        'PUT', xml_req, headers={'Content-Type': 'text/xml'}, parse=False)
        return res

    def virt_server_del(self, edge_id, virt_srv_id):
        """ Delete virtual server.

        :param edge_id: id of the edge acting as load balancer
        :param virt_srv_id: id of the virtual server to delete
        :return: True
        """
        self.call('/api/4.0/edges/%s/loadbalancer/config/virtualservers/%s' % (edge_id, virt_srv_id), 'DELETE', '',
                  timeout=600)
        return True

    def virt_server_del_all(self, edge_id):
        """Delete all virtual servers in the edge.

        :param edge_id: edge identifier
        :return: True
        """
        self.call('/api/4.0/edges/%s/loadbalancer/config/virtualservers' % edge_id, 'DELETE', '', timeout=600)
        return True

    def virt_server_enable(self, edge_id, virt_srv_id):
        """Enable virtual server.

        :param edge_id: edge id
        :param virt_srv_id: virtual server id
        :return: True
        """
        # get and parse current configuration
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/virtualservers/%s' % (edge_id, virt_srv_id), 'GET', '',
                        headers={'Content-Type': 'text/xml'}, parse=False)
        root = et.fromstring(res)

        # enable virtual server
        root.find('enabled').text = bool2str(True)

        # reload configuration
        xml_req = ensure_str(et.tostring(root))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/virtualservers/%s' % (edge_id, virt_srv_id),
                        'PUT', xml_req, headers={'Content-Type': 'text/xml'}, parse=False)
        return res

    def virt_server_disable(self, edge_id, virt_srv_id):
        """Disable virtual server.

        :param edge_id: edge id
        :param virt_srv_id: virtual server id
        :return: True
        """
        # get and parse current configuration
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/virtualservers/%s' % (edge_id, virt_srv_id), 'GET', '',
                        headers={'Content-Type': 'text/xml'}, parse=False)
        root = et.fromstring(res)

        # disable virtual server
        root.find('enabled').text = bool2str(False)

        # reload configuration
        xml_req = ensure_str(et.tostring(root))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/virtualservers/%s' % (edge_id, virt_srv_id),
                        'PUT', xml_req, headers={'Content-Type': 'text/xml'}, parse=False)
        return res
