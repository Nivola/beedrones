# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

from logging import getLogger
from urllib.parse import urlencode
import ujson as json
from beecell.simple import truncate, dict_set, bool2str, id_gen
from beedrones.openstack.client import setup_client, OpenstackClient, OpenstackError


class TrilioManager(object):
    """Openstack Trilio platform manager

    http://www.triliodoc.com/3.2/documentation/sphinx-doc/build/html/apicli.html#workload-manager-api-cli-documentation

    :param openstack_manager: instance of OpenstackManager
    :param uri: connection uri
    :param proxy: http proxy [optional]
    :param default_region: default region [optional]
    """
    def __init__(self, openstack_manager, proxy=None, default_region=None):
        self.logger = getLogger(self.__class__.__module__ + u'.' + self.__class__.__name__)

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
        return u'<TrilioManager id=%s>' % id(self)

    def __after_init(self):
        # initialize proxy objects
        self.job_scheduler = JobScheduler(self)
        self.workload = TrilioWorkloads(self)
        self.snapshot = TrilioSnapshots(self)
        self.restore = TrilioSnapshotRestore(self)
        self.license = ManagerLicense(self)


class TrilioObject(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + u'.' + self.__class__.__name__)

        self.manager = manager
        self.omanager = manager.openstack_manager
        self.uri = self.manager.uri
        self.client = None

    def setup(self):
        self.uri = self.omanager.endpoint(u'TrilioVaultWLM')
        if self.uri is None:
            raise OpenstackError(u'Trilio manager is not configured as Openstack endpoint')
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
        # project_id = self.omanager.project.get(name=u'admin')[u'id']

        path = u'/global_job_scheduler'
        res = self.client.call(path, u'GET', data='', token=self.omanager.identity.token)
        self.logger.debug(u'Get trilio global job scheduler: %s' % truncate(res[0]))
        return res[0].get(u'global_job_scheduler', False)

    @setup_client
    def get_tenant_usage(self):
        """Gives storage used and vms protected by tenants.

        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        # get project id
        # project_id = self.omanager.project.get(name=u'admin')[u'id']

        path = u'/workloads/metrics/tenants_usage'
        res = self.client.call(path, u'GET', data='', token=self.omanager.identity.token)
        self.logger.debug(u'Gives storage used and vms protected by tenants: %s' % truncate(res[0]))
        return res[0]

    @setup_client
    def get_storage_usage(self):
        """Get workloads storage usage

        :return: list storage usages
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/workloads/metrics/storage_usage'
        res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Get workloads storage usage: %s' % truncate(res[0]))
        return res[0]

    @setup_client
    def get_protected_vms(self):
        """Gives list of vms protected by tenant.
        To see workload for a specific project change connection project when get token.

        :return: list storage usages
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/workloads/metrics/vms_protected'
        res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'List of vms protected by tenant: %s' % truncate(res[0]))
        return res[0].get(u'protected_vms', [])


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
        path = u'/workloads/metrics/license'
        res = self.client.call(path, u'GET', data='', token=self.omanager.identity.token)
        self.logger.debug(u'Get trilio license: %s' % truncate(res[0]))
        return res[0].get(u'license', {})

    @setup_client
    def check(self):
        """Return the check of the license

        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/workloads/metrics/license_check'
        res = self.client.call(path, u'GET', data='', token=self.omanager.identity.token)
        self.logger.debug(u'Check trilio license: %s' % truncate(res[0]))
        return res[0].get(u'message', None)

    @setup_client
    def add(self, license):
        """Create new license

        :param license: license content
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = json.dumps({u'license': {u'file_name': u'license', u'lic_txt': license}})
        path = u'/workloads/license'
        res = self.client.call(path, u'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug(u'Create trilio license: %s' % truncate(res[0]))
        return res[0].get(u'license', {None})


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
        path = u'/workload_types/detail'
        res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'List workloads types: %s' % truncate(res[0]))
        return res[0].get(u'workload_types', [])

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

        set_key(u'time_in_minutes', time_in_minutes)
        set_key(u'time_from', time_from)
        set_key(u'time_to', time_to)
        path = u'/workloads/audit/auditlog?' + urlencode(data)
        res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Get auditlog of workload manager: %s' % truncate(res[0]))
        return res[0].get(u'auditlog', [])

    @setup_client
    def list(self, all=False):
        """Get all the workloads of a specified tenant the result will be a DICT in this format in unicode UTF8
        To see workload for a specific project change connection project when get token.

        :param all: if True list workloads for all the projects
        :return: list of workloads
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        if all is False:
            path = u'/workloads'
            res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
            self.logger.debug(u'List workloads for connection project: %s' % truncate(res[0]))
            return res[0].get(u'workloads', [])
        else:
            path = u'/workloads?all_workloads=True'
            res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
            self.logger.debug(u'List workloads: %s' % truncate(res[0]))
            return res[0].get(u'workloads', [])

    @setup_client
    def get(self, workload_id):
        """Show the detail of a workload in the connection project

        :param workload_id : ID of the workload to show
        :return: get workload
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/workloads/' + workload_id
        res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Get workload %s: %s' % (workload_id, truncate(res)))
        return res[0].get(u'workload', {})

    @setup_client
    def add(self, name, workload_type_id, instances, metadata={}, desc=None, fullbackup_interval=2,
            start_date=None, end_date=None, start_time=u'0:00 AM', interval=u'24hrs', snapshots_to_retain=4,
            timezone=u'Europe/Rome'):
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
        :return: list of workloads
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            u'name': name,
            u'description': desc,
            u'workload_type_id': workload_type_id,
            u'source_platform': u'openstack',
            u'instances': [{u'instance-id': i} for i in instances],
            u'jobschedule': {
                u'fullbackup_interval': fullbackup_interval,
                u'start_date': start_date,
                u'end_date': end_date,
                u'start_time': start_time,
                u'interval': interval,
                u'retention_policy_value': snapshots_to_retain,
                u'enabled': u'true',
                u'timezone': timezone
            },
            u'metadata': metadata
        }

        path = u'/workloads'
        data = json.dumps({u'workload': data})
        res = self.client.call(path, u'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug(u'Add workload for connection project: %s' % truncate(res[0]))
        return res[0].get(u'workload')

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

        set_key(u'name', name)
        set_key(u'description', desc)
        set_key(u'instances', instances, lambda x: [{u'instance-id': i} for i in x])
        set_key(u'jobschedule.fullbackup_interval', fullbackup_interval)
        set_key(u'jobschedule.start_date', start_date)
        set_key(u'jobschedule.end_date', end_date)
        set_key(u'jobschedule.start_time', start_time)
        set_key(u'jobschedule.interval', interval)
        set_key(u'jobschedule.retention_policy_value', snapshots_to_retain)
        set_key(u'jobschedule.enabled', bool2str(enabled))
        set_key(u'jobschedule.timezone', timezone)
        set_key(u'metadata', metadata)

        path = u'/workloads/' + workload_id
        data = json.dumps({u'workload': data})
        res = self.client.call(path, u'PUT', data=data, token=self.omanager.identity.token)
        self.logger.debug(u'Update workload for connection project: %s' % truncate(res[0]))
        return res[0]

    @setup_client
    def delete(self, workload_id):
        """Delete a workload in the connection project

        :param workload_id : ID of the workload to show
        :return: get workload
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/workloads/' + workload_id
        res = self.client.call(path, u'DELETE', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Delete workload %s: %s' % (workload_id, truncate(res)))
        return res[0]

    @setup_client
    def unlock(self, workload_id):
        """Unlock a workload in the connection project

        :param workload_id : ID of the workload to show
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/workloads/' + workload_id + u'/unlock'
        res = self.client.call(path, u'DELETE', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Delete workload %s: %s' % (workload_id, truncate(res)))
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
        path = u'/workloads/' + workload_id + u'/reset'
        res = self.client.call(path, u'POST', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Reset workload %s: %s' % (workload_id, truncate(res)))
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
            filter[u'date_from'] = date_from
        if date_to is not None:
            filter[u'date_to'] = date_to

        if all is True:
            filter[u'all'] = True
            filter = urlencode(filter)
            path = u'/snapshots?' + filter
            res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
            self.logger.debug(u'Get all the snapshots: %s' % truncate(res))
            return res[0].get(u'snapshots', [])
        elif workload_id is not None:
            filter[u'workload_id'] = workload_id
            filter = urlencode(filter)
            path = u'/snapshots?' + filter
            res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
            self.logger.debug(u'Get snapshots for current project and workload %s: %s' % (workload_id, truncate(res)))
            return res[0].get(u'snapshots', [])
        else:
            path = u'/snapshots' + filter
            res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
            self.logger.debug(u'Get snapshots for current project: %s' % truncate(res))
            return res[0].get(u'snapshots', [])

    @setup_client
    def get(self, snapshot_id):
        """ Display snapshot details.

        :param snapshot_id : unique identifier of snapshot
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/snapshots/' + snapshot_id
        res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Get snapshot %s: %s' % (snapshot_id, truncate(res)))
        return res[0].get(u'snapshot', {})

    @setup_client
    def add(self, workload_id, name=None, desc=None, full=True):
        """Creates an on demand snapshot for a given workload.
        To add workload for a specific project change connection project when get token.

        :param workload_type_id: workload id
        :param name: workload name [optional]
        :param desc: workload description [optional]
        :param full: if True make a full snapshot [optional]
        :return: snapshot
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            u'name': name,
            u'description': desc,
            u'full': bool2str(full)
        }

        path = u'/workloads/' + workload_id
        data = json.dumps({u'snapshot': data})
        res = self.client.call(path, u'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug(u'Add workload %s snapshot for connection project: %s' % (workload_id, truncate(res[0])))
        return res[0].get(u'snapshot')

    @setup_client
    def delete(self, snapshot_id):
        """Remove a workload snapshot.

        :param snapshot_id : unique identifier of snapshot
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/snapshots/' + snapshot_id
        res = self.client.call(path, u'DELETE', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Delete snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]

    @setup_client
    def cancel(self, snapshot_id):
        """Cancel a snapshot that is running. If the snapshot operation is in the middle of the data transfer of a
        resource, it waits for the data transfer operation is complete before terminating the snapshot operation.

        :param snapshot_id : unique identifier of snapshot
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/snapshots/' + snapshot_id + u'/cancel'
        res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Cancel snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]

    @setup_client
    def mounted(self):
        """List of all mounted snapshots

        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/snapshots/mounted/list'
        res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'List of all mounted snapshots: %s' % truncate(res))
        return res[0].get(u'mounted_snapshots', [])

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
            u'mount_vm_id': instance_id,
            u'options': {}
        }

        path = u'/snapshots/' + snapshot_id + u'/mount'
        data = json.dumps({u'mount': data})
        res = self.client.call(path, u'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug(u'Mount snapshot %s to instance %s: %s' % (snapshot_id, instance_id, truncate(res[0])))
        return res[0]

    @setup_client
    def dismount(self, snapshot_id):
        """Dismount a workload snapshot.

        :param snapshot_id : unique identifier of snapshot
        :return: snapshot
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            u'options': {}
        }

        path = u'/snapshots/' + snapshot_id + u'/dismount'
        data = json.dumps({u'mount': data})
        res = self.client.call(path, u'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug(u'Dismount snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]


class TrilioSnapshotRestore(TrilioObject):
    """This class will manage the trilio snapshot restore.

    :param manager: TrilioManager instance
    """
    def __init__(self, manager):
        TrilioObject.__init__(self, manager)

    @setup_client
    def list(self, snapshot_id=False):
        """Lists snapshot restores.
        To see workload for a specific project change connection project when get token.

        :param snapshot_id : unique identifier of snapshot
        :return: snapshots restore list
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        filter = u''
        if snapshot_id is not None:
            filter[u'snapshot_id'] = snapshot_id
            filter = urlencode(filter)

        path = u'/restores/detail' + filter
        res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Get snapshot restores: %s' % truncate(res))
        return res[0].get(u'restores', [])

    @setup_client
    def get(self, restore_id):
        """Show details about a workload snapshot restore

        :param snapshot_id : unique identifier of restore
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/restores/' + restore_id
        res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Get restore %s: %s' % (restore_id, truncate(res)))
        return res[0].get(u'restore', {})

    @setup_client
    def delete(self, restore_id):
        """Delete a restore.

        :param restore_id : unique identifier of restore
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/restores/' + restore_id
        res = self.client.call(path, u'DELETE', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Delete restore %s: %s' % (restore_id, truncate(res)))
        return res[0]

    @setup_client
    def cancel(self, restore_id):
        """Cancel a restore.

        :param restore_id : unique identifier of restore_id
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = u'/restores/' + restore_id + u'/cancel'
        res = self.client.call(path, u'GET', data=u'', token=self.omanager.identity.token)
        self.logger.debug(u'Cancel restore %s: %s' % (restore_id, truncate(res)))
        return res[0]

    @setup_client
    def selective(self, snapshot_id, config):
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
        :return: snapshot
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        config[u'restore_type'] = u'selective'
        config[u'oneclickrestore'] = False
        data = {
            u'restore': {
                u'name': config.get(u'name', u'restore'),
                u'description': config.get(u'description', u'restore'),
                u'options': config
            }
        }
        path = u'/snapshots/' + snapshot_id
        data = json.dumps(data)
        res = self.client.call(path, u'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug(u'Selective restore of snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]

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
        config[u'restore_type'] = u'oneclick'
        data = {
            u'restore': {
                u'name': config.get(u'name', u'restore'),
                u'description': config.get(u'description', u'restore'),
                u'options': config
            }
        }
        path = u'/snapshots/' + snapshot_id
        data = json.dumps(data)
        res = self.client.call(path, u'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug(u'Oneclick restore of snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]

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
        config[u'restore_type'] = u'inplace'
        config[u'oneclickrestore'] = False
        data = {
            u'restore': {
                u'name': config.get(u'name', u'restore'),
                u'description': config.get(u'description', u'restore'),
                u'options': config
            }
        }
        path = u'/snapshots/' + snapshot_id
        data = json.dumps(data)
        res = self.client.call(path, u'POST', data=data, token=self.omanager.identity.token)
        self.logger.debug(u'Inplace restore of snapshot %s: %s' % (snapshot_id, truncate(res[0])))
        return res[0]

    def server(self, snapshot_id, server_id, server_name=None, overwrite=False, name=u'restore', desc=u'restore'):
        server = self.omanager.server.get(oid=server_id)
        avz = server.get(u'OS-EXT-AZ:availability_zone')
        ports = self.omanager.server.get_port_interfaces(server_id)
        net_mapping = [{
            u'snapshot_network': {u'id': p.get(u'net_id'),
                                  u'subnet': {u'id': p.get(u'fixed_ips')[0].get(u'subnet_id')}},
            u'target_network': {u'id': p.get(u'net_id'),
                                u'subnet': {u'id': p.get(u'fixed_ips')[0].get(u'subnet_id')}}} for p in ports]
        if server_name is None:
            server_name = u'%s-restore-%s' % (server.get(u'name'), id_gen(length=4))

        if overwrite is True:
            vdisks = [{u'id': v.get(u'id'),
                       u'availability_zone': avz,
                       u'new_volume_type': self.omanager.volume.get(oid=v.get(u'id')).get(u'volume_type')}
                      for v in server.get(u'os-extended-volumes:volumes_attached', [])]
            config = {
                u'type': u'openstack',
                u'name': name,
                u'description': desc,
                u'openstack': {
                    u'restore_topology': False,
                    u'instances': [
                        {
                            u'id': server_id,
                            u'name': server_name,
                            u'availability_zone': avz,
                            u'include': True,
                            u'flavor': {
                                u'id': server.get(u'flavor').get(u'id')
                            },
                            u'vdisks': vdisks,
                            u'nics': [

                            ]
                        }
                    ],
                    u'networks_mapping': {
                        u'networks': net_mapping
                    }
                }
            }
            res = self.inplace(snapshot_id, config)
            self.logger.debug(u'Replace server %s from snapshot %s' % (server_id, snapshot_id))
        else:
            vdisks = [{u'id': v.get(u'id'),
                       u'availability_zone': avz,
                       u'new_volume_type': self.omanager.volume.get(oid=v.get(u'id')).get(u'volume_type')}
                      for v in server.get(u'os-extended-volumes:volumes_attached', [])]
            config = {
                u'type': u'openstack',
                u'name': name,
                u'description': desc,
                u'openstack': {
                    u'instances': [
                        {
                            u'id': server_id,
                            u'name': server_name,
                            u'restore_boot_disk': True,
                            u'include': True,
                            u'vdisks': vdisks,
                            u'nics': [

                            ]
                        }
                    ],
                    u'networks_mapping': {
                        u'networks': net_mapping
                    }
                }
            }
            res = self.selective(snapshot_id, config)
            self.logger.debug(u'Restore server %s from snapshot %s' % (server_id, snapshot_id))
        return res

    def volume(self, snapshot_id, volume_id, overwrite=False, name=u'restore', desc=u'restore'):
        volume = self.omanager.volume.get(oid=volume_id)
        attachments = volume.get(u'attachments', [])
        if len(attachments) > 0:
            server_id = attachments[0].get(u'server_id')
        else:
            raise OpenstackError(u'Volume %s is not attached to a server' % volume_id)
        if overwrite is False:
            raise OpenstackError(u'Volume can not be restored as new. Only volume overwrite is supported.')
        else:
            vdisks = [{u'id': volume_id, u'restore_cinder_volume': True}]
            config = {
                u'type': u'openstack',
                u'name': name,
                u'description': desc,
                u'openstack': {
                    u'instances': [
                        {
                            u'id': server_id,
                            u'restore_boot_disk': False,
                            u'include': True,
                            u'vdisks': vdisks
                        }
                    ]
                }
            }
            res = self.inplace(snapshot_id, config)
            self.logger.debug(u'Restore server %s from snapshot %s' % (server_id, snapshot_id))
        return res

