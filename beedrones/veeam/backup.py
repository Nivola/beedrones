# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2026 CSI-Piemonte

from beecell.simple import truncate
from beedrones.veeam.client_veeam import VeeamEntity


class VeeamBackup(VeeamEntity):
    """ """

    def list(self, job_id=None, backup_name=None, page_size=10, page=1):
        """Get veeam backups

        :return: list of backups
        :raise VeeamError:
        """
        params = {
            "page_size": page_size,
            "page": page,
            "orderAsc":"True",
            "orderColumn":"Name",
        }
        if job_id:
            params["jobIdFilter"] = job_id
        if backup_name:
            params["nameFilter"] = backup_name

        res = self.http_list("v1/backups",**params)

        self.logger.debug("list backups: %s" % truncate(res, 1000))
        return res

    def get(self, backup):
        """Get veeam backup

        :param backup: backup id
        :return: backup
        :raise VeeamError:
        """
        res = self.http_get("v1/backups/%s" % backup)
        self.logger.debug("get backup: %s" % truncate(res, 1000))
        return res
