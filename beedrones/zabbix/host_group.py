# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixHostGroup(ZabbixEntity):
    """ZabbixHostGroup"""

    def list(self, selecthosts=None, **filter):
        """Get zabbix hostgroups

        :return: list of hostgroups
        :raise ZabbixError:
        """
        params = {"output": "extend", "filter": filter}
        if selecthosts is not None:
            params["selectHosts"] = selecthosts
        params.update(filter)
        res = self.call("hostgroup.get", params=params)
        self.logger.debug("list hostgroups: %s" % truncate(res))
        return res

    def get(self, hostgroup):
        """Get zabbix hostgroup

        :param hostgroup: hostgroup id
        :return: hostgroup
        :raise ZabbixError:
        """
        params = {"output": "extend", "groupids": hostgroup}
        res = self.call("hostgroup.get", params=params)
        if len(res) == 0:
            raise ZabbixError("hostgroup %s not found" % hostgroup)
        res = res[0]
        self.logger.debug("get hostgroup: %s" % truncate(res))
        return res

    def hosts(self, hostgroup):
        """Get hosts that belong to the hostgroup

        :param hostgroup: hostgroup id
        :return: list of hosts
        :raise ZabbixError:
        """
        params = {"output": ["hosts"], "selectHosts": "extend", "groupids": hostgroup}
        res = self.call("hostgroup.get", params=params)
        if len(res) == 0:
            raise ZabbixError("hostgroup %s not found" % hostgroup)
        res = res[0]
        self.logger.debug("get hosts for hostgroup %s: %s" % (hostgroup, truncate(res)))
        return res

    def templates(self, hostgroup):
        """Get templates that belong to the hostgroup

        :param hostgroup: hostgroup id
        :return: list of templates
        :raise ZabbixError:
        """
        params = {
            "output": ["templates"],
            "selectTemplates": "extend",
            "groupids": hostgroup,
        }
        res = self.call("hostgroup.get", params=params)
        if len(res) == 0:
            raise ZabbixError("hostgroup %s not found" % hostgroup)
        res = res[0]
        self.logger.debug("get templates for hostgroup %s: %s" % (hostgroup, truncate(res)))
        return res

    def get_items(self, group):
        """get zabbix item by group id

        :param group: group id
        :return: list of items
        :raise ZabbixError:
        """
        params = {"output": "extend", "groupids": group}
        res = self.call("item.get", params=params)
        self.logger.debug("get items: %s" % truncate(res))
        return res

    def get_triggers(self, group):
        """get zabbix triggers by group id

        :param group: group id
        :return: list of triggers
        :raise ZabbixError:
        """
        params = {"output": "extend", "groupids": group}
        res = self.call("trigger.get", params=params)
        self.logger.debug("get triggers: %s" % truncate(res))
        return res

    def add(self, name):
        """create zabbix host group

        :param name: zabbix group name
        :return: group id
        :raise ZabbixError:
        """
        params = {"name": name}
        res = self.call("hostgroup.create", params=params)
        self.logger.debug("create group %s: %s" % (name, truncate(res)))
        return res

    def update(self, group, name):
        """update zabbix host group

        :param group: group id
        :param name: name to rename group
        :return: group id
        :raise ZabbixError:
        """
        params = {"groupid": group, "name": name}
        res = self.call("hostgroup.update", params=params)
        self.logger.debug("create group %s: %s" % (name, truncate(res)))
        return res

    def delete(self, group):
        """delete zabbix host group from groupid

        :param group: group id
        :return: group id
        :raise ZabbixError:
        """
        params = [group]
        res = self.call("hostgroup.delete", params=params)
        self.logger.debug("delete group %s: %s" % (group, truncate(res)))
        return res
