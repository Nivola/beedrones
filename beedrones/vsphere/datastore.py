# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from pyVmomi import vmodl
from pyVmomi import vim
from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereDatastore(VsphereObject):
    """
    """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self):
        """Get datastore with some properties:
            ['obj']._moId, ['parent']._moId, ['name', ''), ['overallStatus']

        return: list of vim.Cluster
        """
        props = ['name', 'parent', 'overallStatus', 'summary.accessible', 'summary.capacity',
                 'summary.freeSpace', 'summary.maintenanceMode', 'summary.type']
        view = self.manager.get_container_view(obj_type=[vim.Datastore])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.Datastore,
                                               path_set=props,
                                               include_mors=True)
        view = self.manager.get_container_view(obj_type=[vim.StoragePod])
        props = ['name', 'parent', 'overallStatus', 'summary.capacity', 'summary.freeSpace']
        data2 = self.manager.collect_properties(view_ref=view,
                                                obj_type=vim.StoragePod,
                                                path_set=props,
                                                include_mors=True)
        data.extend(data2)
        return data

    def get(self, morid):
        """Get datastore by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        container = None
        obj = self.manager.get_object(morid, [vim.Datastore, vim.StoragePod], container=container)
        return obj

    #
    # summary
    #
    def info(self, obj):
        """datastore main info
        """
        info = {
            'id': obj.get('obj')._moId,
            'parent': obj.get('parent')._moId,
            'name': obj.get('name'),
            'overallStatus': obj.get('overallStatus'),
            'accessible': obj.get('summary.accessible', ''),
            'size': round(obj.get('summary.capacity') / 1073741824),
            'freespace': round(obj.get('summary.freeSpace') / 1073741824),
            'maintenanceMode': obj.get('summary.maintenanceMode', ''),
            'type': obj.get('summary.type')
        }
        return info

    def detail(self, obj):
        """datastore main info
        """
        info = {
            'id': obj._moId,
            'parent': obj.parent._moId,
            'name': obj.name,
            'overallStatus': obj.overallStatus,
            'accessible': getattr(obj.summary, 'accessible', ''),
            'size': round(getattr(obj.summary, 'capacity', 0) / 1073741824),
            'url': getattr(obj.summary, 'url', ''),
            'freespace': round(getattr(obj.summary, 'freeSpace', 0) / 1073741824),
            'maintenanceMode': getattr(obj.summary, 'maintenanceMode', ''),
            'multipleHostAccess': getattr(obj.summary, 'multipleHostAccess', ''),
            'type': getattr(obj.summary, 'type', ''),
            'uncommitted': getattr(obj.summary, 'uncommitted', '')
        }

        return info

    def usage(self):
        """storage usage
        """
        pass

    #
    # monitor
    #

    def issues(self, datastore):
        """
        """
        pass

    def perfomance(self, datastore):
        """
        """
        pass

    def tasks(self, datastore):
        """
        """
        pass

    def events(self, datastore):
        """
        """
        pass

    #
    # manage
    #
    def list_objects(self, datastore):
        pass

    def browse_files(self, datastore, path='/'):
        """
        """
        try:
            res = []
            browser = datastore.browser
            # print browser.supportedType

            task = browser.SearchDatastore_Task(datastorePath='[%s] %s' %
                                                              (datastore.name, path))
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg, code=0)
        return task

    def parse_files(self, result):
        """ """
        try:
            res = []
            files = result.file
            for item in files:
                res.append({'type': type(item).__name__,
                            'dynamicType': item.dynamicType,
                            'path': item.path,
                            'fileSize': item.fileSize,
                            'modification': item.modification,
                            'owner': item.owner})
        except Exception as error:
            self.logger.error(error, exc_info=False)
            raise VsphereError(error, code=0)
        return res

    def mount(self, datastore):
        """
        """
        pass

    def unmount(self, datastore):
        """
        """
        pass

    def enter_maintenance(self, datastore):
        """
        """
        pass

    def exit_maintenance(self, datastore):
        """
        """
        pass

    #
    # related object
    #
    def get_servers(self, morid):
        """
        """
        container = None
        obj = self.manager.get_object(morid, [vim.Datastore], container=container)
        view = self.manager.get_container_view(obj_type=[vim.VirtualMachine], container=obj)
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.VirtualMachine,
                                               path_set=self.manager.server_props,
                                               include_mors=True)
        obj = self.manager.get_object(morid, [vim.StoragePod], container=container)
        view = self.manager.get_container_view(obj_type=[vim.VirtualMachine], container=obj)
        data2 = self.manager.collect_properties(view_ref=view,
                                                obj_type=vim.VirtualMachine,
                                                path_set=self.manager.server_props,
                                                include_mors=True)
        data.extend(data2)
        return data

    def get_hosts(self, datastore):
        """
        """
        try:
            hosts = datastore.host
            res = []
            for host in hosts:
                host = host.key
                res.append({'name': host.name,
                            'id': host._moId})
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg, code=0)
        return res
