# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError
from typing import List


class ZabbixUser(ZabbixEntity):
    """ZabbixUser"""

    SEVERITY_INFORMATION: int = 2  # Information
    SEVERITY_WARNING: int = 4  # Warning
    SEVERITY_AVERAGE: int = 8  # Average
    SEVERITY_HIGH: int = 16  # High
    SEVERITY_DISASTER: int = 32  # Disaster

    def list(self, usrgrpids=None, **filter):
        """Get zabbix users

        :return: list of users
        :raise ZabbixError:
        """
        params = {
            "output": "extend",
            "filter": filter,
            "selectUsrgrps": "extend",
            "selectMedias": "extend",
        }
        if usrgrpids is not None:
            params["usrgrpids"] = usrgrpids
        params.update(filter)

        res = self.call("user.get", params=params)
        self.logger.debug("list users: %s" % truncate(res))
        return res

    def get(self, user_id):
        """Get zabbix user

        :param user: user id
        :return: user
        :raise ZabbixError:
        """
        params = {
            "output": "extend",
            "userids": user_id,
            "selectUsrgrps": "extend",
            "selectMedias": "extend",
            # "selectMediatypes": "extend",
        }
        res = self.call("user.get", params=params)
        if len(res) == 0:
            raise ZabbixError("user %s not found" % user_id)
        res = res[0]
        self.logger.debug("get user: %s" % truncate(res))
        return res

    def add(self, username, passwd, usrgrpid, email: List[str]):
        """create zabbix user

        :param username: zabbix user name
        :param passwd: zabbix user passwd
        :param usrgrpid: zabbix usrgrpid
        :param email: zabbix user email
        :return: user id
        :raise ZabbixError:
        """
        user_medias = []
        for email_item in email:
            user_media = {
                "mediatypeid": "1",  # email
                "active": 0,
                "period": "1-7,00:00-24:00",
                "sendto": email_item,
                "severity": self.SEVERITY_HIGH + self.SEVERITY_DISASTER,  # 32 + 16, all severity 63,
            }
            user_medias.append(user_media)

        params = {"alias": username, "passwd": passwd, "usrgrps": [{"usrgrpid": usrgrpid}], "user_medias": user_medias}
        self.logger.debug("create user %s - params: %s" % (username, params))
        res = self.call("user.create", params=params)
        self.logger.debug("create user %s: %s" % (username, truncate(res)))
        return res

    def update(self, userid, email: List[str], severity: int):
        """update zabbix user

        :param user_id: user id
        :param name: name to rename user
        :return: user_id
        :raise ZabbixError:
        """
        user_medias = []
        for email_item in email:
            user_media = {
                "mediatypeid": "1",  # email
                "active": 0,
                "period": "1-7,00:00-24:00",
                "sendto": email_item,
                "severity": severity,
            }
            user_medias.append(user_media)

        params = {
            "userid": userid,
            # "alias": username,
            # "passwd": passwd,
            # "usrgrps": [
            #     {
            #         "usrgrpid": usrgrpid
            #     }
            # ],
            "user_medias": user_medias,
        }
        self.logger.debug("update user %s - params: %s" % (userid, params))
        res = self.call("user.update", params=params)
        self.logger.debug("update user %s: %s" % (userid, truncate(res)))
        return res

    def delete(self, user_id):
        """delete zabbix user

        :param user_id: user id
        :return: user_id
        :raise ZabbixError:
        """
        params = [user_id]
        res = self.call("user.delete", params=params)
        self.logger.debug("delete user %s: %s" % (user_id, truncate(res)))
        return res
