# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import truncate
from beedrones.awx.client import AwxEntity


class AwxJob(AwxEntity):
    """ """

    def list(self, **params):
        """Get awx jobs

        :return: list of jobs
        :raise AwxError:
        """
        res = self.http_list("jobs/", **params)
        self.logger.debug("list jobs: %s" % truncate(res))
        return res

    def get(self, job):
        """Get awx job

        :param job: job id
        :return: job
        :raise AwxError:
        """
        res = self.http_get("jobs/%s/" % job)
        self.logger.debug("get job: %s" % truncate(res))
        return res

    def delete(self, job):
        """Delete awx job

        :param job: awx job id
        :return: True
        :raise AwxError:
        """
        self.http_delete("jobs/%s/" % job)
        return True

    def cancel(self, job):
        """Cancel awx job

        :param job: awx job id
        :return: True
        :raise AwxError:
        """
        self.http_post("jobs/%s/cancel/" % job)
        self.logger.debug("delete job %s" % job)
        return True

    def relaunch(self, job):
        """Relaunch awx job

        :param job: awx job id
        :return: True
        :raise AwxError:
        """
        self.http_post("jobs/%s/relaunch/" % job)
        self.logger.debug("relaunch job %s" % job)
        return True

    def stdout(self, job):
        """Get awx job stdout

        :param job: job id
        :return: job
        :raise AwxError:
        """
        res = self.http_get("jobs/%s/stdout/" % job, format="json")
        self.logger.debug("get job %s stdout" % job)
        return res

    def events(self, job, query=None):
        """Get awx job events

        :param job: job id
        :param query: job event query
        :return: job
        :raise AwxError:
        """
        uri = "jobs/%s/job_events/" % job
        res = self.http_list(uri, **query)
        self.logger.debug("get job %s events" % job)
        return res
