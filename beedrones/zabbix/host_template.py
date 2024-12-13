# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixHostTemplate(ZabbixEntity):
    """ZabbixHostTemplate"""

    def list(self, **filter):
        """Get awx templates

        :param filter: custom filter fields
        :return: list of templates
        :raise ZabbixError:
        """
        params = {"output": "extend"}
        params.update(filter)
        res = self.call("template.get", params=params)
        self.logger.debug("list templates: %s" % truncate(res))
        return res

    def get(self, template):
        """Get awx template

        :param template: template id
        :return: template
        :raise ZabbixError:
        """
        params = {"output": "extend", "templateids": template}
        res = self.call("template.get", params=params)
        if len(res) == 0:
            raise ZabbixError("template %s not found" % template)
        res = res[0]
        self.logger.debug("get template: %s" % truncate(res))
        return res

    def hosts(self, template):
        """Get the hosts that are linked to the template

        :param template: template id
        :return: list of hosts
        :raise ZabbixError:
        """
        params = {"output": ["hosts"], "selectHosts": "extend", "templateids": template}
        res = self.call("template.get", params=params)
        if len(res) == 0:
            raise ZabbixError("template %s not found" % template)
        res = res[0]
        self.logger.debug("get hosts for template %s: %s" % (template, truncate(res)))
        return res

    def groups(self, template):
        """Get the hostgroups that the template belongs to

        :param template: template id
        :return: list of hostgroups
        :raise ZabbixError:
        """
        params = {
            "output": ["groups"],
            "selectGroups": "extend",
            "templateids": template,
        }
        res = self.call("template.get", params=params)
        if len(res) == 0:
            raise ZabbixError("template %s not found" % template)
        res = res[0]
        self.logger.debug("get hostgroups for template %s: %s" % (template, truncate(res)))
        return res

    def export(self, template):
        """export template to a file

        :param template: template id to export
        :return: template in json format
        :raise ZabbixError:
        """
        params = {"options": {"templates": [template]}, "format": "json"}
        res = self.call("configuration.export", params=params)
        self.logger.debug("export template %s: %s" % (template, truncate(res)))
        return res

    def load(self, source, format="xml"):
        """import a template from a file

        :param source: string config to import
        :param source: string format
        :return: True/False
        :raise ZabbixError:
        """
        params = {
            "format": format,
            "rules": {
                "groups": {"createMissing": True},
                "hosts": {"createMissing": False, "updateExisting": False},
                "templates": {
                    "createMissing": True,
                    "updateExisting": True,
                },
                "templateScreens": {
                    "createMissing": True,
                    "updateExisting": True,
                },
                "templateLinkage": {"createMissing": True},
                "applications": {
                    "createMissing": True,
                },
                "items": {
                    "createMissing": True,
                    "updateExisting": True,
                    "deleteMissing": False,
                },
                "discoveryRules": {
                    "createMissing": True,
                    "updateExisting": True,
                },
                "triggers": {
                    "createMissing": True,
                    "updateExisting": True,
                },
                "graphs": {
                    "createMissing": True,
                    "updateExisting": True,
                },
                "valueMaps": {
                    "createMissing": True,
                },
            },
            "source": source,
        }
        res = self.call("configuration.import", params=params)
        self.logger.debug("import template from source: %s" % truncate(res))
        return res

    def create(self, name, groupids, description=""):
        """Create template

        :param name: template name
        :param groupids: hostgroups to add the template to
        :param description: template description
        :return: template id
        :raise ZabbixError:
        """
        if groupids is None:
            groupids = []

        params = {
            "host": name,
            "description": description,
            "groups": [{"groupid": item} for item in groupids],
        }

        res = self.call("template.create", params=params)
        self.logger.debug("create template: %s" % truncate(res))
        return res

    def delete(self, template):
        """delete template

        :param template: template id
        :return: template id
        :raise ZabbixError:
        """
        params = [template]
        res = self.call("template.delete", params=params)
        self.logger.debug("delete template %s: %s" % (template, truncate(res)))
        return res
