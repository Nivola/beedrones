# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixHost(ZabbixEntity):
    """ZabbixHost"""

    ITEM_TYPE_MAP = {
        "0": "Zabbix agent",
        "2": "Zabbix trapper",
        "3": "Simple check",
        "5": "Zabbix internal",
        "7": "Zabbix agent (active)",
        "9": "Web item",
        "10": "External check",
        "11": "Database monitor",
        "12": "IPMI agent",
        "13": "SSH agent",
        "14": "Telnet agent",
        "15": "Calculated",
        "16": "JMX agent",
        "17": "SNMP trap",
        "18": "Dependent item",
        "19": "HTTP agent",
        "20": "SNMP agent",
        "21": "Script",
    }

    def list(self, **filter):
        """Get zabbix hosts

        :return: list of hosts
        :raise ZabbixError:
        """
        params = {"output": "extend"}
        params.update(filter)
        res = self.call("host.get", params=params)
        self.logger.debug("list hosts: %s" % truncate(res))
        return res

    def get(self, host):
        """Get zabbix host

        :param host: host id
        :return: host
        :raise ZabbixError:
        """
        params = {"output": "extend", "hostids": host}
        res = self.call("host.get", params=params)
        if len(res) == 0:
            raise ZabbixError("host %s not found" % host)
        res = res[0]
        self.logger.debug("get host: %s" % truncate(res))
        return res

    def groups(self, host):
        """Get host groups the host belongs to

        :param host: host id
        :return: list of hostgroups
        :raise ZabbixError:
        """
        params = {"output": ["hostid"], "selectGroups": "extend", "hostids": host}
        res = self.call("host.get", params=params)
        if len(res) == 0:
            raise ZabbixError("host %s not found" % host)
        res = res[0]
        self.logger.debug("get groups for host %s: %s" % (host, truncate(res)))
        return res

    def interfaces(self, host):
        """Get interfaces used by the host

        :param host: host id
        :return: list of interfaces
        :raise ZabbixError:
        """
        params = {"output": ["hostid"], "selectInterfaces": "extend", "hostids": host}
        res = self.call("host.get", params=params)
        if len(res) == 0:
            raise ZabbixError("host %s not found" % host)
        res = res[0]
        self.logger.debug("get interfaces for host %s: %s" % (host, truncate(res)))
        return res

    def templates(self, host):
        """Get templates linked to host

        :param host: host id
        :return: list of templates
        :raise ZabbixError:
        """
        params = {
            "output": ["hostid"],
            "selectParentTemplates": "extend",
            "hostids": host,
        }
        res = self.call("host.get", params=params)
        if len(res) == 0:
            raise ZabbixError("host %s not found" % host)
        res = res[0]
        self.logger.debug("get templates for host %s: %s" % (host, truncate(res)))
        return res

    def link_templates(self, host, templates):
        """link templates to an host. Templates already linked are removed if they are not in list

        :param host: host id
        :param templates: list of template id
        :return: True/False
        :raise ZabbixError:
        """
        params = {"hostid": host, "templates": [{"templateid": t} for t in templates]}
        res = self.call("host.update", params=params)
        self.logger.debug("link templates %s to host %s: %s" % (templates, host, truncate(res)))
        return res

    def unlink_templates(self, host, templates):
        """unlink templates from an host

        :param host: host id
        :param templates: list of template id
        :return: True/False
        :raise ZabbixError:
        """
        params = {
            "hostid": host,
            "templates_clear": [{"templateid": t} for t in templates],
        }
        res = self.call("host.update", params=params)
        self.logger.debug("unlink templates %s from host %s: %s" % (templates, host, truncate(res)))
        return res

    def link_group(self, host, groups):
        """link an host to groups: groups  already linked are removed if they are not in groups list

        :param hostid: hostid
        :param groups: list of group id
        :return: True/False
        :raise ZabbixError:
        """
        params = {"hostid": host, "templates": [{"groupid": t} for t in groups]}
        res = self.call("host.update", params=params)
        self.logger.debug("link groups %s to host %s: %s" % (groups, host, truncate(res)))
        return res

    def create(
        self,
        name,
        interfaces,
        groupids=None,
        templateids=None,
        description="",
        status=0,
    ):
        """Create host

        :param name: host name
        :param ip_addr: ip address of the interfaces to be created for the host
        :param port: port of the interfaces to be created for the host
        :param groupids: hostgroups to add the host to
        :param templateids: templates to be linked to the host
        :param description: host description
        :param status: 0 - (default) monitored host', 1 - unmonitored host
        :return: host id
        :raise ZabbixError:
        """
        if groupids is None:
            groupids = []
        if templateids is None:
            templateids = []

        params = {
            "host": name,
            "description": description,
            # "status": status, # Incorrect status for host
            "groups": [{"groupid": item} for item in groupids],
            "templates": [{"templateid": item} for item in templateids],
            "interfaces": [
                {
                    "main": 1,
                    "type": 1,
                    "useip": 1,
                    "ip": item["ip_addr"],
                    "dns": "",
                    "port": item["port"],
                    "bulk": 1,
                }
                for item in interfaces
            ],
        }

        res = self.call("host.create", params=params)
        self.logger.debug("create host: %s" % truncate(res))
        return res

    def delete(self, host):
        """Delete zabbix host

        :param host: host id
        :return: host
        :raise ZabbixError:
        """
        params = [host]
        res = self.call("host.delete", params=params)
        self.logger.debug("delete host: %s" % truncate(res))
        return res

    def update(self, host, **props):
        """Update property of the host

        :param host: host id
        :return: host
        :raise ZabbixError:
        """
        params = {
            "output": "extend",
            "hostid": host,
        }
        for k, v in props.items():
            params[k] = v
        res = self.call("host.update", params=params)
        self.logger.debug("update host: %s" % truncate(res))
        return res

    def get_triggers(self, host):
        """get zabbix triggers by host id

        :param host: hostid
        :return: list of triggers
        :raise ZabbixError:
        """
        params = {"output": "extend", "hostids": host}
        res = self.call("trigger.get", params=params)
        self.logger.debug("get triggers: %s" % truncate(res))
        return res

    def map_item_to_string(self, item):
        """map item int value to string

        :param int item: int value of item
        """
        return self.ITEM_TYPE_MAP[item]

    def get_items(self, host, **filter):
        """get zabbix item by host id

        :param host: hostid
        :param filter: custom filter
        :return: list of items
        :raise ZabbixError:
        """
        params = {"output": "extend", "hostids": host}
        params.update(filter)
        res = self.call("item.get", params=params)
        self.logger.debug("get items: %s" % truncate(res))
        return res

    def create_item(
        self,
        hostid,
        name,
        description,
        agent_type,
        value_type,
        interfaceid,
        key,
        delay,
        history,
        trends,
    ):
        """create zabbix item script on zabbix agent

        :param hostid: zabbix host hostid
        :param name: key name
        :param description: item description/comment
        :param agent_type: zabbix type. Possible values:
            0 - Zabbix agent',
            1 - SNMPv1 agent',
            2 - Zabbix trapper',
            3 - simple check',
            4 - SNMPv2 agent',
            5 - Zabbix internal',
            6 - SNMPv3 agent',
            7 - Zabbix agent (active)',
            8 - Zabbix aggregate',
            9 - web item',
            10 - external check',
            11 - database monitor',
            12 - IPMI agent',
            13 - SSH agent',
            14 - TELNET agent',
            15 - calculated',
            16 - JMX agent.
        :param value_type: zabbix value_type. Possible values:
            0 - numeric float',
            1 - character',
            2 - log',
            3 - numeric unsigned',
            4 - text.
        :param interfaceid: zabbix host interfaceid
        :param key: item key
        :param delay: check interval in seconds
        :param history: Number of days to keep item's history data
        :param trends: Number of days to keep item's trends data
        :return: host id
        :raise ZabbixError:
        """
        params = {
            "name": name,
            "description": description,
            "key_": key,
            "hostid": hostid,
            "type": agent_type,
            "value_type": value_type,
            "interfaceid": interfaceid,
            "delay": delay,
            "history": history,
            "trends": trends,
        }

        res = self.call("item.create", params=params)
        self.logger.debug("create script item: %s" % truncate(res))
        return res
