# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beecell.simple import truncate
from beedrones.awx.client import AwxEntity


class AwxCredential(AwxEntity):
    """ """

    def list(self, **params):
        """Get awx credentials

        :return: list of credentials
        :raise AwxError:
        """
        res = self.http_list("credentials/", **params)
        self.logger.debug("list credentials: %s" % truncate(res))
        return res

    def get(self, credential):
        """Get awx credential

        :param credential: credential id
        :return: credential
        :raise AwxError:
        """
        res = self.http_get("credentials/%s/" % credential)
        self.logger.debug("get credential: %s" % truncate(res))
        return res

    def add(self, name, **params):
        """Add awx credential

        :param str name: Name of this credential.
        :param str description: Optional description of this credential. [default=""]
        :param int organization: Inherit permissions from organization roles. If provided on creation, do not give
            either user or team. [default=None]
        :param int user: Write-only field used to add user to owner role. If provided, do not give either team or
            organization. Only valid for creation. [default=None]
        :param int team: Write-only field used to add team to owner role. If provided, do not give either user or
            organization. Only valid for creation. [default=None]
        :param kind: (choice)
            ssh: Machine (default)
            net: Network
            scm: Source Control
            aws: Amazon Web Services
            vmware: VMware vCenter
            satellite6: Red Hat Satellite 6
            cloudforms: Red Hat CloudForms
            gce: Google Compute Engine
            azure_rm: Microsoft Azure Resource Manager
            openstack: OpenStack
            rhv: Red Hat Virtualization
            insights: Insights
            tower: Ansible Tower
        :param host: The hostname or IP address to use. [default=""]
        :param username: Username for this credential. [default=""]
        :param password: Password for this credential (or "ASK" to prompt the user for machine credentials).
            [default=""]
        :param security_token: Security Token for this credential [default=""]
        :param project: The identifier for the project. [default=""]
        :param domain: The identifier for the domain. [default=""]
        :param ssh_key_data: RSA or DSA private key to be used instead of password. [default=""]
        :param ssh_key_unlock: Passphrase to unlock SSH private key if encrypted (or "ASK" to prompt the user for
            machine credentials). [default=""]
        :param become_method: Privilege escalation method. [default=""]
        :param become_username: Privilege escalation username. [default=""]
        :param become_password: Password for privilege escalation method. [default=""]
        :param vault_password: Vault password (or "ASK" to prompt the user). [default=""]
        :param subscription: Subscription identifier for this credential [default=""]
        :param tenant: Tenant identifier for this credential [default=""]
        :param secret: Secret Token for this credential [default=""]
        :param client: Client Id or Application Id for the credential [default=""]
        :param authorize: Whether to use the authorize mechanism. (boolean, default=False)
        :param authorize_password: Password used by the authorize mechanism. [default=""]
        :return: credential
        :raise AwxError:
        """
        params.update(
            {
                "name": name,
                # 'organization': organization,
            }
        )
        res = self.http_post("credentials/", data=params)
        self.logger.debug("add credential: %s" % truncate(res))
        return res

    def add_ssh(
        self,
        name,
        organization,
        username,
        password=None,
        ssh_key_data=None,
        ssh_key_unlock=None,
        become="no_become",
        **params,
    ):
        """add git credentials

        :param name: name of credential
        :param organization: organization id of credential
        :param username: ssh username
        :param password: ssh password (instead of ssh_key_data)
        :param ssh_key_data: ssh private key (instead of password)
        :param ssh_key_unlock: ssh private key pass phrase, if exists (instead of password)
        :param become: become method used by ansible (sudo)
        :return: credential
        :raise AwxError:
        """
        if password is not None:
            if become == "no_become":
                inp = {"username": username, "password": password}
            else:
                inp = {
                    "username": username,
                    "password": password,
                    "become_method": become,
                }
        else:
            if become == "no_become":
                inp = {"username": username, "ssh_key_data": ssh_key_data}
            else:
                inp = {
                    "username": username,
                    "ssh_key_data": ssh_key_data,
                    "become_method": become,
                }
            if ssh_key_unlock is not None:
                inp["ssh_key_unlock"] = ssh_key_unlock

        params.update(
            {
                "name": name,
                "organization": organization,
                "credential_type": 1,
                "inputs": inp,
            }
        )
        res = self.http_post("credentials/", data=params)
        self.logger.debug("add ssh credential: %s" % truncate(res))
        return res

    def add_git(self, name, organization, username, password, **params):
        """add git credentials

        :param name: name of credential
        :param organization: organization id of credential
        :param username: username
        :param password: password
        :return: credential
        :raise AwxError:
        """
        params.update(
            {
                "name": name,
                "organization": organization,
                "credential_type": 2,
                "inputs": {"username": username, "password": password},
            }
        )
        res = self.http_post("credentials/", data=params)
        self.logger.debug("add git credential: %s" % truncate(res))
        return res

    def delete(self, credential):
        """Delete awx credential

        :param credential: awx credential id
        :return: True
        :raise AwxError:
        """
        self.http_delete("credentials/%s/" % credential)
        self.logger.debug("delete credential %s" % credential)
        return True

    def type_list(self, **params):
        """List credential types

        :return: credential types list
        :raise AwxError:
        """
        res = self.http_list("credential_types/", **params)
        self.logger.debug("list credential types: %s" % truncate(res))
        return res

    def type_get(self, oid):
        """Get credential type

        :param oid: credential id
        :return: credential types list
        :raise AwxError:
        """
        res = self.http_get("credential_types/%s" % oid)
        self.logger.debug("get credential type: %s" % truncate(res))
        return res
