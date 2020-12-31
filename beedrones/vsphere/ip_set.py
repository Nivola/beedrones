# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

from beedrones.vsphere.client import VsphereObject
from xmltodict import parse as xmltodict


class VsphereNetworkIpSet(VsphereObject):
    """
    """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self):
        """ """
        res = self.call('/api/2.0/services/ipset/scope/globalroot-0',
                        'GET', '')['list']['ipset']
        if isinstance(res, dict):
            res = [res]
        return res

    def get(self, oid):
        """
        :param oid: securitygroup id
        :return: None if security group does not exist
        """
        res = self.call('/api/2.0/services/ipset/%s' % oid, 'GET', '')
        return res['ipset']

    def info(self, sg):
        """
        """
        res = sg
        return sg

    def detail(self, sg):
        """
        """
        res = sg
        return sg

    def create(self, name, desc, ipset):
        """

        :param name: ip set name
        :param desc: ip set description
        :param ipset: list of ip. Ex. 10.112.201.8-10.112.201.14
        :return: mor id
        """

        data = ['<ipset>',
                '<objectId/>',
                '<type>',
                '<typeName/>',
                '</type>',
                '<description>%s</description>',
                '<name>%s</name>',
                '<revision>0</revision>',
                '<objectTypeName/>',
                '<value>%s</value>',
                '</ipset>']
        data = ''.join(data) % (desc, name, ipset)
        res = self.call('/api/2.0/services/ipset/globalroot-0',
                        'POST', data, headers={'Content-Type': 'text/xml'},
                        timeout=600)
        return res

    def update(self, oid, name=None, description=None, value=None):
        """Modify/Edit ipset properties
        Modified by Miko( TO DO by Sergio )

        :param oid: securitygroup id( morefid )
        :param name: new name of the ipset to modify
        :param description: new description to modify
        :param value: new ipset to modify
        """

        data = self.call('/api/2.0/services/ipset/%s' % oid, 'GET', '', parse=False)
        # TODO modify data content to update configuration

        # self.logger.debug('MIKO_IP_SET :%s' %data)

        res = xmltodict(data, dict_constructor=dict)

        noName = False
        noDescription = False
        noValue = False

        if name == None:
            name = res['ipset']['name']
            noName = True
        elif name == res['ipset']['name']:
            noName = True
            # self.logger.debug('MIKO_IP_SET: sono in name ')

        if description == None:
            description = res['ipset']['description']
            noDescription = True
        elif description == res['ipset']['description']:
            noDescription = True
            # self.logger.debug('MIKO_IP_SET: sono in description ')

        if value == None:
            value = res['ipset']['value']
            noValue = True
        elif value == res['ipset']['value']:
            noValue = True
            # self.logger.debug('MIKO_IP_SET: sono in value ')

        '''        
        Request:
            PUT https://NSX-Manager-IP-Address/api/2.0/services/ipset/objectId

        Request Body:
            <ipset>
                <objectId>ipset-ae40752f-3b9b-4885-b63c-551fbaa459ab</objectId>
                <type>
                    <typeName>IPSet</typeName>
                </type>
                <description>Updated Description</description>
                <name>TestIPSet1updated</name>
                <revision>2</revision>
                <objectTypeName />
                <value>10.112.200.1,10.112.200.4-10.112.200.10</value>
            </ipset>
        '''
        if (noName) and (noDescription) and (noValue):
            # no update to do
            res = data
            self.logger.debug('MIKO_IP_SET: NO DATA TO MODIFY ')
        else:
            revision = int(res['ipset']['revision']) + 1

            newData = ['<ipset>',
                       '<objectId>%s</objectId>',
                       '<type>',
                       '<typeName>IPSet</typeName>',
                       '</type>',
                       '<description>%s</description>',
                       '<name>%s</name>',
                       '<revision>%s</revision>',
                       '<objectTypeName />',
                       '<value>%s</value>',
                       '</ipset>']

            newData = ''.join(newData) % (oid, description, name, revision, value)

            res = self.call('/api/2.0/services/ipset/%s' % oid, 'PUT',
                            newData, headers={'Content-Type': 'text/xml'}, parse=False)

        return res

    def delete(self, oid):
        """
        :param oid: securitygroup id
        """
        res = self.call('/api/2.0/services/ipset/%s' % oid, 'DELETE', '', timeout=600)
        return True
