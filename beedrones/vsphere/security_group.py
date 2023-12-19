# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from six import ensure_text
from beedrones.vsphere.client import VsphereObject


class VsphereNetworkSecurityGroup(VsphereObject):
    """ """

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self):
        """ """
        res = self.call("/api/2.0/services/securitygroup/scope/globalroot-0", "GET", "")["list"]["securitygroup"]
        if isinstance(res, dict):
            res = [res]
        return res

    def list_by_server(self, vmid):
        """
        :param moid: server morid
        """
        res = self.call("/api/2.0/services/securitygroup/lookup/virtualmachine/%s" % vmid, "GET", "")
        return res

    def get(self, oid):
        """
        :param oid: securitygroup id
        :return: None if security group does not exist
        """
        res = self.call("/api/2.0/services/securitygroup/%s" % oid, "GET", "")
        return res["securitygroup"]

    def info(self, sg):
        """ """
        sg["id"] = sg.pop("objectId")
        return sg

    def detail(self, sg):
        """ """
        sg["id"] = sg.pop("objectId")
        return sg

    def create(self, name):
        """Create security group

        <member>
        <objectId></objectId>
        <objectTypeName></objectTypeName>
        <vsmUuid></vsmUuid>
        <revision></revision>
        <type>
        <typeName></typeName>
        </type>
        <name></name>
        <scope>
        <id></id>
        <objectTypeName></objectTypeName>
        <name></name>
        </scope>
        <clientHandle></clientHandle>
        <extendedAttributes></extendedAttributes>
        </member>

        <excludeMember>
        <objectId></objectId>
        <objectTypeName></objectTypeName>
        <vsmUuid></vsmUuid>
        <revision></revision>
        <type>
        <typeName></typeName>
        </type>
        <name></name>
        <scope>
        <id></id>
        <objectTypeName></objectTypeName>
        <name></name>
        </scope>
        <clientHandle></clientHandle>
        <extendedAttributes></extendedAttributes>
        </excludeMember>

        <dynamicMemberDefinition>
        <dynamicSet>
        <operator></operator>
        <dynamicCriteria>
        <operator></operator>
        <key></key>
        <criteria></criteria>
        <value></value>
        </dynamicCriteria>
        <dynamicCriteria>
        </dynamicCriteria>
        </dynamicSet>
        </dynamicMemberDefinition>

        :param name: logical switch name
        :return: mor id
        """
        data = [
            "<securitygroup>",
            "<name>%s</name>" % name,
            "<scope>",
            "<id>globalroot-0</id>",
            "<objectTypeName>GlobalRoot</objectTypeName>",
            "<name>Global</name>",
            "</scope>",
            "</securitygroup>",
        ]
        data = "".join(data)
        res = self.call(
            "/api/2.0/services/securitygroup/bulk/globalroot-0",
            "POST",
            data,
            headers={"Content-Type": "text/xml"},
            timeout=600,
        )
        return ensure_text(res)

    def update(self, oid):
        """Update security group

        TODO:

        :param oid: securitygroup id
        """
        pass

    def delete(self, oid, force=False):
        """Delete security group

        :param oid: securitygroup id
        """
        uri = "/api/2.0/services/securitygroup/%s" % oid
        if force is True:
            uri += "?force=true"
        res = self.call(uri, "DELETE", "", timeout=600)
        return res

    def get_allowed_member_type(self, oid):
        """Retrieve a list of valid elements that can be added to a security group.

        :param oid: security group id
        """
        res = self.call("/api/2.0/services/securitygroup/scope/globalroot-0/memberTypes", "GET", "")
        return res

    def add_member(self, oid, moid):
        """
        :param oid: security group id
        :param moid: member morid
        """
        res = self.call(
            "/api/2.0/services/securitygroup/%s/members/%s" % (oid, moid),
            "PUT",
            "",
            timeout=600,
        )
        return res

    def delete_member(self, oid, moid):
        """
        :param oid: security group id
        :param moid: member morid
        """
        res = self.call(
            "/api/2.0/services/securitygroup/%s/members/%s" % (oid, moid),
            "DELETE",
            "",
            timeout=600,
        )
        return res
