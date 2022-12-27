# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.password import random_password
from beecell.simple import truncate
from beecell.types.type_dict import dict_get
from beedrones.cmp.business import CmpBusinessAbstractService
from beedrones.cmp.client import CmpBaseService, CmpApiManagerError, CmpApiClientError


class CmpBusinessNetaasService(CmpBusinessAbstractService):
    """Cmp business compute service
    """
    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        self.backup = None
        self.vpc = CmpBusinessNetaasVpcService(self.manager)
        self.sg = CmpBusinessNetaasSecurityGroupService(self.manager)


class CmpBusinessNetaasVpcService(CmpBusinessAbstractService):
    """Cmp business network service - vpc
    """
    VERSION = 'v1.0'

    def list(self, *args, **kwargs):
        """get vpcs

        :param accounts: list of account id comma separated
        :param page: list page
        :param size: list page size
        :param tags: list of tag comma separated
        :param states: list of state comma separated                
        :param ids: list of vpc id comma separated
        :param name: list of vpc id comma separated
        :return: list of vpcs {'count':.., 'page':.., 'total':.., 'sort':.., 'vpcs':..}
        :raise CmpApiClientError:
        """
        params = ['accounts', 'states', 'tags', 'ids']
        mappings = {
            'tags': lambda x: x.split(','),
            'ids': lambda x: x.split(','),
            'states': lambda x: x.split(','),
        }
        aliases = {
            'accounts': 'owner-id.N',
            'ids': 'instance-id.N',
            'tags': 'tag-value.N',
            'states': 'state.N',
            'size': 'Nvl_MaxResults',
            'page': 'Nvl_NextToken'
        }
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri('computeservices/vpc/describevpcs', preferred_version='v1.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeVpcsResponse')
        res = {
            'count': len(res.get('vpcSet')),
            'page': kwargs.get('NextToken', 0),
            'total': res.get('nvl-vpcTotal'),
            'sort': {'field': 'id', 'order': 'asc'},
            'vpcs': res.get('vpcSet')
        }
        self.logger.debug('get vpcs: %s' % truncate(res))
        return res

    def get(self, oid, **kwargs):
        """get vpc

        :param oid: vpc id or uuid
        :return: vpc
        :raise CmpApiClientError:
        """
        if self.is_uuid(oid):
            kwargs.update({'vpc-id.N': [oid]})
        # elif self.is_name(oid):
        #     kwargs.update({'name.N': [oid]})

        # params = ['vpc-id.N', 'name.N']
        params = ['vpc-id.N']
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri('computeservices/vpc/describevpcs', preferred_version='v1.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeVpcsResponse.vpcSet', default=[])
        if len(res) > 0:
            res = res[0]
        else:
            raise CmpApiManagerError('vpc %s does not exist' % oid)
        self.logger.debug('get vpc%s: %s' % (oid, truncate(res)))
        return res

    # def add(self, name, account, subnet, itype, image, sg, **kwargs):
    #     """Add security group
    #
    #     :param str name: security group name
    #     :param str account: parent account id
    #     :param str type: security group type
    #     :param str subnet: security group subnet id
    #     :param str image: security group image id
    #     :param str sg: security group security group id
    #     :param str AdditionalInfo: security group description [optional]
    #     :param str KeyName: security group ssh key name [optional]
    #     :param str AdminPassword: security group admin/root password [optional]
    #     :param list BlockDevices: block evice config. Use [{'index': 0, 'type':.. 'uuid':.., 'size':..}] to update
    #         root block device. Add {'index': [1..100], 'type':.. 'uuid':.., 'size':..} to create additional block
    #         devices. Set uuid (compute volume uuid) when you want to clone existing volume [optional]
    #     :param str Nvl_Hypervisor: security group hypervisor. Can be: openstack or vsphere [default=openstack]
    #     :param str Nvl_HostGroup: security group host group. Ex. oracle [optional]
    #     :param bool Nvl_MultiAvz: set to False create vm to work only in the selected availability zone [default=False]
    #     :param dict Nvl_Metadata: security group custom metadata [optional]
    #     :return:
    #     :raises CmpApiClientError: raise :class:`CmpApiClientError`
    #     """
    #     data = {
    #         'Name': name,
    #         'owner-id': account,
    #         'AdditionalInfo': '',
    #         'SubnetId': subnet,
    #         'InstanceType': itype,
    #         'ImageId': image,
    #         'SecurityGroupId.N': [sg]
    #     }
    #
    #     hypervisor = kwargs.get('Nvl_Hypervisor', 'openstack')
    #     if hypervisor not in self.AVAILABLE_HYPERVISORS:
    #         raise CmpApiManagerError('supported hypervisor are %s' % self.AVAILABLE_HYPERVISORS)
    #     data['Nvl_Hypervisor'] = hypervisor
    #
    #     data['Nvl_MultiAvz'] = kwargs.get('Nvl_MultiAvz', True)
    #     data['AdminPassword'] = kwargs.get('AdminPassword', random_password(10))
    #
    #     # set disks
    #     blocks = [{'Ebs': {}}]
    #     data['BlockDeviceMapping.N'] = blocks
    #     block_devices = kwargs.get('BlockDevices', [])
    #     for block_device in block_devices:
    #         index = block_device.get('index')
    #
    #         if index == 0:
    #             blocks[0] = self.__config_block(block_device)
    #         else:
    #             blocks.append(self.__config_block(block_device))
    #
    #     other_params = ['AdditionalInfo', 'KeyName', 'Nvl_Metadata', 'Nvl_HostGroup']
    #     data.update(self.format_request_data(kwargs, other_params))
    #     uri = self.get_uri('computeservices/vpc/createvpc')
    #     res = self.api_post(uri, data={'instance': data})
    #     res = dict_get(res, 'RunInstanceResponse.instancesSet.0.instanceId')
    #     self.logger.debug('Create security group %s' % res)
    #     return res
    #
    # def __set_data(self, input_data, input_field, search_data, search_field):
    #     custom_data = input_data.get(input_field, None)
    #     if custom_data is None:
    #         data = dict_get(search_data, search_field)
    #     else:
    #         data = custom_data
    #     return data
    #
    # def clone(self, oid, name, **kwargs):
    #     """clone security group
    #
    #     :param oid: id of the security group to clone
    #     :param name: security group name
    #     :param kwargs.account: parent account id [optional]
    #     :param kwargs.type: security group type [optional]
    #     :param kwargs.subnet: security group subnet id [optional]
    #     :param kwargs.sg: security group security group id [optional]
    #     :param kwargs.sshkey: security group ssh key name [optional]
    #     :param str kwargs.AdminPassword: security group admin/root password [optional]
    #     :param bool kwargs.Nvl_MultiAvz: set to False create vm to work only in the selected availability zone
    #         [default=False]
    #     :param dict kwargs.Nvl_Metadata: security group custom metadata [optional]
    #     :return:
    #     :raises CmpApiClientError: raise :class:`CmpApiClientError`
    #     """
    #     # get original vm
    #     vm = self.get(oid)
    #
    #     image_name = dict_get(vm, 'nvl-imageName')
    #     account = self.__set_data(kwargs, 'account', vm, 'nvl-ownerId')
    #     image = self.manager.business.service.inst.list(image_name, account_id=account)
    #     itype = self.__set_data(kwargs, 'type', vm, 'instanceType')
    #     subnet = self.__set_data(kwargs, 'subnet', vm, 'subnetId')
    #     sg = self.__set_data(kwargs, 'sg', vm, 'groupSet.0.groupId')
    #     kwargs['KeyName'] = self.__set_data(kwargs, 'sshkey', vm, 'keyName')
    #
    #     # set disks
    #     blocks = []
    #     index = 0
    #     for disk in vm.get('blockDeviceMapping', []):
    #         blocks.append({
    #             'index': index,
    #             'uuid': dict_get(disk, 'ebs.volumeId'),
    #             'size': dict_get(disk, 'ebs.volumeSize')
    #         })
    #     kwargs['BlockDevices'] = blocks
    #
    #     res = self.add(name, account, subnet, itype, image, sg, **kwargs)
    #     return res
    #
    # def load(self, oid, **kwargs):
    #     """import security group from existing resource
    #
    #     :param oid: id of the security group
    #     :param container: container id where import security group', 'action': 'store', 'type': str}),
    #     :param name: security group name', 'action': 'store', 'type': str}),
    #     :param vm: physical id of the security group to import', 'action': 'store', 'type': str}),
    #     :param image: compute image id', 'action': 'store', 'type': str}),
    #     :param pwd: security group password', 'action': 'store', 'type': str}),
    #     :param -sshkey: security group ssh key name
    #     :param account: parent account id
    #
    #
    #     :param -type: security group type
    #     :param -subnet: security group subnet id
    #     :param -sg: security group security group id
    #
    #     :param -pwd: security group admin/root password', 'action': 'store', 'type': str,
    #                     'default': None}),
    #     :param -multi-avz: if set to False create vm to work only in the selected availability zone '
    #                                   '[default=True]. Use when subnet cidr is public', 'action': 'store', 'type': str,
    #                           'default': True}),
    #     :param -meta: security group custom metadata
    #     :return:
    #     :raises CmpApiClientError: raise :class:`CmpApiClientError`
    #     """
    #     data = self.format_request_data(kwargs, ['name', 'desc', 'ext_id', 'active', 'attribute', 'tags'])
    #     uri = self.get_uri('security groups/%s' % oid)
    #     res = self.api_put(uri, data={'resource': data})
    #     self.logger.debug('Update security group %s' % oid)
    #     return res
    #
    # def update(self, oid, **kwargs):
    #     """Update security group
    #
    #     :param oid: id of the security group
    #     :param kwargs.InstanceType: security group type [optional]
    #     :param kwargs.sgs: list of security group security group id to add or remove. Syntax: [<sg_id>:ADD, <sg_id>:DE]
    #         [optional]
    #     :return:
    #     :raises CmpApiClientError: raise :class:`CmpApiClientError`
    #     """
    #     data = {'InstanceId': oid}
    #     sgs = kwargs.pop('sgs', None)
    #     if sgs is not None:
    #         data['GroupId.N'] = sgs
    #     data.update(self.format_request_data(kwargs, ['InstanceType']))
    #     uri = self.get_uri('computeservices/vpc/modifyinstanceattribute')
    #     res = self.api_put(uri, data={'instance': data})
    #     self.logger.debug('Update security group %s' % oid)
    #     return res
    #
    # def delete(self, oid, delete_services=True, delete_tags=True):
    #     """Delete security group
    #
    #     :param oid: id of the security group
    #     :param delete_services: if True delete chiild services
    #     :param delete_tags: if True delete child tags
    #     :return:
    #     :raises CmpApiClientError: raise :class:`CmpApiClientError`
    #     """
    #     kwargs = {'InstanceId.N': [oid]}
    #     params = ['InstanceId.N']
    #     data = self.format_paginated_query(kwargs, params)
    #     uri = self.get_uri('computeservices/vpc/terminateinstances')
    #     self.api_delete(uri, data=data)
    #     self.logger.debug('delete security group %s' % oid)
    #
    # def get_types(self, *args, **kwargs):
    #     """get security group types
    #
    #     :param account: account id
    #     :param size: list page
    #     :param page: list page size
    #     :return: list of security group types {'count':.., 'page':.., 'total':.., 'sort':.., 'types':..}
    #     :raise CmpApiClientError:
    #     """
    #     params = ['account', 'size', 'page']
    #     mappings = {}
    #     aliases = {
    #         'account': 'owner-id',
    #         'size': 'MaxResults',
    #         'page': 'NextToken'
    #     }
    #     data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
    #     uri = self.get_uri('computeservices/vpc/describeinstancetypes', preferred_version='v2.0', **kwargs)
    #     res = self.api_get(uri, data=data)
    #     res = dict_get(res, 'DescribeInstanceTypesResponse')
    #     res = {
    #         'count': len(res.get('instanceTypesSet')),
    #         'page': kwargs.get('NextToken', 0),
    #         'total': res.get('instanceTypesTotal'),
    #         'sort': {'field': 'id', 'order': 'asc'},
    #         'types': res.get('instanceTypesSet')
    #     }
    #     self.logger.debug('get security group types: %s' % truncate(res))
    #     return res


