# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from pyVmomi import vim
from beedrones.vsphere.client import VsphereObject


class VsphereDatacenter(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self):
        """Get _datacenters with some properties:
        ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']
        """
        props = ["name", "parent", "overallStatus"]
        view = self.manager.get_container_view(obj_type=[vim.Datacenter])
        data = self.manager.collect_properties(
            view_ref=view, obj_type=vim.Datacenter, path_set=props, include_mors=True
        )
        return data

    def get(self, morid):
        """Get _datacenter by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        obj = self.manager.get_object(morid, [vim.Datacenter], container=None)
        return obj

    def remove(self, dc):
        """
        :param dc: dc instance. Get with get_by_****
        """
        task = dc.Destroy_Task()
        return task

    #
    # summary
    #

    def info(self, obj):
        """Datacenter info

        :param obj: dc instance. Get with get_by_****
        """
        info = {
            "id": obj.get("obj")._moId,
            "parent": obj.get("parent")._moId,
            "name": obj.get("name"),
            "overallStatus": obj.get("overallStatus"),
        }

        return info

    def detail(self, obj):
        """Datacenter details

        :param obj: dc instance. Get with get_by_****
        """
        info = {
            "id": obj._moId,
            "parent": obj.parent._moId,
            "name": obj.name,
            "overallStatus": obj.overallStatus,
        }
        return info

    def sessions(self):
        """List datacenter sessions"""
        info = []
        content = self.manager.si.RetrieveContent()
        session_manager = content.sessionManager
        for s in session_manager.sessionList:
            info.append(
                {
                    "key": getattr(s, "key"),
                    "user_name": getattr(s, "userName"),
                    "full_name": getattr(s, "fullName"),
                    "login_time": getattr(s, "loginTime"),
                    "last_active_time": getattr(s, "lastActiveTime"),
                    "locale": getattr(s, "locale"),
                    "message_locale": getattr(s, "messageLocale"),
                    "ip_address": getattr(s, "ipAddress"),
                    "user_Agent": getattr(s, "userAgent"),
                }
            )
        info.sort(key=lambda x: x.get("last_active_time"))
        return info
