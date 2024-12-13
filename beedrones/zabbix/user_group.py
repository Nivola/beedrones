# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte


from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixUserGroup(ZabbixEntity):
    """ZabbixUserGroup"""

    def list(self, userids=None, **filter):
        """Get zabbix usergroups

        :return: list of usergroups
        :raise ZabbixError:
        """
        params = {"output": "extend", "filter": filter, "selectUsers": "extend"}
        if userids is not None:
            params["userids"] = userids
        params.update(filter)

        res = self.call("usergroup.get", params=params)
        self.logger.debug("list usergroups: %s" % truncate(res))
        return res

    def get(self, usergroup_id):
        """Get zabbix usergroup id

        :param usergroup: usergroup id
        :return: usergroup
        :raise ZabbixError:
        """
        params = {
            "output": "extend",
            # "filter": filter,
            "usrgrpids": usergroup_id,
            "selectUsers": "extend",
            "selectRights": "extend",
        }
        res = self.call("usergroup.get", params=params)
        self.logger.debug("get usergroup res: %s" % res)
        if len(res) == 0:
            raise ZabbixError("usergroup %s not found" % usergroup_id)
        res = res[0]
        self.logger.debug("get usergroup: %s" % truncate(res))
        return res

    def add(self, name, hostgroup_id):
        """create zabbix host group

        :param name: zabbix group name
        :return: group id
        :raise ZabbixError:
        """
        params = {
            "name": name,
            "rights": {"permission": 2, "id": hostgroup_id},  # read-only access
            "gui_access": "3",  # Frontend access = disabled
            # "userids": "12"
        }
        res = self.call("usergroup.create", params=params)
        self.logger.debug("create usergroup %s: %s" % (name, truncate(res)))
        return res

    def update(self, usergroup_id, hostgroup_id, permission):
        """update zabbix host group

        :param group: group id
        :param name: name to rename group
        :return: group id
        :raise ZabbixError:
        """
        params = {
            "usrgrpid": usergroup_id,
            # "users_status": "0",
            "hostgroup_rights": [{"id": hostgroup_id, "permission": permission}],
        }
        res = self.call("usergroup.update", params=params)
        self.logger.debug("update usergroup %s: %s" % (usergroup_id, truncate(res)))
        return res

    def delete(self, usergroup_id):
        """delete zabbix user group id

        :param group: group id
        :return: group id
        :raise ZabbixError:
        """
        params = [usergroup_id]
        res = self.call("usergroup.delete", params=params)
        self.logger.debug("delete usergroup %s: %s" % (usergroup_id, truncate(res)))
        return res
