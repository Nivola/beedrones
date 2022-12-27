# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.password import random_password
from beecell.simple import truncate
from beecell.types.type_dict import dict_get
from beedrones.cmp.business import CmpBusinessAbstractService
from beedrones.cmp.client import CmpBaseService, CmpApiManagerError


class CmpBusinessCpaasService(CmpBusinessAbstractService):
    """Cmp business compute service
    """
    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        self.backup = None
        self.instance = CmpBusinessCpaasInstanceService(self.manager)


class CmpBusinessCpaasInstanceService(CmpBusinessAbstractService):
    """Cmp business compute service - compute instance
    """
    VERSION = 'v2.0'
    AVAILABLE_HYPERVISORS = ['openstack', 'vsphere']

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

    def list(self, *args, **kwargs):
        """get virtual machines

        :param accounts: list of account id comma separated
        :param ids: list of vm id comma separated
        :param name: vm name
        :param names: vm name pattern
        :param types: list of type comma separated
        :param launch-time.N: launch time interval. Ex. 2021-01-30T:2021-01-31T
        :param tags: list of tag comma separated
        :param instance-state-name.N: list of instance state comma separated
        :param sg: list of security group id comma separated. Ex. pending, running, error
        :param page: list page
        :param size: list page size
        :param services: print instance service enabling. Ex. backup, monitoring
        :return: list of virtual machines {'count':.., 'page':.., 'total':.., 'sort':.., 'instances':..}
        :raise CmpApiClientError:
        """
        params = ['accounts', 'ids', 'types', 'name', 'names', 'tags', 'sg', 'states']
        mappings = {
            'tags': lambda x: x.split(','),
            'types': lambda x: x.split(','),
            'ids': lambda x: x.split(','),
            'name': lambda x: x.split(','),
            'names': lambda x: '%' + x + '%',
            'sg': lambda x: x.split(','),
            'launch-time.N': lambda x: x.split(','),
            'states': lambda x: x.split(','),
        }
        aliases = {
            'accounts': 'owner-id.N',
            'ids': 'instance-id.N',
            'types': 'instance-type.N',
            'name': 'name.N',
            'names': 'name-pattern',
            'tags': 'tag-key.N',
            'sg': 'instance.group-id.N',
            'launch_time': 'launch-time.N',
            'states': 'instance-state-name.N',
            'size': 'MaxResults',
            'page': 'NextToken'
        }
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri('computeservices/instance/describeinstances', preferred_version='v2.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeInstancesResponse.reservationSet.0')
        res = {
            'count': len(res.get('instancesSet')),
            'page': kwargs.get('NextToken', 0),
            'total': res.get('nvl-instanceTotal'),
            'sort': {'field': 'id', 'order': 'asc'},
            'instances': res.get('instancesSet')
        }
        self.logger.debug('get virtual machines: %s' % truncate(res))
        return res

    def get(self, oid, **kwargs):
        """get virtual machine

        :param oid: virtual machine id or uuid
        :return: virtual machine
        :raise CmpApiClientError:
        """
        if self.is_uuid(oid):
            kwargs.update({'instance-id.N': [oid]})
        elif self.is_name(oid):
            kwargs.update({'name.N': [oid]})

        params = ['instance-id.N', 'name.N']
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri('computeservices/instance/describeinstances', preferred_version='v2.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeInstancesResponse.reservationSet.0.instancesSet', default=[])
        if len(res) > 0:
            res = res[0]
        else:
            raise CmpApiManagerError('virtual machine %s does not exist' % oid)
        self.logger.debug('get virtual machine %s: %s' % (oid, truncate(res)))
        return res

    def __config_block(self, data):
        uuid = data.get('uuid', None)
        size = data.get('size', None)
        volume_type = data.get('type', None)
        if uuid is not None:
            ebs = {'Nvl_VolumeId': uuid}
        elif size is not None:
            ebs = {'VolumeSize': size}
        if volume_type is not None:
            ebs['VolumeType'] = volume_type
        return {'Ebs': ebs}

    def add(self, name, account, subnet, itype, image, sg, **kwargs):
        """Add virtual machine

        :param str name: virtual machine name
        :param str account: parent account id
        :param str type: virtual machine type
        :param str subnet: virtual machine subnet id
        :param str image: virtual machine image id
        :param str sg: virtual machine security group id
        :param str PrivateIpAddress: static ip address [optional]
        :param str AdditionalInfo: virtual machine description [optional]
        :param str KeyName: virtual machine ssh key name [optional]
        :param str AdminPassword: virtual machine admin/root password [optional]
        :param list BlockDevices: block evice config. Use [{'index': 0, 'type':.. 'uuid':.., 'size':..}] to update
            root block device. Add {'index': [1..100], 'type':.. 'uuid':.., 'size':..} to create additional block
            devices. Set uuid (compute volume uuid) when you want to clone existing volume [optional]
        :param str Nvl_Hypervisor: virtual machine hypervisor. Can be: openstack or vsphere [default=openstack]
        :param str Nvl_HostGroup: virtual machine host group. Ex. oracle [optional]
        :param bool Nvl_MultiAvz: set to False create vm to work only in the selected availability zone [default=False]
        :param dict Nvl_Metadata: virtual machine custom metadata [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'Name': name,
            'owner-id': account,
            'AdditionalInfo': '',
            'SubnetId': subnet,
            'InstanceType': itype,
            'ImageId': image,
            'SecurityGroupId.N': [sg]
        }

        hypervisor = kwargs.get('Nvl_Hypervisor', 'openstack')
        if hypervisor not in self.AVAILABLE_HYPERVISORS:
            raise CmpApiManagerError('supported hypervisor are %s' % self.AVAILABLE_HYPERVISORS)
        data['Nvl_Hypervisor'] = hypervisor

        data['Nvl_MultiAvz'] = kwargs.get('Nvl_MultiAvz', True)
        data['AdminPassword'] = kwargs.get('AdminPassword', random_password(10))

        # set disks
        blocks = [{'Ebs': {}}]
        data['BlockDeviceMapping.N'] = blocks
        block_devices = kwargs.get('BlockDevices', [])
        for block_device in block_devices:
            index = block_device.get('index')

            if index == 0:
                blocks[0] = self.__config_block(block_device)
            else:
                blocks.append(self.__config_block(block_device))

        other_params = ['AdditionalInfo', 'KeyName', 'Nvl_Metadata', 'Nvl_HostGroup', 'PrivateIpAddress']
        data.update(self.format_request_data(kwargs, other_params))
        uri = self.get_uri('computeservices/instance/runinstances')
        res = self.api_post(uri, data={'instance': data})
        res = dict_get(res, 'RunInstanceResponse.instancesSet.0.instanceId')
        self.logger.debug('Create virtual machine %s' % res)
        return res

    def __set_data(self, input_data, input_field, search_data, search_field):
        custom_data = input_data.get(input_field, None)
        if custom_data is None:
            data = dict_get(search_data, search_field)
        else:
            data = custom_data
        return data

    def clone(self, oid, name, **kwargs):
        """clone virtual machine

        :param oid: id of the virtual machine to clone
        :param name: virtual machine name
        :param kwargs.account: parent account id [optional]
        :param kwargs.type: virtual machine type [optional]
        :param kwargs.subnet: virtual machine subnet id [optional]
        :param kwargs.sg: virtual machine security group id [optional]
        :param kwargs.sshkey: virtual machine ssh key name [optional]
        :param str kwargs.AdminPassword: virtual machine admin/root password [optional]
        :param bool kwargs.Nvl_MultiAvz: set to False create vm to work only in the selected availability zone
            [default=False]
        :param dict kwargs.Nvl_Metadata: virtual machine custom metadata [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        # get original vm
        vm = self.get(oid)

        image_name = dict_get(vm, 'nvl-imageName')
        account = self.__set_data(kwargs, 'account', vm, 'nvl-ownerId')
        image = self.manager.business.service.inst.list(image_name, account_id=account)
        itype = self.__set_data(kwargs, 'type', vm, 'instanceType')
        subnet = self.__set_data(kwargs, 'subnet', vm, 'subnetId')
        sg = self.__set_data(kwargs, 'sg', vm, 'groupSet.0.groupId')
        kwargs['KeyName'] = self.__set_data(kwargs, 'sshkey', vm, 'keyName')

        # set disks
        blocks = []
        index = 0
        for disk in vm.get('blockDeviceMapping', []):
            blocks.append({
                'index': index,
                'uuid': dict_get(disk, 'ebs.volumeId'),
                'size': dict_get(disk, 'ebs.volumeSize')
            })
        kwargs['BlockDevices'] = blocks

        res = self.add(name, account, subnet, itype, image, sg, **kwargs)
        return res

    def load(self, oid, **kwargs):
        """import virtual machine from existing resource

        :param oid: id of the virtual machine
        :param container: container id where import virtual machine', 'action': 'store', 'type': str}),
        :param name: virtual machine name', 'action': 'store', 'type': str}),
        :param vm: physical id of the virtual machine to import', 'action': 'store', 'type': str}),
        :param image: compute image id', 'action': 'store', 'type': str}),
        :param pwd: virtual machine password', 'action': 'store', 'type': str}),
        :param -sshkey: virtual machine ssh key name
        :param account: parent account id


        :param -type: virtual machine type
        :param -subnet: virtual machine subnet id
        :param -sg: virtual machine security group id

        :param -pwd: virtual machine admin/root password', 'action': 'store', 'type': str,
                        'default': None}),
        :param -multi-avz: if set to False create vm to work only in the selected availability zone '
                                      '[default=True]. Use when subnet cidr is public', 'action': 'store', 'type': str,
                              'default': True}),
        :param -meta: virtual machine custom metadata
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = self.format_request_data(kwargs, ['name', 'desc', 'ext_id', 'active', 'attribute', 'tags'])
        uri = self.get_uri('virtual machines/%s' % oid)
        res = self.api_put(uri, data={'resource': data})
        self.logger.debug('Update virtual machine %s' % oid)
        return res

    def update(self, oid, **kwargs):
        """Update virtual machine

        :param oid: id of the virtual machine
        :param kwargs.InstanceType: virtual machine type [optional]
        :param kwargs.sgs: list of virtual machine security group id to add or remove. Syntax: [<sg_id>:ADD, <sg_id>:DE]
            [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {'InstanceId': oid}
        sgs = kwargs.pop('sgs', None)
        if sgs is not None:
            data['GroupId.N'] = sgs
        data.update(self.format_request_data(kwargs, ['InstanceType']))
        uri = self.get_uri('computeservices/instance/modifyinstanceattribute')
        res = self.api_put(uri, data={'instance': data})
        self.logger.debug('Update virtual machine %s' % oid)
        return res

    def delete(self, oid, delete_services=True, delete_tags=True):
        """Delete virtual machine

        :param oid: id of the virtual machine
        :param delete_services: if True delete chiild services
        :param delete_tags: if True delete child tags
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        kwargs = {'InstanceId.N': [oid]}
        data = self.format_request_data(kwargs, ['InstanceId.N'])
        uri = self.get_uri('computeservices/instance/terminateinstances')
        self.api_delete(uri, data=data)
        self.logger.debug('delete virtual machine %s' % oid)

    def start(self, oid, schedule=None):
        """Start virtual machine

        :param oid: id of the virtual machine
        :param schedule: schedule definition. Pass as json file using crontab or timedelta syntax.
            Ex. {\"type\": \"timedelta\", \"minutes\": 1}        
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        kwargs = {'InstanceId.N': [oid], 'Schedule': schedule}
        params = ['InstanceId.N', 'Schedule']
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri('computeservices/instance/startinstances')
        self.api_delete(uri, data=data)
        self.logger.debug('start virtual machine %s' % oid)

    def stop(self, oid, schedule=None):
        """Stop virtual machine

        :param oid: id of the virtual machine
        :param schedule: schedule definition. Pass as json file using crontab or timedelta syntax.
            Ex. {\"type\": \"timedelta\", \"minutes\": 1}        
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        kwargs = {'InstanceId.N': [oid], 'Schedule': schedule}
        params = ['InstanceId.N', 'Schedule']
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri('computeservices/instance/stoptinstances')
        self.api_delete(uri, data=data)
        self.logger.debug('stop virtual machine %s' % oid)

    def reboot(self, oid, schedule=None):
        """Reboot virtual machine

        :param oid: id of the virtual machine
        :param schedule: schedule definition. Pass as json file using crontab or timedelta syntax.
            Ex. {\"type\": \"timedelta\", \"minutes\": 1}        
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        kwargs = {'InstanceId.N': [oid], 'Schedule': schedule}
        params = ['InstanceId.N', 'Schedule']
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri('computeservices/instance/rebootinstances')
        self.api_delete(uri, data=data)
        self.logger.debug('reboot virtual machine %s' % oid)

    def enable_monitoring(self, oid, templates=None):
        """enable virtual machine monitoring

        :param oid: id of the virtual machine
        :param templates: monitoring template list      
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        kwargs = {'InstanceId.N': [oid], 'Nvl_Templates': templates}
        params = ['InstanceId.N', 'Nvl_Templates']
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri('computeservices/instance/monitorinstances')
        self.api_delete(uri, data=data)
        self.logger.debug('enable virtual machine %s monitoring' % oid)

    def enable_logging(self, oid, files=None, pipeline=None):
        """enable virtual machine logging

        :param oid: id of the virtual machine
        :param files: list of file to capture
        :param pipeline: log collector pipeline port
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        kwargs = {'InstanceId.N': [oid], 'Files': files, 'Pipeline': pipeline}
        params = ['InstanceId.N', 'Files', 'Pipeline']
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri('computeservices/instance/forwardloginstances')
        self.api_delete(uri, data=data)
        self.logger.debug('enable virtual machine %s logging' % oid)

    def get_console(self, oid, *args, **kwargs):
        """get virtual machine console

        :param oid: virtual machine id or uuid
        :return: virtual machine console
        :raise CmpApiClientError:
        """
        kwargs.update({'InstanceId': oid})
        params = ['InstanceId']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('computeservices/instance/getconsole', preferred_version='v2.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'GetConsoleResponse.console', default={})
        self.logger.debug('get virtual machine %s console: %s' % (oid, truncate(res)))
        return res

    def get_types(self, *args, **kwargs):
        """get virtual machine types

        :param account: account id
        :param size: list page
        :param page: list page size
        :return: list of virtual machine types {'count':.., 'page':.., 'total':.., 'sort':.., 'types':..}
        :raise CmpApiClientError:
        """
        params = ['account', 'size', 'page']
        mappings = {}
        aliases = {
            'account': 'owner-id',
            'size': 'MaxResults',
            'page': 'NextToken'
        }
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri('computeservices/instance/describeinstancetypes', preferred_version='v2.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeInstanceTypesResponse')
        res = {
            'count': len(res.get('instanceTypesSet')),
            'page': kwargs.get('NextToken', 0),
            'total': res.get('instanceTypesTotal'),
            'sort': {'field': 'id', 'order': 'asc'},
            'types': res.get('instanceTypesSet')
        }
        self.logger.debug('get virtual machine types: %s' % truncate(res))
        return res

    #
    # snapshot
    #
    def get_snapshots(self, oid, *args, **kwargs):
        """list virtual machine snapshots

        :param oid: virtual machine id or uuid
        :return: virtual machine console
        :raise CmpApiClientError:
        """
        kwargs = {'InstanceId.N': [oid]}
        params = ['InstanceId.N']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('computeservices/instance/describeinstancesnapshots' % oid)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeInstanceSnapshotsResponse.instancesSet', default={})
        self.logger.debug('get virtual machine %s snapshots: %s' % (oid, truncate(res)))
        return res
    
    def add_snapshot(self, oid, snapshot, *args, **kwargs):
        """Add virtual machine snapshot

        :param oid: virtual machine id or uuid
        :param snapshot: snapshot name
        :return: 
        :raise CmpApiClientError:
        """
        kwargs = {'InstanceId.N': [oid], 'SnapshotName': snapshot}
        params = ['InstanceId.N', 'SnapshotName']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('computeservices/instance/createinstancesnapshots' % oid)
        res = self.api_put(uri, data=data)
        self.logger.debug('add virtual machine %s snapshot: %s' % (oid, truncate(res)))
        return res
    
    def del_snapshot(self, oid, snapshot, *args, **kwargs):
        """Delete virtual machine snapshot

        :param oid: virtual machine id or uuid
        :param SnapshotId: snapshot id
        :return: 
        :raise CmpApiClientError:
        """
        kwargs = {'InstanceId.N': [oid], 'SnapshotId': snapshot}
        params = ['InstanceId.N', 'SnapshotId']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('computeservices/instance/deleteinstancesnapshots' % oid)
        res = self.api_put(uri, data=data)
        self.logger.debug('delete virtual machine %s snapshot: %s' % (oid, truncate(res)))
        return res
    
    def revert_snapshot(self, oid, snapshot, *args, **kwargs):
        """Revert virtual machine snapshot

        :param oid: virtual machine id or uuid
        :param snapshot: snapshot name
        :return: 
        :raise CmpApiClientError:
        """
        kwargs = {'InstanceId.N': [oid], 'SnapshotId': snapshot}
        params = ['InstanceId.N', 'SnapshotId']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('computeservices/instance/revertinstancesnapshots' % oid)
        res = self.api_put(uri, data=data)
        self.logger.debug('revert virtual machine %s snapshot: %s' % (oid, truncate(res)))
        return res
    
    #
    # user
    #
    def __user_action(self, oid, action, **user_params):
        """Run user action on the virtual machine"""
        params = {'Nvl_Action': action}
        params.update(user_params)
        data = {
            'InstanceId': oid,
            'Nvl_User': params
        }
        data = {'instance': data}
        uri = self.get_uri('computeservices/instance/modifyinstanceattribute' % oid)
        res = self.api_put(uri, data=data).get('ModifyInstanceAttributeResponse')
        self.logger.debug('manage virtual machine %s users: %s' % (oid, truncate(res)))
        return res
        
    def add_user(self, oid, name, pwd, key, *args, **kwargs):
        """add virtual machine user

        :param oid: virtual machine id or uuid
        :param name: user name
        :param pwd: user password
        :param key: ssh key id
        :return: 
        :raise CmpApiClientError:
        """
        res = self.__user_action(oid, 'add', Nvl_Name=name, Nvl_Password=pwd, Nvl_SshKey=key)
        self.logger.debug('add virtual machine %s user: %s' % oid)
        return res

    def del_user(self, oid, name, *args, **kwargs):
        """delete virtual machine user

        :param oid: virtual machine id or uuid
        :param name: user name
        :return: 
        :raise CmpApiClientError:
        """
        res = self.__user_action(oid, 'delete', Nvl_Name=name)
        self.logger.debug('delete virtual machine %s user: %s' % oid)
        return res
    
    def set_user_password(self, oid, name, pwd, *args, **kwargs):
        """set virtual machine user password

        :param oid: virtual machine id or uuid
        :param name: user name
        :param pwd: user password
        :return: 
        :raise CmpApiClientError:
        """
        res = self.__user_action(oid, 'set-password', Nvl_Name=name, Nvl_Password=pwd)
        self.logger.debug('set virtual machine %s user password: %s' % oid)
        return res

    #
    # backup
    #
    def get_backup_restore_points(self, oid, *args, **kwargs):
        """list virtual machine backup restore points

        :param oid: virtual machine id or uuid
        :return: virtual machine console
        :raise CmpApiClientError:
        """
        kwargs = {'InstanceId.N': [oid]}
        params = ['InstanceId.N']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('computeservices/instancebackup/describebackuprestorepoints',
                           preferred_version='v1.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeBackupRestorePointsResponse.instanceBackupSet.0', default=[])
        self.logger.debug('get virtual machine %s snapshots: %s' % (oid, truncate(res)))
        return res

    def add_backup_restore_point(self, oid, full=True, *args, **kwargs):
        """Add virtual machine backup restore point

        :param oid: virtual machine id or uuid
        :param full: if True make a full backup
        :return:
        :raise CmpApiClientError:
        """
        data = {
            'InstanceId.N': [oid],
            'BackupFull': full
        }
        uri = self.get_uri('computeservices/instancebackup/createbackuprestorepoints')
        res = self.api_post(uri, data=data)
        uuid = dict_get(res, 'CreateBackupRestorePoints.instanceBackupSet.0.instanceId')
        self.logger.debug('add virtual machine %s backup restore point: %s' % (oid, uuid))
        return res

    def del_backup_restore_point(self, oid, restore_point_id, *args, **kwargs):
        """Delete virtual machine backup restore point

        :param oid: virtual machine id or uuid
        :param SnapshotId: snapshot id
        :return:
        :raise CmpApiClientError:
        """
        data = {
            'InstanceId.N': [oid],
            'RestorePointId': restore_point_id
        }
        uri = self.get_uri('computeservices/instancebackup/deletebackuprestorepoints' % oid)
        res = self.api_delete(uri, data=data)
        self.logger.debug('delete virtual machine %s backup restore point %s' % (oid, restore_point_id))
        return res

    def get_backup_restores(self, oid, restore_point, *args, **kwargs):
        """list virtual machine backup restores

        :param oid: virtual machine id or uuid
        :param restore_point: restore point id
        :return: virtual machine console
        :raise CmpApiClientError:
        """
        kwargs = {'InstanceId.N': [oid], 'RestorePoint': restore_point}
        params = ['InstanceId.N', 'RestorePoint']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('computeservices/instancebackup/describebackuprestores',
                           preferred_version='v1.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeBackupRestoresResponse.instanceBackupRestoreSet.0.restores', default=[])
        self.logger.debug('get virtual machine %s backup restores: %s' % (oid, truncate(res)))
        return res

    def add_backup_restore(self, oid, restore_point_id, name, *args, **kwargs):
        """Restore a virtual machine from backup

        :param oid: id of the virtual machine to restore
        :param name: restored virtual machine name
        :param restore_point: id of restore point
        :return:
        :raise CmpApiClientError:
        """
        data = {
            'InstanceId': oid,
            'RestorePointId': restore_point_id,
            'InstanceName': name,
        }
        uri = self.get_uri('computeservices/instancebackup/createbackuprestores')
        res = self.api_post(uri, data={'instance': data})
        uuid = dict_get(res, 'CreateBackupRestoreResponse.instancesSet.0.instanceId')
        self.logger.debug('restore a virtual machine from backup: %s' % (oid, uuid))
        return uuid
    
    #
    # backup job
    #
    def get_backup_jobs(self, account, *args, **kwargs):
        """list backup jobs

        :param account: account id
        :return: list of job
        :raise CmpApiClientError:
        """
        kwargs = {'owner-id.N': [account]}
        params = ['owner-id.N']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('computeservices/instancebackup/describebackupjobs',
                           preferred_version='v1.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeBackupJobsResponse.jobSet', default=[])
        self.logger.debug('list account %s backup jobs: %s' % (account, truncate(res)))
        return res

    def get_backup_job(self, account, job_id, *args, **kwargs):
        """Get backup job

        :param account: account id
        :param job_id: job id
        :return: job
        :raise CmpApiClientError:
        """
        kwargs = {'owner-id.N': [account], 'JobId': job_id}
        params = ['owner-id.N', 'JobId']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('computeservices/instancebackup/describebackupjobs',
                           preferred_version='v1.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeBackupJobsResponse.jobSet.0', default={})
        self.logger.debug('get account %s backup job: %s' % (account, truncate(res)))
        return res

    def get_backup_job_policies(self, account, *args, **kwargs):
        """Get backup job policies

        :param account: account id
        :return: list of job policies
        :raise CmpApiClientError:
        """
        kwargs = {'owner-id': account}
        params = ['owner-id']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('computeservices/instancebackup/describebackupjobpolicies',
                           preferred_version='v1.0', **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, 'DescribeBackupJobPoliciesResponse.jobPoliciesSet', default={})
        self.logger.debug('get account %s backup job policies: %s' % (account, truncate(res)))
        return res

    def add_backup_job(self, name, account, zone, instances, hypervisor='openstack',
                       policy='bk-job-policy-7-7-retention', *args, **kwargs):
        """Add account backup job

        :param name: job name
        :param account: account id
        :param zone: job availability zone
        :param instances: list of instance id to add
        :param hypervisor: job hypervisor [openstack]
        :param policy: job hypervisor [bk-job-policy-7-7-retention]
        :return: job
        :raise CmpApiClientError:
        """
        data = {
            'owner-id': account,
            'InstanceId.N': instances,
            'Name': name,
            'AvailabilityZone': zone,
            'Policy': policy,
            'Hypervisor': hypervisor
        }
        uri = self.get_uri('computeservices/instancebackup/createbackupjob', preferred_version='v1.0', **kwargs)
        res = self.api_post(uri, data=data)
        uuid = dict_get(res, 'CreateBackupJob.jobsSet.0.jobId')
        self.logger.debug('add account %s backup job: %s' % (account, uuid))
        return res

    def update_backup_job(self, account, job_id, *args, **kwargs):
        """Update account backup job

        :param joib_id: job id
        :param account: account id
        :param kwargs.Name: job name [optional]
        :param kwargs.Enabled: enable or disable job [optional]
        :param kwargs.Policy: job policy [optional]
        :return:
        :raise CmpApiClientError:
        """
        data = {
            'owner-id': account,
            'JobId': job_id
        }
        other_params = ['Name', 'Enabled', 'Policy']
        data.update(self.format_request_data(kwargs, other_params))
        uri = self.get_uri('computeservices/instancebackup/modifybackupjob', preferred_version='v1.0', **kwargs)
        res = self.api_put(uri, data=data)
        self.logger.debug('update account %s backup job %s' % (account, job_id))
        return res

    def del_backup_job(self, account, job_id, *args, **kwargs):
        """Delete account backup job

        :param joib_id: job id
        :param account: account id
        :return: job_id
        :raise CmpApiClientError:
        """
        data = {
            'owner-id': account,
            'JobId': job_id
        }
        uri = self.get_uri('computeservices/instancebackup/deletebackupjob', preferred_version='v1.0', **kwargs)
        res = self.api_delete(uri, data=data)
        self.logger.debug('delete account %s backup job %s' % (account, job_id))
        return job_id

    def add_instance_to_backup_job(self, account, job_id, instance_id, *args, **kwargs):
        """Add instance to account backup job

        :param joib_id: job id
        :param account: account id
        :param instance_id: instance id
        :return: job_id
        :raise CmpApiClientError:
        """
        data = {
            'owner-id': account,
            'InstanceId': instance_id,
            'JobId': job_id,
        }
        uri = self.get_uri('computeservices/instancebackup/addbackupjobinstance', preferred_version='v1.0', **kwargs)
        res = self.api_post(uri, data=data)
        self.logger.debug('add instance %s to account %s backup job %s' % (instance_id, account, job_id))
        return job_id

    def del_instance_from_backup_job(self, account, job_id, instance_id, *args, **kwargs):
        """Delete instance from account backup job

        :param joib_id: job id
        :param account: account id
        :param instance_id: instance id
        :return: job_id
        :raise CmpApiClientError:
        """
        data = {
            'owner-id': account,
            'InstanceId': instance_id,
            'JobId': job_id,
        }
        uri = self.get_uri('computeservices/instancebackup/delbackupjobinstance', preferred_version='v1.0', **kwargs)
        res = self.api_post(uri, data=data)
        self.logger.debug('delete instance %s from account %s backup job %s' % (instance_id, account, job_id))
        return job_id
