# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

import json
from beecell.simple import truncate
from beedrones.awx.client import AwxEntity


class AwxHost(AwxEntity):
    """
    """
    def list(self, **params):
        """Get awx hosts

        :return: list of hosts
        :raise AwxError:
        """
        res = self.http_list('hosts/', **params)
        self.logger.debug('list hosts: %s' % truncate(res))
        return res

    def get(self, host):
        """Get awx host

        :param host: host id
        :return: host
        :raise AwxError:
        """
        res = self.http_get('hosts/%s/' % host)
        self.logger.debug('get host: %s' % truncate(res))
        return res

    def add(self, name, inventory, desc=None, vars=None):
        """Add awx host

        :param name: Name of this host. (string, required)
        :param description: Optional description of this host. (string, default="")
        :param inventory: inventory containing this host. (field, required)
        :param variables: Host variables in JSON or YAML format. (string, default="")
        :return: host
        :raise AwxError:
        """
        data = {
          'description': desc if desc is None else name,
          'variables': json.dumps(vars) if isinstance(vars, dict) is True else '',
          'enabled': True,
          # 'instance_id': None,
          'inventory': inventory,
          'name': name
        }
        res = self.http_post('hosts/', data=data)
        self.logger.debug('add host: %s' % truncate(res))
        return res

    def delete(self, host):
        """Delete awx host

        :param host: awx host id
        :return: True
        :raise AwxError:
        """
        self.http_delete('hosts/%s/' % host)
        return True
