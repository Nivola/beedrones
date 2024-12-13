# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import truncate
from beedrones.veeam.client_veeam import VeeamEntity


class VeeamRestorePoint(VeeamEntity):
    """ """

    def list(self, backup_id=None, restorepoint_name=None, page_size=20, page=1):
        """Get veeam restorepoints

        :return: list of restorepoints
        :raise VeeamError:
        """
        res = self.http_list(
            "v1/objectRestorePoints",
            page_size=page_size,
            page=page,
            backupIdFilter=backup_id,
            nameFilter=restorepoint_name,
            orderAsc="False",
            orderColumn="CreationTime",
        )
        self.logger.debug("list restorepoints: %s" % truncate(res, 1000))
        return res

    def get(self, restorepoint):
        """Get veeam restorepoint

        :param restorepoint: restorepoint id
        :return: restorepoint
        :raise VeeamError:
        """
        res = self.http_get("v1/objectRestorePoints/%s" % restorepoint)
        self.logger.debug("get restorepoint: %s" % truncate(res, 1000))
        return res
