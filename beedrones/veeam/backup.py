# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import truncate
from beedrones.veeam.client_veeam import VeeamEntity


class VeeamBackup(VeeamEntity):
    """ """

    def list(self, job_id, backup_name=None, page_size=10, page=1):
        """Get veeam backups

        :return: list of backups
        :raise VeeamError:
        """
        res = self.http_list(
            "v1/backups",
            page_size=page_size,
            page=page,
            jobIdFilter=job_id,
            nameFilter=backup_name,
            orderAsc="True",
            orderColumn="Name",
        )
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
