# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import truncate
from beedrones.awx.client import AwxEntity


class AwxInventoryScript(AwxEntity):
    """ """

    def list(self, **params):
        """Get awx inventory_scripts

        :return: list of inventory_scripts
        :raise AwxError:
        """
        res = self.http_list("inventory_scripts/", **params)
        self.logger.debug("list inventory scripts: %s" % truncate(res))
        return res

    def get(self, inventory_script):
        """Get awx inventory_script

        :param inventory_script: inventory_script id
        :return: inventory_script
        :raise AwxError:
        """
        res = self.http_get("inventory_scripts/%s/" % inventory_script)
        self.logger.debug("get inventory script: %s" % truncate(res))
        return res

    def add(self, name, organization, script, **params):
        """Add awx inventory_script

        :param name: Name of this custom inventory script. (string, required)
        :param description: Optional description of this custom inventory script. (string, default="")
        :param script: (string, required)
        :param organization: Organization owning this inventory script (field, required)
        :return: inventory script
        :raise AwxError:
        """
        params.update({"name": name, "organization": organization, "script": script})
        res = self.http_post("inventory_scripts/", data=params)
        self.logger.debug("add inventory script: %s" % truncate(res))
        return res

    def delete(self, inventory_script):
        """Delete awx inventory_script

        :param inventory_script: awx inventory_script id
        :return: True
        :raise AwxError:
        """
        self.http_delete("inventory_scripts/%s/" % inventory_script)
        self.logger.debug("delete inventory script %s" % inventory_script)
        return True