class CmpBusinessNetaasSubnetService(CmpBusinessAbstractService):
    """Cmp business network service - subnet
    """
    VERSION = 'v1.0'


class CmpBusinessNetaasSecurityGroupService(CmpBusinessAbstractService):
    """Cmp business network service - security group
    """
    VERSION = 'v1.0'
    
    def list(self, *args, **kwargs):
        """get security groups

        :param accounts: list of account id comma separated
        :param ids: list of security group id comma separated
        :param vpcs: list of vpc id comma separated
        :param tags: list of tag comma separated
        :param page: list page
        :param size: list page size
        :return: list of security groups {'count':.., 'page':.., 'total':.., 'sort':.., 'security_groups':..}
        :raise CmpApiClientError:
        """
        params = ['accounts', 'ids', 'tags', 'vpcs']
        mappings = {
            'tags': lambda x: x.split(','),
            'vpcs': lambda x: x.split(','),
            'ids': lambda x: x.split(',')
        }
        aliases = {
            'accounts': 'owner-id.N',
            'ids': 'group-id.N',
            'tags': 'tag-key.N',
            'vpcs': 'vpc-id.N',
            'size': 'MaxResults',
            'page': 'NextToken'
        }
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri('computeservices/securitygroup/describesecuritygroups', preferred_version='v1.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeSecurityGroupsResponse')
        res = {
            'count': len(res.get('securityGroupInfo')),
            'page': kwargs.get('page', 0),
            'total': res.get('nvl-securityGroupTotal'),
            'sort': {'field': 'id', 'order': 'asc'},
            'security_groups': res.get('securityGroupInfo')
        }
        self.logger.debug('get security groups: %s' % truncate(res))
        return res

    def get(self, oid, **kwargs):
        """get security group

        :param oid: security group id or uuid
        :return: security groups
        :raise CmpApiClientError:
        """
        kwargs = {'GroupName.N': [oid]}
        params = ['GroupName.N', 'name.N']
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri('computeservices/securitygroup/describesecuritygroups', preferred_version='v1.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeSecurityGroupsResponse.securityGroupInfo', default=[])
        if len(res) > 0:
            res = res[0]
        else:
            raise CmpApiManagerError('security group %s does not exist' % oid)
        self.logger.debug('get security group %s: %s' % (oid, truncate(res)))
        return res

    def add(self, name, vpc, template=None, **kwargs):
        """Add security group

        :param str name: security group name
        :param str vpc: parent vpc id
        :param str template: security group template id [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'GroupName': name,
            'VpcId': vpc
        }
        sg_type = template
        if sg_type is not None:
            data['GroupType'] = sg_type

        uri = self.get_uri('computeservices/securitygroup/createsecuritygroup')        
        res = self.api_post(uri, data={'security_group': data})
        res = dict_get(res, 'CreateSecurityGroupResponse.groupId')
        self.logger.debug('Create security group %s' % res)
        return res

    def delete(self, oid):
        """Delete security group

        :param oid: id of the security group
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('computeservices/securitygroup/deletesecuritygroup')
        self.api_delete(uri, data={'security_group': {'GroupName': oid}})
        self.logger.debug('delete security group %s' % oid)

    def add_rule(self, oid, rule_type, proto=None, port=None, dest=None, source=None):
        """add security group rule

        :param oid: id of the security group
        :param rule_type: egress or ingress. For egress rule the destination. For ingress rule specify the source
        :param proto: protocol. can be tcp, udp, icmp or -1 for all. [optional]
        :param port: can be an integer between 0 and 65535 or a range with start and end in the same interval. Range
            format is <start>-<end>. Use -1 for all ports. Set subprotocol if proto is icmp (8 for ping). [optional]
        :param dest: rule destination. Syntax <type>:<value>. Destination type can be SG, CIDR. For SG value must be
            <sg_id>. For CIDR value should like 10.102.167.0/24. [optional]
        :param source: rule source. Syntax <type>:<value>. Source type can be SG, CIDR. For SG value must be <sg_id>.
            For CIDR value should like 10.102.167.0/24. [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        from_port = -1
        to_port = -1
        if port is not None:
            port = str(port)
            port = port.split('-')
            if len(port) == 1:
                from_port = to_port = port[0]
            else:
                from_port, to_port = port

        if proto is None:
            proto = '-1'

        if rule_type not in ['ingress', 'egress']:
            raise CmpApiClientError('rule type must be ingress or egress')
        if rule_type == 'ingress':
            if source is None:
                raise CmpApiClientError('ingress rule require source')
            dest = source.split(':')
        elif rule_type == 'egress':
            if dest is None:
                raise CmpApiClientError('egress rule require destination')
            dest = dest.split(':')
        if dest[0] not in ['SG', 'CIDR']:
            raise CmpApiClientError('source/destination type must be SG or CIDR')
        data = {
            'GroupName': oid,
            'IpPermissions.N': [
                {
                    'FromPort': from_port,
                    'ToPort': to_port,
                    'IpProtocol': proto
                }
            ]
        }
        if dest[0] == 'SG':
            data['IpPermissions.N'][0]['UserIdGroupPairs'] = [{
                'GroupName': dest[1]
            }]
        elif dest[0] == 'CIDR':
            data['IpPermissions.N'][0]['IpRanges'] = [{
                'CidrIp': dest[1]
            }]
        else:
            raise Exception('Wrong rule type')

        if rule_type == 'egress':
            uri = self.get_uri('computeservices/securitygroup/authorizesecuritygroupegress')
            self.task_key = 'AuthorizeSecurityGroupEgressResponse.nvl-activeTask'
        elif rule_type == 'ingress':
            uri = self.get_uri('computeservices/securitygroup/authorizesecuritygroupingress')
            self.task_key = 'AuthorizeSecurityGroupIngressResponse.nvl-activeTask'
        res = self.api_post(uri, data={'rule': data})
        self.logger.debug('create security group %s rule' % oid)
        return res

    def del_rule(self, oid, rule_type, proto=None, port=None, dest=None, source=None):
        """delete security group rule

        :param oid: id of the security group
        :param rule_type: egress or ingress. For egress rule the destination. For ingress rule specify the source
        :param proto: protocol. can be tcp, udp, icmp or -1 for all. [optional]
        :param port: can be an integer between 0 and 65535 or a range with start and end in the same interval. Range
            format is <start>-<end>. Use -1 for all ports. Set subprotocol if proto is icmp (8 for ping). [optional]
        :param dest: rule destination. Syntax <type>:<value>. Destination type can be SG, CIDR. For SG value must be
            <sg_id>. For CIDR value should like 10.102.167.0/24. [optional]
        :param source: rule source. Syntax <type>:<value>. Source type can be SG, CIDR. For SG value must be <sg_id>.
            For CIDR value should like 10.102.167.0/24. [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        from_port = -1
        to_port = -1
        if port is not None:
            port = str(port)
            port = port.split('-')
            if len(port) == 1:
                from_port = to_port = port[0]
            else:
                from_port, to_port = port

        if proto is None:
            proto = '-1'

        if rule_type not in ['ingress', 'egress']:
            raise Exception('rule type must be ingress or egress')
        if rule_type == 'ingress':
            if source is None:
                raise Exception('ingress rule require source')
            dest = source.split(':')
        elif rule_type == 'egress':
            if dest is None:
                raise Exception('egress rule require destination')
            dest = dest.split(':')
        if dest[0] not in ['SG', 'CIDR']:
            raise Exception('source/destination type must be SG or CIDR')
        data = {
            'GroupName': oid,
            'IpPermissions.N': [
                {
                    'FromPort': from_port,
                    'ToPort': to_port,
                    'IpProtocol': proto
                }
            ]
        }
        if dest[0] == 'SG':
            data['IpPermissions.N'][0]['UserIdGroupPairs'] = [{'GroupName': dest[1]}]
        elif dest[0] == 'CIDR':
            data['IpPermissions.N'][0]['IpRanges'] = [{'CidrIp': dest[1]}]
        else:
            raise Exception('wrong rule type')

        if rule_type == 'egress':
            uri = self.get_uri('computeservices/securitygroup/revokesecuritygroupegress')
            self.task_key = 'RevokeSecurityGroupEgressResponse.nvl-activeTask'
        elif rule_type == 'ingress':
            uri = self.get_uri('computeservices/securitygroup/revokesecuritygroupingress')
            self.task_key = 'RevokeSecurityGroupIngressResponse.nvl-activeTask'
        self.api_delete(uri, data={'rule': data})
        self.logger.debug('delete security group %s rule' % oid)


class CmpBusinessNetaasGatewayService(CmpBusinessAbstractService):
    """Cmp business network service - gateway
    """
    VERSION = 'v1.0'
