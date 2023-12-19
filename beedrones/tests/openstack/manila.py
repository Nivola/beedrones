# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

import json
import random
from time import sleep
import os
from beedrones.tests.test_util import BeedronesTestCase, runtest
from beedrones.tests.openstack.client import OpenstackClientTestCase
from beecell.simple import id_gen

share_id = None

tests = [
    "test_authorize",
    "test_ping",
    "test_limits",
    "test_services",
    "test_list_shares",
    "test_get_share",
    "test_add_share",
    "test_update_share",
    "test_grant_access",
    "test_list_access",
    "test_revoke_access",
    "test_reset_status",
    "test_extend",
    "test_shrink",
    ## 'test_unmanage',
    ## 'test_revert',
    "test_delete_share",
    ## 'test_delete_share_force',
    ## 'test_list_share_snapshots',
    ## 'test_get_share_snapshot',
    ## 'test_add_share_snapshot',
    ## 'test_update_share_snapshot',
    ## 'test_delete_share_snapshot',
    ## 'test_manage_share_snapshot',
    ## 'test_unmanage_share_snapshot',
    ## 'test_reset_status_share_snapshot',
    ## 'test_delete_share_force_share_snapshot',
    "test_list_share_types",
    "test_get_share_type",
    "test_get_share_type_extra_spec",
    ## 'test_list_default_share_types',
    ## 'test_get_share_type_access',
    ## 'test_add_share_type',
    ## 'test_add_share_type_extra_specs',
    ## 'test_add_share_type_access',
    ## 'test_delete_share_type_access',
    ## 'test_delete_share_type',
    ## 'test_list_stoarge_pool',
    ## 'test_get_quota_set',
    ## 'test_get_quota_set_default',
    ## 'test_update_quota_set',
    ## 'test_delete_quota_set',
    ## 'test_list_security_services',
    ## 'test_get_security_service',
    ## 'test_add_share_security_service',
    ## 'test_update_share_security_service',
    ## 'test_delete_share_security_service',
]

oid = None
name = None
tenant = None


