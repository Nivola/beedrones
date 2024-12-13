# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import jsonDumps

import ujson as json
from logging import getLogger
from beecell.simple import truncate
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import urlopen
from beedrones.openstack.client import (
    OpenstackClient,
    OpenstackError,
    OpenstackObject,
    setup_client,
)


class OpenstackManilaObject(OpenstackObject):
    def setup(self):
        self.uri = self.manager.endpoint("manilav2")
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)
        self.set_manila_microversion("2.42")


class OpenstackManila(OpenstackManilaObject):
    """Openstack manila client"""

    def __init__(self, manager):
        OpenstackManilaObject.__init__(self, manager)

        self.share = OpenstackManilaShare(self)
        self.share_type = OpenstackManilaShareType(self)
        self.storage_pool = OpenstackManilaStoragePool(self)
        self.quota_set = OpenstackManilaQuotaSet(self)
        self.security_service = OpenstackManilaSecurityService(self)
        self.network = OpenstackManilaShareNetwork(self)
        self.server = OpenstackManilaShareServer(self)

    @setup_client
    def api(self, version=None):
        """Get manila api versions.

        :param version: api version
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if version is None:
            redux_uri = self.uri.split("/")[0] + "//" + self.uri.split("/")[2]
            client = OpenstackClient(redux_uri, self.manager.proxy, timeout=self.manager.timeout)
            path = "/"
            self.logger.debug("Path to check: %s%s" % (client.path, path))
            res = client.call(path, "GET", data="", token=self.manager.identity.token)
            self.logger.debug("Get openstack manila api: %s" % truncate(res[0]))
            return res[0]["versions"]
        else:
            redux_uri = self.uri.split("/")[0] + "//" + self.uri.split("/")[2]
            client = OpenstackClient(redux_uri, self.manager.proxy, timeout=self.manager.timeout)
            path = "/%s/" % version
            self.logger.debug("Path to check: %s%s" % (client.path, path))
            res = client.call(path, "GET", data="", token=self.manager.identity.token)
            self.logger.debug("Get openstack manila api %s: %s" % (version, truncate(res[0])))
            return res[0]["version"]

    @setup_client
    def limits(self):
        """Limits are the resource limitations that are allowed for each tenant (project). An administrator can
        configure limits in the manila.conf file.
        Users can query their rate and absolute limits. The absolute limits contain information about:

        * Total maximum share memory, in GBs.
        * Number of share-networks.
        * Number of share-snapshots.
        * Number of shares.
        * Shares and total used memory, in GBs.
        * Snapshots and total used memory, in GBs.

        Rate limits control the frequency at which users can issue specific API requests. Administrators use rate
        limiting to configure limits on the type and number of API calls that can be made in a specific time interval.
        For example, a rate limit can control the number of GET requests that can be processed during a one-minute
        period.

        :return:
        :raise OpenstackError:
        """
        path = "/limits"
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack manila limits: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def services(self):
        """Lists all services optionally filtered with the specified search options.

        :return: service list
        :raise OpenstackError:
        """
        path = "/services"
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack manila limits: %s" % truncate(res[0]))
        return res[0]["services"]

    @setup_client
    def messages(self, *args, **kwargs):
        """User messages are automatically created when an asynchronous action fails on a resource. In such situations
        an error is logged in the appropriate log file but end users may not have access to the log files. User
        messages can be used by users to get error details for failed actions. This is handy for example when creating
        shares - if a share creation fails because a scheduling filter doesn’t find suitable back-end host for the
        share, this share will end up in error state, but from user messages API users can get details about the last
        executed filter which helps them identify the issue and perhaps re-attempt the creation request with different
        parameters.

        :return: messages list
        :raise OpenstackError:
        """
        path = "/messages"
        if len(kwargs.keys()) > 0:
            path += "?" + urlencode(kwargs)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack manila messages: %s" % truncate(res[0]))
        return res[0]["messages"]


class OpenstackManilaShare(OpenstackManilaObject):
    """Openstack manila share client.

    A share is a remote, mountable file system. You can mount a share to and access a share from several hosts by
    several users at a time.
    You can create a share and associate it with a network, list shares, and show information for, update, and delete a
    share.
    To create a share, specify one of these supported protocols:

    * NFS. Network File System (NFS).
    * CIFS. Common Internet File System (CIFS).
    * GLUSTERFS. Gluster file system (GlusterFS).
    * HDFS. Hadoop Distributed File System (HDFS).
    * CEPHFS. Ceph File System (CephFS).
    * MAPRFS. MapR File System (MAPRFS).

    You can also create snapshots of shares. To create a snapshot, you specify the ID of the share that you want to
    snapshot. A share has one of these status values:

    * creating: The share is being created.
    * deleting: The share is being deleted.
    * deleted: The share was deleted.
    * error: An error occurred during share creation.
    * error_deleting: An error occurred during share deletion.
    * available: The share is ready to use.
    * inactive: The share is inactive.
    * manage_starting: Share manage started.
    * manage_error: Share manage failed.
    * unmanage_starting: Share unmanage started.
    * unmanage_error: Share cannot be unmanaged.
    * unmanaged: Share was unmanaged.
    * extending: The extend, or increase, share size request was issued successfully.
    * extending_error: Extend share failed.
    * shrinking: Share is being shrunk.
    * shrinking_error: Failed to update quota on share shrinking.
    * shrinking_possible_data_loss_error: Shrink share failed due to possible data loss.
    * migrating: Share is currently migrating.
    * migrating_to: Share is a migration destination.
    * replication_change: The share is undergoing a replication change.
    * reverting: Share is being reverted to a snapshot.
    * reverting_error: Share revert to snapshot failed.
    """

    def __init__(self, manila):
        OpenstackManilaObject.__init__(self, manila.manager)

        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)
        self.action = OpenstackManilaShareAction(manila)
        self.snapshot = OpenstackManilaShareSnapshot(manila)

    @setup_client
    def list(self, details=False, **kwargs):
        """Lists all shares.

        :param details: (Optional) if True get item with details
        :param all_tenants: (Optional) (Admin only). Defines whether to list shares or share groups for all tenants.
            Set to 1 to list shares or sharegroups for all tenants. Set to 0 to list shares or share groups only for
            the current tenant.
        :param kwargs.share_network_id: (Optional) The UUID of the share network to filter resources by.
        :return: list of dict with share info
        :raise OpenstackError:
        """
        path = "/shares"
        if details is True:
            path += "/detail"
        kwargs["all_tenants"] = kwargs.get("all_tenants", 1)
        path += "?" + urlencode(kwargs)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack shares list: %s" % truncate(res[0]))
        return res[0]["shares"]

    @setup_client
    def get(self, share_id):
        """Get share by id

        :param share_id: id of the share
        :return: dict with share info
        :raise OpenstackError:
        """
        path = "/shares/%s" % share_id
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack share: %s" % truncate(res[0]))
        return res[0]["share"]

    @setup_client
    def manage(self):
        """Configures Shared File Systems to manage a share TODO

            TODO

        :return:
        :raise OpenstackError:
        """
        path = "/shares/manage"
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Manage openstack shares: %s" % truncate(res[0]))
        return res[0]["share"]

    @setup_client
    def create(self, share_proto, size, **kvargs):
        """Creates a share.

        :param share_proto: The Shared File Systems protocol. A valid value is NFS, CIFS, GlusterFS,
                HDFS, or CephFS. CephFS supported is starting with API v2.13.
        :param size: The share size, in GBs. The requested share size cannot be greater than the
                allowed GB quota. To view the allowed quota, issue a get limits request.
        :param name: (Optional)The share name.
        :param description: (Optional) The share description.
        :param display_name: (Optional) The share name. The Shared File Systems API supports the use
                of both name and display_name attributes, which are inherited attributes from the Block Storage API.
        :param display_description: (Optional) The share description. The Shared File Systems API
                supports the use of both description and display_description parameters, which are inherited attributes
                from the Block Storage API.
        :param share_type: (Optional) The share type name. If you omit this parameter, the default
                share type is used. To view the default share type set by the administrator, issue a list default share
                types request. You cannot specify both the share_type and volume_type parameters.
        :param volume_type: (Optional) The volume type. The use of the volume_type object is
                deprecated but supported. It is recommended that you use the share_type object when you create a share
                type. When you issue a create a share type request, you can submit a request body with either a
                share_type or volume_type object. No matter which object type you include in the request, the API
                creates both a volume_type object and a share_type object. Both objects have the same ID. When you issue
                a list share types request, the response shows both share_types and volume_types objects.
        :param snapshot_id: (Optional) The UUID of the share's base snapshot.
        :param is_public: (Optional) The level of visibility for the share. Set to true to make
                share public. Set to false to make it private. Default value is false.
        :param share_group_id :(Optional) The UUID of the share group.
        :param metadata: (Optional) One or more metadata key and value pairs as a dictionary of
                strings.
        :param share_network_id: (Optional) The UUID of a share network where the share server
                exists or will be created. If share_network_id is None and you provide a snapshot_id, the
                share_network_id value from the snapshot is used.
        :param availability_zone: (Optional) The availability zone.
        :return:
        :raise OpenstackError:
        """
        data = {"share_proto": share_proto, "size": size}

        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        path = "/shares"
        data = jsonDumps({"share": data})
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack create share: %s" % truncate(res[0]))
        return res[0]["share"]

    @setup_client
    def update(self, share_id, **kvargs):
        """Updates a share.

        :param share_id: id of the share
        :param is_public : (Optional) The level of visibility for the share. Set to true to make share public. Set to
            false to make it private. Default value is false.
        :param display_name : (Optional) The snapshot name. If you specify this attribute, the snapshot name is updated.
        :param display_description : (Optional) The share description. If you specify this parameter, the share
            description is updated.
        :return:
        :raise OpenstackError:
        """
        data = {}
        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        path = "/shares/%s" % share_id
        data = jsonDumps({"share": data})
        res = self.client.call(path, "PUT", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack update share: %s" % truncate(res[0]))
        return res[0]["share"]

    @setup_client
    def delete(self, share_id):
        """Deletes a share.

        :param share_id: id of the share
        :return:
        :raise OpenstackError:
        """
        path = "/shares/%s" % share_id
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack delete share %s: %s" % (share_id, truncate(res[0])))
        return res[0]

    @setup_client
    def list_export_locations(self, share_id, **kwargs):
        """List export locations

        :param share_id: id of the share
        :return: list of dict with share export locations info
        :raise OpenstackError:
        """
        path = "/shares/%s/export_locations" % share_id
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack share export locations list: %s" % truncate(res[0]))
        return res[0]["export_locations"]

    @setup_client
    def get_export_location(self, share_id, export_location_id):
        """Show single export location

        :param share_id: id of the share
        :param export_location_id: export location id
        :return: dict with share info
        :raise OpenstackError:
        """
        path = "/shares/%s/export_locations/%s" % (share_id, export_location_id)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack share export location: %s" % truncate(res[0]))
        return res[0]["export_location"]


class OpenstackManilaShareAction(OpenstackManilaObject):
    """Share actions include granting or revoking share access, listing the available access rules for a share,
    explicitly updating the state of a share, resizing a share and un-managing a share.
    As administrator, you can reset the state of a share and force- delete a share in any state. Use the policy.json
    file to grant permissions for this action to other roles.
    You can set the state of a share to one of these supported states:
    - available
    - error
    - creating
    - deleting
    - error_deleting
    """

    def __init__(self, manila):
        OpenstackManilaObject.__init__(self, manila.manager)

        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)

    @setup_client
    def action(self, share_id, action, data):
        """Helper method to send action

        :param share_id: share id
        :param action: action
        :param data: data to send
        :return: action response as dict
        :raise OpenstackError:
        """
        path = "/shares/%s/action" % share_id
        data = jsonDumps(data)
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack action %s to share %s: %s" % (action, share_id, truncate(res[0])))
        return res[0]

    @setup_client
    def grant_access(self, share_id, access_level, access_type, access_to):
        """All manila shares begin with no access. Clients must be provided with explicit access via this API.
        To grant access, specify one of these supported share access levels:
        - rw. Read and write (RW) access.
        - ro. Read-only (RO) access.
        You must also specify one of these supported authentication methods:
        - ip. Authenticates an instance through its IP address. The value specified should be a valid IPv4 or an IPv6
          address, or a subnet in CIDR notation. A valid format is X:X:X:X:X:X:X:X, X:X:X:X:X:X:X:X/XX, XX.XX.XX.XX,
          or XX.XX.XX.XX/XX, etc. For example 0.0.0.0/0 or ::/0.
        - cert. Authenticates an instance through a TLS certificate. Specify the TLS identity as the IDENTKEY. A valid
          value is any string up to 64 characters long in the common name (CN) of the certificate. The meaning of a
          string depends on its interpretation.
        - user. Authenticates by a user or group name. A valid value is an alphanumeric string that can contain some
          special characters and is from 4 to 255 characters long.

        Grants access to a share.

        :param share_id: share id
        :param access_level: The access level to the share. To grant or deny access to a share,
                you specify one of the following share access levels: - rw. Read and write (RW) access. - ro.
                Read- only (RO) access.
        :param access_type: The access rule type. A valid value for the share access rule type is
                one of the following values: - ip. Authenticates an instance through its IP address. A valid format is
                XX.XX.XX.XX or XX.XX.XX.XX/XX. For example 0.0.0.0/0. - cert. Authenticates an instance through a TLS
                certificate. Specify the TLS identity as the IDENTKEY. A valid value is any string up to 64 characters
                long in the common name (CN) of the certificate. The meaning of a string depends on its interpretation.
                - user. Authenticates by a user or group name. A valid value is an alphanumeric string that can contain
                some special characters and is from 4 to 32 characters long.
        :param access_to: The value that defines the access. The back end grants or denies the
                access to it. A valid value is one of these values: - ip. Authenticates an instance through its IP
                address. A valid format is XX.XX.XX.XX or XX.XX.XX.XX/XX. For example 0.0.0.0/0. - cert. Authenticates
                an instance through a TLS certificate. Specify the TLS identity as the IDENTKEY. A valid value is any
                string up to 64 characters long in the common name (CN) of the certificate. The meaning of a string
                depends on its interpretation. - user. Authenticates by a user or group name. A valid value is an
                alphanumeric string that can contain some special characters and is from 4 to 32 characters long.
        :return:

            {
                "share_id": "406ea93b-32e9-4907-a117-148b3945749f",
                "created_at": "2015-09-07T09:14:48.000000",
                "updated_at": null,
                "access_type": "ip",
                "access_to": "0.0.0.0/0",
                "access_level": "rw",
                "access_key": null,
                "id": "a25b2df3-90bd-4add-afa6-5f0dbbd50452"
            }

        :raise OpenstackError:
        """
        data = {
            "allow_access": {
                "access_level": access_level,
                "access_type": access_type,
                "access_to": access_to,
            }
        }

        res = self.action(share_id, "grant_access", data).get("access", {})
        return res

    @setup_client
    def revoke_access(self, share_id, access_id):
        """The shared file systems service stores each access rule in its database and assigns it a unique ID. This ID
        can be used to revoke access after access has been requested.

        :param share_id: share id
        :param access_id: The UUID of the access rule to which access is granted.
        :return:
        :raise OpenstackError:
        """
        data = {"deny_access": {"access_id": access_id}}

        res = self.action(share_id, "revoke_access", data)
        return res

    @setup_client
    def list_access(self, share_id):
        """Lists access rules for a share. The Access ID returned is necessary to deny access.

        :param share_id: share id
        :return:

            [
                {
                    "access_level": "rw",
                    "state": "error",
                    "id": "507bf114-36f2-4f56-8cf4-857985ca87c1",
                    "access_type": "cert",
                    "access_to": "example.com",
                    "access_key": null
                },
                {
                    "access_level": "rw",
                    "state": "active",
                    "id": "a25b2df3-90bd-4add-afa6-5f0dbbd50452",
                    "access_type": "ip",
                    "access_to": "0.0.0.0/0",
                    "access_key": null
                }
            ]

        :raise OpenstackError:
        """
        data = {"access_list": None}

        res = self.action(share_id, "list_access", data).get("access_list", [])
        return res

    @setup_client
    def reset_status(self, share_id, status):
        """Administrator only. Explicitly updates the state of a share.

        :param share_id: share id
        :param status: The share access status, which is new, error, active.
        :return:
        :raise OpenstackError:
        """
        data = {"reset_status": {"status": status}}

        res = self.action(share_id, "reset_status", data)
        return res

    @setup_client
    def force_delete(self, share_id):
        """Administrator only. Force-deletes a share in any state.

        :param share_id: share id
        :return:
        :raise OpenstackError:
        """
        data = {"force_delete": None}

        res = self.action(share_id, "force_delete", data)
        return res

    @setup_client
    def extend(self, share_id, new_size):
        """Increases the size of a share.

        :param share_id: share id
        :param new_size: New size of the share, in GBs.
        :return:
        :raise OpenstackError:
        """
        data = {"extend": {"new_size": new_size}}

        res = self.action(share_id, "extend", data)
        return res

    @setup_client
    def shrink(self, share_id, new_size):
        """Shrinks the size of a share.

        :param share_id: share id
        :param new_size: New size of the share, in GBs.
        :return:
        :raise OpenstackError:
        """
        data = {"shrink": {"new_size": new_size}}

        res = self.action(share_id, "shrink", data)
        return res

    @setup_client
    def unmanage(self, share_id):
        """Unmanage a share.

        :param share_id: share id
        :return:
        :raise OpenstackError:
        """
        data = {"unmanage": None}

        res = self.action(share_id, "unmanage", data)
        return res

    @setup_client
    def revert(self, share_id, snapshot_id):
        """Reverts a share to the specified snapshot, which must be the most recent one known to manila.

        :param share_id: share id
        :param snapshot_id: The UUID of the snapshot.
        :return:
        :raise OpenstackError:
        """
        data = {"revert": {"snapshot_id": snapshot_id}}

        res = self.action(share_id, "revert", data)
        return res


class OpenstackManilaShareSnapshot(OpenstackManilaObject):
    """Openstack manila share snapshot. Use the shared file service to make snapshots of shares. A share snapshot is a
    point-in-time, read-only copy of the data that is contained in a share. You can create, manage, update, and delete
    share snapshots. After you create or manage a share snapshot, you can create a share from it. You can also revert a
    share to its most recent snapshot.
    You can update a share snapshot to rename it, change its description, or update its state to one of these supported
    states:
    * available
    * error
    * creating
    * deleting
    * error_deleting
    * manage_starting
    * manage_error
    * unmanage_starting
    * unmanage_error
    * restoring
    As administrator, you can also reset the state of a snapshot and force-delete a share snapshot in any state.
    """

    def __init__(self, manila):
        OpenstackManilaObject.__init__(self, manila.manager)

        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)

    @setup_client
    def list(self, details=False, **kwargs):
        """Lists all share snapshots.

        :param details: (Optional) if True get item with details
        :param name: (Optional) The name pattern that can be used to filter shares, share snapshots, share networks or
            share groups.
        :return: list of dict with snapshot info
        :raise OpenstackError:
        """
        path = "/snapshots"
        if details is True:
            path += "/detail"
        path += "?" + urlencode(kwargs)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack share snapshots list: %s" % truncate(res[0]))
        return res[0]["snapshots"]

    @setup_client
    def get(self, snapshot_id):
        """Shows details for a share snapshot.

        :param snapshot_id: The UUID of the snapshot.
        :return: dict with snapshot info
        :raise OpenstackError:
        """
        path = "/snapshots/%s" % snapshot_id
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack share snapshot: %s" % truncate(res[0]))
        return res[0]["snapshot"]

    @setup_client
    def create(self, share_id, **kvargs):
        """Creates a snapshot from a share.

        :param share_id: The UUID of the share from which to create a snapshot.
        :param force: (Optional) Indicates whether snapshot creation must be attempted when a share's status is not
            available. Set to true to force snapshot creation when the share is busy performing other operations.
            Default is false.
        :param name: (Optional) The snapshot name.
        :param display_name: (Optional) The snapshot name. The Shared File Systems API supports the use of both name
            and display_name attributes, which are inherited attributes from the Block Storage API.
        :param description: (Optional) The snapshot description.
        :param display_description: (Optional) The snapshot description. The shared file systems API supports the use
            of both name and display_name attributes, which are inherited attributes from the block storage API.
        :return: dict with snapshot info
        :raise OpenstackError:
        """
        data = {"share_id": share_id}

        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        path = "/snapshots"
        data = jsonDumps({"snapshot": data})
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack create share snapshot: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def update(self, snapshot_id, **kvargs):
        """Updates a share snapshot. You can update these attributes:
        * display_name, which also changes the name of the share snapshot.
        * display_description, which also changes the description of the share snapshot.
        If you try to update other attributes, they retain their previous values.

        :param snapshot_id: id of the snapshot
        :param display_name: (Optional) The snapshot name. The Shared File Systems API supports he use of both name
            and display_name attributes, which are inherited attributes from the Block Storage API.
        :param display_description: (Optional) The snapshot description. The shared file systems API supports the use
            of both name and display_name attributes, which are inherited attributes from the block storage API.
        :return: dict with snapshot info
        :raise OpenstackError:
        """
        data = {}
        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        path = "/snapshots/%s" % snapshot_id
        data = jsonDumps({"snapshot": data})
        res = self.client.call(path, "PUT", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack update share snapshot %s: %s" % (snapshot_id, truncate(res[0])))
        return res[0]

    @setup_client
    def delete(self, snapshot_id):
        """Deletes a share.

        :param snapshot_id: id of the snapshot
        :return:
        :raise OpenstackError:
        """
        path = "/snapshots/%s" % snapshot_id
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack delete share snapshot %s: %s" % (snapshot_id, truncate(res[0])))
        return res[0]

    @setup_client
    def manage(self, snapshot_id, provider_location, **kvargs):
        """Configures Shared File Systems to manage a share snapshot.

        :param snapshot_id: id of the snapshot
        :param provider_location: Provider location of the snapshot on the backend.
        :param name: (Optional) The snapshot name.
        :param display_name: (Optional) The snapshot name. The Shared File Systems API supports the use of both name
            and display_name attributes, which are inherited attributes from the Block Storage API.
        :param description: (Optional) The snapshot description.
        :param display_description: (Optional) The snapshot description. The shared file systems API supports the use
            of both name and display_name attributes, which are inherited attributes from the block storage API.
        :param driver_options: (Optional) A set of one or more key and value pairs, as a dictionary of strings, that
            describe driver options.
        :return: dict with snapshot info
        :raise OpenstackError:
        """
        data = {"provider_location": provider_location}
        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        path = "/snapshots/%s" % snapshot_id
        data = jsonDumps({"snapshot": data})
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack manage share snapshot %s: %s" % (snapshot_id, truncate(res[0])))
        return res[0]

    @setup_client
    def unmanage(self, snapshot_id, provider_location, **kvargs):
        """Configures Shared File Systems to stop managing a share snapshot.

        :param snapshot_id: id of the snapshot
        :return:
        :raise OpenstackError:
        """
        path = "/snapshots/%s/action" % snapshot_id
        data = jsonDumps({"unmanage": None})
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack unmanage share snapshot %s: %s" % (snapshot_id, truncate(res[0])))
        return res[0]

    @setup_client
    def reset_status(self, snapshot_id, status):
        """Administrator only. Explicitly updates the state of a share snapshot.

        :param snapshot_id: id of the snapshot
        :param status: The snapshot status, which can be available, error, creating, deleting,
            manage_starting, manage_error, unmanage_starting, unmanage_error or error_deleting.
        :return:
        :raise OpenstackError:
        """
        path = "/snapshots/%s/action" % snapshot_id
        data = jsonDumps({"reset_status": {"status": status}})
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack reset share snapshot %s status to %s" % (snapshot_id, status))
        return res[0]

    @setup_client
    def force_delete(self, snapshot_id):
        """Administrator only. Force-deletes a share snapshot in any state.

        :param snapshot_id: id of the snapshot
        :return:
        :raise OpenstackError:
        """
        path = "/snapshots/%s/action" % snapshot_id
        data = jsonDumps({"force_delete": None})
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack force delete share snapshot %s: %s" % (snapshot_id, truncate(res[0])))
        return res[0]


class OpenstackManilaShareType(OpenstackManilaObject):
    """A share type enables you to filter or choose back ends before you create a share. A share type behaves in the
    same way as a Block Storage volume type behaves.
    You set a share type to private or public and manage the access to the private share types.
    When you issue a create a share type request, you can submit a request body with either a share_type or
    volume_type object.
    No matter which object type you include in the request, the API creates both a volume_type object and a share_type
    object. Both objects have the same ID. When you issue a list share types request, the response shows both
    share_type and volume_type objects.
    """

    def __init__(self, manila):
        OpenstackManilaObject.__init__(self, manila.manager)

        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)

    @setup_client
    def list(self, default=False, desc=None):
        """Lists all types.

        :param default: (Optional) if True list default share types
        :param desc: (Optional) type description
        :return:
        :raise OpenstackError:
        """
        path = "/types"
        if default is True:
            path += "/default"
        if desc is not None:
            path += "?description=%s" % desc
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)

        resp = res[0]["share_types"]
        if desc is not None:
            resp = []
            for item in res[0]["share_types"]:
                if item["description"] == desc:
                    resp.append(item)

        self.logger.debug("Openstack manila share types list: %s" % truncate(resp))
        return resp

    @setup_client
    def get(self, share_type_id):
        """Shows details for a specified share type.

        :param share_type_id: id of the share type
        :return:

            {
                "required_extra_specs": {"driver_handles_share_servers": "True"},
                "share_type_access:is_public": true,
                "extra_specs": {"driver_handles_share_servers": "True"},
                "id": "420e6a31-3f3d-4ed7-9d11-59450372182a",
                "name": "default",
                "description": "share type description"
            }

        :raise OpenstackError:
        """
        path = "/types/%s" % share_type_id
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack manila share type: %s" % truncate(res[0]))
        return res[0]["share_type"]

    @setup_client
    def get_extra_spec(self, share_type_id):
        """Lists the extra specifications for a share type.

        :param share_type_id: id of the share type
        :return:

            {
                "replication_type": "readable",
                "driver_handles_share_servers": "True",
                "create_share_from_snapshot_support": "True",
                "revert_to_snapshot_support": "False",
                "mount_snapshot_support": "False",
                "snapshot_support": "True"
            }

        :raise OpenstackError:
        """
        path = "/types/%s/extra_specs" % share_type_id
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack manila share type extra_specs: %s" % truncate(res[0]))
        return res[0]["extra_specs"]

    @setup_client
    def get_access(self, share_type_id):
        """Shows access details for a share type. You can view access details for private share types only.

        :param share_type_id: id of the share type

        :return:

            [
                {
                    "share_type_id": "1732f284-401d-41d9-a494-425451e8b4b8",
                    "project_id": "818a3f48dcd644909b3fa2e45a399a27"
                },
                {
                    "share_type_id": "1732f284-401d-41d9-a494-425451e8b4b8",
                    "project_id": "e1284adea3ee4d2482af5ed214f3ad90"
                }
            ]

        :raise OpenstackError:
        """
        path = "/types/%s/share_type_access" % share_type_id
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack manila share type access: %s" % truncate(res[0]))
        return res[0]["share_type_access"]

    @setup_client
    def create(self, name, is_public=True, **kvargs):
        """Creates a share type.

        :param name: The share type name. Minor versions support only the share_type parameter where the share type
            name is expected.
        :param description: (Optional) The description of the share type.
        :param is_public: (Optional) Indicates whether a share type is publicly accessible. Default is true, or
            publicly accessible.
        :param replication_type: (Optional) The share replication type.
        :param driver_handles_share_servers: (Optional) An extra specification that defines the driver mode for share
            server, or storage, life cycle management. The Shared File Systems service creates a share server for the
            export of shares. This value is true when the share driver manages, or handles, the share server life
            cycle. This value is false when an administrator rather than a share driver manages the storage life cycle.
        :param mount_snapshot_support: (Optional) Boolean extra spec used for filtering of back ends by their
            capability to mount share snapshots.
        :param revert_to_snapshot_support: (Optional) Boolean extra spec used for filtering of back ends by their
            capability to revert shares to snapshots.
        :param create_share_from_snapshot_support: (Optional) Boolean extra spec used for filtering of back ends by
            their capability to create shares from snapshots.
        :param snapshot_support: (Optional) An extra specification that filters back ends by whether they do or do not
            support share snapshots.
        :return:

            {
                "required_extra_specs": {
                    "driver_handles_share_servers": true
                },
                "share_type_access:is_public": true,
                "extra_specs": {
                    "replication_type": "readable",
                    "driver_handles_share_servers": "True",
                    "mount_snapshot_support": "False",
                    "revert_to_snapshot_support": "False",
                    "create_share_from_snapshot_support": "True",
                    "snapshot_support": "True"
                },
                "id": "7fa1342b-de9d-4d89-bdc8-af67795c0e52",
                "name": "testing",
                "description": "share type description"
            }

        :raise OpenstackError:
        """
        data = {
            "name": name,
            "share_type_access:is_public": is_public,
            "description": kvargs.get("description", name),
            "extra_specs": {},
        }

        for k, v in kvargs.items():
            if v is not None:
                data["extra_specs"][k] = v

        path = "/types"
        data = jsonDumps({"share_type": data})
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debugu("Openstack create share type: %s" % truncate(res[0]))
        return res[0]["share_type"]

    @setup_client
    def set_extra_spec(self, share_type_id, extra_specs):
        """Sets an extra specification for the share type.
        Each driver implementation determines which extra specification keys it uses. For details, see Capabilities
        (https://docs.openstack.org/manila/latest/admin/capabilities_and_extra_specs.html) and Extra-Specs and
        documentation for your driver.

        Administrators can create share types with these extra specifications that are used to filter back ends:
        - driver_handles_share_servers. Required. Defines the driver mode for share server, or storage, life cycle
          management. The Shared File Systems service creates a share server for the export of shares.
          Set to True when the share driver manages or handles the share server life cycle.
          Set to False when an administrator rather than a share driver manages the share server life cycle.
        - snapshot_support. Filters back ends by whether they do or do not support share snapshots.
          Set to True to find back ends that support share snapshots.
          Set to False to find back ends that do not support share snapshots.
        Administrators can also set additional extra specifications for a share type for the following purposes:
        - Filter back ends. Specify these unqualified extra specifications in this format: extra_spec=value. For
          example, netapp_raid_type=raid4.
        - Set data for the driver. Except for the special capabilities prefix, you specify these qualified extra
          specifications with its prefix followed by a colon: vendor:extra_spec=value. For example,
          netapp:thin_provisioned=true.
        The scheduler uses the special capabilities prefix for filtering. The scheduler can only create a share on a
        back end that reports capabilities that match the un-scoped extra-spec keys for the share type. For details,
        see Capabilities and Extra-Specs.
        Each driver implementation determines which extra specification keys it uses. For details, see the
        documentation for the driver.

        :param share_type_id: id of the share type
        :param extra_specs: The extra specifications for the share type.

                {
                    "my_key": "my_value"
                }

        :return:

            {
                "my_key": "my_value"
            }

        :raise OpenstackError:
        """
        path = "/types/%s/extra_specs" % share_type_id
        data = jsonDumps({"extra_specs": extra_specs})
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debugu("Openstack create share %s type extra spec: %s" % (share_type_id, truncate(res[0])))
        return res[0]["share_type"]

    @setup_client
    def unset_extra_spec(self, share_type_id, extra_spec_key):
        """Unsets an extra specification for the share type.

        :param share_type_id: id of the share type
        :param extra_spec_key: The extra specification key

                {
                    "my_key": "my_value"
                }

        :return:

            {
                "my_key": "my_value"
            }

        :raise OpenstackError:
        """
        path = "/types/%s/extra_specs/%s" % (share_type_id, extra_spec_key)
        data = ""
        res = self.client.call(path, "DELETE", data=data, token=self.manager.identity.token)
        self.logger.debugu("Openstack delete share %s type extra spec: %s" % (share_type_id, truncate(res[0])))
        return res[0]["share_type"]

    @setup_client
    def action(self, share_type_id, project, add=True, delete=False):
        """Adds/Removes share type access for a project. You can add or remove access to private share types only.

        :param share_type_id: id of the share type
        :param project: The UUID of the project to which access to the share type is granted

                {
                    "my_key": "my_value"
                }

        :return:

            {
                "my_key": "my_value"
            }

        :raise OpenstackError:
        """
        path = "/types/%s/action" % share_type_id
        if add is True:
            action = "add"
        elif delete is True:
            action = "remove"
        else:
            raise OpenstackError("Action is not supported")
        data = jsonDumps({"%sProjectAccess" % action: {"project": project}})
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debugu(
            "Openstack %s share type %s access to project %s: %s" % (action, share_type_id, project, truncate(res[0]))
        )
        return res[0]

    @setup_client
    def delete(self, share_type_id):
        """Deletes a share type.

        :param share_type_id: id of the share type
        :return:
        :raise OpenstackError:
        """
        path = "/types/%s" % share_type_id
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack delete share type %s: %s" % (share_type_id, truncate(res[0])))
        return res[0]


class OpenstackManilaStoragePool(OpenstackManilaObject):
    """An administrator can list all back-end storage pools that are known to the scheduler service."""

    def __init__(self, manila):
        OpenstackManilaObject.__init__(self, manila.manager)

        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)

    @setup_client
    def list(self, details=False, **kwargs):
        """Lists all shares.

        :param details: (Optional) if True get item with details
        :param pool: (Optional) The pool name for the back end.
        :param host: (Optional) The host name for the back end.
        :param backend: (Optional) The name of the back end.
        :param capabilities: (Optional) The capabilities for the storage back end.
        :param share_type: (Optional) The share type name or UUID. Allows filtering back end pools based on the
            extra-specs in the share type.
        :return:

            [
                {
                    "host": "LONDON",
                    "capabilities": {
                        "qos": false,
                        "driver_version": "1.0",
                        "snapshot_support": true,
                        "timestamp": "2016-07-05T22:40:32.632330",
                        "share_backend_name": "GENERIC1",
                        "total_capacity_gb": "unknown",
                        "driver_handles_share_servers": true,
                        "server_pools_mapping": {},
                        "share_group_stats": {
                            "consistent_snapshot_support": null
                        },
                        "pools": null,
                        "vendor_name": "Open Source",
                        "reserved_percentage": 0,
                        "free_capacity_gb": "unknown",
                        "storage_protocol": "NFS_CIFS",
                        "replication_domain": null
                    },
                    "name": "openstack3@generic1#GENERIC1",
                    "pool": "GENERIC1",
                    "backend": "generic1"
                }
            ]

            capabilities are visible only with details=True

        :raise OpenstackError:
        """
        path = "/scheduler-stats/pools"
        if details is True:
            path += "/detail"
        path += "?" + urlencode(kwargs)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack manila storage pools list: %s" % truncate(res[0]))
        return res[0]["pools"]


class OpenstackManilaQuotaSet(OpenstackManilaObject):
    """Provides quotas management support."""

    def __init__(self, manila):
        OpenstackManilaObject.__init__(self, manila.manager)

        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)

    @setup_client
    def get_default(self, tenant_id, **kwargs):
        """Get default quota sets.

        :param tenant_id: (Optional) The UUID for the tenant for which you want to show, update,
                or delete quotas.

        :return:

            {
                "gigabytes": 1000,
                "shares": 50,
                "snapshot_gigabytes": 1000,
                "snapshots": 50,
                "id": "16e1ab15c35a457e9c2b2aa189f544e1",
                "share_networks": 10,
                "share_groups": 10,
                "share_group_snapshots": 10
            }

        :raise OpenstackError:
        """
        path = "/quota-sets/%s/defaults" % tenant_id
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack get manile default quota sets: %s" % truncate(res[0]))
        return res[0]["quota_set"]

    @setup_client
    def get(self, tenant_id, details=False, **kwargs):
        """Shows quotas for a tenant. If you specify the optional user_id query parameter, you get the quotas for this
            user in the tenant. If you omit this parameter, you get the quotas for the project.

        :param details: (Optional) if True get item with details
        :param tenant_id: The UUID for the tenant for which you want to show, update,
                or delete quotas.
        :param user_id: (Optional) The UUID of the user. If you specify this query parameter, you
                update the quotas for this user in the tenant. If you omit this parameter, you update the quotas for
                the project.
        :param share_type: The name or UUID of the share type. If you specify this parameter in
                the URI, you show, update, or delete quotas for this share type.

        :return:

            {
                "id": "16e1ab15c35a457e9c2b2aa189f544e1",
                "gigabytes": {"in_use": 0, "limit": 1000, "reserved": 0},
                "shares": {"in_use": 0, "limit": 50, "reserved": 0},
                "snapshot_gigabytes": {"in_use": 0, "limit": 1000, "reserved": 0},
                "snapshots": {"in_use": 0, "limit": 50, "reserved": 0},
                "share_networks": {"in_use": 0, "limit": 10, "reserved": 0},
                "share_groups": {"in_use": 0, "limit": 10, "reserved": 0},
                "share_group_snapshots": {"in_use": 0, "limit": 10, "reserved": 0}
            }

        :raise OpenstackError:
        """
        path = "/quota-sets/%s" % tenant_id
        if details is True:
            path += "/detail"
        path += "?" + urlencode(kwargs)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack get manila quota sets: %s" % truncate(res[0]))
        return res[0]["quota_set"]

    @setup_client
    def update(self, tenant_id, **kvargs):
        """Updates quotas for a tenant. If you specify the optional user_id query parameter, you update the quotas for
        this user in the tenant. If you omit this parameter, you update the quotas for the project.



        :param tenant_id: The UUID for the tenant for which you want to show, update,
                or delete quotas.
        :param user_id: (Optional) The UUID of the user. If you specify this query parameter, you
                update the quotas for this user in the tenant. If you omit this parameter, you update the quotas for
                the project.
        :param force: (Optional) Indicates whether to permit or deny the force- update of a quota
                that is already used and the requested value exceeds the configured quota. Set to True to permit the
                force-update of the quota. Set to False to deny the force- update of the quota.
        :param gigabytes: (Optional) The number of gigabytes for the tenant.
        :param snapshots: (Optional) The number of snapshots for the tenant.
        :param snapshot_gigabytes: (Optional) The number of gigabytes for the snapshots for the
                tenant.
        :param shares: (Optional) The number of shares for the tenant.
        :param share_networks: (Optional) The number of share networks for the tenant.
        :param share_groups: (Optional) The number of share groups allowed for each tenant or user.
        :param share_group_snapshots: (Optional) The number of share group snapshots allowed for
                each tenant or user.
        :param share_type: (Optional) The name or UUID of the share type. If you specify this
                parameter in the URI, you show, update, or delete quotas for this share type.

        :return:

        :raise OpenstackError:
        """
        data = {}
        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        path = "/quota-sets/%s" % tenant_id
        data = jsonDumps({"quota_set": data})
        res = self.client.call(path, "PUT", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack update manila quota set: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def delete(self, tenant_id, **kvargs):
        """Delete a quota set.



        :param tenant_id: The UUID for the tenant for which you want to show, update,
                or delete quotas.
        :param user_id: (Optional) The UUID of the user. If you specify this query parameter, you
                update the quotas for this user in the tenant. If you omit this parameter, you update the quotas for
                the project.
        :param share_type: (Optional) The name or UUID of the share type. If you specify this
                parameter in the URI, you show, update, or delete quotas for this share type.

        :return:

        :raise OpenstackError:
        """
        data = {}
        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        path = "/quota-sets/%s" % tenant_id
        data = jsonDumps({"quota_set": data})
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack delete manila quota set: %s" % (truncate(res[0])))
        return res[0]


class OpenstackManilaShareNetwork(OpenstackManilaObject):
    """A share network resource stores network information to create and manage share servers. Shares created with
    share networks are exported on these networks with the help of share servers.
    You can create, update, view, and delete a share network.
    When you create a share network, you may optionally specify an associated neutron network and subnetwork.
    For more information about supported plug-ins for share networks, see Manila Network Plugins.
    A share network resource has these attributes:
    * The IP block in Classless Inter-Domain Routing (CIDR) notation from which to allocate the network.
    * The IP version of the network.
    * The network type, which is vlan, vxlan, gre, or flat.
    * If the network uses segmentation, a segmentation identifier. For example, VLAN, VXLAN, and GRE networks use
      segmentation.
    A share network resource can also have a user defined name and description.
    """

    def __init__(self, manila):
        OpenstackManilaObject.__init__(self, manila.manager)

        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)

    @setup_client
    def list(self, details=False, **kwargs):
        """Lists all share networks.

        :param details: (Optional) if True get item with details
        :param name~: (Optional) The name pattern that can be used to filter shares, share snapshots, share networks
            or share groups.
        :param description~: (Optional) The description pattern that can be used to filter shares, share snapshots,
            share networks or share groups.
        :param neutron_net_id: neutron network id
        :param neutron_subnet_id: neutron subnet id
        :return: list of dict with share network info
        :raise OpenstackError:
        """
        path = "/share-networks"
        if details is True:
            path += "/detail"
        kwargs["all_tenants"] = True
        path += "?" + urlencode(kwargs)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack share networks list: %s" % truncate(res[0]))
        return res[0]["share_networks"]

    @setup_client
    def get(self, network_id):
        """Shows details for a share network.

        :param network_id: The UUID of the share-network.
        :return: dict with share network info
        :raise OpenstackError:
        """
        path = "/share-networks/%s" % network_id
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack share network: %s" % truncate(res[0]))
        return res[0]["share_network"]

    @setup_client
    def create(self, **kvargs):
        """Create share network

        :param neutron_net_id: (Optional) The UUID of a neutron network when setting up or updating a share network
            subnet with neutron. Specify both a neutron network and a neutron subnet that belongs to that neutron
            network.
        :param neutron_subnet_id: (Optional) The UUID of the neutron subnet when setting up or updating a share
            network subnet with neutron. Specify both a neutron network and a neutron subnet that belongs to that
            neutron network.
        :param name: (Optional) The user defined name of the resource. The value of this field is limited to 255
            characters.
        :param description: (Optional) The user defined description of the resource. The value of this field is
            limited to 255 characters.
        :param availability_zone: (Optional) The UUID or name of an availability zone for the share network subnet.
        :return: dict with share network info
        :raise OpenstackError:
        """
        data = {}

        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        path = "/share-networks"
        data = jsonDumps({"share_network": data})
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack create share network: %s" % truncate(res[0]))
        return res[0]["share_network"]

    @setup_client
    def update(self, share_network_id, **kvargs):
        """Updates a share network. Note that if the share network is used by any share server, you can update only
        the name and description attributes.

        :param share_network_id: The UUID of the share network.
        :param name: (Optional) The user defined name of the resource. The value of this field is limited to 255
            characters.
        :param description: (Optional) The user defined description of the resource. The value of this field is
            limited to 255 characters.
        :param neutron_net_id: (Optional) The UUID of a neutron network when setting up or updating a share network
            subnet with neutron. Specify both a neutron network and a neutron subnet that belongs to that neutron
            network.
        :param neutron_subnet_id: (Optional) The UUID of the neutron subnet when setting up or updating a share network
            subnet with neutron. Specify both a neutron network and a neutron subnet that belongs to that neutron
            network.
        :return: dict with share network info
        :raise OpenstackError:
        """
        data = {}
        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        path = "/share-networks/%s" % share_network_id
        data = jsonDumps({"share_network": data})
        res = self.client.call(path, "PUT", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack update share network %s: %s" % (share_network_id, truncate(res[0])))
        return res[0]["share_network"]

    @setup_client
    def delete(self, share_network_id):
        """Deletes a share network

        :param share_network_id: The UUID of the share network.
        :return:
        :raise OpenstackError:
        """
        path = "/share-networks/%s" % share_network_id
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack delete share network %s: %s" % (share_network_id, truncate(res[0])))
        return res[0]

    @setup_client
    def add_security_service(self, share_network_id, security_service_id):
        """Add security service to share network

        :param share_network_id: The UUID of the share network.
        :param security_service_id: The security service ID.
        :return: dict with share network info
        :raise OpenstackError:
        """
        data = {"add_security_service": {"security_service_id": security_service_id}}
        path = "/share-networks/%s/action" % share_network_id
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Add security service to share network %s" % share_network_id)
        return res[0]

    @setup_client
    def del_security_service(self, share_network_id, security_service_id):
        """Remove security service from share network

        :param share_network_id: The UUID of the share network.
        :param security_service_id: The security service ID.
        :return: dict with share network info
        :raise OpenstackError:
        """
        data = {"remove_security_service": {"security_service_id": security_service_id}}
        path = "/share-networks/%s/action" % share_network_id
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Remove security service to share network %s" % share_network_id)
        return res[0]


class OpenstackManilaSecurityService(OpenstackManilaObject):
    """You can create, update, view, and delete a security service. A security service stores configuration information
    for clients for authentication and authorization (AuthN/AuthZ). For example, a share server will be the client for
    an existing service such as LDAP, Kerberos, or Microsoft Active Directory.
    You can associate a share with from one to three security service types:
    * ldap. LDAP.
    * kerberos. Kerberos.
    * active_directory. Microsoft Active Directory.
    You can configure a security service with these options:
    * A DNS IP address.
    * An IP address or host name.
    * A domain.
    * A user or group name.
    * The password for the user, if you specify a user name.
    """

    def __init__(self, manila):
        OpenstackManilaObject.__init__(self, manila.manager)

        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)

    @setup_client
    def list(self, details=False, **kwargs):
        """Lists all security services.



        :param details: (Optional) if True get item with details

        :return:

            [
                {
                    "status": "new",
                    "type": "kerberos",
                    "id": "3c829734-0679-4c17-9637-801da48c0d5f",
                    "name": "SecServ1"
                },
                {
                    "status": "new",
                    "type": "ldap",
                    "id": "5a1d3a12-34a7-4087-8983-50e9ed03509a",
                    "name": "SecServ2"
                }
            ]

            with details = True

            [
                {
                    "status": "new",
                    "domain": null,
                    "project_id": "16e1ab15c35a457e9c2b2aa189f544e1",
                    "name": "SecServ1",
                    "created_at": "2015-09-07T12:19:10.000000",
                    "description": "Creating my first Security Service",
                    "updated_at": null,
                    "server": null,
                    "dns_ip": "10.0.0.0/24",
                    "user": "demo",
                    "password": "supersecret",
                    "type": "kerberos",
                    "id": "3c829734-0679-4c17-9637-801da48c0d5f",
                    "share_networks": []
                },..
            ]

        :raise OpenstackError:
        """
        path = "/security-services"
        if details is True:
            path += "/detail"
        path += "?" + urlencode(kwargs)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack share security_services list: %s" % truncate(res[0]))
        return res[0]["security_services"]

    @setup_client
    def get(self, security_service_id):
        """Shows details for a security service.



        :param security_service_id: The UUID of the security_service.

        :return:

            {
                "status": "new",
                "domain": null,
                "project_id": "16e1ab15c35a457e9c2b2aa189f544e1",
                "name": "SecServ1",
                "created_at": "2015-09-07T12:19:10.000000",
                "updated_at": null,
                "server": null,
                "dns_ip": "10.0.0.0/24",
                "user": "demo",
                "password": "supersecret",
                "type": "kerberos",
                "id": "3c829734-0679-4c17-9637-801da48c0d5f",
                "description": "Creating my first Security Service"
            }

        :raise OpenstackError:
        """
        path = "/security-services/%s" % security_service_id
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack share security_service: %s" % truncate(res[0]))
        return res[0]["security_service"]

    @setup_client
    def create(self, type, name, **kvargs):
        """Creates a security service.



        :param type: The security service type. A valid value is ldap, kerberos, or
                active_directory.
        :param name: The security service name.
        :param description: (Optional) The security service description. If you specify this value,
                the description is updated.
        :param dns_ip: (Optional) The DNS IP address that is used inside the tenant network.
        :param user: (Optional) The security service user or group name that is used by the tenant.
        :param password: (Optional) The user password, if you specify a user
        :param domain: (Optional) The security service domain.
        :param server: (Optional) The security service host name or IP address.

        :return:

            {
                "status": "new",
                "domain": null,
                "project_id": "16e1ab15c35a457e9c2b2aa189f544e1",
                "name": "SecServ1",
                "created_at": "2015-09-07T12:19:10.695211",
                "updated_at": null,
                "server": null,
                "dns_ip": "10.0.0.0/24",
                "user": "demo",
                "password": "supersecret",
                "type": "kerberos",
                "id": "3c829734-0679-4c17-9637-801da48c0d5f",
                "description": "Creating my first Security Service"
            }

        :raise OpenstackError:
        """
        data = {"type": type, "name": name}

        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        path = "/security-services"
        data = jsonDumps({"security_service": data})
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack create share security_service: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def update(self, security_service_id, **kvargs):
        """Updates a security service. If the security service is in active state, you can update only the name and
        description attributes. A security service in active state is attached to a share network with an associated
        share server.



        :param security_service_id: id of the security_service
        :param type: The security service type. A valid value is ldap, kerberos, or
                active_directory.
        :param name: The security service name.
        :param description: (Optional) The security service description. If you specify this value,
                the description is updated.
        :param dns_ip: (Optional) The DNS IP address that is used inside the tenant network.
        :param user: (Optional) The security service user or group name that is used by the tenant.
        :param password: (Optional) The user password, if you specify a user
        :param domain: (Optional) The security service domain.
        :param server: (Optional) The security service host name or IP address.

        :return:

            {
                "status": "new",
                "domain": null,
                "project_id": "16e1ab15c35a457e9c2b2aa189f544e1",
                "name": "SecServ1",
                "created_at": "2015-09-07T12:19:10.695211",
                "updated_at": null,
                "server": null,
                "dns_ip": "10.0.0.0/24",
                "user": "demo",
                "password": "supersecret",
                "type": "kerberos",
                "id": "3c829734-0679-4c17-9637-801da48c0d5f",
                "description": "Creating my first Security Service"
            }

        :raise OpenstackError:
        """
        data = {}
        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        path = "/security-services/%s" % security_service_id
        data = jsonDumps({"security_service": data})
        res = self.client.call(path, "PUT", data=data, token=self.manager.identity.token)
        self.logger.debug("Openstack update share security_service %s: %s" % (security_service_id, truncate(res[0])))
        return res[0]

    @setup_client
    def delete(self, security_service_id):
        """Deletes a security service.



        :param security_service_id: id of the security_service

        :return:
        :raise OpenstackError:
        """
        path = "/security-services/%s" % security_service_id
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack delete share security_service %s: %s" % (security_service_id, truncate(res[0])))
        return res[0]


class OpenstackManilaShareServer(OpenstackManilaObject):
    """A share server is created by multi-tenant back-end drivers where shares are hosted. For example, with the
    generic driver, shares are hosted on Compute VMs.
    Administrators can perform read and delete actions for share servers. An administrator can delete an active share
    server only if it contains no dependent shares. If an administrator deletes the share server, the Shared File
    Systems service creates a share server in response to a subsequent create share request.
    An administrator can use the policy.json file to grant permissions for share server actions to other roles.
    The status of a share server indicates its current state. After you successfully set up a share server, its status
    is active. If errors occur during set up such as when server data is not valid, its status is error.
    The possible share servers statuses are:
    * active - Share server was successfully set up.
    * error - The set up or deletion of the share server failed.
    * deleting - The share server has no dependent shares and is being deleted.
    * creating - The share server is being created on the back end with data from the database.
    """

    def __init__(self, manila):
        OpenstackManilaObject.__init__(self, manila.manager)

        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)

    @setup_client
    def list(self, **kwargs):
        """Lists all share servers.

        :return: list of dict with share server info
        :raise OpenstackError:
        """
        path = "/share-servers"
        path += "?" + urlencode(kwargs)
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack share servers list: %s" % truncate(res[0]))
        return res[0]["share_servers"]

    @setup_client
    def get(self, server_id):
        """Shows details for a share server.

        :param server_id: The UUID of the share-server.
        :return: dict with share server info
        :raise OpenstackError:
        """
        path = "/share-servers/%s" % server_id
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack share server: %s" % truncate(res[0]))
        return res[0]["share_server"]

    @setup_client
    def delete(self, share_server_id):
        """Deletes a share server

        :param share_server_id: The UUID of the share server.
        :return:
        :raise OpenstackError:
        """
        path = "/share-servers/%s" % share_server_id
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Openstack delete share server %s: %s" % (share_server_id, truncate(res[0])))
        return res[0]

    @setup_client
    def manage(self, **kvargs):
        """Manages a share server

        :param host: The host of the destination back end, in this format: host@backend. - host. The host name for
            the destination back end. - backend. The name of the destination back end.
        :param identifier:  The identifier of the share server in the back-end storage system.
        :param share_network: The share network ID.
        :param driver_options: (Optional) A set of one or more key and value pairs, as a dictionary of strings, that
            describe driver options. Details for driver options should be taken from appropriate share driver
            documentation.
        :param share_network_subnet_id: (Optional) The UUID of the share network subnet that the share server will
            pertain to. If not specified, the share network’s default subnet UUID will be used.
        :return: dict with share server info
        :raise OpenstackError:
        """
        data = {}

        for k, v in kvargs.items():
            if v is not None:
                data[k] = v

        data = {"share_server": data}
        path = "/share-servers/manage"
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Manage share server")
        return res[0]["share_server"]

    @setup_client
    def unmanage(self, share_server_id, force=False):
        """Unmanage a share server.
        An administrator can remove a share server from the Shared File System service’s management if there are no
        associated shares that the service is aware of. The share server will not be torn down in the back end.

        Preconditions: Share server status must be either error, manage_error, active or unmanage_error.

        :param share_server_id: The UUID of the share server.
        :param force: Indicates whether to permit or deny the force- update of a quota that is already used and the
            requested value exceeds the configured quota. Set to True to permit the force-update of the quota. Set to
            False to deny the force- update of the quota.
        :return: dict with share server info
        :raise OpenstackError:
        """
        data = {"unmanage": {"force": force}}
        path = "/share-servers/%s/action" % share_server_id
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Unmanage share server %s" % share_server_id)
        return res[0]

    @setup_client
    def reset_status(self, share_server_id, status="active"):
        """Resets a share server status
        Administrator only. Explicitly updates the state of a share server.

        :param share_server_id: The UUID of the share server.
        :param status: The share server status, which can be active, error, creating, deleting, manage_starting,
            manage_error, unmanage_starting, unmanage_error or error_deleting.
        :return: dict with share server info
        :raise OpenstackError:
        """
        data = {"reset_status": {"status": status}}
        path = "/share-servers/%s/action" % share_server_id
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Reset status of share server %s" % share_server_id)
        return res[0]
