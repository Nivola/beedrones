# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import truncate
from beedrones.veeam.client_veeam import VeeamEntity


class VeeamJob(VeeamEntity):
    """ """

    def list(self, job_name, page_size=20, page=1):
        """Get veeam jobs

        :return: list of jobs
        :raise VeeamError:
        """
        # res = self.http_list("v1/jobs", page_size=page_size, page=page, nameFilter=job_name, orderAsc="True", orderColumn="Name")
        res = self.http_list("v1/jobs/states", page_size=page_size, page=page, nameFilter=job_name, typeFilter="Backup")
        self.logger.debug("list jobs: %s" % truncate(res, 1000))
        return res

    def get(self, job):
        """Get veeam job

        :param job: job id
        :return: job
        :raise VeeamError:
        """
        # res = self.http_get("v1/jobs/%s" % job)
        res = self.http_get("v1/jobs/states", idFilter=job)
        self.logger.debug("get job: %s" % truncate(res, 1000))
        return res

    def delete(self, job):
        """Delete veeam job

        :param job: veeam job id
        :return: True
        :raise VeeamError:
        """
        self.http_delete("v1/jobs/%s" % job)
        return True
