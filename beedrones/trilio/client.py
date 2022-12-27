# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from time import sleep
from ujson import dumps
from logging import getLogger
from urllib.parse import urlencode
from beecell.types.type_dict import dict_set, dict_get
from beecell.types.type_string import truncate, bool2str
from beecell.simple import id_gen
from beedrones.openstack.client import setup_client, OpenstackClient, OpenstackError, OpenstackNotFound


class TrilioManager(object):
    """Openstack Trilio platform manager

    http://www.triliodoc.com/3.2/documentation/sphinx-doc/build/html/apicli.html#workload-manager-api-cli-documentation

    :param openstack_manager: instance of OpenstackManager
    :param uri: connection uri
    :param proxy: http proxy [optional]
    :param default_region: default region [optional]
    """
    def __init__(self, openstack_manager, proxy=None, default_region=None):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        # openstack manager instance
        self.openstack_manager = openstack_manager

        # trilio manager uri
        self.uri = None

        # http(s) proxy
        self.proxy = proxy
        # region
        self.region = default_region

        self.__after_init()

    def __repr__(self):
        return '<TrilioManager id=%s>' % id(self)

    def __after_init(self):
        # initialize proxy objects
        self.job_scheduler = JobScheduler(self)
        self.workload = TrilioWorkloads(self)
        self.snapshot = TrilioSnapshots(self)
        self.restore = TrilioSnapshotRestore(self)
        self.license = ManagerLicense(self)


