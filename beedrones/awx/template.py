# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import truncate
from beedrones.awx.client import AwxEntity


class AwxJobTemplate(AwxEntity):
    """ """

    def list(self, **params):
        """Get awx job_templates

        :return: list of job_templates
        :raise AwxError:
        """
        res = self.http_list("job_templates/", **params)
        self.logger.debug("list job templates: %s" % truncate(res))
        return res

    def get(self, job_template):
        """Get awx job_template

        :param job_template: job_template id
        :return: job_template
        :raise AwxError:
        """
        res = self.http_get("job_templates/%s/" % job_template)
        self.logger.debug("get job template: %s" % truncate(res))
        return res

    def add(
        self,
        name,
        job_type,
        inventory,
        project,
        playbook,
        verbosity=0,
        job_tags="",
        **params,
    ):
        """Add awx job_template

        :param str name: Name of this job template.
        :param str description: Optional description of this job template. [default=""]
        :param str job_type: (choice)
            run: Run (default)
            check: Check
        :param int inventory: (field, default=None)
        :param int project: (field, default=None)
        :param str playbook: [default=""]
        :param int forks: (integer, default=0)
        :param str limit: [default=""]
        :param int verbosity: (choice)
            0: 0 (Normal) (default)
            1: 1 (Verbose)
            2: 2 (More Verbose)
            3: 3 (Debug)
            4: 4 (Connection Debug)
            5: 5 (WinRM Debug)
        :param str extra_vars: [default=""]
        :param str job_tags: [default=""]
        :param bool force_handlers: [default=False]
        :param str skip_tags: [default=""]
        :param str start_at_task: [default=""]
        :param int timeout: The amount of time (in seconds) to run before the task is canceled. (integer, default=0)
        :param bool use_fact_cache: If enabled, Tower will act as an Ansible Fact Cache Plugin; persisting facts at the
            end of a playbook run to the database and caching facts for use by Ansible. [default=False]
        :param str host_config_key: [default=""]
        :param bool ask_diff_mode_on_launch: [default=False]
        :param bool ask_variables_on_launch: [default=False]
        :param bool ask_limit_on_launch: [default=False]
        :param bool ask_tags_on_launch: [default=False]
        :param bool ask_skip_tags_on_launch: [default=False]
        :param bool ask_job_type_on_launch: [default=False]
        :param bool ask_verbosity_on_launch: [default=False]
        :param bool ask_inventory_on_launch: [default=False]
        :param bool ask_credential_on_launch: [default=False]
        :param bool survey_enabled: [default=False]
        :param bool become_enabled: [default=False]
        :param bool diff_mode: If enabled, textual changes made to any templated files on the host are shown in the
            standard output [default=False]
        :param bool allow_simultaneous: [default=False]
        :param str custom_virtualenv: Local absolute file path containing a custom Python virtualenv to use [default=""]
        :param int job_slice_count: The number of jobs to slice into at runtime. Will cause the Job Template to launch
            a workflow if value is greater than 1. (integer, default=1)
        :return: job_template
        :raise AwxError:
        """
        params.update(
            {
                "name": name,
                "job_type": job_type,
                "inventory": inventory,
                "project": project,
                "playbook": playbook,
                "job_tags": job_tags,
                "verbosity": 0,
            }
        )
        res = self.http_post("job_templates/", data=params)
        self.logger.debug("add job template: %s" % truncate(res))
        return res

    def delete(self, job_template):
        """Delete awx job_template

        :param job_template: awx job_template id
        :return: True
        :raise AwxError:
        """
        self.http_delete("job_templates/%s/" % job_template)
        self.logger.debug("delete job template %s" % job_template)
        return True

    def launch(self, job_template, **params):
        """Launch job template in awx

        :param job_template: awx job template id
        :return: job template
        :raise AwxError:
        """
        res = self.http_post("job_templates/%s/launch/" % job_template, data=params)
        self.logger.debug("launch job template %s" % job_template)
        return res

    def list_jobs(self, job_template, **params):
        """list Jobs for a Job Template

        :param job_template: awx job template id
        :return: jobs
        :raise AwxError:
        """
        res = self.http_list("job_templates/%s/jobs/" % job_template, data=params)
        self.logger.debug("list Jobs for a Job Template %s: %s" % (job_template, truncate(res)))
        return res