class OpenstackManilaTestCase(OpenstackClientTestCase):
    @classmethod
    def setUpClass(cls):
        OpenstackClientTestCase.setUpClass()
        cls.test_files_path = os.path.abspath(OpenstackManilaTestCase.__module__).replace("__main__", "hot")

        cls.tenant_id = "5588f12c725148db81a46e35f874fe61"

    def test_ping(self):
        res = self.client.manila.api()
        self.logger.debug(res)

    def test_limits(self):
        res = self.client.manila.limits()
        self.logger.debug(res)

    def test_services(self):
        res = self.client.manila.services()
        self.logger.debug(res)

    #
    # shares
    #
    def share_status(self, share, accepted_status=None):
        if accepted_status is None:
            accepted_status = ["available", "error"]
        status = self.client.manila.share.get(share)["status"]
        while status not in accepted_status:
            sleep(2)
            status = self.client.manila.share.get(share)["status"]

    def test_list_shares(self):
        global share_id
        res = self.client.manila.share.list()
        self.logger.debug(res)
        share_id = res[0]["id"]

    def test_get_share(self):
        global share_id
        res = self.client.manila.share.get(share_id)
        self.logger.debug(res)

    def test_get_share_export_locations(self):
        global share_id
        res = self.client.manila.share.list_export_locations(share_id)
        self.logger.debug(res)

    def test_add_share(self):
        global share_id
        share_proto = "nfs"
        size = 10
        name = "test-share-01"
        share_type = "1669e3ea-b0a0-4f7d-b78b-e82a39bb6546"
        is_public = False
        availability_zone = "nova"
        res = self.client.manila.share.create(
            share_proto,
            size,
            name=name,
            description=name,
            share_type=share_type,
            is_public=is_public,
            availability_zone=availability_zone,
        )
        self.share_status(res["id"])
        self.logger.debug(res)
        share_id = res["id"]

    def test_update_share(self):
        global share_id
        display_name = "test-share-01-update"
        res = self.client.manila.share.update(share_id, display_name=display_name)
        self.logger.debug(res)

    def test_delete_share(self):
        global share_id
        res = self.client.manila.share.delete(share_id)
        self.logger.debug(res)

    def test_delete_share_force(self):
        global share_id
        res = self.client.manila.share.action.force_delete(share_id)
        self.logger.debug(res)

    #
    # share action
    #
    def test_grant_access(self):
        global share_id
        access_level = "rw"
        access_type = "ip"
        access_to = "158.102.160.0/24"
        res = self.client.manila.share.action.grant_access(share_id, access_level, access_type, access_to)
        self.logger.debug(res)

    def test_list_access(self):
        global share_id, access_id
        res = self.client.manila.share.action.list_access(share_id)
        self.logger.debug(res)
        access_id = res[0]["id"]

    def test_revoke_access(self):
        global share_id, access_id
        res = self.client.manila.share.action.revoke_access(share_id, access_id)
        self.logger.debug(res)

    def test_reset_status(self):
        global share_id
        status = "available"
        res = self.client.manila.share.action.reset_status(share_id, status)
        self.logger.debug(res)

    def test_extend(self):
        global share_id
        new_size = 11
        res = self.client.manila.share.action.extend(share_id, new_size)
        self.share_status(share_id)
        self.logger.debug(res)

    def test_shrink(self):
        global share_id
        new_size = 9
        res = self.client.manila.share.action.shrink(share_id, new_size)
        self.share_status(share_id)
        self.logger.debug(res)

    def test_unmanage(self):
        global share_id
        res = self.client.manila.share.action.unmanage(share_id)
        self.logger.debug(res)

    def test_revert(self):
        global share_id
        snapshot_id = None
        res = self.client.manila.share.action.revert(share_id, snapshot_id)
        self.logger.debug(res)

    #
    # share snapshots
    #
    def test_list_share_snapshots(self):
        global oid
        res = self.client.manila.share.snapshot.list()
        self.logger.debug(res)
        oid = res[0]["id"]

    def test_get_share_snapshot(self):
        global oid
        res = self.client.manila.share.snapshot.get(oid)
        self.logger.debug(res)

    def test_add_share_snapshot(self):
        global oid
        share_id = oid
        name = "test-share-snapshot-01"
        res = self.client.manila.share.snapshot.create(share_id, name=name)
        self.logger.debug(res)

    def test_update_share_snapshot(self):
        global oid
        display_name = "test-share.snapshot-01-update"
        res = self.client.manila.share.snapshot.update(oid, display_name=display_name)
        self.logger.debug(res)

    def test_delete_share_snapshot(self):
        global oid
        res = self.client.manila.share.snapshot.delete(oid)
        self.logger.debug(res)

    def test_manage_share_snapshot(self):
        global oid
        res = self.client.manila.share.snapshot.manage(oid)
        self.logger.debug(res)

    def test_unmanage_share_snapshot(self):
        global oid
        res = self.client.manila.share.snapshot.unmanage(oid)
        self.logger.debug(res)

    def test_reset_status_share_snapshot(self):
        global oid
        res = self.client.manila.share.snapshot.reset_status(oid)
        self.logger.debug(res)

    def test_delete_share_force_share_snapshot(self):
        global oid
        res = self.client.manila.share.snapshot.force_delete(oid)
        self.logger.debug(res)

    #
    # share types
    #
    def test_list_share_types(self):
        global oid
        res = self.client.manila.share_type.list()
        self.logger.debug(res)
        oid = res[0]["id"]

    def test_list_default_share_types(self):
        res = self.client.manila.share_type.list(default=True)
        self.logger.debug(res)

    def test_get_share_type(self):
        global oid
        res = self.client.manila.share_type.get(oid)
        self.logger.debug(res)

    def test_get_share_type_extra_spec(self):
        global oid
        res = self.client.manila.share_type.get_extra_spec(oid)
        self.logger.debug(res)

    def test_get_share_type_access(self):
        global oid
        res = self.client.manila.share_type.get_access(oid)
        self.logger.debug(res)

    #
    # share pools
    #
    def test_list_stoarge_pool(self):
        res = self.client.manila.storage_pool.list()
        self.logger.debug(res)

    #
    # quota set
    #
    def test_get_quota_set(self):
        res = self.client.manila.quota_set.get(self.tenant_id, details=False)
        self.logger.debug(res)

    def test_get_quota_set_default(self):
        res = self.client.manila.quota_set.get_default(self.tenant_id)
        self.logger.debug(res)

    def test_update_quota_set(self):
        res = self.client.manila.quota_set.update(self.tenant_id)
        self.logger.debug(res)

    def test_delete_quota_set(self):
        res = self.client.manila.quota_set.delete(self.tenant_id)
        self.logger.debug(res)

    #
    # share.security_services
    #
    def test_list_security_services(self):
        global oid
        res = self.client.manila.security_service.list()
        self.logger.debug(res)
        oid = res[0]["id"]

    def test_get_security_service(self):
        global oid
        res = self.client.manila.security_service.get(oid)
        self.logger.debug(res)

    def test_add_security_service(self):
        global oid
        share_id = oid
        name = "test-share-security-service-01"
        res = self.client.manila.security_service.create(share_id, name=name)
        self.logger.debug(res)

    def test_update_security_service(self):
        global oid
        display_name = "test-share.security_service-01-update"
        res = self.client.manila.security_service.update(oid, display_name=display_name)
        self.logger.debug(res)

    def test_delete_security_service(self):
        global oid
        res = self.client.manila.security_service.delete(oid)
        self.logger.debug(res)


if __name__ == "__main__":
    runtest(OpenstackManilaTestCase, tests)