class TrilioObject(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.manager = manager
        self.omanager = manager.openstack_manager
        self.uri = self.manager.uri
        self.client = None

    def setup(self):
        self.uri = self.omanager.endpoint('TrilioVaultWLM')
        if self.uri is None:
            raise OpenstackError('Trilio manager is not configured as Openstack endpoint')
        self.client = OpenstackClient(self.uri, self.manager.proxy)


class JobScheduler(TrilioObject):
    """This class will manage the trilio job_scheduler

    :param manager: TrilioManager instance
    """
    @setup_client
    def get_global_job_scheduler(self):
        """Return the status ( true or false ) of the Cloud Wide TrilioVault Job Scheduler

        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        # get project id
        # project_id = self.omanager.project.get(name='admin')['id']

        path = '/global_job_scheduler'
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Get trilio global job scheduler: %s' % truncate(res[0]))
        return res[0].get('global_job_scheduler', False)

    @setup_client
    def get_tenant_usage(self):
        """Gives storage used and vms protected by tenants.

        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        # get project id
        # project_id = self.omanager.project.get(name='admin')['id']

        path = '/workloads/metrics/tenants_usage'
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Gives storage used and vms protected by tenants: %s' % truncate(res[0]))
        return res[0]

    @setup_client
    def get_storage_usage(self):
        """Get workloads storage usage

        :return: list storage usages
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/workloads/metrics/storage_usage'
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Get workloads storage usage: %s' % truncate(res[0]))
        return res[0]

    @setup_client
    def get_protected_vms(self):
        """Gives list of vms protected by tenant.
        To see workload for a specific project change connection project when get token.

        :return: list storage usages
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/workloads/metrics/vms_protected'
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('List of vms protected by tenant: %s' % truncate(res[0]))
        return res[0].get('protected_vms', [])


class ManagerLicense(TrilioObject):
    """This class will manage the trilio license

    :param manager: TrilioManager instance
    """
    @setup_client
    def list(self):
        """Return the list of the license

        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/workloads/metrics/license'
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Get trilio license: %s' % truncate(res[0]))
        return res[0].get('license', {})

    @setup_client
    def check(self):
        """Return the check of the license

        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/workloads/metrics/license_check'
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Check trilio license: %s' % truncate(res[0]))
        return res[0].get('message', None)

    @setup_client
    def add(self, license):
        """Create new license

        :param license: license content
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = dumps({'license': {'file_name': 'license', 'lic_txt': license}})
        path = '/workloads/license'
        res = self.client.call(path, 'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug('Create trilio license: %s' % truncate(res[0]))
        return res[0].get('license', {None})


class TrilioWorkloads(TrilioObject):
    """This class will manage the trilio workloads.
    A workload is a collection of VMs that are managed together as one entity for backup and recovery purposes.
    Each workload includes a workload type and a job scheduler defines how frequently the backup need to be performed
    and how many backups need to be retained on the backup media.

    The following table describes the metadata flags to exclude volumes or nova boot disks from backups.
    Nova Boot 	set metadata exclude_boot_disk_from_backup to true on instance to exclude nova boot disk from backup
    Cinder Volume 	set exclude_from_backup to true on cinder volume to exclude it from backup

    :param manager: TrilioManager instance
    """
    def __init__(self, manager):
        TrilioObject.__init__(self, manager)

    @setup_client
    def types(self):
        """Lists registered workload types

        :return: list of workload types
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/workload_types/detail'
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('List workloads types: %s' % truncate(res[0]))
        return res[0].get('workload_types', [])

    @setup_client
    def auditlog(self, time_in_minutes=1440, time_from=None, time_to=None):
        """Get auditlog of workload manager

        :param time_in_minutes: time in minutes(default is 24 hrs.)
        :param time_from: From date time in format 'MM-DD-YYYY'
        :param time_to: To date time in format 'MM-DD-YYYY'(defult is current day)
        :return: list of audilog
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {}

        def set_key(key, value, func=None):
            if value is not None:
                if func is not None:
                    value = func(value)
                dict_set(data, key, value)

        set_key('time_in_minutes', time_in_minutes)
        set_key('time_from', time_from)
        set_key('time_to', time_to)
        path = '/workloads/audit/auditlog?' + urlencode(data)
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Get auditlog of workload manager: %s' % truncate(res[0]))
        return res[0].get('auditlog', [])

    @setup_client
    def list(self, all=False):
        """Get all the workloads of a specified tenant the result will be a DICT in this format in unicode UTF8
        To see workload for a specific project change connection project when get token.

        :param all: if True list workloads for all the projects
        :return: list of workloads
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        if all is False:
            path = '/workloads?detail=True'
            res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
            self.logger.debug('+++++ List workloads for connection project: %s' % truncate(res[0]))
            return res[0].get('workloads', [])
        else:
            path = '/workloads?all_workloads=True'
            res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
            self.logger.debug('+++++ List workloads: %s' % truncate(res[0]))
            return res[0].get('workloads', [])

    @setup_client
    def get(self, workload_id):
        """Show the detail of a workload in the connection project

        :param workload_id : ID of the workload to show
        :return: get workload
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/workloads/' + workload_id
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Get workload %s: %s' % (workload_id, truncate(res)))
        return res[0].get('workload', {})

    @setup_client
    def add(self, name, workload_type_id, instances, metadata={}, desc=None, fullbackup_interval=2,
            start_date=None, end_date=None, start_time='0:00 AM', interval='24hrs', snapshots_to_retain=4,
            timezone='Europe/Rome'):
        """Creates a new workload (a backup group) that includes one more VMs identified by their GUID.
        To add workload for a specific project change connection project when get token.

        :param name: workload name
        :param workload_type_id: workload type id
        :param instances: list of instances
        :param metadata: metadata
        :param desc: workload description [optional]
        :param fullbackup_interval: fullbackup interval [default=2]
        :param start_date: start date. Ex. '06/05/2014' [optional]
        :param end_date: end date. Ex. '07/15/2014' [optional]
        :param start_time: start time. Ex. '2:30 PM' [optional]
        :param interval: interval.  [default=24hrs]
        :param snapshots_to_retain: snapshots to retain [default=4]
        :param timezone: timezone [default=Europe/Rome]
        :return: workload
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            'name': name,
            'description': desc,
            'workload_type_id': workload_type_id,
            'source_platform': 'openstack',
            'instances': [{'instance-id': i} for i in instances],
            'jobschedule': {
                'fullbackup_interval': fullbackup_interval,
                'start_date': start_date,
                'end_date': end_date,
                'start_time': start_time,
                'interval': interval,
                'retention_policy_value': snapshots_to_retain,
                'enabled': 'true',
                'timezone': timezone
            },
            'metadata': metadata
        }

        path = '/workloads'
        data = dumps({'workload': data})
        self.logger.debug('Add workload for connection project - data: %s' % data)
        res = self.client.call(path, 'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug('Add workload for connection project - res: %s' % truncate(res[0]))
        return res[0].get('workload')

    @setup_client
    def update(self, workload_id, name=None, instances=None, metadata=None, desc=None, fullbackup_interval=None,
               start_date=None, end_date=None, start_time=None, interval=None, snapshots_to_retain=None, timezone=None,
               enabled=None):
        """Creates a new workload (a backup group) that includes one more VMs identified by their GUID.
        To add workload for a specific project change connection project when get token.

        :param workload_id: workload id
        :param name: workload name [optional]
        :param instances: list of instances [optional]
        :param metadata: metadata [optional]
        :param desc: workload description [optional]
        :param fullbackup_interval: fullbackup interval [optional]
        :param start_date: start date. Ex. '06/05/2014' [optional]
        :param end_date: end date. Ex. '07/15/2014' [optional]
        :param start_time: start time. Ex. '2:30 PM' [optional]
        :param interval: interval [optional]
        :param snapshots_to_retain: snapshots to retain [optional]
        :param timezone: timezone [optional]
        :param enable: enable workload [optional]
        :return: list of workloads
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {}

        def set_key(key, value, func=None):
            if value is not None:
                if func is not None:
                    value = func(value)
                dict_set(data, key, value)

        set_key('name', name)
        set_key('description', desc)
        set_key('instances', instances, lambda x: [{'instance-id': i} for i in x])
        set_key('jobschedule.fullbackup_interval', fullbackup_interval)
        set_key('jobschedule.start_date', start_date)
        set_key('jobschedule.end_date', end_date)
        set_key('jobschedule.start_time', start_time)
        set_key('jobschedule.interval', interval)
        set_key('jobschedule.retention_policy_value', snapshots_to_retain)
        set_key('jobschedule.enabled', bool2str(enabled))
        set_key('jobschedule.timezone', timezone)
        set_key('metadata', metadata)

        path = '/workloads/' + workload_id
        data = dumps({'workload': data})
        self.client.timeout = 60
        res = self.client.call(path, 'PUT', data=data, token=self.omanager.identity.token)
        self.logger.debug('Update workload for connection project: %s' % truncate(res[0]))
        return res[0]

    @setup_client
    def delete(self, workload_id):
        """Delete a workload in the connection project

        :param workload_id : ID of the workload to show
        :return: get workload
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/workloads/' + workload_id
        self.client.timeout = 60
        res = self.client.call(path, 'DELETE', data='', token=self.omanager.identity.token)
        self.logger.debug('Delete workload %s: %s' % (workload_id, truncate(res)))
        return res[0]

    @setup_client
    def unlock(self, workload_id):
        """Unlock a workload in the connection project

        :param workload_id : ID of the workload to show
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/workloads/' + workload_id + '/unlock'
        res = self.client.call(path, 'DELETE', data='', token=self.omanager.identity.token)
        self.logger.debug('Delete workload %s: %s' % (workload_id, truncate(res)))
        return res[0]

    @setup_client
    def reset(self, workload_id):
        """Reset a workload in the connection project.
        TrilioVault uses storage based snapshots for calculating backup images of application resources. For cinder
        volumes, it uses cinder snapshots and for ceph based nova backends, it uses ceph snapshots for calculating
        the backup images. Depending the state of the workload backup operation, each of these resources may have one
        or more snapshots outstanding. Workload-reset deletes all outstanding snapshots on all resources of the
        application. Workload-reset is useful if you want to decommission the application, but you still want to
        keep all the backups of the application.
        It is highly recommended to perform workload-reset before deleting any application resources from OpenStack.

        :param workload_id : ID of the workload to show
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/workloads/' + workload_id + '/reset'
        res = self.client.call(path, 'POST', data='', token=self.omanager.identity.token)
        self.logger.debug('Reset workload %s: %s' % (workload_id, truncate(res)))
        return res[0]


class TrilioSnapshots(TrilioObject):
    """This class will manage the trilio snapshots.
    Snapshot or backups are created from workloads. Snapshots can be created on an on-demand basis
    or by the underlying job scheduler.

    :param manager: TrilioManager instance
    """
    def __init__(self, manager):
        TrilioObject.__init__(self, manager)

    @setup_client
    def list(self, all=False, workload_id=None, date_from=None, date_to=None):
        """Lists snapshots.
        To see workload for a specific project change connection project when get token.

        :param all: if True list workloads for all the projects
        :param workload_id : unique identifier of workload
        :param date_from: From date in format 'YYYY-MM-DDTHH:MM:SS' eg 2016-10-10T00:00:00, If don't specify time then
            it takes 00:00 by default
        :param date_to: To date in format 'YYYY-MM-DDTHH:MM:SS'(defult is current day), Specify HH:MM:SS to get
            snapshots within same day inclusive/exclusive results for date_from and date_to
        :return: snapshots list
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        filter = {}
        if date_from is not None:
            filter['date_from'] = date_from
        if date_to is not None:
            filter['date_to'] = date_to

        if all is True:
            filter['all'] = True
            # filter = urlencode(filter)
            # path = '/snapshots?' + filter
            # res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
            # self.logger.debug('Get all the snapshots: %s' % truncate(res))
            # return res[0].get('snapshots', [])
        if workload_id is not None:
            filter['workload_id'] = workload_id
            # filter = urlencode(filter)
            # path = '/snapshots?' + filter
            # res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
            # self.logger.debug('Get snapshots for current project and workload %s: %s' % (workload_id, truncate(res)))
            # return res[0].get('snapshots', [])
        #else:
        filter = urlencode(filter)
        path = '/snapshots?' + filter
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Get snapshots for current project: %s' % truncate(res))
        return res[0].get('snapshots', [])

    @setup_client
    def get(self, snapshot_id):
        """ Display snapshot details.

        :param snapshot_id : unique identifier of snapshot
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/snapshots/' + snapshot_id
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Get snapshot %s: %s' % (snapshot_id, truncate(res)))
        return res[0].get('snapshot', {})

    @setup_client
    def add(self, workload_id, name=None, desc=None, full=True):
        """Creates an on demand snapshot for a given workload.
        To add workload for a specific project change connection project when get token.

        :param workload_id: workload id
        :param name: workload name [optional]
        :param desc: workload description [optional]
        :param full: if True make a full snapshot [optional]
        :return: snapshot
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            'name': name,
            'description': desc,
            'full': full
        }

        path = '/workloads/' + workload_id
        data = dumps({'snapshot': data})
        res = self.client.call(path, 'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug('Add workload %s snapshot for connection project: %s' % (workload_id, truncate(res[0])))
        return res[0].get('snapshot')

    @setup_client
    def delete(self, snapshot_id):
        """Remove a workload snapshot.

        :param snapshot_id : unique identifier of snapshot
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/snapshots/' + snapshot_id
        res = self.client.call(path, 'DELETE', data='', token=self.omanager.identity.token)
        self.logger.debug('Delete snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]

    @setup_client
    def cancel(self, snapshot_id):
        """Cancel a snapshot that is running. If the snapshot operation is in the middle of the data transfer of a
        resource, it waits for the data transfer operation is complete before terminating the snapshot operation.

        :param snapshot_id : unique identifier of snapshot
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/snapshots/' + snapshot_id + '/cancel'
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Cancel snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]

    def wait_for_status(self, snapshot_id, final_status='available'):
        """wait for snapshot status

        :param snapshot_id: snapshot id
        :param final_status: snapshot final status
        :raise OpenstackError: raise :class:`.OpenstackError`
        :return: None
        """
        # loop until action completed or return error
        while True:
            try:
                snapshot = self.get(snapshot_id)
                status = snapshot['status']
            except OpenstackNotFound as ex:
                status = 'deleted'
            except OpenstackError as ex:
                if ex.code == 404:
                    status = 'deleted'

            self.logger.debug('read snapshot %s status: %s' % (snapshot_id, status))
            if status == final_status:
                break
            elif status == 'error':
                raise OpenstackError(snapshot.get('error_msg'))

            sleep(2)
        self.logger.debug('snapshot %s final status: %s' % (snapshot_id, final_status))

    @setup_client
    def mounted(self):
        """List of all mounted snapshots

        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/snapshots/mounted/list'
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('List of all mounted snapshots: %s' % truncate(res))
        return res[0].get('mounted_snapshots', [])

    @setup_client
    def mount(self, snapshot_id, instance_id):
        """Mounts a workload snapshot for exploring individual files.
        Mounts all volumes/partitions that are present in all VMs and provide an URL for end use to explore the file
        system contents on each of these volumes partitions in a file manager view. User can download and view
        individual files. A user cannot modify any contents in the snapshot. Current implementation mounts all Linux
        file systems and NTFS file system mounted on regular partitions. Dynamic volumes are supported in subsequent
        releases. Snapshot cannot be mounted multiple times simultaneously.

        :param snapshot_id : unique identifier of snapshot
        :param instance_id: instance id where mount volume
        :return: snapshot
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            'mount_vm_id': instance_id,
            'options': {}
        }

        path = '/snapshots/' + snapshot_id + '/mount'
        data = dumps({'mount': data})
        res = self.client.call(path, 'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug('Mount snapshot %s to instance %s: %s' % (snapshot_id, instance_id, truncate(res[0])))
        return res[0]

    @setup_client
    def dismount(self, snapshot_id):
        """Dismount a workload snapshot.

        :param snapshot_id : unique identifier of snapshot
        :return: snapshot
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            'options': {}
        }

        path = '/snapshots/' + snapshot_id + '/dismount'
        data = dumps({'mount': data})
        res = self.client.call(path, 'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug('Dismount snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]


class TrilioSnapshotRestore(TrilioObject):
    """This class will manage the trilio snapshot restore.

    :param manager: TrilioManager instance
    """
    def __init__(self, manager):
        TrilioObject.__init__(self, manager)
        self.snapshot = TrilioSnapshots(manager)

    @setup_client
    def list(self, snapshot_id=None):
        """Lists snapshot restores.
        To see workload for a specific project change connection project when get token.

        :param snapshot_id : unique identifier of snapshot
        :return: snapshots restore list
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        filter = {}
        if snapshot_id is not None:
            filter['snapshot_id'] = snapshot_id

        filter = urlencode(filter)
        path = '/restores/detail?' + filter
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Get snapshot restores: %s' % truncate(res))
        return res[0].get('restores', [])

    @setup_client
    def get(self, restore_id):
        """Show details about a workload snapshot restore

        :param restore_id : unique identifier of restore
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/restores/' + restore_id
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Get restore %s: %s' % (restore_id, truncate(res)))
        return res[0].get('restore', {})

    @setup_client
    def delete(self, restore_id):
        """Delete a restore.

        :param restore_id : unique identifier of restore
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/restores/' + restore_id
        res = self.client.call(path, 'DELETE', data='', token=self.omanager.identity.token)
        self.logger.debug('Delete restore %s: %s' % (restore_id, truncate(res)))
        return res[0]

    @setup_client
    def cancel(self, restore_id):
        """Cancel a restore.

        :param restore_id : unique identifier of restore_id
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/restores/' + restore_id + '/cancel'
        res = self.client.call(path, 'GET', data='', token=self.omanager.identity.token)
        self.logger.debug('Cancel restore %s: %s' % (restore_id, truncate(res)))
        return res[0]

    @setup_client
    def selective(self, snapshot_id, config, prj_token=None):
        """Selective Restore workload snapshot.
        The selective restore method provides a significant amount of flexibility to recover instances. With the
        selective restore, user can choose different target networks, target volume types, include/exclude specific
        instances to restore, and target flavor for each instance, etc.

        example of config:
        {
            "description": "prova_restore",
            "oneclickrestore": false,
            "openstack": {
              "instances": [
                {
                  "name": "restored1",
                  "availability_zone": "nova",
                  "nics": [],
                  "vdisks": [
                    {
                      "new_volume_type": "nfs",
                      "id": "4d6d5194-39fb-45e9-b2b3-80c4d38aafcb",
                      "availability_zone": "nova"
                    }
                  ],
                  "flavor": {
                    "id": "803791f2-3c6e-4598-a4ae-8ce7bc251401"
                  },
                  "include": true,
                  "id": "383fb185-5966-4852-a6b1-e6a1816fcc20"
                }
              ],
              "restore_topology": false,
              "networks_mapping": {
                "networks": [
                  {
                    "snapshot_network": {
                      "subnet": {
                        "id": "ed3577c0-0528-4fb3-803b-7caff8878494"
                      },
                      "id": "94b35e31-4bbd-44da-97d2-6296da047bfe"
                    },
                    "target_network": {
                      "subnet": {
                        "id": "ed3577c0-0528-4fb3-803b-7caff8878494"
                      },
                      "id": "94b35e31-4bbd-44da-97d2-6296da047bfe"
                    }
                  }
                ]
              }
            },
            "restore_type": "selective",
            "type": "openstack",
            "name": "prova_restore"
        }

        :param snapshot_id : unique identifier of snapshot
        :param config: restore configuration
        :param prj_token: token created for the target project of the restore [optional]
        :return: snapshot
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        config['restore_type'] = 'selective'
        config['oneclickrestore'] = False
        config['type'] = 'openstack'
        data = {
            'restore': {
                'name': config.get('name', 'restore'),
                'description': config.get('description', 'restore'),
                'options': config
            }
        }
        path = '/snapshots/' + snapshot_id
        data = dumps(data)
        if prj_token is None:
            prj_token = self.omanager.identity.token
        res = self.client.call(path, 'POST', data=data, token=prj_token)
        self.logger.debug('Selective restore of snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]['restore']

    @setup_client
    def onclick(self, snapshot_id, config):
        """Restore a workload snapshot.
        One-click restore restores the selected snapshot to the exact location including the same network/subnet,
        volume types, security groups, IP addresses and so on. One-click Restore only works when original instances
        are deleted.

        :param snapshot_id : unique identifier of snapshot
        :param config: restore configuration
        :return: snapshot
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        config['restore_type'] = 'oneclick'
        config['type'] = 'openstack'
        data = {
            'restore': {
                'name': config.get('name', 'restore'),
                'description': config.get('description', 'restore'),
                'options': config
            }
        }
        path = '/snapshots/' + snapshot_id
        data = dumps(data)
        res = self.client.call(path, 'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug('Oneclick restore of snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]['restore']

    @setup_client
    def inplace(self, snapshot_id, config):
        """Selective Restore workload snapshot.
        One click and selective restores creates brand new resources when restoring virtual resources from the backup
        media. In some cases it is not desirable to construct new resources. Instead user may want to restore an
        existing volume to a particular point in time. In-place restore functionality will overwrite existing volume
        with the data from the backup media.

        :param snapshot_id : unique identifier of snapshot
        :param config: restore configuration
        :return: snapshot
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        config['restore_type'] = 'inplace'
        config['oneclickrestore'] = False
        config['type'] = 'openstack'
        data = {
            'restore': {
                'name': config.get('name', 'restore'),
                'description': config.get('description', 'restore'),
                'options': config
            }
        }
        path = '/snapshots/' + snapshot_id
        data = dumps(data)
        res = self.client.call(path, 'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug('Inplace restore of snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]['restore']

    def server(self, snapshot_id, server_id, server_name=None, target_network=None, target_subnet=None,
               keep_original_ip=False, overwrite=False, new_token=None):
        """restore a server

        :param snapshot_id: snapshot id
        :param server_id: id of the server to restore
        :param server_name: name of the restored server [optional]
        :param target_network: target network id. Set also target subnet Only server with one network is supported
            [optional]
        :param target_subnet: target subnet id. Only server with one network is supported [optional]
        :param overwrite: if True overwrite existing server [default=False]
        :param keep_original_ip: if True keep original ip [default=False]
        :param new_token: new token to use to change project during selective restore [optional]
        :return:
        """
        snapshot = self.snapshot.get(snapshot_id)
        instances = [i for i in snapshot['instances'] if server_id == i['id']]
        if len(instances) > 0:
            server = instances[0]
        else:
            err = 'server %s was not found in snapshot %s' % (server_id, snapshot_id)
            self.logger.error(err)
            raise OpenstackError(err)

        # set server name
        if server_name is None:
            server_name = '%s-restore-%s' % (server.get('name'), id_gen(length=4))

        # get params
        availability_zone = dict_get(server, 'metadata.availability_zone')
        flavor = dict_get(server, 'flavor')
        nics = server['nics']
        ports = self.omanager.server.get_port_interfaces(server_id)
        vdisks = []
        vdisk_index = 0
        for v in server.get('vdisks', []):
            vdisks.append({
                'id': v.get('volume_id'),
                'availability_zone': v.get('availability_zone'),
                'new_volume_type': v.get('volume_type')})
            vdisk_index += 1

        # server network mapping
        net_mapping = [{
            'snapshot_network': {
                'id': p.get('net_id'),
                'subnet': {'id': dict_get(p, 'fixed_ips.0.subnet_id')}
            },
            'target_network': {
                'id': p.get('net_id'),
                'subnet': {'id': dict_get(p, 'fixed_ips.0.subnet_id')}
            }
        } for p in ports]

        if target_network is not None:
            if target_subnet is None:
                raise OpenstackError('target subnet must be specified')
            net_mapping[0]['target_network'] = {'id': target_network, 'subnet': target_subnet}

        # keep original ip
        new_nics = []
        if keep_original_ip is True:
            new_nics = [
                {
                    'mac_address': nic['mac_address'],
                    'ip_address': nic['ip_address'],
                    'network': {
                        'subnet': {
                            'id': nic['network']['subnet']['id']
                        },
                        'id': nic['network']['id']
                    },
                    'id': nic['network']['id']
                } for nic in nics]

        # create server config
        server_config = {
            'name': server_name,
            'description': server_name,
            'openstack': {
                'restore_topology': False,
                'instances': [
                    {
                        'id': server_id,
                        'name': server_name,
                        'availability_zone': availability_zone,
                        'include': True,
                        'flavor': flavor,
                        'vdisks': vdisks,
                        'nics': new_nics
                    }
                ],
                'networks_mapping': {'networks': net_mapping}
            }
        }
        self.logger.debug('restore server %s with config %s' % (server_id, server_config))

        if overwrite is True:
            res = self.inplace(snapshot_id, server_config)
            self.logger.debug('replace server %s from snapshot %s' % (server_id, snapshot_id))
        else:
            res = self.selective(snapshot_id, server_config, prj_token=new_token)
            self.logger.debug('restore server %s from snapshot %s' % (server_id, snapshot_id))
        return res

    # def server_old_sergio(self, snapshot_id, server_id, server_name=None, overwrite=False, name='restore', desc='restore'):
    #     server = self.omanager.server.get(oid=server_id)
    #     avz = server.get('OS-EXT-AZ:availability_zone')
    #     ports = self.omanager.server.get_port_interfaces(server_id)
    #     net_mapping = [{
    #         'snapshot_network': {'id': p.get('net_id'),
    #                               'subnet': {'id': p.get('fixed_ips')[0].get('subnet_id')}},
    #         'target_network': {'id': p.get('net_id'),
    #                             'subnet': {'id': p.get('fixed_ips')[0].get('subnet_id')}}} for p in ports]
    #     if server_name is None:
    #         server_name = '%s-restore-%s' % (server.get('name'), id_gen(length=4))
    #
    #     if overwrite is True:
    #         vdisks = [{'id': v.get('id'),
    #                    'availability_zone': avz,
    #                    'new_volume_type': self.omanager.volume.get(oid=v.get('id')).get('volume_type')}
    #                   for v in server.get('os-extended-volumes:volumes_attached', [])]
    #         config = {
    #             'type': 'openstack',
    #             'name': name,
    #             'description': desc,
    #             'openstack': {
    #                 'restore_topology': False,
    #                 'instances': [
    #                     {
    #                         'id': server_id,
    #                         'name': server_name,
    #                         'availability_zone': avz,
    #                         'include': True,
    #                         'flavor': {
    #                             'id': server.get('flavor').get('id')
    #                         },
    #                         'vdisks': vdisks,
    #                         'nics': [
    #
    #                         ]
    #                     }
    #                 ],
    #                 'networks_mapping': {
    #                     'networks': net_mapping
    #                 }
    #             }
    #         }
    #         res = self.inplace(snapshot_id, config)
    #         self.logger.debug('Replace server %s from snapshot %s' % (server_id, snapshot_id))
    #     else:
    #         vdisks = [{'id': v.get('id'),
    #                    'availability_zone': avz,
    #                    'new_volume_type': self.omanager.volume.get(oid=v.get('id')).get('volume_type')}
    #                   for v in server.get('os-extended-volumes:volumes_attached', [])]
    #         config = {
    #             'type': 'openstack',
    #             'name': name,
    #             'description': desc,
    #             'openstack': {
    #                 'instances': [
    #                     {
    #                         'id': server_id,
    #                         'name': server_name,
    #                         'restore_boot_disk': True,
    #                         'include': True,
    #                         'vdisks': vdisks,
    #                         'nics': [
    #
    #                         ]
    #                     }
    #                 ],
    #                 'networks_mapping': {
    #                     'networks': net_mapping
    #                 }
    #             }
    #         }
    #         res = self.selective(snapshot_id, config)
    #         self.logger.debug('Restore server %s from snapshot %s' % (server_id, snapshot_id))
    #     return res

    # def server_old_miko(self, snapshot_id, id_server_2_restore, prj_token, target_project_name=None,
    #            flavor=None, same_ip=False, new_ip=None, network_remapping=None, server_name=None,
    #            name='restore', desc='restore'):
    #     """Selective server restore from a snapshot.
    #
    #     :param snapshot_id : unique identifier of snapshot
    #     :param id_server_2_restore : id of the server to restore from the snapshot
    #     :param prj_token : token of the project where to restore the server
    #     :param target_project_name : openstack project name whrere to restore the server
    #     :param flavor :  flavor of the restored server
    #     :param same_ip : [boolean] if True, the server will be restored with the same ip of the snapshot otherwise
    #     the ip will change with one of the original subnet
    #     :param server_name : name of the restored server
    #     :param name : name of the restoring task
    #     :param desc : description of the restoring task
    #
    #     TO DO: all that concerning the setting fixed ip and different networks/subnets
    #     :param new_ip : TO DO
    #     :param network_remapping : TO DO
    #
    #     :raise OpenstackError: raise :class:`.OpenstackError`
    #     """
    #     res = []
    #     new_nics = []
    #     instanced_found = False
    #
    #     instances = self.snapshot.get(snapshot_id)
    #     self.logger.debug('Instances contained into snapshot id <%s> : %s' % (snapshot_id, instances))
    #
    #     for instance in instances['instances']:
    #         if id_server_2_restore == instance['id']:
    #             instanced_found = True
    #             nics = instance['nics']
    #             self.logger.debug("nics: %s" % nics)
    #             num_nics = len(nics)
    #             self.logger.debug("# di nics found in instance: %s" % num_nics)
    #
    #             if server_name is None:
    #                 server_name = instance['name']
    #
    #             if network_remapping is None:
    #                 net_mapping = {"networks": [{
    #                      'snapshot_network': {'id': nic['network']['id'],
    #                                           'subnet': {'id': nic['network']['subnet']['id']}},
    #                      'target_network': {'id': nic['network']['id'],
    #                                         'subnet': {'id': nic['network']['subnet']['id']}}} for nic in nics]}
    #                 self.logger.debug("network mapping :%s" % net_mapping)
    #             else:
    #                 self.logger.error("'network remapping' Not implemented yet!")
    #                 raise OpenstackError("Trilio 'network remapping' Not implemented yet!")
    #
    #             if same_ip:
    #                 new_nics = [
    #                     {
    #                         'mac_address': nic['mac_address'],
    #                         'ip_address': nic['ip_address'],
    #                         'network': {
    #                             'subnet': {
    #                                 'id': nic['network']['subnet']['id']
    #                             },
    #                             'id': nic['network']['id']
    #                         },
    #                         'id': nic['network']['id']
    #                     } for nic in nics]
    #             else:
    #                 if network_remapping is None:
    #                     if new_ip is None:
    #                         # in questo caso l'ip viene generato automaticamente con uno libero
    #                         new_nics = []
    #                     else:
    #                         # forzo l'ip con quello passato come parametro
    #                         self.logger.error("setting fixed ips not implemented yet!")
    #                         raise OpenstackError("Trilio setting fixed ip not implemented yet!")
    #
    #             self.logger.debug("new nics: %s" % new_nics)
    #
    #             if flavor is None:
    #                 flavor = instance['flavor']
    #                 self.logger.debug("Flavor :%s" % flavor)
    #
    #             # availability_zone = instance['vdisks'][0]['availability_zone']
    #             # volume_type = instance['vdisks'][0]['volume_type']
    #
    #             config = {
    #                 "description": desc,
    #                 "name": name,
    #                 "oneclickrestore": "False",
    #                 "openstack": {
    #                     "instances": [{
    #                         "name": server_name,
    #                         "availability_zone": "nova",
    #                         "nics": new_nics,
    #                         "vdisks": [],
    #                         "flavor": flavor,
    #                         "include": "True",
    #                         "id": id_server_2_restore
    #                     }],
    #                     "restore_topology": "False",
    #                     "networks_mapping": net_mapping
    #                 },
    #                 "restore_type": "selective",
    #                 "type": "openstack"
    #             }
    #
    #             self.logger.info("CONFIG :%s" % config)
    #
    #             # new_prj_token = self.omanager.identity.get_token('admin', '******', target_project_name, 'default')
    #             # prj_token = new_prj_token['token']
    #
    #             res = self.selective(snapshot_id, config, prj_token)
    #             self.logger.debug('Restore server <%s> from snapshot <%s> into openstack project <%s>' %
    #                               (id_server_2_restore,  snapshot_id, target_project_name))
    #         else:
    #             if not instanced_found:
    #                 self.logger.debug("NOT id='%s' FOUND: la snapshot contiene il server '%s' con id '%s'" %
    #                                   (id_server_2_restore, instance['name'], instance['id']))
    #                 res = "NO ID found in snapshot"
    #     return res

    def volume(self, snapshot_id, volume_id, overwrite=False, name='restore', desc='restore'):
        volume = self.omanager.volume.get(oid=volume_id)
        attachments = volume.get('attachments', [])
        if len(attachments) > 0:
            server_id = attachments[0].get('server_id')
        else:
            raise OpenstackError('Volume %s is not attached to a server' % volume_id)
        if overwrite is False:
            raise OpenstackError('Volume can not be restored as new. Only volume overwrite is supported.')
        else:
            vdisks = [{'id': volume_id, 'restore_cinder_volume': True}]
            config = {
                'type': 'openstack',
                'name': name,
                'description': desc,
                'openstack': {
                    'instances': [
                        {
                            'id': server_id,
                            'restore_boot_disk': False,
                            'include': True,
                            'vdisks': vdisks
                        }
                    ]
                }
            }
            res = self.inplace(snapshot_id, config)
            self.logger.debug('Restore server %s from snapshot %s' % (server_id, snapshot_id))
        return res

