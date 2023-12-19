# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import truncate
from beedrones.awx.client import AwxEntity


class AwxAdHocCommand(AwxEntity):
    """ """

    def list(self, **params):
        """Get awx ad_hoc_commands

        :return: list of ad_hoc_commands
        :raise AwxError:
        """
        res = self.http_list("ad_hoc_commands/", **params)
        self.logger.debug("list ad hoc commands: %s" % truncate(res))
        return res

    def get(self, ad_hoc_command):
        """Get awx ad_hoc_command

        :param ad_hoc_command: ad_hoc_command id
        :return: ad_hoc_command
        :raise AwxError:
        """
        res = self.http_get("ad_hoc_commands/%s/" % ad_hoc_command)
        self.logger.debug("get ad hoc command: %s" % truncate(res))
        return res

    def add(
        self,
        inventory,
        limit="",
        credential="",
        module_name="command",
        module_args="",
        verbosity=0,
        extra_vars="",
        become_enabled=False,
    ):
        """List of ad hoc commands associated with the selected inventory

        :param inventory: inventory_host id
        :param limit: limit [default='']
        :param credential: credential [default='']
        :param module_name: module name [default='command']
        :param module_args: module args [default='']
        :param verbosity: 0 (Normal) (default), 1 (Verbose), 2 (More Verbose), 3 (Debug), 4 (Connection Debug),
            5 (WinRM Debug)
        :param extra_vars: extra vars [default='']
        :param become_enabled: become enabled [default=False]
        :return: inventory
        :raise AwxError:
        """
        data = {
            "job_type": "run",
            "limit": limit,
            "inventory": inventory,
            "credential": credential,
            "module_name": module_name,
            "module_args": module_args,
            "verbosity": verbosity,
            "extra_vars": extra_vars,
            "become_enabled": become_enabled,
        }
        res = self.http_post("ad_hoc_commands/", data=data)
        self.logger.debug("add ad_hoc_commands: %s" % truncate(res))
        return res

    def delete(self, ad_hoc_command):
        """Delete awx ad_hoc_command

        :param ad_hoc_command: awx ad_hoc_command id
        :return: True
        :raise AwxError:
        """
        self.http_delete("ad_hoc_commands/%s/" % ad_hoc_command)
        self.logger.debug("delete ad hoc command %s" % ad_hoc_command)
        return True

    def stdout(self, ad_hoc_command):
        """Get awx ad_hoc_command stdout

        :param ad_hoc_command: ad_hoc_command id
        :return: command response
        :raise AwxError:
        """
        res = self.http_get("ad_hoc_commands/%s/stdout/" % ad_hoc_command, format="json")
        self.logger.debug("get ad hoc command %s stdout" % ad_hoc_command)
        return res

    def relaunch(self, ad_hoc_command):
        """relaunch awx ad_hoc_command stdout

        :param ad_hoc_command: ad_hoc_command id
        :return: command response
        :raise AwxError:
        """
        res = self.http_post("ad_hoc_commands/%s/relaunch/" % ad_hoc_command)
        self.logger.debug("relaunch ad hoc command %s" % ad_hoc_command)
        return res
