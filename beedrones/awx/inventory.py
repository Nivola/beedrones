# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

import json
from beecell.simple import truncate
from beedrones.awx.client import AwxEntity
from beecell.simple import jsonDumps


class AwxInventory(AwxEntity):
    """
    """
    def list(self, **params):
        """Get awx inventories

        :return: list of inventories
        :raise AwxError:
        """
        res = self.http_list('inventories/', **params)
        self.logger.debug('list inventories: %s' % truncate(res))
        return res

    def get(self, inventory):
        """Get awx inventory

        :param inventory: inventory id
        :return: inventory
        :raise AwxError:
        """
        res = self.http_get('inventories/%s/' % inventory)
        self.logger.debug('get inventory: %s' % truncate(res))
        return res

    def add(self, name, organization, **params):
        """Add awx inventory

        :param name: Name of this inventory. (string, required)
        :param description: Optional description of this inventory. (string, default="")
        :param organization: Organization containing this inventory. (field, required)
        :param kind: Kind of inventory being represented. (choice)
            "": Hosts have a direct link to this inventory. (default)
            smart: Hosts for inventory generated using the host_filter property.
        :param host_filter: Filter that will be applied to the hosts of this inventory. (string, default="")
        :param variables: Inventory variables in JSON or YAML format. (string, default="")
        :param insights_credential: Credentials to be used by hosts belonging to this inventory when accessing Red Hat
            Insights API. (field, default=None)
        :return: inventory
        :raise AwxError:
        """
        params.update({
            'name': name,
            'organization': organization
        })
        res = self.http_post('inventories/', data=params)
        self.logger.debug('add inventory: %s' % truncate(res))
        return res

    def delete(self, inventory):
        """Delete awx inventory

        :param inventory: awx inventory id
        :return: True
        :raise AwxError:
        """
        self.http_delete('inventories/%s/' % inventory)
        return True

    def source_list(self, inventory, **params):
        """Get awx inventory sources

        :return: list of inventories sources
        :raise AwxError:
        """
        res = self.http_list('inventories/%s/inventory_sources' % inventory, **params)
        self.logger.debug('list inventory %s source: %s' % (inventory, truncate(res)))
        return res

    def source_get(self, inventory_source):
        """Get awx inventory_source

        :param inventory_source: inventory_source id
        :return: inventory
        :raise AwxError:
        """
        res = self.http_get('inventory_sources/%s/' % inventory_source)
        self.logger.debug('get inventory source: %s' % truncate(res))
        return res

    def source_sync(self, inventory_source):
        """Sync an inventory source

        :param inventory_source: awx inventory source id
        :return: job
        :raise AwxError:
        """
        res = self.http_post('inventory_sources/%s/update/' % inventory_source)
        self.logger.debug('sync inventory source: %s' % truncate(res))
        return res

    def group_list(self, inventory, **params):
        """Get awx inventory groups

        :return: list of inventories groups
        :raise AwxError:
        """
        res = self.http_list('inventories/%s/groups' % inventory, **params)
        self.logger.debug('get inventory groups: %s' % truncate(res))
        return res

    def group_get(self, inventory_group):
        """Get awx inventory group

        :param inventory_group: inventory_group id
        :return: inventory
        :raise AwxError:
        """
        res = self.http_get('groups/%s/' % inventory_group)
        self.logger.debug('get inventory group: %s' % truncate(res))
        return res

    def group_add(self, inventory, name, desc=None, vars=None):
        """Add awx inventory group

        :param inventory: inventory_group id
        :param name: group name
        :param desc: group description [default=name]
        :param vars: group variables [optional]
        :return: inventory
        :raise AwxError:
        """
        data = {
            'name': name,
            'description': desc if desc is None else name,
            'variables': jsonDumps(vars) if isinstance(vars, dict) is True else ''
        }
        res = self.http_post('inventories/%s/groups/' % inventory, data=data)
        self.logger.debug('create inventory group: %s' % truncate(res))
        return res

    def group_del(self, inventory_group):
        """Delete awx inventory group

        :param inventory_group: inventory_group id
        :return: inventory
        :raise AwxError:
        """
        res = self.http_delete('groups/%s/' % inventory_group)
        self.logger.debug('delete inventory group: %s' % truncate(res))
        return res

    def group_host_list(self, inventory_group, **params):
        """Get awx inventory hosts

        :param inventory_group: inventory_group id
        :return: list of inventories hosts
        :raise AwxError:
        """
        res = self.http_list('groups/%s/hosts/' % inventory_group, **params)
        self.logger.debug('get inventory group hosts: %s' % truncate(res))
        return res

    def host_list(self, inventory, **params):
        """Get awx inventory hosts

        :return: list of inventories hosts
        :raise AwxError:
        """
        res = self.http_list('inventories/%s/hosts/' % inventory, **params)
        self.logger.debug('get inventory hosts: %s' % truncate(res))
        return res

    def host_get(self, inventory_host):
        """Get awx inventory_host

        :param inventory_host: inventory_host id
        :return: inventory
        :raise AwxError:
        """
        res = self.http_get('hosts/%s/' % inventory_host)
        self.logger.debug('get inventory host: %s' % truncate(res))
        return res

    def host_add(self, inventory, name, desc=None, vars=None):
        """Add awx inventory host

        :param inventory: inventory_host id
        :param name: host name
        :param desc: host description [default=name]
        :param vars: host variables [optional]
        :return: inventory
        :raise AwxError:
        """
        data = {
            'name': name,
            'description': desc if desc is None else name,
            'variables': jsonDumps(vars) if isinstance(vars, dict) is True else ''
        }
        res = self.http_post('inventories/%s/hosts/' % inventory, data=data)
        self.logger.debug('create inventory host: %s' % truncate(res))
        return res

    def add_hoc_command_get(self, inventory):
        """List of ad hoc commands associated with the selected inventory

        :param inventory: inventory_host id
        :return: inventory
        :raise AwxError:
        """
        res = self.http_list('inventories/%s/ad_hoc_commands/' % inventory)
        self.logger.debug('list inventory ad hoc commands: %s' % truncate(res))
        return res

    def add_hoc_command_add(self, inventory, limit='', credential='', module_name='command', module_args='',
                            verbosity=0, extra_vars='', become_enabled=False):
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
            'job_type': 'run',
            'limit': limit,
            'credential': credential,
            'module_name': module_name,
            'module_args': module_args,
            'verbosity': verbosity,
            'extra_vars': extra_vars,
            'become_enabled': become_enabled
        }
        res = self.http_post('inventories/%s/ad_hoc_commands/' % inventory, data=data)
        self.logger.debug('add inventory ad_hoc_commands: %s' % truncate(res))
        return res
