# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from pyVmomi import vim
from beedrones.vsphere.client import VsphereObject


class VsphereVApp(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self):
        """Get vapp with some properties:"""
        properties = ["name", "parent", "overallStatus"]

        view = self.manager.get_container_view(obj_type=[vim.VirtualApp], container=None)
        data = self.manager.collect_properties(
            view_ref=view,
            obj_type=vim.VirtualApp,
            path_set=properties,
            include_mors=True,
        )
        return data

    def get(self, morid):
        """Get vapp by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        container = None
        obj = self.manager.get_object(morid, [vim.VirtualApp], container=container)
        return obj

    def create(self):
        """"""
        pass

    def update(self, vapp):
        """
        :param vapp: vapp instance. Get with get_by_****
        """
        # @TODO
        task = None
        return task

    def remove(self, vapp):
        """
        :param vapp: vapp instance. Get with get_by_****
        """
        task = vapp.Destroy_Task()
        return task

    def info(self, vapp):
        """
        :param vapp: vapp instance. Get with get_by_****
        """
        return {}
