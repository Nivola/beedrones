# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import jsonDumps
from urllib.parse import urlparse, parse_qs

import ujson as json
from six import ensure_text

from beecell.simple import truncate, get_value, dict_get
from six.moves.urllib.parse import urlencode
from base64 import b64encode
from beedrones.openstack.client import (
    OpenstackClient,
    OpenstackError,
    OpenstackObject,
    setup_client,
)


class OpenstackServerObject(OpenstackObject):
    def setup(self):
        self.uri = self.manager.endpoint("nova")
        # change version from 2 to 2.1
        self.uri = self.uri.replace("v2/", "v2.1/")
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)


class OpenstackServer(OpenstackServerObject):
    """

    The server status is returned in the response body. The possible server
    status values are:

    - ACTIVE. The server is active.
    - BUILDING. The server has not finished the original build process.
    - DELETED. The server is permanently deleted.
    - ERROR. The server is in error.
    - HARD_REBOOT. The server is hard rebooting. This is equivalent to pulling the power plug on a physical server,
        plugging it back in, and rebooting it.
    - MIGRATING. The server is being migrated to a new host.
    - PASSWORD. The password is being reset on the server.
    - PAUSED. In a paused state, the state of the server is stored in RAM. A paused server continues to run in frozen
        state.
    - REBOOT. The server is in a soft reboot state. A reboot command was passed to the operating system.
    - REBUILD. The server is currently being rebuilt from an image.
    - RESCUED. The server is in rescue mode. A rescue image is running with the original server image attached.
    - RESIZED. Server is performing the differential copy of data that changed during its initial copy. Server is down
        for this stage.
    - REVERT_RESIZE. The resize or migration of a server failed for some reason. The destination server is being
        cleaned up and the original source server is restarting.
    - SOFT_DELETED. The server is marked as deleted but the disk images are still available to restore.
    - STOPPED. The server is powered off and the disk image still persists.
    - SUSPENDED. The server is suspended, either by request or necessity. This status appears for only the
        XenServer/XCP, KVM, and ESXi hypervisors. Administrative users can suspend an instance if it is infrequently
        used or to perform system maintenance. When you suspend an instance, its VM state is stored on disk, all memory
        is written to disk, and the virtual machine is stopped. Suspending an instance is similar to placing a device in
        hibernation; memory and vCPUs become available to create other instances
    - UNKNOWN. The state of the server is unknown. Contact your cloud provider.
    - VERIFY_RESIZE. System is awaiting confirmation that the server is operational after a move or resize.
    """

    def __init__(self, manager):
        OpenstackServerObject.__init__(self, manager)

    @setup_client
    def list(
        self,
        detail=False,
        image=None,
        flavor=None,
        status=None,
        host=None,
        limit=None,
        marker=None,
        all_tenants=True,
        name=None,
        not_tags=None,
        not_tags_any=None,
        tags=None,
        tags_any=None,
        launched_at=None,
        updated_at=None,
        *args,
        **kvargs,
    ):
        """
        :param detail: if True show server details
        :param all_tenants: if True show server fro all tenant [default=True]
        :param image: Filters the response by an image, as a UUID.
        :param flavor: Filters the response by a flavor, as a UUID. A flavor is a combination of memory, disk size,
            and CPUs.
        :param status: Filters the response by a server status, as a string. For example, ACTIVE.
        :param host: Filters the response by a host name, as a string. This query parameter is typically available to
            only administrative users. If you are a non-administrative user, the API ignores this parameter.
        :param limit: Requests a page size of items. Returns a number of items up to a limit value. Use the limit
            parameter to make an initial limited request and use the ID of the last-seen item from the response as the
            marker parameter value in a subsequent limited request.
        :param marker: The ID of the last-seen item. Use the limit parameter to make an initial limited request and use
            the ID of the last-seen item from the response as the marker parameter value in a subsequent limited
            request.
        :param name: Filters the response by a server name, as a string. You can use regular expressions in the query.
            For example, the ?name=bob regular expression returns both bob and bobb. If you must match on only bob, you
            can use a regular expression that matches the syntax of the underlying database server that is implemented
            for Compute, such as MySQL or PostgreSQL.
        :param not_tags: (Optional) A list of tags to filter the server list by. Servers that don’t match all tags in
            this list will be returned. Boolean expression in this case is ‘NOT (t1 AND t2)’. Tags in query must be
            separated by comma.
        :param not_tags_any: (Optional) A list of tags to filter the server list by. Servers that don’t match any tags
            in this list will be returned. Boolean expression in this case is ‘NOT (t1 OR t2)’. Tags in query must be
            separated by comma.
        :param tags: (Optional) A list of tags to filter the server list by. Servers that match all tags in this list
            will be returned. Boolean expression in this case is ‘t1 AND t2’. Tags in query must be separated by comma.
        :param tags_any: (Optional) A list of tags to filter the server list by. Servers that match any tag in this
            list will be returned. Boolean expression in this case is ‘t1 OR t2’. Tags in query must be separated by
            comma.
        :param launched_at: Filter the server list result by a date and time stamp when the instance was launched. The
            date and time stamp format is ISO 8601: CCYY-MM-DDThh:mm:ss±hh:mm. For example, 2015-08-27T09:49:58-05:00
        :param updated_at: updated at time
        :return: dict with server info
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        query = {}
        path = "/servers"
        if detail is True:
            path = "/servers/detail"

        if image is not None:
            query["image"] = image
        if flavor is not None:
            query["flavor"] = flavor
        if status is not None:
            query["status"] = status
        if host is not None:
            query["host"] = host
        if name is not None:
            query["name"] = name
        if limit is not None:
            query["limit"] = limit
        if marker is not None:
            query["marker"] = marker
        if all_tenants is True:
            query["all_tenants"] = 1
        if not_tags is not None:
            query["not-tags"] = not_tags
        if not_tags_any is not None:
            query["not-tags-any"] = not_tags_any
        if tags is not None:
            query["tags"] = tags
        if tags_any is not None:
            query["tags-any"] = tags_any
        if launched_at is not None:
            query["launched_at"] = launched_at
        if updated_at is not None:
            query["updated_at"] = updated_at

        self.set_nova_microversion("2.60")

        def get_servers(orig_path):
            query.update(kvargs)
            new_path = "%s?%s" % (orig_path, urlencode(query))
            res = self.client.call(new_path, "GET", data="", token=self.manager.identity.token)
            res = res[0]
            url_param = urlparse(dict_get(res, "servers_links.0.href"))
            url_query = parse_qs(url_param.query)
            return res.get("servers", []), url_query.get("marker", None)

        servers = []
        markers = ""
        while markers is not None:
            other_servers, markers = get_servers(path)
            servers.extend(other_servers)
            # set marker for the next request
            if markers is not None:
                query["marker"] = markers[0]

        self.logger.debug("Get openstack servers: %s" % truncate(servers))
        return servers

    @setup_client
    def get(self, oid=None, name=None):
        """
        :param oid: server id
        :param name: Filters the response by a server name, as a string. You can use regular expressions in the query.
            For example, the ?name=bob regular expression returns both bob and bobb. If you must match on only bob, you
            can use a regular expression that matches the syntax of the underlying database server that is implemented
            for Compute, such as MySQL or PostgreSQL.
        :return: dict with server info
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = "/servers/%s" % oid
        elif name is not None:
            path = "/servers/detail?name=%s&all_tenants=1" % name
        else:
            raise OpenstackError("Specify at least project id or name")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack server: %s" % truncate(res[0]))
        if oid is not None:
            server = res[0]["server"]
        elif name is not None:
            server = res[0]["servers"][0]

        return server

    @staticmethod
    def user_data(
        gateway=None,
        hostname=None,
        domain=None,
        dns=None,
        pwd=None,
        sshkey=None,
        users=[],
        cmds=[],
        routes=[],
        noproxy=False,
    ):
        """Setup user data

        :param users: list of dict like {'name':.., 'pwd':[optional], 'sshkeys':[..], 'uid':[optional]}
        :param gateway: network gateway
        :param hostname: server hostname
        :param domain: server domain
        :param dns: server dns
        :param pwd: server root pwd
        :param sshkey: server root sshkey
        :param cmds: list of custom command to execute
        :param route: list of ip route
        :param noproxy: if True remove proxy setting from yum
        :return: entity instance
        """
        user_data = ["#cloud-config", "bootcmd:", "disable_root: false"]
        if gateway:
            user_data.append("  - [ ip, route, change, default, via, %s ]" % gateway)
        if routes:
            for route in routes:
                user_data.append("  - [ %s ]" % route)
        if hostname:
            user_data.append("hostname: %s" % hostname)
            if domain:
                fqdn = "%s.%s" % (hostname, domain)
                # hostname = hostname + ' ' + fqdn
                user_data.append("fqdn: %s" % fqdn)
                user_data.append("hostname: %s" % fqdn)
                user_data.append("manage_etc_hosts: true")
                user_data.append("manage-resolv-conf: true")
            # user_data.append('echo `hostname -I` %s >> /etc/hosts' % hostname)
        if dns and domain:
            user_data.append("resolv_conf:")
            user_data.append("  nameservers: %s" % dns)
            user_data.append("  searchdomains:")
            user_data.append("    - %s" % domain)
            user_data.append("  domain: %s" % domain)
        if cmds:
            user_data.append("runcmd:")
            for cmd in cmds:
                user_data.append("  - %s" % cmd)
        if users:
            user_data.append("users:")
            user_data.append("  - default")
            for user in users:
                user_data.append("  - name: %s" % user["name"])
                user_sshkeys = user.get("sshkeys", None)
                if user_sshkeys is not None:
                    user_data.append("    ssh-authorized-keys:")
                    for sshkey in user_sshkeys:
                        user_data.append("      - %s" % sshkey)
                pwd = user.get("pwd", None)
                if pwd is not None:
                    user_data.append("    lock_passwd: false")
                    user_data.append("    passwd: %s" % pwd)
                uid = user.get("uid", None)
                if uid is not None:
                    user_data.append("    uid: %s" % uid)
        if pwd:
            user_data.append("ssh_pwauth: yes")
            # user_data.append('password: %s' % pwd)
            user_data.append("chpasswd:")
            user_data.append("  list: |")
            user_data.append("    root:%s" % pwd)
            user_data.append("  expire: False")
        if sshkey:
            user_data.append("ssh_authorized_keys:")
            user_data.append("  - %s" % sshkey)
        if noproxy is True:
            user_data.append("runcmd:")
            user_data.append(
                "  - mv /etc/yum.conf /etc/yum.conf.bck && " "sed '/^proxy/d' /etc/yum.conf.bck > /etc/yum.conf"
            )
            user_data.append(
                "  - mv /etc/dnf/dnf.conf /etc/dnf/dnf.conf.bck && "
                "sed '/^proxy/d' /etc/dnf/dnf.conf.bck > /etc/dnf/dnf.conf"
            )
            user_data.append(
                "  - mv /etc/apt/apt.conf /etc/apt/apt.conf.bck && "
                "sed '/^Acquire::http/d' /etc/apt/apt.conf.bck > /etc/apt/apt.conf"
            )

        return ensure_text(b64encode(("\n".join(user_data)).encode("utf-8")))

    @setup_client
    def create(
        self,
        name,
        flavor,
        accessipv4=None,
        accessipv6=None,
        networks=None,
        boot_volume_id=None,
        adminpass=None,
        description="",
        metadata=None,
        image=None,
        security_groups=None,
        personality=None,
        user_data=None,
        availability_zone=None,
        config_drive=False,
        tags=None,
    ):
        """Create server

        :param name: The server name.
        :param description: [TODO] A free form description of the server. Limited to 255 characters in length.
        :param flavor: The flavor reference, as a UUID or full URL, for the flavor for your server instance.
        :param image: The UUID of the image to use for your server instance. This is not required in case of boot from
            volume. In all other cases it is required and must be a valid UUID otherwise API will return 400. [optional]
        :param accessipv4: [TODO] IPv4 address that should be used to access this server. [optional]
        :param accessipv6: [TODO] IPv6 address that should be used to access this server. [optional]
        :param networks: A networks object. Required parameter when there are multiple networks defined for the tenant.
            When you do not specify the networks parameter, the server attaches to the only network created for the
            current tenant. Optionally, you can create one or more NICs on the server. To provision the server
            instance with a NIC for a network, specify the UUID of the network in the uuid attribute in a networks
            object. To provision the server instance with a NIC for an already existing port, specify the port-id in
            the port attribute in a networks object. Starting in microversion 2.32, it's possible to optionally assign
            an arbitrary tag to a virtual network interface, specify the tag attribute in the network object. An
            interface's tag is exposed to the guest in the metadata API and the config drive and is associated to
            hardware metadata for that network interface, such as bus (ex: PCI), bus address (ex: 0000:00:02.0), and
            MAC address. - networks.fixed_ip [optional] : A fixed IPv4 address   for the NIC. Valid with a neutron or
            nova-networks network. Ex: [{'uuid':.., 'fixed_ip':.., 'tag':..}],
        :param boot_volume_id: uuid of the root volume used to boot server.
        :param adminpass: [TODO] The administrative password of the server. [optional]
        :param metadata: Metadata key and value pairs. The maximum size of the metadata key and value is 255 bytes each.
            [optional] Ex. {'My Server Name':'Apache1'}
        :param security_groups: One or more security groups. Specify the name of the security group in the name
            attribute. If you omit this attribute, the API creates the server in the default security group. [optional]
            Ex. [{'name':''default}]
        :param config_drive: Indicates whether a config drive enables metadata injection. The config_drive setting
            provides information about a drive that the instance can mount at boot time. The instance reads files from
            the drive to get information that is normally available through the metadata service. This metadata is
            different from the user data. Not all cloud providers enable the config_drive. [optional]
        :param personality: [TODO] The file path and contents, text only, to inject into the server at launch. The
            maximum size of the file path data is 255 bytes. The maximum limit is the number of allowed bytes in the
            decoded, rather than encoded, data. [optional]
            Ex. [{'path':'/etc/banner.txt', 'contents':'ICAgICAgDQoiQSBjb..'}]
        :param user_data: [TODO] Configuration information or scripts to use upon launch. Must be Base64 encoded.
            [optional] Ex. "IyEvYmluL2Jhc2gKL2Jpbi9zdQpl..."
        :param availability_zone: The availability zone from which to launch the server. When you provision resources,
            you specify from which availability zone you want your instance to be built. Typically, you use availability
            zones to arrange OpenStack compute hosts into logical groups. An availability zone provides a form of
            physical isolation and redundancy from other availability zones. For instance, if some racks in your data
            center are on a separate power source, you can put servers in those racks in their own availability zone.
            Availability zones can also help separate different classes of hardware. By segregating resources into
            availability zones, you can ensure that your application resources are spread across disparate machines to
            achieve high availability in the event of hardware or other failure. [optional]
        :param tags: A list of tags. Tags have the following restrictions:
            Tag is a Unicode bytestring no longer than 60 characters.
            Tag is a non-empty string.
            ‘/’ is not allowed to be in a tag name
            Comma is not allowed to be in a tag name in order to simplify requests that specify lists of tags
            All other characters are allowed to be in a tag name
            Each server can have up to 50 tags. [optional]
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "name": name,
            # 'description': description,
            "flavorRef": flavor,
            "security_groups": [],
            "networks": [],
            "config_drive": config_drive,
        }

        if adminpass is not None:
            data["adminPass"] = adminpass

        if tags is not None:
            data["tags"] = tags

        if accessipv4 is not None:
            data["accessIPv4"] = accessipv4

        if accessipv6 is not None:
            data["accessIPv6"] = accessipv6

        if image is not None:
            data["imageRef"] = image

        if metadata is not None:
            data["metadata"] = metadata

        if user_data is not None:
            data["user_data"] = user_data

        if availability_zone is not None:
            data["availability_zone"] = availability_zone

        if personality is not None:
            data["personality"] = personality

        if security_groups is not None:
            for security_group in security_groups:
                data["security_groups"].append({"name": security_group})

        if networks is not None:
            for network in networks:
                data["networks"].append(network)

        if boot_volume_id is not None:
            data["block_device_mapping_v2"] = [
                {
                    "uuid": boot_volume_id,
                    "device_name": "/dev/vda",
                    "source_type": "volume",
                    "destination_type": "volume",
                    "boot_index": 0,
                }
            ]
        path = "/servers"
        self.set_nova_microversion("2.60")
        res = self.client.call(
            path,
            "POST",
            data=jsonDumps({"server": data}),
            token=self.manager.identity.token,
        )
        self.logger.debug("Create openstack server: %s" % truncate(res[0]))
        return res[0]["server"]

    @setup_client
    def update(self, oid, name, description):
        """Updates the editable attributes of a server.

        :param oid: server id
        :param name: server name
        :param desc: server desc
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s" % oid
        self.set_nova_microversion("2.60")
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = name
        res = self.client.call(
            path,
            "PUT",
            data=jsonDumps({"server": data}),
            token=self.manager.identity.token,
        )
        self.logger.debug("Get openstack server: %s" % truncate(res[0]))
        return res[0]["server"]

    @setup_client
    def rebuild(self, oid, image=None):
        """Rebuild the server.

        :param oid: server id
        :param image: The UUID of the image to use to rebuild your server instance.
        :return:
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s" % oid
        self.set_nova_microversion("2.60")
        path += "/action"
        data = {}
        if image is not None:
            data["imageRef"] = image
        res = self.client.call(
            path,
            "POST",
            data=jsonDumps({"rebuild": data}),
            token=self.manager.identity.token,
        )
        self.logger.debug("Get openstack server: %s" % truncate(res[0]))
        return res[0]["server"]

    @setup_client
    def delete(self, oid, force=False):
        """Deletes a server.

        :param oid: server id
        :param force: if True force delete
        :return: None
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s" % oid
        self.set_nova_microversion("2.60")
        if force is True:
            path += "/action"
            data = {"forceDelete": None}
            res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        else:
            res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def create_image(self, oid, image_name):
        """Create server image.

        :param oid: server id
        :param image: image name
        :return: None
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s" % oid
        self.set_nova_microversion("2.60")
        path += "/action"
        data = {"createImage": {"name": image_name}}
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Create image for server: %s" % truncate(res[0]))
        return res[0]

    #
    # information
    #
    def get_state(self, state):
        """Get server power status mapped to vsphere server status plus additional status.

        vsphere state:
        - noState
        - poweredOn
        - blocked
        - suspended
        - poweredOff
        - crashed

        additional state:
        - resize
        - update
        - deleted
        - reboot

        :param int state: index of status in enum
        """
        mapping = {
            "ACTIVE": "poweredOn",
            "BUILDING": "update",
            "DELETED": "deleted",
            "ERROR": "crashed",
            "HARD_REBOOT": "reboot",
            "MIGRATING": "update",
            "PASSWORD": "update",
            "PAUSED": "suspended",
            "REBOOT": "reboot",
            "REBUILD": "update",
            "RESCUED": "update",
            "RESIZED": "resize",
            "RESIZE": "resize",
            "REVERT_RESIZE": "resize",
            "SOFT_DELETED": "deleted",
            "STOPPED": "poweredOff",
            "SHUTOFF": "poweredOff",  # stopped over okata
            "SUSPENDED": "suspended",
            "UNKNOWN": "noState",
            "VERIFY_RESIZE": "resize",
        }
        if state is None:
            state = "UNKNOWN"
        return mapping.get(state)

    @setup_client
    def info(
        self,
        server,
        flavor_idx=None,
        volume_idx=None,
        image_idx=None,
        flavor=None,
        image=None,
    ):
        """Get server info

        :param server: server object obtained from api request
        :param flavor_idx: index of flavor object obtained from api request
        :param volume_idx: index of volume object obtained from api request
        :param image_idx: index of image object obtained from api request
        :param flavor: flavor object obtained from api request
        :param image: image object obtained from api request
        :return: dict like

            {'cpu': 1,
             'hostname': None,
             'ip_address': [],
             'memory': 2048,
             'os': '',
             'state': 'poweredOff',
             'template': None,
             ''disk':
             'disks':[]}
        """
        try:
            meta = None

            # get flavor info
            memory = 0
            cpu = 0
            if flavor_idx is not None:
                flavor_id = server["flavor"]["id"]
                flavor = flavor_idx[flavor_id]
                memory = flavor["ram"] or None
                cpu = flavor["vcpus"] or None
            if flavor is not None:
                memory = flavor["ram"] or None
                cpu = flavor["vcpus"] or None

            # get volume info
            disk = 0
            disk_num = 0
            disks = []
            if volume_idx is not None:
                volumes_ids = server["os-extended-volumes:volumes_attached"]
                volumes = []
                boot_volume = None
                for volumes_id in volumes_ids:
                    try:
                        vol = volume_idx[volumes_id["id"]]
                        disk += int(vol["size"])
                        disks.append({"size": int(vol["size"]), "free": None, "path": ""})
                        volumes.append(vol)
                        if vol["bootable"] == "true":
                            boot_volume = vol
                        disk_num += 1
                    except:
                        self.logger.warn("Server %s has not boot volume" % server["name"])

            if image_idx is not None:
                # get image from boot volume
                if server["image"] is None or server["image"] == "" and boot_volume is not None:
                    meta = boot_volume["volume_image_metadata"]

                # get image
                elif server["image"] is not None and server["image"] != "":
                    image = image_idx[server["image"]["id"]]
                    meta = image.get("metadata", None)
            if image is not None:
                # get image from boot volume
                if server["image"] is None or server["image"] == "" and boot_volume is not None:
                    meta = boot_volume["volume_image_metadata"]

                # get image
                elif server["image"] is not None and server["image"] != "":
                    meta = image.get("metadata", None)

            os = ""
            if meta is not None:
                try:
                    os_distro = meta["os_distro"]
                    os_version = meta["os_version"]
                    os = "%s %s" % (os_distro, os_version)
                except:
                    os = ""

            # gte ip addresses
            ipaddresses = []
            for ips in server["addresses"].values():
                for ip in ips:
                    ipaddresses.append(ip["addr"])

            data = {
                "os": os,
                "memory": memory,
                "cpu": cpu,
                "state": self.get_state(server["status"]),
                "template": None,
                "hostname": None,
                "ip_address": ipaddresses,
                "disk": disk,
                "disks": disks,
                "disk_num": disk_num,
            }
        except Exception as error:
            self.logger.error(error, exc_info=True)
            data = {}

        return data

    @setup_client
    def detail(self, server):
        """Get server detail

        :param server: server object obtained from api request
        :return: dict like

            {'date': {'created': '2016-10-19T12:26:30Z',
                       'launched': '2016-10-19T12:26:39.000000',
                       'terminated': None,
                       'updated': '2016-10-19T12:26:39Z'},
             'flavor': {'cpu': 1, 'id': '2', 'memory': 2048},
             'metadata': {},
             'networks': [{'name':None,
                            'fixed_ips': [{'ip_address': '172.25.5.156',
                                            'subnet_id': '54fea9ab-9ba4-4c99-a729-f7ce52cae8fd'}],
                            'mac_addr': 'fa:16:3e:17:4d:87',
                            'net_id': 'dc8771c3-f76e-4da6-bb59-e25e67ebb8bb',
                            'port_id': '033e6918-13fc-4af1-818d-1bd65e0d3800',
                            'port_state': 'ACTIVE'}],
             'opsck:build_progress': 0,
             'opsck:config_drive': '',
             'opsck:disk_config': 'MANUAL',
             'opsck:image': '',
             'opsck:internal_name': 'instance-00000a44',
             'opsck:key_name': None,
             'opsck:opsck_user_id': '730cd1699f144275811400d41afa7645',
             'os': 'CentOS 7',
             'state': 'poweredOn',
             'volumes': [{'bootable': 'true',
                           'format': 'qcow2',
                           'id': '83935084-f323-4e31-9a2c-478f2826b46f',
                           'mode': 'rw',
                           'name': 'server-49405-root-volume',
                           'size': 20,
                           'storage': 'cinder-liberty.nuvolacsi.it#RBD',
                           'type': None}]}
        """
        try:
            meta = None

            # get flavor info
            flavor_id = server["flavor"]["id"]
            flavor = self.manager.flavor.get(oid=flavor_id)
            memory = flavor["ram"] or None
            cpu = flavor["vcpus"] or None

            # get volume info
            volumes_ids = server["os-extended-volumes:volumes_attached"]
            volumes = []
            boot_volume = None
            for volumes_id in volumes_ids:
                try:
                    vol = self.manager.volume.get(volumes_id["id"])
                    volumes.append(vol)
                    if vol["bootable"] == "true":
                        boot_volume = vol
                except:
                    self.logger.warn("Server %s has not boot volume" % server["name"])

            # get image from boot volume
            if server["image"] is None or server["image"] == "" and boot_volume is not None:
                meta = boot_volume.get("volume_image_metadata", {})

            # get image
            elif server["image"] is not None and server["image"] != "":
                try:
                    image = self.manager.image.get(oid=server["image"]["id"])
                    meta = image.get("metadata", None)
                except:
                    meta = None

            os = ""
            if meta is not None:
                try:
                    os_distro = meta["os_distro"]
                    os_version = meta["os_version"]
                    os = "%s %s" % (os_distro, os_version)
                except:
                    os = ""

            # networks
            networks = self.get_port_interfaces(server["id"])

            # volumes
            server_volumes = []
            for volume in volumes:
                server_volumes.append(
                    {
                        "id": volume["id"],
                        "type": volume["volume_type"],
                        "bootable": volume["bootable"],
                        "name": volume["name"],
                        "size": volume["size"],
                        "format": volume.get("volume_image_metadata", {}).get("disk_format", None),
                        "mode": volume.get("metadata").get("attached_mode", None),
                        "storage": volume.get("os-vol-host-attr:host", None),
                    }
                )

            data = {
                "os": os,
                "state": self.get_state(server["status"]),
                "flavor": {
                    "id": flavor["id"],
                    "memory": memory,
                    "cpu": cpu,
                },
                "networks": networks,
                "volumes": server_volumes,
                "date": {
                    "created": server["created"],
                    "updated": server["updated"],
                    "launched": server["OS-SRV-USG:launched_at"],
                    "terminated": server["OS-SRV-USG:terminated_at"],
                },
                "metadata": server["metadata"],
                "opsck:internal_name": server["OS-EXT-SRV-ATTR:instance_name"],
                "opsck:opsck_user_id": server["user_id"],
                "opsck:key_name": server["key_name"],
                "opsck:build_progress": get_value(server, "progress", None),
                "opsck:image": server["image"],
                "opsck:disk_config": server["OS-DCF:diskConfig"],
                "opsck:config_drive": server["config_drive"],
                "security_groups": server.get("security_groups", []),
            }

            return data
        except Exception as error:
            self.logger.error(error, exc_info=True)
            data = {}

        return data

    @setup_client
    def security_groups(self, oid):
        """Get server security groups

        :param oid: server id
        :return: dict like

            [{'description': 'Default security group',
              'id': '1c3537ee-931c-4eb0-9d60-345baaa5a5ed',
              'name': 'default',
              'rules': [{'from_port': None,
                          'group': {},
                          'id': '2b5f88f7-9a17-4439-97df-839d6cf7a0e8',
                          'ip_protocol': None,
                          'ip_range': {'cidr': '158.102.160.0/24'},
                          'parent_group_id': '1c3537ee-931c-4eb0-9d60-345baaa5a5ed',
                          'to_port': None}],
              'tenant_id': '8337fff8a6bd4ae6b5f2255af2526212'}]
        """
        try:
            path = "/servers/%s/os-security-groups" % oid
            self.set_nova_microversion("2.60")
            res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
            self.logger.debug("Get openstack server security groups: %s" % truncate(res[0]))
            return res[0]["security_groups"]
        except Exception as error:
            self.logger.error(error, exc_info=True)
            data = []
        # TODO CHECK ME (g) res referenced before assignment return res
        return []

    @setup_client
    def runtime(self, server):
        """Server runtime info"""
        try:
            res = {
                "internal_name": server["OS-EXT-SRV-ATTR:instance_name"],
                "boot_time": server["OS-SRV-USG:launched_at"],
                "availability_zone": {"name": server["OS-EXT-AZ:availability_zone"]},
                "host": {
                    "id": server["hostId"],
                    "name": server["OS-EXT-SRV-ATTR:host"],
                },
                "server_state": server["OS-EXT-STS:vm_state"],
                "task": server["OS-EXT-STS:task_state"],
            }
        except Exception as error:
            self.logger.error(error, exc_info=True)
            data = {}

        return res

    @setup_client
    def diagnostics(self, oid):
        """Shows basic usage data for a server

        :param oid: server id
        :return: Ex.{'cpu0_time': 1040290000000L,
                     'memory': 2097152,
                     'memory-actual': 2097152,
                     'memory-available': 2049108,
                     'memory-major_fault': 537,
                     'memory-minor_fault': 2631107,
                     'memory-rss': 600412,
                     'memory-swap_in': 0,
                     'memory-swap_out': 0,
                     'memory-unused': 1715532,
                     'tap8ce64ffc-26_rx': 114184031,
                     'tap8ce64ffc-26_rx_drop': 0,
                     'tap8ce64ffc-26_rx_errors': 0,
                     'tap8ce64ffc-26_rx_packets': 1287786,
                     'tap8ce64ffc-26_tx': 55137281,
                     'tap8ce64ffc-26_tx_drop': 0,
                     'tap8ce64ffc-26_tx_errors': 0,
                     'tap8ce64ffc-26_tx_packets': 267402,
                     'vda_errors': -1,
                     'vda_read': 138479104,
                     'vda_read_req': 8413,
                     'vda_write': 772407296,
                     'vda_write_req': 80243}
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s/diagnostics" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Shows basic usage data for server %s: %s" % (oid, truncate(res[0])))
        return res[0]

    @setup_client
    def ping(self, oid):
        """Ping a server
        TODO: does not work
        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/os-fping/%s/" % oid
        path = "/os-fping?all_tenants=1&include=%s" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Ping server %s: %s" % (oid, truncate(res[0])))
        return res[0]

    #
    # network
    #
    @setup_client
    def get_port_interfaces(self, oid):
        """List port interfaces for a server

        :param oid: server id
        :return: [{'name':None,
                   'fixed_ips': [{'ip_address': '172.25.5.248',
                                   'subnet_id': '3579e3f7-03ea-44f1-9384-f9f9e0c015de'}],
                   'mac_addr': 'fa:16:3e:4d:43:3d',
                   'net_id': '45b69826-7909-4e37-8c01-85c6c8e63613',
                   'port_id': '8ce64ffc-26a2-40e8-af8a-0fa8a4e3aedc',
                   'port_state': 'ACTIVE'}]
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s/os-interface" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("List port interfaces for server %s: %s" % (oid, truncate(res[0])))
        nets = res[0]["interfaceAttachments"]
        for item in nets:
            item["name"] = None
        return nets

    @setup_client
    def add_port_interfaces(self, oid, port_id=None, net_id=None, fixed_ips=None):
        """Add port interface to a server

        :param oid: server id
        :param port_id: id of the port to add [optional]
        :param net_id: id of the network to add [optional]
        :param fixed_ips: Fixed IP addresses with subnet IDs. [optional]
                          Ex. {'ip_address': '172.25.5.248',
                               'subnet_id': '3579e3f7-03ea-44f1-9384-f9f9e0c015de'}
        :return: {'fixed_ips': [{'ip_address': '172.25.4.242',
                                 'subnet_id': 'f375e490-1103-4c00-9803-2703e3165271'}],
                  'mac_addr': 'fa:16:3e:72:1f:6b',
                  'net_id': '40803c62-f4b1-4afb-bd94-f773a5c70f7b',
                  'port_id': 'c4bc3504-bd3b-416f-b924-e40cd0388877',
                  'port_state': 'DOWN'}
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {}
        if port_id is not None:
            data["port_id"] = port_id
        if net_id is not None:
            data["net_id"] = net_id
        if fixed_ips is not None:
            data["fixed_ips"] = fixed_ips
        path = "/servers/%s/os-interface" % oid
        data = {"interfaceAttachment": data}
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Add port interface for server %s: %s" % (oid, truncate(res[0])))
        return res[0]["interfaceAttachment"]

    @setup_client
    def remove_port_interfaces(self, oid, port_id):
        """Remove port interface from a server

        :param oid: server id
        :return: None
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s/os-interface/%s" % (oid, port_id)
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Remove port interface %s for server %s: %s" % (port_id, oid, truncate(res[0])))
        return res[0]

    def get_ips(self, oid):
        """List ip addresses a server

        :param oid: server id
        :return: {'addresses': {'vlan307': [{'addr': '172.25.5.248', 'version': 4}]}}
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s/ips" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("List ip addresses for server %s: %s" % (oid, truncate(res[0])))
        return res[0]

    #
    # volume
    #
    @setup_client
    def get_volumes(self, oid):
        """List volumes for a server

        :param oid: server id
        :return: [{'device': '/dev/vda',
                   'id': '04a619d8-8515-47e3-b676-be61d61ff1f3',
                   'serverId': 'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
                   'volumeId': '04a619d8-8515-47e3-b676-be61d61ff1f3'},
                  {'device': '/dev/vdb',
                   'id': '930d6924-ebe8-497c-ada3-85d19144aa67',
                   'serverId': 'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
                   'volumeId': '930d6924-ebe8-497c-ada3-85d19144aa67'}]
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s/os-volume_attachments" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("List volumes for server %s: %s" % (oid, truncate(res[0])))
        return res[0]["volumeAttachments"]

    @setup_client
    def add_volume(self, oid, volume_id):
        """Add volume to a server

        :param oid: server id
        :param volume_id: volume id
        :return: {'device': '/dev/vdb',
                  'id': '930d6924-ebe8-497c-ada3-85d19144aa67',
                  'serverId': 'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
                  'volumeId': '930d6924-ebe8-497c-ada3-85d19144aa67'}
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "volumeAttachment": {
                "volumeId": volume_id,
            }
        }
        path = "/servers/%s/os-volume_attachments" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Add volume %s to server %s: %s" % (volume_id, oid, truncate(res[0])))
        return res[0]["volumeAttachment"]

    @setup_client
    def remove_volume(self, oid, volume_id):
        """Remove volume from a server

        :param oid: server id
        :param volume_id: volume id
        :return: None
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        self.set_nova_microversion("2.60")
        path = "/servers/%s/os-volume_attachments/%s" % (oid, volume_id)
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Remove volume %s from server %s: %s" % (volume_id, oid, truncate(res[0])))
        return res[0]

    #
    # metadata
    #
    @setup_client
    def get_metadata(self, oid):
        """Get server metadata

        :param oid: server id
        :return: {"foo": "Foo Value"}
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s/metadata" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("get server %s metadata: %s" % (oid, truncate(res[0])))
        return res[0]["metadata"]

    @setup_client
    def add_metadata(self, oid, metadata):
        """Create or update one or more metadata items for a server. Creates any metadata items that do not already
        exist in the server, replaces exists metadata items that match keys. Does not modify items that are not in the
        request.

        :param oid: server id
        :param metadata: dictionary with metadata
        :return: {"foo": "Foo Value"}
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"metadata": metadata}
        path = "/servers/%s/metadata" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Add server %s metadata: %s" % (oid, truncate(res[0])))
        return res[0]["metadata"]

    @setup_client
    def remove_metadata(self, oid, key):
        """Deletes a metadata item, by key, from a server

        :param oid: server id
        :param key: server metadata key
        :return: True
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s/metadata/%s" % (oid, key)
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete server %s metadata key %s" % (oid, key))
        return True

    #
    # actions
    #
    @setup_client
    def get_actions(self, oid, action_id=None):
        """Lists actions for a server or get action details if action_id is been specified

        :param oid: server id
        :param action_id: action id
        :return: Action list

            [{'action': 'start',
              'instance_uuid': 'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
              'message': None,
              'project_id': 'ad576ba1da5344a992463639ca4abf61',
              'request_id': 'req-3e5728bd-1517-4caf-aa23-4f63aaa9e0d3',
              'start_time': '2016-05-02T12:58:15.000000',
              'user_id': '730cd1699f144275811400d41afa7645'},
             {'action': 'stop',
              'instance_uuid': 'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
              'message': None,
              'project_id': 'ad576ba1da5344a992463639ca4abf61',
              'request_id': 'req-c0d8c0f1-c723-424c-9284-db576639085f',
              'start_time': '2016-05-02T07:46:25.000000',
              'user_id': '730cd1699f144275811400d41afa7645'},
             {'action': 'create',
              'instance_uuid': 'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
              'message': None,
              'project_id': 'ad576ba1da5344a992463639ca4abf61',
              'request_id': 'req-49dc6673-186a-4fd8-97d4-f5be0f37bb7c',
              'start_time': '2016-03-02T13:01:14.000000',
              'user_id': 'c53dbf98272b465fa4663ff530b11ed1'}]

            Action details

             {'action': 'start',
              'events': [{'event': 'compute_start_instance',
                           'finish_time': '2016-05-02T12:58:17.000000',
                           'result': 'Success',
                           'start_time': '2016-05-02T12:58:16.000000',
                           'traceback': None}],
              'instance_uuid': 'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
              'message': None,
              'project_id': 'ad576ba1da5344a992463639ca4abf61',
              'request_id': 'req-3e5728bd-1517-4caf-aa23-4f63aaa9e0d3',
              'start_time': '2016-05-02T12:58:15.000000',
              'user_id': '730cd1699f144275811400d41afa7645'}

        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        if action_id is None:
            path = "/servers/%s/os-instance-actions" % oid
            key = "instanceActions"
        else:
            path = "/servers/%s/os-instance-actions/%s" % (oid, action_id)
            key = "instanceAction"
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("get openstack server %s actions: %s" % (oid, truncate(res[0])))
        return res[0][key]

    @setup_client
    def start(self, oid):
        """Start server

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"os-start": None}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Start openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def stop(self, oid):
        """Stop server

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"os-stop": None}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Stop openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def reboot(self, oid):
        """Reboot server

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"reboot": {"type": "HARD"}}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Reboot openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def pause(self, oid):
        """Pause server

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"pause": None}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Pause openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def unpause(self, oid):
        """Unpauses a paused server and changes its status to ACTIVE.

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"unpause": None}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Unpause openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def lock(self, oid):
        """Lock server

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"lock": None}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Lock openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def unlock(self, oid):
        """Unlock server

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"unlock": None}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Unlock openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def suspend(self, oid):
        """Suspends a server and changes its status to SUSPENDED. Specify the suspend action in the request body.
        Policy defaults enable only users with the administrative role or the owner of the server to perform this
        operation. Cloud providers can change these permissions through the policy.json file.

        Normal response codes: 202
        Error response codes: unauthorized(401), forbidden(403), itemNotFound(404), conflict(409)

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"suspend": None}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Pause openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def resume(self, oid):
        """Resume a server and changes its status to ACTIVE. Specify the resume action in the request body.
        Policy defaults enable only users with the administrative role or the owner of the server to perform this
        operation. Cloud providers can change these permissions through the policy.json file.

        Normal response codes: 202
        Error response codes: unauthorized(401), forbidden(403), itemNotFound(404), conflict(409)

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"resume": None}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Pause openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def set_flavor(self, oid, flavor):
        """Resizes a server. Specify the resize action in the request body.
        A successfully resized server shows a VERIFY_RESIZE status, RESIZED VM status, and finished migration status.
        If you set the resize_confirm_window option of the Compute service to an integer value, the Compute service
        automatically confirms the resize operation after the set interval in seconds.

        Preconditions:
        You can only resize a server when its status is ACTIVE or SHUTOFF.
        If the server is locked, you must have administrator privileges to resize the server.

        Normal response codes: 202
        Error response codes: badRequest(400), unauthorized(401), forbidden(403), itemNotFound(404), conflict(409)

        :param oid: server id
        :param flavor: flavor id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"resize": {"flavorRef": flavor}}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Resize openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def confirm_set_flavor(self, oid):
        """Confirms a pending resize action for a server. Specify the confirmResize action in the request body.
        After you make this request, you typically must keep polling the server status to determine whether the request
        succeeded. A successfully confirming resize operation shows a status of ACTIVE or SHUTOFF and a migration_status
        of confirmed. You can also see the resized server in the compute node that OpenStack Compute manages.

        Preconditions:
        You can only confirm the resized server where the status is VERIFY_RESIZE.
        If the server is locked, you must have administrator privileges to confirm the server.

        Troubleshooting:
        If the server status remains RESIZED, the request failed. Ensure you meet the preconditions and run the request
        again. If the request fails again, investigate the compute back end or ask your cloud provider.

        Normal response codes: 204
        Error response codes: badRequest(400), unauthorized(401), forbidden(403), itemNotFound(404), conflict(409)

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"confirmResize": None}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Confirm resize openstack server: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def add_security_group(self, oid, security_group):
        """Add security group

        :param oid: server id
        :param security_group: security_group id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"addSecurityGroup": {"name": security_group}}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Add security group %s to openstack server %s: %s" % (security_group, oid, truncate(res[0])))
        return res[0]

    @setup_client
    def remove_security_group(self, oid, security_group):
        """Remove security group

        :param oid: server id
        :param security_group: security_group id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"removeSecurityGroup": {"name": security_group}}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug(
            "Remove security group %s from openstack server %s: %s" % (security_group, oid, truncate(res[0]))
        )
        return res[0]

    @setup_client
    def get_vnc_console(self, oid):
        """Get vnc console

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"remote_console": {"protocol": "vnc", "type": "novnc"}}
        path = "/servers/%s/remote-consoles" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Get openstack server %s vnc console : %s" % (oid, truncate(res[0])))
        resp = res[0]["remote_console"]
        return resp

    @setup_client
    def get_console_output(self, oid, length=50):
        """Shows console output for a server.

        :param oid: server id
        :param length: The number of lines to fetch from the end of console log. All lines will be returned if this is
            not specified.
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"os-getConsoleOutput": {"length": length}}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Get openstack server %s console output: %s" % (oid, truncate(res[0])))
        resp = res[0]["output"]
        return resp

    @setup_client
    def create_backup(self, oid, name, bck_type, bck_freq):
        """Create server backup

        TODO:

        :param oid: server id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "createBackup": {
                "name": name,
                "backup_type": bck_type,
                "rotation": bck_freq,
            }
        }
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("create openstack server %s backup rule : %s" % (oid, truncate(res[0])))
        return res[0]["server"]

    @setup_client
    def reset_state(self, oid, state="active"):
        """Resets the state of a server. Specify the os-resetState action and the state in the request body.
        Policy defaults enable only users with the administrative role to perform this operation. Cloud providers can
        change these permissions through the policy.json file.

        Normal response codes: 202
        Error response codes: unauthorized(401), forbidden(403), itemNotFound(404)

        :param oid: server id
        :param state: new server state [default=active]
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"os-resetState": {"state": state}}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Reset openstack server %s state : %s" % (oid, truncate(res[0])))
        return res[0]

    @setup_client
    def migrate(self, oid, host=None):
        """Migrate server

        :param oid: server id
        :param host: The host to which to migrate the server. If you specify null or don't specify this parameter,
            the scheduler chooses a host.
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        if host is None:
            data = {"migrate": None}
        else:
            data = {"migrate": {"host": host}}
        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Migrate openstack server %s : %s" % (oid, truncate(res[0])))
        return res

    @setup_client
    def live_migrate(self, oid, host=None):
        """Live-migrates a server to a new host without rebooting. Specify the os-migrateLive action in the request
        body.
        Use the host parameter to specify the destination host. If this param is null, the scheduler chooses a host.
        If a scheduled host is not suitable to do migration, the scheduler tries up to migrate_max_retries rescheduling
        attempts.

        Normal response codes: 202
        Error response codes: badRequest(400), unauthorized(401), forbidden(403) itemNotFound(404), conflict(409)

        :param oid: server id
        :param host: host name [default=None]
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "os-migrateLive": {
                "block_migration": False,
                "host": host,
            }
        }

        path = "/servers/%s/action" % oid
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Live migrate openstack server %s : %s" % (oid, truncate(res[0])))
        return res

    @setup_client
    def list_migration(self, oid=None):
        """List migrations

        :param oid: server id [optional]
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        self.set_nova_microversion("2.60")
        if oid is not None:
            path = "/servers/%s/migrations" % oid
            res = self.client.call(path, "GET", token=self.manager.identity.token)
            res = res[0].get("migrations", [])
            self.logger.debug("List openstack server %s migrations: %s" % (oid, res))
        else:
            path = "/os-migrations"
            res = self.client.call(path, "GET", token=self.manager.identity.token)
            res = res[0].get("migrations", [])
            self.logger.debug("List openstack servers migrations: %s" % truncate(res))
        return res

    @setup_client
    def force_migration(self, oid, migration_id):
        """Force an in-progress live migration for a given server to complete.
        Preconditions: The server OS-EXT-STS:vm_state value must be active and the server OS-EXT-STS:task_state value
        must be migrating.
        If the server status remains MIGRATING for an inordinate amount of time, the request may have failed. Ensure
        you meet the preconditions and run the request again. If the request fails again, investigate the compute back
        end.

        :param oid: server id
        :param migration_id: migration id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"force_complete": None}
        path = "/servers/%s/migrations/%s/action" % (oid, migration_id)
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "POST", data=data, token=self.manager.identity.token)
        self.logger.debug("Force openstack server %s migration %s" % (oid, migration_id))
        return res

    @setup_client
    def abort_migration(self, oid, migration_id):
        """Abort an in-progress live migration.

        :param oid: server id
        :param migration_id: migration id
        :raise OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/servers/%s/migrations/%s" % (oid, migration_id)
        self.set_nova_microversion("2.60")
        res = self.client.call(path, "DELETE", token=self.manager.identity.token)
        self.logger.debug("Abort openstack server %s migration %s" % (oid, migration_id))
        return res


