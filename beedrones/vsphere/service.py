# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereNetworkService(VsphereObject):
    """
    """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self):
        """List Services on a Scope
        """
        objs = self.call('/api/2.0/services/application/scope/globalroot-0',
                         'GET', '')
        items = objs['list']['application']
        if isinstance(items, dict):
            items = [items]
        res = []
        for item in items:
            if 'element' in item.keys():
                res.append({'id': item['objectId'],
                            'proto': item['element']['applicationProtocol'],
                            'ports': item['element']['value'],
                            'revision': item['revision'],
                            'name': item['name']})
        return res

    def get(self, proto, ports):
        """Get service id

        :param proto: service protocol. Ex. TCP, UDP, ICMP, ..
        :param ports: service ports. Ex. 80, 8080, 7200,7210,7269,7270,7575,  9000-9100
        :return: None if query empty
        """
        objs = self.call('/api/2.0/services/application/scope/globalroot-0',
                         'GET', '')
        items = objs['list']['application']
        datas = {}
        for item in items:
            if 'element' in item.keys():
                val = item['element']['value']
                objectid = item['objectId']
                data = {'id': objectid,
                        'proto': item['element']['applicationProtocol'],
                        'ports': item['element']['value'],
                        'revision': item['revision'],
                        'name': item['name']}
                try:
                    datas[item['element']['applicationProtocol']][val] = data
                except:
                    datas[item['element']['applicationProtocol']] = {val: data}

        try:
            return datas[proto][ports]
        except:
            raise VsphereError('No port found')

    def info(self, sg):
        """
        """
        res = sg
        return sg

    def create(self, protocol, ports, name, desc):
        """Create a new service on the specified scope.

        :param name: ip set name
        :param desc: ip set description
        :param ipset: list of ip. Ex. 10.112.201.8-10.112.201.14
        :return: mor id
        """
        data = ['<application>',
                '<objectId></objectId>',
                '<type>',
                '<typeName/>',
                '</type>',
                '<description>%s</description>',
                '<name>%s</name>',
                '<revision>0</revision>',
                '<objectTypeName></objectTypeName>',
                '<element>',
                '<applicationProtocol>%s</applicationProtocol>',
                '<value>%s</value>',
                '</element>',
                '</application>']
        data = ''.join(data) % (desc, name, protocol, ports)
        res = self.call('/api/2.0/services/application/globalroot-0',
                        'POST', data, headers={'Content-Type': 'text/xml'},
                        timeout=600)
        return res

    def delete(self, oid):
        """Delete a service by specifying its <applicationgroup-id>.
        The force=flag indicates if the delete should be forced or unforced.
        For forced deletes, the object is deleted irrespective of its use in
        other places such as firewall rules, which invalidates other
        configurations referring to the deleted object. For unforced deletes,
        the object is deleted only if it is not being used by any other
        configuration. The default is unforced(false).

        :param oid: securitygroup id
        """
        res = self.call('/api/2.0/services/application/%s' % oid, 'DELETE',
                        '', timeout=600)
        return True
