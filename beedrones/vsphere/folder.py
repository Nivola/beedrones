# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2026 CSI-Piemonte

from typing import Optional
from pyVmomi import vim, vmodl
from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereFolder(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self):
        """Get folders with some properties:
        ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']
        """
        props = ["name", "parent", "childType", "overallStatus", "customValue"]
        view = self.manager.get_container_view(obj_type=[vim.Folder])
        data = self.manager.collect_properties(view_ref=view, obj_type=vim.Folder, path_set=props, include_mors=True)
        return data

    def get(self, morid):
        """Get folder by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        obj = self.manager.get_object(morid, [vim.Folder], container=None)
        return obj

    def get_folders_by_name(self, folder_name):
        """Get folders
        with name like foldername, if present.
        Returns list of folders
        """
        props = ["name", "parent", "childType", "overallStatus", "customValue"]

        cont = self.manager.get_container_view([vim.Folder], container=None)

        data = self.manager.collect_properties(view_ref=cont, obj_type=vim.Folder, path_set=props, include_mors=True)

        folders = []
        for item in data:
            if item.get("name").find(folder_name) >= 0:
                folders.append(item)

        return folders

    def create(
        self,
        name: str,
        folder: Optional[vim.Folder]=None,
        datacenter: Optional[vim.Datacenter]=None,
        host: bool=False,
        network: bool=False,
        storage: bool=False,
        vm: bool=False,
        desc: Optional[str]=None,
    ):
        """Creates a folder.

        :param name: String Name for the folder
        :param desc: folder description [optional]
        :param folder: parent folder
        :param datacenter: parent datacenter
        :param host: if True create a host subfolder
        :param network: if True create a network subfolder
        :param storage: if True create a storage subfolder
        :param vm: if True create a vm subfolder
        """
        try:
            if desc is None:
                desc = name

            _folder: vim.Folder
            if folder is not None:
                _folder = folder.CreateFolder(name=name)
            elif datacenter is not None:
                # vm folder
                if vm is True:
                    _folder = datacenter.vmFolder.CreateFolder(name=name)
                #  Datastore folder
                elif storage is True:
                    _folder = datacenter.datastoreFolder.CreateFolder(name=name)
                # host folder
                elif host is True:
                    _folder = datacenter.hostFolder.CreateFolder(name=name)
                # Network folder
                elif network is True:
                    # NON USATO. TYPO: networkFolder
                    _folder = datacenter.networkFolde.CreateFolder(name=name)
                else:
                    raise vmodl.MethodFault(msg="No type of folder is been specified")
            else:
                raise vmodl.MethodFault(msg="No parent folder is been specified")
            try:
                _folder.setCustomValue("desc", desc)
            except Exception as ex:
                self.logger.error("Folder %s desc can not be set: %s", name, ex)

            self.logger.debug("Create folder %s" % _folder._moId)
            return _folder
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg)

    def remove(self, folder: vim.Folder):
        """
        :param folder: folder instance. Get with get_by_****
        """
        task = folder.Destroy_Task()
        self.logger.debug("Remove folder %s" % folder._moId)
        return task

    def update(self, folder: vim.Folder, name: Optional[str]=None, desc: Optional[str]=None):
        """
        :param folder: folder instance. Get with get_by_****
        :param name: new folder name [optional]
        :param desc: new folder desc [optional]
        """
        task = None
        if desc is not None:
            folder.setCustomValue("desc", desc)
        if name is not None:
            task = folder.Rename_Task(name)
        self.logger.debug("Update folder %s" % folder._moId)
        return task

    #
    # summary
    #

    def info(self, obj):
        """
        :param obj: folder instance. Get with get_by_****
        """
        info = {
            "id": obj.get("obj")._moId,
            "parent": obj.get("parent")._moId,
            "name": obj.get("name"),
            "overallStatus": obj.get("overallStatus"),
            "type": ",".join(obj.get("childType", "")),
        }
        custom_values = obj.get("customValue")
        if len(custom_values) > 0:
            info["desc"] = custom_values[0].value
        return info

    def detail(self, obj):
        """
        :param obj: folder instance. Get with get_by_****
        """
        info = {
            "id": obj._moId,
            "parent": obj.parent._moId,
            "name": obj.name,
            "overallStatus": obj.overallStatus,
            "type": ",".join(obj.childType),
        }
        custom_values = obj.customValue
        if len(custom_values) > 0:
            info["desc"] = custom_values[0].value
        return info

    #
    # monitor
    #

    #
    # manage
    #

    #
    # related object
    #

    def get_servers(self, morid):
        """Get servers with some properties"""
        container = None
        obj = self.manager.get_object(morid, [vim.Folder], container=container)
        view = self.manager.get_container_view(obj_type=[vim.VirtualMachine], container=obj)
        vm_data = self.manager.collect_properties(
            view_ref=view,
            obj_type=vim.VirtualMachine,
            path_set=self.manager.server_props,
            include_mors=True,
        )
        return vm_data