class OpenstackKeyPair(OpenstackServerObject):
    """Generates, imports, and deletes SSH keys."""

    def __init__(self, manager):
        OpenstackServerObject.__init__(self, manager)

    @setup_client
    def list(self, all_tenants=True):
        """Lists keypairs that are associated with the project

        :param all_tenants: if True show server fro all tenanst
        :return: Ex:

            [{'keypair': {'fingerprint': 'd2:30:d8:f2:0f:8a:04:e2:2e:1e:87:61:ce:db:42:16',
                           'name': 'admin',
                           'public_key': 'ssh-rsa AAAAB3NzaC1y..L Generated-by-Nova'}},..
            ]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        query = {}
        path = "/os-keypairs"
        if all_tenants is True:
            query["all_tenants"] = 1

        path = "%s?%s" % (path, urlencode(query))

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack key pairs: %s" % truncate(res[0]))
        keys = res[0]["keypairs"]
        return [k["keypair"] for k in keys]

    @setup_client
    def get(self, name):
        """Shows details for a keypair that is associated with the project

        :param name: key pair name
        :return: Ex: {'created_at': '2016-01-15T14:44:17.000000',
                      'deleted': False,
                      'deleted_at': None,
                      'fingerprint': 'd2:30:d8:f2:0f:8a:04:e2:2e:1e:87:61:ce:db:42:16',
                      'id': 2,
                      'name': 'admin',
                      'public_key': 'ssh-rsa AAAA..yUkaL Generated-by-Nova',
                      'updated_at': None,
                      'user_id': '730cd1699f144275811400d41afa7645'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/os-keypairs/%s" % name
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack key pair %s: %s" % (name, truncate(res[0])))
        return res[0]["keypair"]

    @setup_client
    def create(self, name, public_key=None):
        """Generates or imports a keypair.

        :param name: The name to associate with the keypair.
        :param public_key: The public ssh key to import. If you omit this value,
                           a key is generated.
        :return: Ex.
            {'fingerprint': '5d:41:ed:f6:d2:86:2d:e4:c0:ef:24:0e:89:e9:cc:24',
             'name': 'key_prova',
             'private_key': '-----BEGIN RSA PRIVATE KEY-----\nMIIEqAIB..mB1X
                             DU=\n-----END RSA PRIVATE KEY-----\n',
             'public_key': 'ssh-rsa AAA..FFauV Generated-by-Nova',
             'user_id': '730cd1699f144275811400d41afa7645'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"keypair": {"name": name}}
        if public_key is not None:
            data["keypair"]["public_key"] = public_key

        path = "/os-keypairs"
        res = self.client.call(path, "POST", data=jsonDumps(data), token=self.manager.identity.token)
        self.logger.debug("Create/import openstack keypair: %s" % truncate(res[0]))
        return res[0]["keypair"]

    @setup_client
    def delete(self, name):
        """Deletes a keypair.

        :param name: The keypair name.
        :return: None
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/os-keypairs/%s" % name
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack keypair %s: %s" % (name, truncate(res[0])))
        return res[0]


class OpenstackserverGroup(OpenstackServerObject):
    """Lists, shows information for, creates, and deletes server groups."""

    def __init__(self, manager):
        OpenstackServerObject.__init__(self, manager)

    @setup_client
    def list(self, all_projects=True, limit=20, offset=0):
        """Lists server groups

        :param all_projects: if True show server fro all tenant
        :param int limit: Used in conjunction with offset to return a slice of items. limit is the maximum number of
            items to return. If limit is not specified, or exceeds the configurable max_limit, then max_limit will be
            used instead.
        :param int offset: Used in conjunction with limit to return a slice of items. offset is where to start in the
            list.
        :return: list of dict
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        query = {"limit": limit, "offset": offset}
        path = "/os-server-groups"
        if all_projects is True:
            query["all_projects"] = 1

        path = "%s?%s" % (path, urlencode(query))

        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack server groups: %s" % truncate(res[0]))
        keys = res[0]["server_groups"]
        return keys

    @setup_client
    def get(self, server_group_id):
        """Shows details for a server group

        :param server_group_id: The UUID of the server group
        :return: dict
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/os-server-groups/%s" % server_group_id
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token)
        self.logger.debug("Get openstack server group %s: %s" % (server_group_id, truncate(res[0])))
        return res[0]["server_group"]

    @setup_client
    def create(self, name, policies=None, policy=None, rules=None):
        """Generates a server group

        :param str name: The name of the server group.
        :param list policies: A list of exactly one policy name to associate with the server group. The current valid
            policy names are:
            - anti-affinity - servers in this group must be scheduled to different hosts.
            - affinity - servers in this group must be scheduled to the same host.
            - soft-anti-affinity - servers in this group should be scheduled to different hosts if possible, but if not
              possible then they should still be scheduled instead of resulting in a build failure. This policy was
              added in microversion 2.15.
            - soft-affinity - servers in this group should be scheduled to the same host if possible, but if not
              possible then they should still be scheduled instead of resulting in a build failure. This policy was
              added in microversion 2.15.
        :param str policy: The policy field represents the name of the policy. The current valid policy names are:
            - anti-affinity - servers in this group must be scheduled to different hosts.
            - affinity - servers in this group must be scheduled to the same host.
            - soft-anti-affinity - servers in this group should be scheduled to different hosts if possible, but if not
              possible then they should still be scheduled instead of resulting in a build failure. This policy was
              added in microversion 2.15.
            - soft-affinity - servers in this group should be scheduled to the same host if possible, but if not
              possible then they should still be scheduled instead of resulting in a build failure. This policy was
              added in microversion 2.15.
        :param str rules: (Optional) The rules field, which is a dict, can be applied to the policy. Currently, only
            the max_server_per_host rule is supported for the anti-affinity policy. The max_server_per_host rule allows
            specifying how many members of the anti-affinity group can reside on the same compute host. If not
            specified, only one member from the same anti-affinity group can reside on a given host. Requesting policy
            rules with any other policy than anti-affinity will be 400.
        :return: dict
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"name": name}
        if policies is not None:
            data["policies"] = policies
        if policy is not None:
            data["policy"] = policy
        if rules is not None:
            data["rules"] = rules

        self.set_nova_microversion("2.60")
        path = "/os-server-groups"
        res = self.client.call(
            path,
            "POST",
            data=jsonDumps({"server_group": data}),
            token=self.manager.identity.token,
        )
        self.logger.debug("Create/import openstack server group: %s" % truncate(res[0]))
        return res[0]["server_group"]

    @setup_client
    def delete(self, server_group_id):
        """Deletes a server group

        :param server_group_id: The UUID of the server group
        :return: None
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = "/os-server-groups/%s" % server_group_id
        res = self.client.call(path, "DELETE", data="", token=self.manager.identity.token)
        self.logger.debug("Delete openstack server group %s: %s" % (server_group_id, truncate(res[0])))
        return res[0]
