# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import truncate
from beedrones.awx.client import AwxEntity


class AwxProject(AwxEntity):
    """ """

    def __init__(self, manager):
        AwxEntity.__init__(self, manager)

        self.job = AwxProjectJob(manager)

    def list(self, **params):
        """Get awx projects

        :return: list of projects
        :raise AwxError:
        """
        res = self.http_list("projects/", **params)
        self.logger.debug("list projects: %s" % truncate(res))
        return res

    def get(self, project):
        """Get awx project

        :param project: project id
        :return: project
        :raise AwxError:
        """
        res = self.http_get("projects/%s/" % project)
        self.logger.debug("get project: %s" % truncate(res))
        return res

    def add(self, name, **params):
        """Add awx project

        :param str name: Name of this project. (string, required)
        :param str description: Optional description of this project. [default=""]
        :param str local_path: Local path (relative to PROJECTS_ROOT) containing playbooks and related files for this
            project. [default=""]
        :param str scm_type: Specifies the source control system used to store the project. [defualt=Manual]
            git: Git
            hg: Mercurial
            svn: Subversion
            insights: Red Hat Insights
        :param str scm_url: The location where the project is stored. [default=""]
        :param str scm_branch: Specific branch, tag or commit to checkout. [default=""]
        :param bool scm_clean: Discard any local changes before syncing the project. [default=False]
        :param bool scm_delete_on_update: Delete the project before syncing. [default=False]
        :param credential: [field, default=None]
        :param int timeout: The amount of time (in seconds) to run before the task is canceled. (integer, default=0)
        :param organization: [field, default=None]
        :param bool scm_update_on_launch: Update the project when a job is launched that uses the project. [default=False]
        :param int scm_update_cache_timeout: The number of seconds after the last project update ran that a newproject
            update will be launched as a job dependency. [default=0]
        :param str custom_virtualenv: Local absolute file path containing a custom Python virtualenv to use [default=""]
        :return: project
        :raise AwxError:
        """
        params.update({"name": name})
        res = self.http_post("projects/", data=params)
        self.logger.debug("add project: %s" % truncate(res))
        return res

    def delete(self, project):
        """Delete awx project

        :param project: awx project id
        :return: True
        :raise AwxError:
        """
        self.http_delete("projects/%s/" % project)
        self.logger.debug("delete project %s" % project)
        return True

    def sync(self, project):
        """Sync awx project

        :param project: project id
        :return: project
        :raise AwxError:
        """
        res = self.http_post("projects/%s/update/" % project)
        self.logger.debug("sync project %s" % project)
        return res

    def playbook_list(self, project, **params):
        """List playbooks for project

        :param project: awx project id
        :return: playbooks list
        :raise AwxError:
        """
        res = self.http_list("projects/%s/playbooks/" % project, **params)
        self.logger.debug("get project %s playbooks" % project)
        return res


class AwxProjectJob(AwxEntity):
    """
    status: (choice)
        new: New
        pending: Pending
        waiting: Waiting
        running: Running
        successful: Successful
        failed: Failed
        error: Error
        canceled: Canceled
    """

    def list(self, **params):
        """Get awx projects

        :return: list of projects
        :raise AwxError:
        """
        res = self.http_list("project_updates/", **params)
        self.logger.debug("list project updates: %s" % truncate(res))
        return res

    def get(self, job):
        """Get awx project update job

        :param job: project update job id
        :return: job
        :raise AwxError:
        """
        res = self.http_get("project_updates/%s/" % job)
        self.logger.debug("get project update: %s" % truncate(res))
        return res

    def cancel(self, job):
        """Cancel awx project update job

        :param job: project update job id
        :return: job
        :raise AwxError:
        """
        res = self.http_post("project_updates/%s/cancel/" % job)
        self.logger.debug("cancel project update %s" % job)
        return res

    def stdout(self, job):
        """Get awx project update job stdout

        :param job: project update job id
        :return: job
        :raise AwxError:
        """
        res = self.http_get("project_updates/%s/stdout/" % job, format="json")
        self.logger.debug("get project update %s stdout" % job)
        return res

    def events(self, job, **params):
        """Get awx project update job events

        :param job: project update job id
        :return: job
        :raise AwxError:
        """
        res = self.http_list("project_updates/%s/events/" % job, **params)
        self.logger.debug("get project %s events" % job)
        return res
