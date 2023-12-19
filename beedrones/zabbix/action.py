# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixAction(ZabbixEntity):
    """ZabbixAction"""

    SEVERITY_INFORMATION: int = 1  # Information
    SEVERITY_WARNING: int = 2  # Warning
    SEVERITY_AVERAGE: int = 3  # Average
    SEVERITY_HIGH: int = 4  # High
    SEVERITY_DISASTER: int = 5  # Disaster

    EVENTSOURCE_TRIGGER: int = 0  # 0 - event created by a trigger;
    EVENTSOURCE_DISCOVER: int = 1  # 1 - event created by a discovery rule;
    EVENTSOURCE_AUTOREGISTRATION: int = 2  # 2 - event created by active agent autoregistration;
    EVENTSOURCE_INTERNAL: int = 3  # 3 - internal event;
    EVENTSOURCE_UPDATE: int = 4  # 4 - event created on service status update.

    def list(self, **filter):
        """Get zabbix actions

        :return: list of actions
        :raise ZabbixError:
        """
        params = {
            "output": "extend",
            # "selectOperations": "extend",
            "selectFilter": "extend",
            "filter": filter,
            # "limit": 100
        }
        res = self.call("action.get", params=params)
        self.logger.debug("list actions: %s" % res)
        return res

    def get(self, action_id):
        """Get zabbix action

        :param action: action id
        :return: action
        :raise ZabbixError:
        """
        params = {
            "output": "extend",
            "actionids": action_id,
            "selectFilter": "extend",
            "selectOperations": "extend",
        }
        res = self.call("action.get", params=params)
        if len(res) == 0:
            raise ZabbixError("action %s not found" % action_id)
        res = res[0]
        self.logger.debug("get action: %s" % truncate(res))
        return res

    def enable(self, action):
        """enable zabbix action

        :param action: action id
        :return: action
        :raise ZabbixError:
        """
        params = {"actionid": action, "status": 0}
        res = self.call("action.update", params=params)
        self.logger.debug("enable action %s: %s" % (action, truncate(res)))
        return res

    def disable(self, action):
        """disable zabbix action

        :param action: action id
        :return: action
        :raise ZabbixError:
        """
        params = {"actionid": action, "status": 1}
        res = self.call("action.update", params=params)
        self.logger.debug("disable action %s: %s" % (action, truncate(res)))
        return res

    def create_autoregistration(self, groupid, groupname, templateid, operatingsystem):
        """create autoregistration action based on groups

        :param groupid: groupid (account groupid)
        :param groupname: groupname
        :param templateid: templateid (operating system templateid)
        :param operatingsystem: operatingsystem ("Linux or Windows")
        :return: True/False and True/False
        :raise ZabbixError:
        """
        action_name = groupname + "-" + operatingsystem
        params = {
            "name": action_name,
            "eventsource": self.EVENTSOURCE_AUTOREGISTRATION,
            "status": 0,
            "esc_period": 0,
            "def_shortdata": "Auto registration: {HOST.HOST}",
            "def_longdata": "Host name: {HOST.HOST}\r\nHost IP: {HOST.IP}\r\nAgent port: {HOST.PORT}",
            "filter": {
                "evaltype": 1,
                "conditions": [
                    {"conditiontype": 24, "operator": 2, "value": operatingsystem},
                    {"conditiontype": 24, "operator": 2, "value": groupname},
                ],
            },
            "operations": [
                {"operationtype": 4, "opgroup": [{"groupid": groupid}]},
                {"operationtype": 6, "optemplate": [{"templateid": templateid}]},
            ],
        }
        res = self.call("action.create", params=params)
        self.logger.debug("create action %s: %s" % (action_name, truncate(res)))
        return res

    def add_trigger(self, name, usrgrp_id, hostgroup_id):
        """create zabbix action trigger

        :param name: name
        :param usrgrp_id: zabbix usrgrpid
        :param hostgroup_id: zabbix hostgroup id
        :return: user id
        :raise ZabbixError:
        """
        params = {
            "name": name,
            "eventsource": self.EVENTSOURCE_TRIGGER,  # trigger
            "esc_period": "1h",  # "30m",
            "def_shortdata": "Problem: {EVENT.NAME}",
            "def_longdata": "Problem started at {EVENT.TIME} on {EVENT.DATE}\nProblem name: {EVENT.NAME}\nHost: {HOST.NAME}\nSeverity: {EVENT.SEVERITY}\n",
            "r_shortdata": "Resolved: {EVENT.NAME}",
            "r_longdata": "Problem has been resolved at {EVENT.RECOVERY.TIME} on {EVENT.RECOVERY.DATE}\nProblem name: {EVENT.NAME}\nHost: {HOST.NAME}\nSeverity: {EVENT.SEVERITY}\n",
            "pause_suppressed": "1",
            "filter": {
                "evaltype": 3,
                "formula": "A and B",
                "conditions": [
                    #  host "10084" goes into a PROBLEM state
                    # {
                    #     "conditiontype": 1,
                    #     "operator": 0,
                    #     "value": "10084"
                    # },
                    {
                        # severity higher or equal to XX
                        "conditiontype": 4,
                        "operator": 5,
                        "value": self.SEVERITY_WARNING,
                        "formulaid": "A",
                    },
                    {
                        # hostgroup equals XX
                        "conditiontype": 0,
                        "operator": 0,
                        "value": hostgroup_id,
                        "formulaid": "B",
                    },
                ],
            },
            "operations": [
                {
                    "operationtype": 0,
                    "esc_period": 0,
                    "esc_step_from": 1,
                    "esc_step_to": 1,
                    "opmessage_grp": [{"usrgrpid": usrgrp_id}],
                    "opmessage": {"default_msg": 1, "mediatypeid": "1"},
                },
            ],
            # "recovery_operations": [
            #     {
            #         "operationtype": "11",
            #         "opmessage": {
            #             "default_msg": 1
            #         }
            #     }
            # ],
            # "acknowledge_operations": [
            #     {
            #         "operationtype": "12",
            #         "opmessage": {
            #             "message": "Custom update operation message body",
            #             "subject": "Custom update operation message subject"
            #         }
            #     }
            # ]
        }
        res = self.call("action.create", params=params)
        self.logger.debug("create action %s: %s" % (name, truncate(res)))
        return res

    def update_trigger(self, action_id, hostgroup_id, severity):
        """update zabbix action trigger

        :param action_id: action id
        :param hostgroup_id: zabbix hostgroup_id
        :param severity: zabbix severity
        :return: action_id id
        :raise ZabbixError:
        """
        params = {
            "actionid": action_id,
            "filter": {
                "evaltype": 3,
                "formula": "A and B",
                "conditions": [
                    {
                        # severity higher or equal to XX
                        "conditiontype": 4,
                        "operator": 5,
                        "value": severity,
                        "formulaid": "A",
                    },
                    {
                        # hostgroup equals XX
                        "conditiontype": 0,
                        "operator": 0,
                        "value": hostgroup_id,
                        "formulaid": "B",
                    },
                ],
            },
        }
        res = self.call("action.update", params=params)
        self.logger.debug("update action %s: %s" % (action_id, truncate(res)))
        return res

    def update_trigger_severity(self, action_id, severity):
        """update zabbix action trigger

        :param name: action_id
        :param severity: zabbix severity
        :return: action_id id
        :raise ZabbixError:
        """
        res_action = self.get(action_id)
        filter = res_action["filter"]
        eval_formula = filter.pop("eval_formula")  # remove for update
        conditions = filter["conditions"]

        conditions_updated = []
        for condition in conditions:
            conditiontype = condition["conditiontype"]
            if conditiontype == "4":  # severity higher or equal to XX
                condition.update(
                    {
                        "value": severity,
                    }
                )

            conditions_updated.append(condition)

        filter.update({"conditions": conditions_updated})
        self.logger.debug("update action %s - filter: %s" % (action_id, filter))

        params = {"actionid": action_id, "filter": filter}
        res = self.call("action.update", params=params)
        self.logger.debug("update action %s: %s" % (action_id, truncate(res)))
        return res

    def delete(self, action_id):
        """delete zabbix action id

        :param action_id: action id
        :return: action id
        :raise ZabbixError:
        """
        params = [action_id]
        res = self.call("action.delete", params=params)
        self.logger.debug("delete action %s: %s" % (action_id, truncate(res)))
        return res
