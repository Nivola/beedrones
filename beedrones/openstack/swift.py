# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import jsonDumps

import ujson as json
from uuid import uuid4
from hmac import new as hmacnew
from hashlib import sha1
from time import time
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


class OpenstackSwiftObject(OpenstackObject):
    def setup(self):
        self.uri = self.manager.endpoint("swift")
        self.client = OpenstackClient(self.uri, self.manager.proxy, timeout=self.manager.timeout)


class OpenstackSwift(OpenstackSwiftObject):
    """Openstack Swift client

    Object to manage the openstack Object storage

    """

    def __init__(self, manager):
        OpenstackSwiftObject.__init__(self, manager)

    @setup_client
    def info(self):
        """Shows build information for an Orchestration deployment.

        :raises OpenstackError: raise :class:`.OpenstackError`
        :return list of dictionaries
        """

        path = "/info"
        res = self.client.call(path, "GET", data="", token=self.manager.identity.token, base_path="")
        self.logger.debug("Openstack swift info: %s" % truncate(res[0]))
        return res[0]

    @setup_client
    def account_read(
        self,
        limit=None,
        marker=None,
        end_marker=None,
        prefix=None,
        delimiter=None,
        x_auth_token=None,
        x_service_token=None,
        x_newest=None,
        Accept=None,
        x_trans_id_extra=None,
    ):
        """Show account details and list containers.

            Shows details for an account and lists containers, sorted by name, in the account.

        :param limit (Optional):     query     integer     For an integer value n , limits
            the number of results to n .
        :param marker (Optional):     query     string     For a string value, x , returns
            container names that are greater than the marker value.
        :param end_marker (Optional):     query     string     For a string value, x , returns
            container names that are less than the marker value.
        :param format (Optional):     query     string     The response format. Valid values
            are json, xml, or plain. The default is plain. If you append the format=xml
            or format=json query parameter to the storage account URL, the response shows
            extended container information serialized in that format. If you append the
            format=plain query parameter, the response lists the container names
            separated by newlines.
        :param prefix (Optional):     query     string     Prefix value. Named items in the
            response begin with this value.
        :param delimiter (Optional):     query     string     Delimiter value, which returns
            the object names that are nested in the container. If you do not set a
            prefix and set the delimiter to "/" you may get unexpected results where all
            the objects are returned instead of only those with the delimiter set.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param x_newest (Optional):     header     boolean     If set to true , Object
            Storage queries all replicas to return the most recent one. If you omit this
            header, Object Storage responds faster after it finds one valid replica.
            Because setting this header to true is more expensive for the back end, use
            it only when it is absolutely needed.
        :param Accept (Optional):     header     string     Instead of using the format query
            parameter, set this header to application/json, application/xml, or text/xml.
        :param x_trans_id_extra (Optional):     header     string     Extra transaction
            information. Use the x_trans_id_extra request header to include extra
            information to help you debug any errors that might occur with large object
            upload and other Object Storage transactions. The server appends the first 32
            characters of the x_trans_id_extra request header value to the transaction ID
            value in the generated XTransId response header. You must UTF8encode and
            then URLencode the extra transaction information before you include it in
            the x_trans_id_extra request header. For example, you can include extra
            transaction information when you upload large objects such as images. When
            you upload each segment and the manifest, include the same value in the
            x_trans_id_extra request header. If an error occurs, you can find all
            requests that are related to the large object upload in the Object Storage
            logs. You can also use x_trans_id_extra strings to help operators debug
            requests that fail to receive responses. The operator can search for the
            extra information in the logs.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return List containing a list of dictionary for the body and a dictionary for the header
            ex:
            [
               [
                  {
                     'count':40,
                     'bytes':6724,
                     'name':'3bc86aa4-4936-433f-82e2-0be0139c8c34'
                  },
                  {
                     'count':142,
                     'bytes':31601236,
                     'name':'edd903dd-0eae-48cd-9c2a-bfac88c86c80'
                  },
                ...
               ]
               {
                  'content-length':'1367',
                  'x-account-object-count':'386',
                  'x-account-project-domain-id':'default',
                  'x-account-storage-policy-policy-0-bytes-used':'401532475',
                  'x-account-storage-policy-policy-0-container-count':'19',
                  'x-timestamp':'1452610323.29080',
                  'x-account-storage-policy-policy-0-object-count':'386',
                  'x-trans-id':'txfd84b57feeda4d19bd2ed-005846b8c4',
                  'date':'Tue, 06 Dec 2016 13:10:28 GMT',
                  'x-account-bytes-used':'401532475',
                  'x-account-container-count':'19',
                  'content-type':'application/json; charset=utf-8',
                  'accept-ranges':'bytes'
               }
            ]
            where:
            count  integer: The number of objects in the container.
            bytes  integer: The total number of bytes that are stored in Object Storage for the account.
            name    string: The name of the container.
        """
        query = {"format": "json"}
        headers = {}
        path = ""
        if limit is not None:
            query["limit"] = limit
        if marker is not None:
            query["marker"] = marker
        if end_marker is not None:
            query["end_marker"] = end_marker
        if prefix is not None:
            query["prefix"] = prefix
        if delimiter is not None:
            query["delimiter"] = delimiter
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if x_newest is not None:
            headers["X-Newest"] = x_newest
        if Accept is not None:
            headers["Accept"] = Accept
        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra

        path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "GET", data="", headers=headers, token=self.manager.identity.token)
        self.logger.debug("Openstack swift info: %s" % truncate(res[0]))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        r = [res[0]]
        r.append(result)
        return r

    @setup_client
    def account_metadata_get(self):
        """Show account metadata.

        :info Shows metadata for an account.
                Metadata for the account includes:
                    Number of containers
                    Number of objects
                    Total number of bytes that are stored in Object Storage for the account
                Because the storage system can store large amounts of data, take care
                when you represent the total bytes response as an integer; when possible,
                convert it to a 64-bit unsigned integer if your platform supports that
                primitive type.
        :param account (Optional):     path     string     The unique name for the account. An
            account is also known as the project or tenant.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return a dictionary with lowercase header key
        ex.
        {
           'content-length':'0',
           'x-account-meta-prova2':'provavalore2',
           'x-account-object-count':'386',
           'x-account-meta-x-account-meta-prova':'provavalore',
           'x-account-project-domain-id':'default',
           'x-account-storage-policy-policy-0-bytes-used':'401532475',
           'x-account-storage-policy-policy-0-container-count':'19',
           'x-timestamp':'1452610323.29080',
           'x-account-storage-policy-policy-0-object-count':'386',
           'x-trans-id':'txe8b890916500425b95a1c-0058469906',
           'date':'Tue, 06 Dec 2016 10:55:02 GMT',
           'x-account-bytes-used':'401532475',
           'x-account-container-count':'19',
           'content-type':'application/json; charset=utf-8',
           'accept-ranges':'bytes',
           'x-account-meta-prova':'provavalore'
        }
        """
        query = {"format": "json"}

        path = ""

        path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "HEAD", data="", token=self.manager.identity.token)
        self.logger.debug("Show account metadata: %s" % truncate(res[0]))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        return result

    @setup_client
    def account_metadata_post(
        self,
        x_auth_token=None,
        x_service_token=None,
        x_account_meta_temp_url_key=None,
        x_account_meta_temp_url_key_2=None,
        x_account_meta_name=None,
        x_remove_account_name=None,
        x_account_access_control=None,
        x_trans_id_extra=None,
    ):
        """Create, update, or delete account metadata.

        :info: Account metadata operations
            POST request header contains     Result

            A metadata key without a value.
            The metadata key already exists for the account.
                    The API removes the metadata item from the account.

            A metadata key without a value.
            The metadata key does not already exist for the account.
                    The API ignores the metadata key.

            A metadata key value.
            The metadata key already exists for the account.
                    The API updates the metadata key value for the account.

            A metadata key value.
            The metadata key does not already exist for the account.
                    The API adds the metadata key and value pair, or item, to the account.

            One or more account metadata items are omitted.
            The metadata items already exist for the account.
                    The API does not change the existing metadata items.

        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param x_account_meta_temp_url_key (Optional):     header     string     The secret
            key value for temporary URLs.
        :param  x_account_meta_temp_url_key_2 (Optional):     header     string     A second
            secret key value for temporary URLs. The second key enables you to rotate keys by
            having two active keys at the same time.
        :param x_account_meta_name (Optional):     header     dictionary     The account metadata.
            The name is the name of metadata item that you want to add, update, or delete. To
            delete this item, send an empty value in this header. You must specify an
            X-Account-Meta-name header for each metadata item (for each name) that you want to
            add, update, or delete.
        :param x_remove_account_name (Optional):     header     string     Removes the metadata
            item named name. For example, X-Remove-Account-Meta-Blue removes custom metadata.
        :param x_account_access_control (Optional): header     string
            Note: X-Account-Access-Control is not supported by Keystone auth.
            Sets an account access control list (ACL) that grants access to containers and
            objects in the account. See Account ACLs for more information.
        :param x_trans_id_extra (Optional): header  string     Extra transaction information.
            Use the X-Trans-Id-Extra request header to include extra information to help you
            debug any errors that might occur with large object upload and other Object Storage
            transactions. The server appends the first 32 characters of the X-Trans-Id-Extra
            request header value to the transaction ID value in the generated X-Trans-Id response
            header. You must UTF-8-encode and then URL-encode the extra transaction information
            before you include it in the X-Trans-Id-Extra request header. For example, you can
            include extra transaction information when you upload large objects such as images.
            When you upload each segment and the manifest, include the same value in the
            X-Trans-Id-Extra request header. If an error occurs, you can find all requests that
            are related to the large object upload in the Object Storage logs. You can also use
            X-Trans-Id-Extra strings to help operators debug requests that fail to receive responses.
            The operator can search for the extra information in the logs.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return dictionary with lowercase header key containing also a 'resp-code' key with the
            response code that must be 204 if success.
            ex:
             {
               'date':'Tue, 06 Dec 2016 11:16:31 GMT',
               'content-length':'0',
               'resp-code':204,
               'content-type':'text/html; charset=UTF-8',
               'x-trans-id':'tx827ed9c263d34b07bebc4-0058469e0f'
            }
        """
        headers = {}
        path = ""

        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if x_account_meta_temp_url_key is not None:
            headers["X-Account-Meta-Temp-URL-Key"] = x_account_meta_temp_url_key
        if x_account_meta_temp_url_key_2 is not None:
            headers["X-Account-Meta-Temp-URL-Key-2"] = x_account_meta_temp_url_key_2
        if x_account_meta_name is not None:
            for key in x_account_meta_name:
                headers["X-Account-Meta-%s" % key] = x_account_meta_name[key]
        if x_remove_account_name is not None:
            headers["X-Remove-Account-%s" % x_account_meta_name] = ""
        if x_account_access_control is not None:
            headers["X-Account-Access-Control"] = x_account_access_control
        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra

        res = self.client.call(path, "POST", data="", headers=headers, token=self.manager.identity.token)
        self.logger.debug(
            "Openstack swift account metadata headers %s creation: %s" % (jsonDumps(headers), truncate(res[0]))
        )
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        result["resp-code"] = res[2]
        return result

    @setup_client
    def container_read(
        self,
        container=None,
        limit=None,
        marker=None,
        end_marker=None,
        prefix=None,
        delimiter=None,
        pseudo_path=None,
        x_auth_token=None,
        x_service_token=None,
        x_newest=None,
        Accept=None,
        x_container_meta_temp_url_key=None,
        x_container_meta_temp_url_key_2=None,
        x_trans_id_extra=None,
    ):
        """Show account details and list containers.

            Shows details for an account and lists containers, sorted by name, in the account.
        :param container (Optional):     path     string     The unique (within an account)
            name for the container. The container name must be from 1 to 256 characters long
            and can start with any character and contain any pattern. Character set must be UTF-8.
            The container name cannot contain a slash (/) character because this character delimits
            the container and object name. For example, the path /v1/account/www/pages specifies the
            www container, not the www/pages container.
        :param limit (Optional):     query     integer     For an integer value n , limits
            the number of results to n .
        :param marker (Optional):     query     string     For a string value, x , returns
            container names that are greater than the marker value.
        :param end_marker (Optional):     query     string     For a string value, x , returns
            container names that are less than the marker value.
        :param format (Optional):     query     string     The response format. Valid values
            are json, xml, or plain. The default is plain. If you append the format=xml
            or format=json query parameter to the storage account URL, the response shows
            extended container information serialized in that format. If you append the
            format=plain query parameter, the response lists the container names
            separated by newlines.
        :param prefix (Optional):     query     string     Prefix value. Named items in the
            response begin with this value.
        :param delimiter (Optional):     query     string     Delimiter value, which returns
            the object names that are nested in the container. If you do not set a
            prefix and set the delimiter to "/" you may get unexpected results where all
            the objects are returned instead of only those with the delimiter set.
        :param pseudo_path (Optional):     query     string     For a string value, returns the
            object names that are nested in the pseudo path.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param x_newest (Optional):     header     boolean     If set to true , Object
            Storage queries all replicas to return the most recent one. If you omit this
            header, Object Storage responds faster after it finds one valid replica.
            Because setting this header to true is more expensive for the back end, use
            it only when it is absolutely needed.
        :param Accept (Optional):     header     string     Instead of using the format query
            parameter, set this header to application/json, application/xml, or text/xml.
        :param x_container_meta_temp_url_key (Optional):     header     string
            The secret key value for temporary URLs.
        :param x_container_meta_temp_url_key_2 (Optional):     header     string
            A second secret key value for temporary URLs. The second key enables you to
            rotate keys by having two active keys at the same time.
        :param x_trans_id_extra (Optional):     header     string     Extra transaction
            information. Use the x_trans_id_extra request header to include extra
            information to help you debug any errors that might occur with large object
            upload and other Object Storage transactions. The server appends the first 32
            characters of the x_trans_id_extra request header value to the transaction ID
            value in the generated XTransId response header. You must UTF8encode and
            then URLencode the extra transaction information before you include it in
            the x_trans_id_extra request header. For example, you can include extra
            transaction information when you upload large objects such as images. When
            you upload each segment and the manifest, include the same value in the
            x_trans_id_extra request header. If an error occurs, you can find all
            requests that are related to the large object upload in the Object Storage
            logs. You can also use x_trans_id_extra strings to help operators debug
            requests that fail to receive responses. The operator can search for the
            extra information in the logs.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return List containing a list of dictionary for the body and a dictionary for the header
            ex:
            [
               [

                  {
                     "bytes":108,
                     "last_modified":"2016-03-17T15:51:10.869220",
                     "hash":"d3b6e5736a3d22aa4c933860deea7885",
                     "name":"s3ql_seq_no_1",
                     "content_type":"application\/octet-stream"
                  },
                  {
                     "bytes":108,
                     "last_modified":"2016-03-17T15:51:58.590460",
                     "hash":"ee27455b1dbc170b8a6d0d91009bbd76",
                     "name":"s3ql_seq_no_2",
                     "content_type":"application\/octet-stream"
                  },
                  {
                     "bytes":108,
                     "last_modified":"2016-03-18T08:21:59.964870",
                     "hash":"8f94d10825b1e96afa381059ecf2a253",
                     "name":"s3ql_seq_no_3",
                     "content_type":"application\/octet-stream"
                  },
                  ...
               ],
               {
                  "content-length":"9433",
                  "x-container-object-count":"52",
                  "accept-ranges":"bytes",
                  "x-storage-policy":"Policy-0",
                  "x-container-bytes-used":"352706235",
                  "x-timestamp":"1458229823.08452",
                  "x-trans-id":"tx48414dc585d1476bb82c6-005846c317",
                  "date":"Tue, 06 Dec 2016 13:54:31 GMT",
                  "content-type":"application\/json; charset=utf-8"
               }
            ]
        """
        query = {"format": "json"}
        headers = {}
        if container is not None:
            path = "/%s" % container
        else:
            path = ""
        if limit is not None:
            query["limit"] = limit
        if marker is not None:
            query["marker"] = marker
        if end_marker is not None:
            query["end_marker"] = end_marker
        if prefix is not None:
            query["prefix"] = prefix
        if delimiter is not None:
            query["delimiter"] = delimiter
        if pseudo_path is not None:
            query["path"] = pseudo_path
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if x_newest is not None:
            headers["X-Newest"] = x_newest
        if Accept is not None:
            headers["Accept"] = Accept
        if x_container_meta_temp_url_key is not None:
            headers["X-Container-Meta-Temp-URL-Key"] = x_container_meta_temp_url_key
        if x_container_meta_temp_url_key_2 is not None:
            headers["X-Container-Meta-Temp-URL-Key-2"] = x_container_meta_temp_url_key_2

        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra

        path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "GET", data="", headers=headers, token=self.manager.identity.token)
        self.logger.debug("Openstack swift info: %s" % truncate(res[0]))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        r = [res[0]]
        r.append(result)
        return r

    @setup_client
    def container_put(
        self,
        container=None,
        x_auth_token=None,
        x_service_token=None,
        x_container_read=None,
        x_container_write=None,
        x_container_sync_to=None,
        x_container_sync_key=None,
        x_versions_location=None,
        x_history_location=None,
        x_container_meta_name=None,
        x_container_meta_access_control_allow_origin=None,
        x_container_meta_access_control_max_age=None,
        x_container_meta_access_control_expose_headers=None,
        x_container_meta_quota_bytes=None,
        x_container_meta_quota_count=None,
        x_container_meta_temp_url_key=None,
        x_container_meta_temp_url_key_2=None,
        x_trans_id_extra=None,
        x_storage_policy=None,
    ):
        """Create container. You do not need to check whether a container already exists before issuing a PUT
            operation because the operation is idempotent: It creates a container or updates
            an existing container, as appropriate.
        :param container (Optional):     path     string     The unique (within an account)
            name for the container. The container name must be from 1 to 256 characters long
            and can start with any character and contain any pattern. Character set must be UTF-8.
            The container name cannot contain a slash (/) character because this character delimits
            the container and object name. For example, the path /v1/account/www/pages specifies the
            www container, not the www/pages container.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param x_container_read (Optional):     header     string     Sets a container access
            control list (ACL) that grants read access. The scope of the access is specific to
            the container. The ACL grants the ability to perform GET or HEAD operations on objects
            in the container or to perform a GET or HEAD operation on the container itself. The
            format and scope of the ACL is dependent on the authorization system used by the
            Object Storage service.
        :param x_container_write (Optional):     header     string     Sets a container access
            control list (ACL) that grants write access. The scope of the access is specific to the
            container. The ACL grants the ability to perform PUT, POST and DELETE operations on objects
            in the container. It does not grant write access to the container metadata. The format of
            the ACL is dependent on the authorization system used by the Object Storage service.
        :param x_container_sync_to (Optional):     header     string     Sets the destination
            for container synchronization. Used with the secret key indicated in the
            X-Container-Sync-Key header. If you want to stop a container from synchronizing, send a
            blank value for the X-Container-Sync-Key header.
        :param x_container_sync_key (Optional):     header     string     Sets the secret key for
            container synchronization. If you remove the secret key, synchronization is halted.
        :param x_versions_location (Optional):     header     string     The URL_encoded UTF_8
            representation of the container that stores previous versions of objects. If neither
            this nor X-History-Location is set, versioning is disabled for this container.
            X-Versions-Location and X-History-Location cannot both be set at the same time.
            For more information about object versioning, see Object versioning.
        :param x_history_location (Optional):     header     string     The URL_encoded UTF_8
            representation of the container that stores previous versions of objects. If neither
            this nor X-Versions-Location is set, versioning is disabled for this container.
            X-History-Location and X-Versions-Location cannot both be set at the same time.
        :param x_container_meta_name (Optional):     header     dictionary     The container metadata,
            where name is the name of metadata item. You must specify an X-Container-Meta-name header
            for each metadata item (for each name) that you want to add or update.
        :param x_container_meta_access_control_allow_origin (Optional):     header     string
            Originating URLs allowed to make cross-origin requests (CORS), separated by spaces. This
            heading applies to the container only, and all objects within the container with this
            header applied are CORS-enabled for the allowed origin URLs. A browser (user-agent)
            typically issues a preflighted request , which is an OPTIONS call that verifies the origin
            is allowed to make the request. The Object Storage service returns 200 if the originating
            URL is listed in this header parameter, and issues a 401 if the originating URL is not
            allowed to make a cross-origin request. Once a 200 is returned, the browser makes a
            second request to the Object Storage service to retrieve the CORS-enabled object.
        :param x_container_meta_access_control_max_age (Optional):     header     string
            Maximum time for the origin to hold the preflight results. A browser may make an OPTIONS
            call to verify the origin is allowed to make the request. Set the value to an integer
            number of seconds after the time that the request was received.
        :param x_container_meta_access_control_expose_headers (Optional):     header     string
            Headers the Object Storage service exposes to the browser (technically, through the
            user-agent setting), in the request response, separated by spaces. By default the Object
            Storage service returns the following headers:
            All "simple response headers" as listed on http://www.w3.org/TR/cors/#simple-response-header.
            The headers etag, x-timestamp, x-trans-id, x-openstack-request-id.
            All metadata headers (X-Container-Meta-* for containers and X-Object-Meta-* for objects).
            headers listed in X-Container-Meta-Access-Control-Expose-Headers.
        :param x_container_meta_quota_bytes (Optional):     header     string
            Sets maximum size of the container, in bytes. Typically these values are set by an
            administrator. Returns a 413 response (request entity too large) when an object PUT
            operation exceeds this quota value. This value does not take effect immediately. see
            Container Quotas for more information.
        :param x_container_meta_quota_count (Optional):     header     string     Sets maximum
            object count of the container. Typically these values are set by an administrator. Returns
            a 413 response (request entity too large) when an object PUT operation exceeds this quota
            value. This value does not take effect immediately. see Container Quotas for more information.
        :param x_container_meta_temp_url_key (Optional):     header     string     The secret
            key value for temporary URLs.
        :param  x_container_meta_temp_url_key_2 (Optional):     header     string     A second
            secret key value for temporary URLs. The second key enables you to rotate keys by
            having two active keys at the same time.
        :param x_trans_id_extra (Optional): header  string     Extra transaction information.
            Use the X-Trans-Id-Extra request header to include extra information to help you
            debug any errors that might occur with large object upload and other Object Storage
            transactions. The server appends the first 32 characters of the X-Trans-Id-Extra
            request header value to the transaction ID value in the generated X-Trans-Id response
            header. You must UTF-8-encode and then URL-encode the extra transaction information
            before you include it in the X-Trans-Id-Extra request header. For example, you can
            include extra transaction information when you upload large objects such as images.
            When you upload each segment and the manifest, include the same value in the
            X-Trans-Id-Extra request header. If an error occurs, you can find all requests that
            are related to the large object upload in the Object Storage logs. You can also use
            X-Trans-Id-Extra strings to help operators debug requests that fail to receive responses.
            The operator can search for the extra information in the logs.
        :param x_storage_policy (Optional):     header     string     In requests, specifies the
            name of the storage policy to use for the container. In responses, is the storage policy
            name. The storage policy of the container cannot be changed.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return dictionary with lowercase header key containing also a 'resp-code' key with the
            response code that must be 204 if success.
            ex:
             {
               'date':'Tue, 06 Dec 2016 11:16:31 GMT',
               'content-length':'0',
               'resp-code':204,
               'content-type':'text/html; charset=UTF-8',
               'x-trans-id':'tx827ed9c263d34b07bebc4-0058469e0f'
            }
        """
        headers = {}
        if container is not None:
            path = "/%s" % container
        else:
            path = ""
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if x_container_read is not None:
            headers["X-Container-Read"] = x_container_read
        if x_container_write is not None:
            headers["X-Container-Write"] = x_container_write
        if x_container_sync_to is not None:
            headers["X-Container-Sync-To"] = x_container_sync_to
        if x_container_sync_key is not None:
            headers["X-Container-Sync-Key"] = x_container_sync_key
        if x_versions_location is not None:
            headers["X-Versions-Location"] = x_versions_location
        if x_history_location is not None:
            headers["X-History-Location"] = x_history_location
        if x_container_meta_name is not None:
            for key in x_container_meta_name:
                headers["X-Container-Meta-%s" % key] = x_container_meta_name[key]
        if x_container_meta_access_control_allow_origin is not None:
            headers["X-Container-Meta-Access-Control-Allow-Origin"] = x_container_meta_access_control_allow_origin
        if x_container_meta_access_control_max_age is not None:
            headers["X-Container-Meta-Access-Control-Max-Age"] = x_container_meta_access_control_max_age
        if x_container_meta_access_control_expose_headers is not None:
            headers["X-Container-Meta-Access-Control-Expose-Headers"] = x_container_meta_access_control_expose_headers
        if x_container_meta_quota_bytes is not None:
            headers["X-Container-Meta-Quota-Bytes"] = x_container_meta_quota_bytes
        if x_container_meta_quota_count is not None:
            headers["X-Container-Meta-Quota-Count"] = x_container_meta_quota_count
        if x_container_meta_temp_url_key is not None:
            headers["X-Container-Meta-Temp-URL-Key"] = x_container_meta_temp_url_key
        if x_container_meta_temp_url_key_2 is not None:
            headers["X-Container-Meta-Temp-URL-Key-2"] = x_container_meta_temp_url_key_2
        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra
        if x_storage_policy is not None:
            headers["X-Storage-Policy"] = x_storage_policy

        res = self.client.call(path, "PUT", data="", headers=headers, token=self.manager.identity.token)
        self.logger.debug("Openstack swift container headers %s creation: %s" % (jsonDumps(headers), truncate(res[0])))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        result["resp-code"] = res[2]
        return result

    @setup_client
    def container_delete(self, container, x_auth_token=None, x_service_token=None, x_trans_id_extra=None):
        """Deletes an empty container.

        :info This operation fails unless the container is empty. An empty container has no objects.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param x_trans_id_extra (Optional): header  string     Extra transaction information.
            Use the X-Trans-Id-Extra request header to include extra information to help you
            debug any errors that might occur with large object upload and other Object Storage
            transactions. The server appends the first 32 characters of the X-Trans-Id-Extra
            request header value to the transaction ID value in the generated X-Trans-Id response
            header. You must UTF-8-encode and then URL-encode the extra transaction information
            before you include it in the X-Trans-Id-Extra request header. For example, you can
            include extra transaction information when you upload large objects such as images.
            When you upload each segment and the manifest, include the same value in the
            X-Trans-Id-Extra request header. If an error occurs, you can find all requests that
            are related to the large object upload in the Object Storage logs. You can also use
            X-Trans-Id-Extra strings to help operators debug requests that fail to receive responses.
            The operator can search for the extra information in the logs.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return a dictionary with lowercase header key
        ex.

        [
           "",
           {
              "date":"Wed, 07 Dec 2016 14:38:51 GMT",
              "content-length":"0",
              "content-type":"text\/html; charset=UTF-8",
              "resp-code":204,
              "x-trans-id":"txc3d25868b625494d9d899-0058481efa"
           }
        ]
        """
        headers = {}
        path = "/%s" % container
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra

        result = {}
        try:
            res = self.client.call(
                path,
                "DELETE",
                data="",
                headers=headers,
                token=self.manager.identity.token,
            )
            r = [res[0]]
            result["resp-code"] = res[2]
            for item in res[1]:
                result[item[0]] = item[1]
            self.logger.debug("Delete container %s: %s" % (container, truncate(res[0])))
        except OpenstackError as ex:
            if str(ex.code) == "409":
                r = ["409 Conflict!There was a conflict when trying to complete your request"]
                result["resp-code"] = 409
                self.logger.debug("Delete container %s error: %s" % (container, ex.code))
            else:
                raise ex
        r.append(result)
        return r

    @setup_client
    def container_metadata_post(
        self,
        container=None,
        x_auth_token=None,
        x_service_token=None,
        x_container_read=None,
        x_remove_container_name=None,
        x_container_write=None,
        x_container_sync_to=None,
        x_container_sync_key=None,
        x_versions_location=None,
        x_history_location=None,
        x_remove_versions_location=None,
        x_remove_history_location=None,
        x_container_meta_name=None,
        x_container_meta_access_control_allow_origin=None,
        x_container_meta_access_control_max_age=None,
        x_container_meta_access_control_expose_headers=None,
        x_container_meta_quota_bytes=None,
        x_container_meta_quota_count=None,
        x_container_meta_web_directory_type=None,
        x_container_meta_temp_url_key=None,
        x_container_meta_temp_url_key_2=None,
        x_trans_id_extra=None,
        x_storage_policy=None,
    ):
        """Create, update, or delete container metadata

        :info Creates, updates, or deletes custom metadata for a container.
            To create, update, or delete a custom metadata item, use the X -Container-Meta-{name}
            header, where {name} is the name of the metadata item.
        :param container (Optional):     path     string     The unique (within an account)
            name for the container. The container name must be from 1 to 256 characters long
            and can start with any character and contain any pattern. Character set must be UTF-8.
            The container name cannot contain a slash (/) character because this character delimits
            the container and object name. For example, the path /v1/account/www/pages specifies the
            www container, not the www/pages container.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param x_container_read (Optional):     header     string     Sets a container access
            control list (ACL) that grants read access. The scope of the access is specific to
            the container. The ACL grants the ability to perform GET or HEAD operations on objects
            in the container or to perform a GET or HEAD operation on the container itself. The
            format and scope of the ACL is dependent on the authorization system used by the
            Object Storage service.
        :param x_remove_container_name (Optional): header     string     Removes the metadata
            item named name. For example, X-Remove-Container-Read removes the X-Container-Read
            metadata item and X-Remove-Container-Meta-Blue removes custom metadata.
        :param x_container_write (Optional):     header     string     Sets a container access
            control list (ACL) that grants write access. The scope of the access is specific to the
            container. The ACL grants the ability to perform PUT, POST and DELETE operations on objects
            in the container. It does not grant write access to the container metadata. The format of
            the ACL is dependent on the authorization system used by the Object Storage service.
        :param x_container_sync_to (Optional):     header     string     Sets the destination
            for container synchronization. Used with the secret key indicated in the
            X-Container-Sync-Key header. If you want to stop a container from synchronizing, send a
            blank value for the X-Container-Sync-Key header.
        :param x_container_sync_key (Optional):     header     string     Sets the secret key for
            container synchronization. If you remove the secret key, synchronization is halted.
        :param x_versions_location (Optional):     header     string     The URL_encoded UTF_8
            representation of the container that stores previous versions of objects. If neither
            this nor X-History-Location is set, versioning is disabled for this container.
            X-Versions-Location and X-History-Location cannot both be set at the same time.
            For more information about object versioning, see Object versioning.
        :param x_history_location (Optional):     header     string     The URL_encoded UTF_8
            representation of the container that stores previous versions of objects. If neither
            this nor X-Versions-Location is set, versioning is disabled for this container.
            X-History-Location and X-Versions-Location cannot both be set at the same time.
        :param x_remove_versions_location (Optional): header     string     Set to any value to disable
            versioning. Note that this disables version that was set via X-History-Location as well.
        :param x_remove_history_location (Optional): header     string     Set to any value to disable
            versioning. Note that this disables version that was set via X-Versions-Location as well.
        :param x_container_meta_name (Optional):     header     dictionary     The container metadata,
            where name is the name of metadata item. You must specify an X-Container-Meta-name header
            for each metadata item (for each name) that you want to add or update.
        :param x_container_meta_access_control_allow_origin (Optional):     header     string
            Originating URLs allowed to make cross-origin requests (CORS), separated by spaces. This
            heading applies to the container only, and all objects within the container with this
            header applied are CORS-enabled for the allowed origin URLs. A browser (user-agent)
            typically issues a preflighted request , which is an OPTIONS call that verifies the origin
            is allowed to make the request. The Object Storage service returns 200 if the originating
            URL is listed in this header parameter, and issues a 401 if the originating URL is not
            allowed to make a cross-origin request. Once a 200 is returned, the browser makes a
            second request to the Object Storage service to retrieve the CORS-enabled object.
        :param x_container_meta_access_control_max_age (Optional):     header     string
            Maximum time for the origin to hold the preflight results. A browser may make an OPTIONS
            call to verify the origin is allowed to make the request. Set the value to an integer
            number of seconds after the time that the request was received.
        :param x_container_meta_access_control_expose_headers (Optional):     header     string
            Headers the Object Storage service exposes to the browser (technically, through the
            user-agent setting), in the request response, separated by spaces. By default the Object
            Storage service returns the following headers:
            All "simple response headers" as listed on http://www.w3.org/TR/cors/#simple-response-header.
            The headers etag, x-timestamp, x-trans-id, x-openstack-request-id.
            All metadata headers (X-Container-Meta-* for containers and X-Object-Meta-* for objects).
            headers listed in X-Container-Meta-Access-Control-Expose-Headers.
        :param x_container_meta_quota_bytes (Optional):     header     string
            Sets maximum size of the container, in bytes. Typically these values are set by an
            administrator. Returns a 413 response (request entity too large) when an object PUT
            operation exceeds this quota value. This value does not take effect immediately. see
            Container Quotas for more information.
        :param x_container_meta_quota_count (Optional):     header     string     Sets maximum
            object count of the container. Typically these values are set by an administrator. Returns
            a 413 response (request entity too large) when an object PUT operation exceeds this quota
            value. This value does not take effect immediately. see Container Quotas for more information.
        :param x_container_meta_web_directory_typ (Optional):header     string     Sets the
            content-type of directory marker objects. If the header is not set, default is
            application/directory. Directory marker objects are 0-byte objects that represent
            directories to create a simulated hierarchical structure. For example, if you set
            "X-Container- Meta-Web-Directory-Type: text/directory", Object Storage treats 0-byte
            objects with a content-type of text/directory as directories rather than objects.
        :param x_container_meta_temp_url_key (Optional):     header     string     The secret
            key value for temporary URLs.
        :param  x_container_meta_temp_url_key_2 (Optional):     header     string     A second
            secret key value for temporary URLs. The second key enables you to rotate keys by
            having two active keys at the same time.
        :param x_trans_id_extra (Optional): header  string     Extra transaction information.
            Use the X-Trans-Id-Extra request header to include extra information to help you
            debug any errors that might occur with large object upload and other Object Storage
            transactions. The server appends the first 32 characters of the X-Trans-Id-Extra
            request header value to the transaction ID value in the generated X-Trans-Id response
            header. You must UTF-8-encode and then URL-encode the extra transaction information
            before you include it in the X-Trans-Id-Extra request header. For example, you can
            include extra transaction information when you upload large objects such as images.
            When you upload each segment and the manifest, include the same value in the
            X-Trans-Id-Extra request header. If an error occurs, you can find all requests that
            are related to the large object upload in the Object Storage logs. You can also use
            X-Trans-Id-Extra strings to help operators debug requests that fail to receive responses.
            The operator can search for the extra information in the logs.
        :param x_storage_policy (Optional):     header     string     In requests, specifies the
            name of the storage policy to use for the container. In responses, is the storage policy
            name. The storage policy of the container cannot be changed.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return dictionary with lowercase header key containing also a 'resp-code' key with the
            response code that must be 204 if success.
            ex:
             {
               'date':'Tue, 06 Dec 2016 11:16:31 GMT',
               'content-length':'0',
               'resp-code':204,
               'content-type':'text/html; charset=UTF-8',
               'x-trans-id':'tx827ed9c263d34b07bebc4-0058469e0f'
            }
        """
        headers = {}
        if container is not None:
            path = "/%s" % container
        else:
            path = ""
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if x_container_read is not None:
            headers["X-Container-Read"] = x_container_read
        if x_remove_container_name is not None:
            headers["X-Remove-Container-name "] = x_container_read
        if x_container_write is not None:
            headers["X-Container-Write"] = x_container_write
        if x_container_sync_to is not None:
            headers["X-Container-Sync-To"] = x_container_sync_to
        if x_container_sync_key is not None:
            headers["X-Container-Sync-Key"] = x_container_sync_key
        if x_versions_location is not None:
            headers["X-Versions-Location"] = x_versions_location
        if x_history_location is not None:
            headers["X-History-Location"] = x_history_location
        if x_remove_versions_location is not None:
            headers["X-Remove-Versions-Location"] = x_remove_versions_location
        if x_remove_history_location is not None:
            headers["X-Remove-History-Location"] = x_remove_history_location
        if x_container_meta_name is not None:
            for key in x_container_meta_name:
                headers["X-Container-Meta-%s" % key] = x_container_meta_name[key]
        if x_container_meta_access_control_allow_origin is not None:
            headers["X-Container-Meta-Access-Control-Allow-Origin "] = x_container_meta_access_control_allow_origin
        if x_container_meta_access_control_max_age is not None:
            headers["X-Container-Meta-Access-Control-Max-Age"] = x_container_meta_access_control_max_age
        if x_container_meta_access_control_expose_headers is not None:
            headers["X-Container-Meta-Access-Control-Expose-Headers"] = x_container_meta_access_control_expose_headers
        if x_container_meta_quota_bytes is not None:
            headers["X-Container-Meta-Quota-Bytes"] = x_container_meta_quota_bytes
        if x_container_meta_quota_count is not None:
            headers["X-Container-Meta-Quota-Count"] = x_container_meta_quota_count
        if x_container_meta_web_directory_type is not None:
            headers["X-Container-Meta-Web-Directory-Type"] = x_container_meta_web_directory_type
        if x_container_meta_temp_url_key is not None:
            headers["X-Container-Meta-Temp-URL-Key"] = x_container_meta_temp_url_key
        if x_container_meta_temp_url_key_2 is not None:
            headers["X-Container-Meta-Temp-URL-Key-2"] = x_container_meta_temp_url_key_2
        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra
        if x_storage_policy is not None:
            headers["X-Storage-Policy"] = x_storage_policy

        res = self.client.call(path, "POST", data="", headers=headers, token=self.manager.identity.token)
        self.logger.debug("Openstack swift container headers %s modify: %s" % (jsonDumps(headers), truncate(res[0])))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        result["resp-code"] = res[2]
        return result

    @setup_client
    def container_metadata_get(
        self,
        container=None,
        x_auth_token=None,
        x_service_token=None,
        x_newest=None,
        x_trans_id_extra=None,
    ):
        """Show container metadata.

        :info Shows container metadata, including the number of objects and the total bytes
            of all objects stored in the container.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param x_newest (Optional):     header     boolean     If set to true , Object
            Storage queries all replicas to return the most recent one. If you omit this
            header, Object Storage responds faster after it finds one valid replica.
            Because setting this header to true is more expensive for the back end, use
            it only when it is absolutely needed.
        :param x_trans_id_extra (Optional): header  string     Extra transaction information.
            Use the X-Trans-Id-Extra request header to include extra information to help you
            debug any errors that might occur with large object upload and other Object Storage
            transactions. The server appends the first 32 characters of the X-Trans-Id-Extra
            request header value to the transaction ID value in the generated X-Trans-Id response
            header. You must UTF-8-encode and then URL-encode the extra transaction information
            before you include it in the X-Trans-Id-Extra request header. For example, you can
            include extra transaction information when you upload large objects such as images.
            When you upload each segment and the manifest, include the same value in the
            X-Trans-Id-Extra request header. If an error occurs, you can find all requests that
            are related to the large object upload in the Object Storage logs. You can also use
            X-Trans-Id-Extra strings to help operators debug requests that fail to receive responses.
            The operator can search for the extra information in the logs.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return a dictionary with lowercase header key
        ex.

        {
           "content-length":"0",
           "x-container-object-count":"0",
           "accept-ranges":"bytes",
           "x-storage-policy":"Policy-0",
           "x-container-bytes-used":"0",
           "x-timestamp":"1481039613.06786",
           "x-container-meta-meta1":"container_metadata_post",
           "x-trans-id":"tx1a0d166b0e5b45ef8e33f-0058480c52",
           "date":"Wed, 07 Dec 2016 13:19:14 GMT",
           "content-type":"text\/plain; charset=utf-8"
        }
        """
        headers = {}
        if container is not None:
            path = "/%s" % container
        else:
            path = ""
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if x_newest is not None:
            headers["X-Newest"] = x_newest
        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra

        res = self.client.call(path, "HEAD", data="", headers=headers, token=self.manager.identity.token)
        self.logger.debug("Show container metadata: %s" % truncate(res[0]))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        return result

    @setup_client
    def object_get(
        self,
        container=None,
        c_object=None,
        x_auth_token=None,
        x_service_token=None,
        x_newest=None,
        temp_url_sig=None,
        temp_url_expires=None,
        filename=None,
        multipart_manifest=None,
        content_range=None,
        if_match=None,
        if_none_match=None,
        if_modified_since=None,
        if_unmodified_since=None,
        x_trans_id_extra=None,
    ):
        """Get object content and metadata

        :info Downloads the object content and gets the object metadata.
            This operation returns the object metadata in the response headers and the object
            content in the response body.
            If this is a large object, the response body contains the concatenated content of the
            segment objects. To get the manifest instead of concatenated segment objects for a static
            large object, use the multipart-manifest query parameter.
        :param container (Optional):     path     string     The unique (within an account)
            name for the container. The container name must be from 1 to 256 characters long
            and can start with any character and contain any pattern. Character set must be UTF-8.
            The container name cannot contain a slash (/) character because this character delimits
            the container and object name. For example, the path /v1/account/www/pages specifies the
            www container, not the www/pages container.
        :param c_object (Optional):     query     string     The unique name for the object.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param x_newest (Optional):     header     boolean     If set to true , Object
            Storage queries all replicas to return the most recent one. If you omit this
            header, Object Storage responds faster after it finds one valid replica.
            Because setting this header to true is more expensive for the back end, use
            it only when it is absolutely needed.
        :param temp_url_sig :     query     string     Used with temporary URLs to sign the
            request with an HMAC-SHA1 cryptographic signature that defines the allowed HTTP
            method, expiration date, full path to the object, and the secret key for the temporary
            URL. For more information about temporary URLs, see Temporary URL middleware.
        :param temp_url_expires :     query     integer     The date and time in UNIX Epoch time
            stamp format when the signature for temporary URLs expires. For example,
            1440619048 is equivalent to Mon, Wed, 26 Aug 2015 19:57:28 GMT. For more information
            about temporary URLs, see Temporary URL middleware.
        :param filename (Optional):     query     string     Overrides the default file name.
            Object Storage generates a default file name for GET temporary URLs that is based
            on the object name. Object Storage returns this value in the Content-Disposition
            response header. Browsers can interpret this file name value as a file attachment
            to save. For more information about temporary URLs, see Temporary URL middleware.
        :param multipart_manifest (Optional):     query     string     If you include the
            multipart-manifest=get query parameter and the object is a large object, the object
            contents are not returned. Instead, the manifest is returned in the X-Object-Manifest
            response header for dynamic large objects or in the response body for static large
            objects.
        :param content_range (Optional):     header     string     The ranges of content to get. You
            can use the Range header to get portions of data by using one or more range specifications.
            To specify many ranges, separate the range specifications with a comma. The types of
            range specifications are: - Byte range specification. Use FIRST_BYTE_OFFSET to specify
            the start of the data range, and LAST_BYTE_OFFSET to specify the end. You can omit the
            LAST_BYTE_OFFSET and if you do, the value defaults to the offset of the last byte of data.
            - Suffix byte range specification. Use LENGTH bytes to specify the length of the data range.
            The following forms of the header specify the following ranges of data:
                Range: bytes=-5. The last five bytes.
                Range: bytes=10-15. The six bytes of data after a 10-byte offset.
                Range: bytes=10-15,-5. A multi-part response that contains the last five bytes and the
                    six bytes of data after a 10-byte offset. The Content-Type response header contains
                     multipart/byteranges.
                Range: bytes=4-6. Bytes 4 to 6 inclusive.
                Range: bytes=2-2. Byte 2, the third byte of the data.
                Range: bytes=6-. Byte 6 and after.
                Range: bytes=1-3,2-5. A multi-part response that contains bytes 1 to 3 inclusive, and
                    bytes 2 to 5 inclusive. The Content-Type response header contains multipart/byteranges.

        :param if_match (Optional):     header     string  Verify if a entity matches.
        :param if_none_match (Optional):     header     string     A client that has one or more entities
            previously obtained from the resource can verify that none of those entities is current by
            including a list of their associated entity tags in the If-None-Match header field.
        :param if_modified_since (Optional):     header     string Verify if a entity has been modified
            since the data.
        :param if_unmodified_since (Optional):     header     string Verify if a entity has not
            been modified since the data.
        :param x_trans_id_extra (Optional):     header     string     Extra transaction
            information. Use the x_trans_id_extra request header to include extra
            information to help you debug any errors that might occur with large object
            upload and other Object Storage transactions. The server appends the first 32
            characters of the x_trans_id_extra request header value to the transaction ID
            value in the generated XTransId response header. You must UTF8encode and
            then URLencode the extra transaction information before you include it in
            the x_trans_id_extra request header. For example, you can include extra
            transaction information when you upload large objects such as images. When
            you upload each segment and the manifest, include the same value in the
            x_trans_id_extra request header. If an error occurs, you can find all
            requests that are related to the large object upload in the Object Storage
            logs. You can also use x_trans_id_extra strings to help operators debug
            requests that fail to receive responses. The operator can search for the
            extra information in the logs.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return List containing a list of dictionary for the body and a dictionary for the header
            ex:
            [
               [

                  {
                     "bytes":108,
                     "last_modified":"2016-03-17T15:51:10.869220",
                     "hash":"d3b6e5736a3d22aa4c933860deea7885",
                     "name":"s3ql_seq_no_1",
                     "content_type":"application\/octet-stream"
                  },
                  {
                     "bytes":108,
                     "last_modified":"2016-03-17T15:51:58.590460",
                     "hash":"ee27455b1dbc170b8a6d0d91009bbd76",
                     "name":"s3ql_seq_no_2",
                     "content_type":"application\/octet-stream"
                  },
                  {
                     "bytes":108,
                     "last_modified":"2016-03-18T08:21:59.964870",
                     "hash":"8f94d10825b1e96afa381059ecf2a253",
                     "name":"s3ql_seq_no_3",
                     "content_type":"application\/octet-stream"
                  },
                  ...
               ],
               {
                  "content-length":"9433",
                  "x-container-object-count":"52",
                  "accept-ranges":"bytes",
                  "x-storage-policy":"Policy-0",
                  "x-container-bytes-used":"352706235",
                  "x-timestamp":"1458229823.08452",
                  "x-trans-id":"tx48414dc585d1476bb82c6-005846c317",
                  "date":"Tue, 06 Dec 2016 13:54:31 GMT",
                  "content-type":"application\/json; charset=utf-8"
               }
            ]
        """
        query = {}
        headers = {}
        if container is not None and c_object is not None:
            path = "/%s/%s" % (container, c_object)
        else:
            path = "//"  # so that raises an error
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if x_newest is not None:
            headers["X-Newest"] = x_newest
        if temp_url_sig is not None:
            query["temp_url_sig"] = temp_url_sig
        if temp_url_expires is not None:
            query["temp_url_expires"] = temp_url_expires
        if filename is not None:
            query["filename"] = filename
        if multipart_manifest is not None:
            query["multipart-manifest"] = multipart_manifest
        if content_range is not None:
            query["Range"] = content_range
        if if_match is not None:
            headers["If-Match "] = if_match
        if if_none_match is not None:
            headers["If-None-Match"] = if_none_match
        if if_modified_since is not None:
            headers["If-Modified-Since"] = if_modified_since
        if if_unmodified_since is not None:
            headers["If-Unmodified-Since"] = if_unmodified_since
        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra

        if len(query) > 0:
            path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "GET", data="", headers=headers, token=self.manager.identity.token)
        self.logger.debug("Openstack swift info: %s" % truncate(res[0]))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        r = [res[0]]
        r.append(result)
        return r

    @setup_client
    def object_put(
        self,
        container=None,
        c_object=None,
        x_auth_token=None,
        x_service_token=None,
        temp_url_sig=None,
        temp_url_expires=None,
        x_object_manifest=None,
        multipart_manifest=None,
        content_lengt=None,
        transfer_encoding=None,
        content_type=None,
        x_detect_content_type=None,
        x_copy_from=None,
        etag=None,
        content_disposition=None,
        content_encoding=None,
        x_delete_at=None,
        x_delete_after=None,
        x_object_meta_name=None,
        if_none_match=None,
        x_trans_id_extra=None,
        data="",
    ):
        """Put object content and metadata

        :info Creates an object with data content and metadata, or replaces an existing
            object with data content and metadata.
            The PUT operation always creates an object. If you use this operation on an
            existing object, you replace the existing object and metadata rather than modifying
            the object. Consequently, this operation returns the Created (201) response code.
            If you use this operation to copy a manifest object, the new object is a normal
            object and not a copy of the manifest. Instead it is a concatenation of all the segment
            objects. This means that you cannot copy objects larger than 5 GB.
        :param container (Optional):     path     string     The unique (within an account)
            name for the container. The container name must be from 1 to 256 characters long
            and can start with any character and contain any pattern. Character set must be UTF-8.
            The container name cannot contain a slash (/) character because this character delimits
            the container and object name. For example, the path /v1/account/www/pages specifies the
            www container, not the www/pages container.
        :param c_object (Optional):     query     string     The unique name for the object.
        :param multipart_manifest (Optional):     query     string     If you include the
            multipart-manifest=put query parameter, the object is a static large object manifest
            and the body contains the manifest.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param temp_url_sig :     query     string     Used with temporary URLs to sign the
            request with an HMAC-SHA1 cryptographic signature that defines the allowed HTTP
            method, expiration date, full path to the object, and the secret key for the temporary
            URL. For more information about temporary URLs, see Temporary URL middleware.
        :param temp_url_expires :     query     integer     The date and time in UNIX Epoch time
            stamp format when the signature for temporary URLs expires. For example,
            1440619048 is equivalent to Mon, Wed, 26 Aug 2015 19:57:28 GMT. For more information
            about temporary URLs, see Temporary URL middleware.
        :param x_object_manifest (Optional):     header     string     Set to specify that this is a
            dynamic large object manifest object. The value is the container and object name prefix
            of the segment objects in the form container/prefix. You must UTF-8-encode and then URL-encode
            the names of the container and prefix before you include them in this header.
        :param content_length (Optional):     header     integer     Set to the length of the object
            content (i.e. the length in bytes of the request body). Do not set if chunked transfer
            encoding is being used.
        :param transfer_encoding (Optional):     header     string     Set to chunked to enable
            chunked transfer encoding. If used, do not set the Content-Length header to a non-zero value.
        :param content_type (Optional):     header     string     Sets the MIME type for the object.
        :param x_detect_content_type (Optional):     header     boolean     If set to true, Object
            Storage guesses the content type based on the file extension and ignores the value sent
            in the Content-Type header, if present.
        :param x_copy_from (Optional):     header     string     If set, this is the name of an
            object used to create the new object by copying the X-Copy-From object. The value is
            in form {container}/{object}. You must UTF-8-encode and then URL-encode the names of
            the container and object before you include them in the header. Using PUT with
            X-Copy-From has the same effect as using the COPY operation to copy an object.
            Using Range header with X-Copy-From will create a new partial copied object with
            bytes set by Range.
        :param etag (Optional):     header     string     The MD5 checksum value of the request
            body. For example, the MD5 checksum value of the object content. You are strongly
            recommended to compute the MD5 checksum value of object content and include it
            in the request. This enables the Object Storage API to check the integrity of
            the upload. The value is not quoted.
        :param content_disposition (Optional):     header     string     If set, specifies
            the override behavior for the browser. For example, this header might specify
            that the browser use a download program to save this file rather than show the
            file, which is the default.
        :param content_encoding (Optional):     header     string     If set, the value of
            the Content-Encoding metadata.
        :param x_delete_at (Optional)     header     integer     The date and time in UNIX
            Epoch time stamp format when the system removes the object. For example,
            1440619048 is equivalent to Mon, Wed, 26 Aug 2015 19:57:28 GMT.
        :param x_delete_after (Optional)     header     integer     The number of seconds
            after which the system removes the object. Internally, the Object Storage
            system stores this value in the X-Delete-At metadata item.
        :param x_object_meta_name (Optional)     header     string     The object metadata,
            where name is the name of the metadata item. You must specify an X-Object-Meta-name
            header for each metadata name item that you want to add or update.
        :param if_none_match (Optional):     header     string     In combination with Expect: 100-Continue,
            specify an "If-None-Match: *" header to query whether the server already has a copy of the
            object before any data is sent.
        :param x_trans_id_extra (Optional):     header     string     Extra transaction
            information. Use the x_trans_id_extra request header to include extra
            information to help you debug any errors that might occur with large object
            upload and other Object Storage transactions. The server appends the first 32
            characters of the x_trans_id_extra request header value to the transaction ID
            value in the generated XTransId response header. You must UTF8encode and
            then URLencode the extra transaction information before you include it in
            the x_trans_id_extra request header. For example, you can include extra
            transaction information when you upload large objects such as images. When
            you upload each segment and the manifest, include the same value in the
            x_trans_id_extra request header. If an error occurs, you can find all
            requests that are related to the large object upload in the Object Storage
            logs. You can also use x_trans_id_extra strings to help operators debug
            requests that fail to receive responses. The operator can search for the
            extra information in the logs.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return List containing a list of dictionary for the body and a dictionary for the header
            ex:
            {
               "content-length":"0",
               "resp-code":201,
               "last-modified":"Thu, 15 Dec 2016 09:22:35 GMT",
               "etag":"d41d8cd98f00b204e9800998ecf8427e",
               "x-trans-id":"tx81d4b804da094190be852-00585260da",
               "date":"Thu, 15 Dec 2016 09:22:34 GMT",
               "content-type":"text\/html; charset=UTF-8"
            }
        """
        query = {}
        headers = {}
        if container is not None and c_object is not None:
            path = "/%s/%s" % (container, c_object)
        else:
            path = "//"  # so that raises an error
        if temp_url_sig is not None:
            query["temp_url_sig"] = temp_url_sig
        if temp_url_expires is not None:
            query["temp_url_expires"] = temp_url_expires
        if multipart_manifest is not None:
            query["multipart-manifest"] = multipart_manifest
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if x_object_manifest is not None:
            headers["X-Object-Manifest"] = x_object_manifest
        if content_lengt is not None:
            headers["Content-Length"] = content_lengt
        if transfer_encoding is not None:
            headers["Transfer-Encoding"] = transfer_encoding
        if content_type is not None:
            headers["Content-Type  "] = content_type
        if x_detect_content_type is not None:
            headers["X-Detect-Content-Type"] = x_detect_content_type
        if x_copy_from is not None:
            headers["X-Copy-From"] = x_copy_from
        if etag is not None:
            headers["ETag"] = etag
        if content_disposition is not None:
            headers["Content-Disposition"] = content_disposition
        if content_encoding is not None:
            headers["Content-Encoding "] = content_encoding
        if x_delete_at is not None:
            headers["X-Delete-At "] = x_delete_at
        if x_delete_after is not None:
            headers["X-Delete-After "] = x_delete_after
        if x_object_meta_name is not None:
            headers["X-Object-Meta-name "] = x_object_meta_name
        if if_none_match is not None:
            headers["If-None-Match"] = if_none_match
        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra

        if len(query) > 0:
            path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "PUT", data=data, headers=headers, token=self.manager.identity.token)
        self.logger.debug("Openstack swift put object: %s" % truncate(res[0]))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        result["resp-code"] = res[2]
        return result

    @setup_client
    def object_copy(
        self,
        container=None,
        c_object=None,
        x_auth_token=None,
        x_service_token=None,
        multipart_manifest=None,
        content_lengt=None,
        transfer_encoding=None,
        destination=None,
        destination_account=None,
        x_fresh_metadata=None,
        content_type=None,
        content_disposition=None,
        content_encoding=None,
        x_object_meta_name=None,
        x_trans_id_extra=None,
    ):
        """Copy object content and metadata

        :info Copies an object to another object in the object store.
            You can copy an object to a new object with the same name. Copying to the same
            name is an alternative to using POST to add metadata to an object. With POST, you
            must specify all the metadata. With COPY, you can add additional metadata to the object.
            With COPY, you can set the X-Fresh-Metadata header to true to copy the object without
            any existing metadata.
            Alternatively, you can use PUT with the X-Copy-From request header to accomplish the
            same operation as the COPY object operation.
            The COPY operation always creates an object. If you use this operation on an existing
            object, you replace the existing object and metadata rather than modifying the object.
            Consequently, this operation returns the Created (201) response code.
            Normally, if you use this operation to copy a manifest object, the new object is a normal
            object and not a copy of the manifest. Instead it is a concatenation of all the segment
            objects. This means that you cannot copy objects larger than 5 GB in size.
            To copy the manifest object, you include the multipart-manifest=get query string in the
            COPY request. The new object contains the same manifest as the original. The segment
            objects are not copied. Instead, both the original and new manifest objects share the
            same set of segment objects.
            All metadata is preserved during the object copy. If you specify metadata on the request
            to copy the object, either PUT or COPY , the metadata overwrites any conflicting keys
            on the target (new) object.
        :param container (Optional):     path     string     The unique (within an account)
            name for the container. The container name must be from 1 to 256 characters long
            and can start with any character and contain any pattern. Character set must be UTF-8.
            The container name cannot contain a slash (/) character because this character delimits
            the container and object name. For example, the path /v1/account/www/pages specifies the
            www container, not the www/pages container.
        :param c_object (Optional):     query     string     The unique name for the object.
        :param multipart_manifest (Optional):     query     string     If you include the
            multipart-manifest=put query parameter, the object is a static large object manifest
            and the body contains the manifest.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param destination :     header     string     The container and object name of the
            destination object in the form of /container/object. You must UTF-8-encode and then
            URL-encode the names of the destination container and object before you include them
            in this header.
        :param destination_account (Optional):     header     string     Specifies the account name where
            the object is copied to. If not specified, the object is copied to the account which
            owns the object (i.e., the account in the path).
        :param content_type (Optional):     header     string     Sets the MIME type for the object.
        :param content_encoding (Optional):     header     string     If set, the value of
            the Content-Encoding metadata.
        :param content_disposition (Optional):     header     string     If set, specifies
            the override behavior for the browser. For example, this header might specify
            that the browser use a download program to save this file rather than show
            the file, which is the default.
        :param x_object_meta_name (Optional):     header     string     The object metadata,
            where name is the name of the metadata item. You must specify an X-Object-Meta-name
            header for each metadata name item that you want to add or update.
        :param X-Fresh-Metadata (Optional):     header     boolean     Enables object
            creation that omits existing user metadata. If set to true, the COPY request
            creates an object without existing user metadata. Default value is false.
        :param x_trans_id_extra (Optional):     header     string     Extra transaction
            information. Use the x_trans_id_extra request header to include extra
            information to help you debug any errors that might occur with large object
            upload and other Object Storage transactions. The server appends the first 32
            characters of the x_trans_id_extra request header value to the transaction ID
            value in the generated XTransId response header. You must UTF8encode and
            then URLencode the extra transaction information before you include it in
            the x_trans_id_extra request header. For example, you can include extra
            transaction information when you upload large objects such as images. When
            you upload each segment and the manifest, include the same value in the
            x_trans_id_extra request header. If an error occurs, you can find all
            requests that are related to the large object upload in the Object Storage
            logs. You can also use x_trans_id_extra strings to help operators debug
            requests that fail to receive responses. The operator can search for the
            extra information in the logs.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return List containing a list of dictionary for the body and a dictionary for the header
            ex:
            {
               "content-length":"0",
               "resp-code":201,
               "last-modified":"Thu, 15 Dec 2016 09:22:35 GMT",
               "etag":"d41d8cd98f00b204e9800998ecf8427e",
               "x-trans-id":"tx81d4b804da094190be852-00585260da",
               "date":"Thu, 15 Dec 2016 09:22:34 GMT",
               "content-type":"text\/html; charset=UTF-8"
            }
        """
        query = {}
        headers = {}
        if container is not None and c_object is not None:
            path = "/%s/%s" % (container, c_object)
        else:
            path = "//"  # so that raises an error
        if multipart_manifest is not None:
            query["multipart-manifest"] = multipart_manifest
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if content_lengt is not None:
            headers["Content-Length"] = content_lengt
        if transfer_encoding is not None:
            headers["Transfer-Encoding"] = transfer_encoding
        if content_type is not None:
            headers["Content-Type  "] = content_type
        if content_disposition is not None:
            headers["Content-Disposition"] = content_disposition
        if content_encoding is not None:
            headers["Content-Encoding "] = content_encoding
        if x_object_meta_name is not None:
            headers["X-Object-Meta-name "] = x_object_meta_name
        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra
        if destination is not None:
            headers["Destination"] = destination
        if destination_account is not None:
            headers["Destination-Account"] = destination_account
        if x_fresh_metadata is not None:
            headers["X-Fresh-Metadata"] = x_fresh_metadata

        if len(query) > 0:
            path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "COPY", data="", headers=headers, token=self.manager.identity.token)
        self.logger.debug("Openstack swift put object: %s" % truncate(res[0]))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        result["resp-code"] = res[2]
        return result

    @setup_client
    def object_delete(
        self,
        container=None,
        c_object=None,
        x_auth_token=None,
        x_service_token=None,
        multipart_manifest=None,
        x_trans_id_extra=None,
    ):
        """Delete object

        :info Permanently deletes an object from the object store.
            Object deletion occurs immediately at request time. Any subsequent GET, HEAD,
            POST, or DELETE operations will return a 404 Not Found error code.
            For static large object manifests, you can add the ?multipart- manifest=delete
            query parameter. This operation deletes the segment objects and, if all
            deletions succeed, this operation deletes the manifest object.
            An alternative to using the DELETE operation is to use the POST operation
            with the bulk-delete query parameter.
        :param container (Optional):     path     string     The unique (within an account)
            name for the container. The container name must be from 1 to 256 characters long
            and can start with any character and contain any pattern. Character set must be UTF-8.
            The container name cannot contain a slash (/) character because this character delimits
            the container and object name. For example, the path /v1/account/www/pages specifies the
            www container, not the www/pages container.
        :param c_object (Optional):     query     string     The unique name for the object.
        :param multipart_manifest (Optional):     query     string     If you include the
            multipart-manifest=put query parameter, the object is a static large object manifest
            and the body contains the manifest.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param x_trans_id_extra (Optional):     header     string     Extra transaction
            information. Use the x_trans_id_extra request header to include extra
            information to help you debug any errors that might occur with large object
            upload and other Object Storage transactions. The server appends the first 32
            characters of the x_trans_id_extra request header value to the transaction ID
            value in the generated XTransId response header. You must UTF8encode and
            then URLencode the extra transaction information before you include it in
            the x_trans_id_extra request header. For example, you can include extra
            transaction information when you upload large objects such as images. When
            you upload each segment and the manifest, include the same value in the
            x_trans_id_extra request header. If an error occurs, you can find all
            requests that are related to the large object upload in the Object Storage
            logs. You can also use x_trans_id_extra strings to help operators debug
            requests that fail to receive responses. The operator can search for the
            extra information in the logs.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return List containing a list of dictionary for the body and a dictionary for the header
            ex:
            {
               "date":"Wed, 04 Jan 2017 16:51:51 GMT",
               "content-length":"0",
               "content-type":"text\/html; charset=UTF-8",
               "resp-code":204,
               "x-trans-id":"txa0340314131a499faddf0-00586d2827"
            }
        """
        query = {}
        headers = {}
        if container is not None and c_object is not None:
            path = "/%s/%s" % (container, c_object)
        else:
            path = "//"  # so that raises an error
        if multipart_manifest is not None:
            query["multipart-manifest"] = multipart_manifest
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token

        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra

        if len(query) > 0:
            path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "DELETE", data="", headers=headers, token=self.manager.identity.token)
        self.logger.debug("Openstack swift delete object: %s" % truncate(res[0]))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        result["resp-code"] = res[2]
        return result

    @setup_client
    def object_metadata_get(
        self,
        container=None,
        c_object=None,
        x_auth_token=None,
        x_service_token=None,
        x_newest=None,
        temp_url_sig=None,
        temp_url_expires=None,
        filename=None,
        multipart_manifest=None,
        if_match=None,
        if_none_match=None,
        if_modified_since=None,
        if_unmodified_since=None,
        x_trans_id_extra=None,
    ):
        """Shows object metadata.

        :param container (Optional):     path     string     The unique (within an account)
            name for the container. The container name must be from 1 to 256 characters long
            and can start with any character and contain any pattern. Character set must be UTF-8.
            The container name cannot contain a slash (/) character because this character delimits
            the container and object name. For example, the path /v1/account/www/pages specifies the
            www container, not the www/pages container.
        :param c_object (Optional):     query     string     The unique name for the object.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param x_newest (Optional):     header     boolean     If set to true , Object
            Storage queries all replicas to return the most recent one. If you omit this
            header, Object Storage responds faster after it finds one valid replica.
            Because setting this header to true is more expensive for the back end, use
            it only when it is absolutely needed.
        :param temp_url_sig :     query     string     Used with temporary URLs to sign the
            request with an HMAC-SHA1 cryptographic signature that defines the allowed HTTP
            method, expiration date, full path to the object, and the secret key for the temporary
            URL. For more information about temporary URLs, see Temporary URL middleware.
        :param temp_url_expires :     query     integer     The date and time in UNIX Epoch time
            stamp format when the signature for temporary URLs expires. For example,
            1440619048 is equivalent to Mon, Wed, 26 Aug 2015 19:57:28 GMT. For more information
            about temporary URLs, see Temporary URL middleware.
        :param filename (Optional):     query     string     Overrides the default file name.
            Object Storage generates a default file name for GET temporary URLs that is based
            on the object name. Object Storage returns this value in the Content-Disposition
            response header. Browsers can interpret this file name value as a file attachment
            to save. For more information about temporary URLs, see Temporary URL middleware.
        :param multipart_manifest (Optional):     query     string     If you include the
            multipart-manifest=get query parameter and the object is a large object, the object
            contents are not returned. Instead, the manifest is returned in the X-Object-Manifest
            response header for dynamic large objects or in the response body for static large
            objects.
        :param if_match (Optional):     header     string  Verify if a entity matches.
        :param if_none_match (Optional):     header     string     A client that has one or more entities
            previously obtained from the resource can verify that none of those entities is current by
            including a list of their associated entity tags in the If-None-Match header field.
        :param if_modified_since (Optional):     header     string Verify if a entity has been modified
            since the data.
        :param if_unmodified_since (Optional):     header     string Verify if a entity has not
            been modified since the data.
        :param x_trans_id_extra (Optional):     header     string     Extra transaction
            information. Use the x_trans_id_extra request header to include extra
            information to help you debug any errors that might occur with large object
            upload and other Object Storage transactions. The server appends the first 32
            characters of the x_trans_id_extra request header value to the transaction ID
            value in the generated XTransId response header. You must UTF8encode and
            then URLencode the extra transaction information before you include it in
            the x_trans_id_extra request header. For example, you can include extra
            transaction information when you upload large objects such as images. When
            you upload each segment and the manifest, include the same value in the
            x_trans_id_extra request header. If an error occurs, you can find all
            requests that are related to the large object upload in the Object Storage
            logs. You can also use x_trans_id_extra strings to help operators debug
            requests that fail to receive responses. The operator can search for the
            extra information in the logs.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return A dictionary with the object header
            ex:
            {
               "content-length":"10",
               "resp-code":200,
               "accept-ranges":"bytes",
               "last-modified":"Thu, 05 Jan 2017 09:36:42 GMT",
               "etag":"e1871fb9aabe5901031fec957c8aee6d",
               "x-timestamp":"1483609001.31817",
               "x-trans-id":"txda20f8d06f06441194b41-00586e180b",
               "date":"Thu, 05 Jan 2017 09:55:23 GMT",
               "content-type":"application\/json"
            }
        """
        query = {}
        headers = {}
        if container is not None and c_object is not None:
            path = "/%s/%s" % (container, c_object)
        else:
            path = "//"  # so that raises an error
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if x_newest is not None:
            headers["X-Newest"] = x_newest
        if temp_url_sig is not None:
            query["temp_url_sig"] = temp_url_sig
        if temp_url_expires is not None:
            query["temp_url_expires"] = temp_url_expires
        if filename is not None:
            query["filename"] = filename
        if multipart_manifest is not None:
            query["multipart-manifest"] = multipart_manifest
        if if_match is not None:
            headers["If-Match "] = if_match
        if if_none_match is not None:
            headers["If-None-Match"] = if_none_match
        if if_modified_since is not None:
            headers["If-Modified-Since"] = if_modified_since
        if if_unmodified_since is not None:
            headers["If-Unmodified-Since"] = if_unmodified_since
        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra

        if len(query) > 0:
            path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "HEAD", data="", headers=headers, token=self.manager.identity.token)
        self.logger.debug("Openstack swift get metadata object: %s" % truncate(res[0]))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        result["resp-code"] = res[2]
        return result

    @setup_client
    def object_metadata_post(
        self,
        container=None,
        c_object=None,
        bulk_delete=None,
        extract_archive=None,
        x_auth_token=None,
        x_service_token=None,
        content_type=None,
        content_disposition=None,
        content_encoding=None,
        x_delete_at=None,
        x_delete_after=None,
        x_object_meta_name=None,
        x_trans_id_extra=None,
    ):
        """Put object content and metadata

        :info Creates an object with data content and metadata, or replaces an existing
            object with data content and metadata.
            The PUT operation always creates an object. If you use this operation on an
            existing object, you replace the existing object and metadata rather than modifying
            the object. Consequently, this operation returns the Created (201) response code.
            If you use this operation to copy a manifest object, the new object is a normal
            object and not a copy of the manifest. Instead it is a concatenation of all the segment
            objects. This means that you cannot copy objects larger than 5 GB.
        :param container (Optional):     path     string     The unique (within an account)
            name for the container. The container name must be from 1 to 256 characters long
            and can start with any character and contain any pattern. Character set must be UTF-8.
            The container name cannot contain a slash (/) character because this character delimits
            the container and object name. For example, the path /v1/account/www/pages specifies the
            www container, not the www/pages container.
        :param c_object (Optional):     query     string     The unique name for the object.
        :param bulk_delete (Optional):    query     string     When the bulk-delete query parameter
            is present in the POST request, multiple objects or containers can be deleted with
            a single request. See Bulk Delete for how this feature is used.
        :param extract_archive (Optional):      query     string     When the extract-archive
            query parameter is present in the POST request, an archive (tar file) is uploaded
            and extracted to create multiple objects. See Extract Archive for how this feature is used.
        :param x_auth_token (Optional):     header     string     Authentication token. If you
            omit this header, your request fails unless the account owner has granted
            you access through an access control list (ACL).
        :param x_service_token (Optional):     header     string     A service token. See
            OpenStack Service Using Composite Tokens for more information.
        :param content_length (Optional):     header     integer     Set to the length of the object
            content (i.e. the length in bytes of the request body). Do not set if chunked transfer
            encoding is being used.
        :param content_type (Optional):     header     string     Sets the MIME type for the object.
        :param content_disposition (Optional):     header     string     If set, specifies
            the override behavior for the browser. For example, this header might specify
            that the browser use a download program to save this file rather than show the
            file, which is the default.
        :param content_encoding (Optional):     header     string     If set, the value of
            the Content-Encoding metadata.
        :param x_delete_at (Optional)     header     integer     The date and time in UNIX
            Epoch time stamp format when the system removes the object. For example,
            1440619048 is equivalent to Mon, Wed, 26 Aug 2015 19:57:28 GMT.
        :param x_delete_after (Optional)     header     integer     The number of seconds
            after which the system removes the object. Internally, the Object Storage
            system stores this value in the X-Delete-At metadata item.
        :param x_object_meta_name (Optional)     header     string     The object metadata,
            where name is the name of the metadata item. You must specify an X-Object-Meta-name
            header for each metadata name item that you want to add or update.
        :param x_trans_id_extra (Optional):     header     string     Extra transaction
            information. Use the x_trans_id_extra request header to include extra
            information to help you debug any errors that might occur with large object
            upload and other Object Storage transactions. The server appends the first 32
            characters of the x_trans_id_extra request header value to the transaction ID
            value in the generated XTransId response header. You must UTF8encode and
            then URLencode the extra transaction information before you include it in
            the x_trans_id_extra request header. For example, you can include extra
            transaction information when you upload large objects such as images. When
            you upload each segment and the manifest, include the same value in the
            x_trans_id_extra request header. If an error occurs, you can find all
            requests that are related to the large object upload in the Object Storage
            logs. You can also use x_trans_id_extra strings to help operators debug
            requests that fail to receive responses. The operator can search for the
            extra information in the logs.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return Dictionary with header
            ex:
            {
               "date":"Thu, 05 Jan 2017 10:15:25 GMT",
               "content-length":"76",
               "content-type":"text\/html; charset=UTF-8",
               "resp-code":202,
               "x-trans-id":"tx1e5f26d423c24aa99e116-00586e1cbc"
            }
        """
        query = {}
        headers = {}
        if container is not None and c_object is not None:
            path = "/%s/%s" % (container, c_object)
        else:
            path = "//"  # so that raises an error
        if bulk_delete is not None:
            query["bulk-delete"] = bulk_delete
        if extract_archive is not None:
            query["extract-archive"] = extract_archive
        if x_auth_token is not None:
            headers["X-Auth-Token"] = x_auth_token
        if x_service_token is not None:
            headers["X-Service-Token"] = x_service_token
        if content_type is not None:
            headers["Content-Type  "] = content_type
        if content_disposition is not None:
            headers["Content-Disposition"] = content_disposition
        if content_encoding is not None:
            headers["Content-Encoding "] = content_encoding
        if x_delete_at is not None:
            headers["X-Delete-At "] = x_delete_at
        if x_delete_after is not None:
            headers["X-Delete-After "] = x_delete_after
        if x_object_meta_name is not None:
            headers["X-Object-Meta-name "] = x_object_meta_name
        if x_trans_id_extra is not None:
            headers["X-Trans-Id-Extra"] = x_trans_id_extra

        if len(query) > 0:
            path = "%s?%s" % (path, urlencode(query))
        res = self.client.call(path, "POST", data="", headers=headers, token=self.manager.identity.token)
        self.logger.debug("Openstack swift put object: %s" % truncate(res[0]))
        result = {}
        for item in res[1]:
            result[item[0]] = item[1]
        result["resp-code"] = res[2]
        return result

    def generate_key(self, container=None, key=None):
        """Generate key for temporary URLs

        :raises OpenstackError: raise :class:`.OpenstackError`
        :return string with the key
        """
        if key is None:
            key = str(uuid4())[:32]
        if container is None:
            res = self.account_metadata_post(x_account_meta_temp_url_key=key)
            self.logger.debug("Generating key for account")
        else:
            res = self.container_metadata_post(container=container, x_container_meta_temp_url_key=key)
            self.logger.debug('Generating key for container "%s"' % container)
        if str(res["resp-code"]) == "204":
            return key
        else:
            raise Exception("ERROR in key generation")

    def generate_temp_url(self, container=None, c_object=None, timeout=3600, method=None, key=None):
        """Generate object content and metadata

        :raises OpenstackError: raise :class:`.OpenstackError`
        :return string with full temp url signed
        """
        if container is None:
            container = "signaling"  # 1
        if c_object is None:
            c_object = str(uuid4())  # 2

        version = self.uri.split("/")[3]
        project = self.uri.split("/")[4]
        path = "/%s/%s/%s/%s" % (version, project, container, c_object)
        self.logger.debug("Path to be authorized %s" % path)

        expires = int(time()) + int(timeout)

        standard_methods = ["GET", "PUT", "HEAD", "POST", "DELETE"]
        if method.upper() not in standard_methods:
            self.logger.warning(
                "Non default HTTP method %s for tempurl specified, possibly an error",
                method.upper(),
            )

        hmac_body = "%s\n%s\n%s" % (method.upper(), str(expires), path)
        sig = hmacnew(key, hmac_body, sha1).hexdigest()

        path_full = "/%s/%s" % (container, c_object)
        path_full = "{}?temp_url_sig={}&temp_url_expires={}".format(path_full, sig, expires)
        temp_url = "%s%s" % (self.uri, path_full)
        return temp_url
