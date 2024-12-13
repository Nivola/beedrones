# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte

from time import time

from beecell.simple import truncate
from beedrones.zabbix.client import ZabbixEntity, ZabbixError


class ZabbixItService(ZabbixEntity):
    """ZabbixItService"""

    def list(self, **filter):
        """Get zabbix it_services

        :param filter: custom filter
        :return: list of it_services
        :raise ZabbixError:
        """
        params = {
            "output": "extend",
            "selectParent": "extend",
            "selectDependencies": "extend",
            # 'selectParentDependencies': 'extend',
            # 'selectTimes': 'extend',
            # 'selectAlarms': 'extend',
            "selectTrigger": "extend",
        }
        params.update(filter)
        res = self.call("service.get", params=params)
        self.logger.debug("list it_services: %s" % truncate(res))
        return res

    def get(self, it_service):
        """Get zabbix it_service

        :param it_service: it_service id
        :return: it_service
        :raise ZabbixError:
        """
        params = {
            "output": "extend",
            "serviceids": it_service,
            "selectParent": "extend",
            "selectDependencies": "extend",
            # 'selectParentDependencies': 'extend',
            "selectTimes": "extend",
            "selectAlarms": "extend",
            "selectTrigger": "extend",
        }
        res = self.call("service.get", params=params)
        if len(res) == 0:
            raise ZabbixError("it service %s not found" % it_service)
        res = res[0]
        self.logger.debug("get it service: %s" % truncate(res))
        return res

    def get_sla(self, it_service, time_from=None, time_to=None):
        """Get zabbix it_service

        :param it_service: it_service id
        :param time_from: time from
        :param time_to: time to
        :return: it_service
        :raise ZabbixError:
        """
        if time_to is None:
            time_to = time()
        if time_from is None:
            time_from = time_to - 86400
        params = {
            "output": "extend",
            "serviceids": it_service,
            "intervals": [{"from": time_from, "to": time_to}],
        }
        res = self.call("service.getsla", params=params)
        res = res.get(it_service, {})
        self.logger.debug("get it service sla: %s" % truncate(res))
        return res
