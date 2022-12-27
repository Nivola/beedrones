# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import jsonDumps

from beecell.simple import truncate
from beedrones.awx.client import AwxEntity


class AwxOrganization(AwxEntity):
    """
    """
    def list(self, **params):
        """Get awx organizations

        :return: list of organizations
        :raise AwxError:
        """
        res = self.http_list('organizations/', **params)
        self.logger.debug('list organizations: %s' % truncate(res))
        return res

    def get(self, organization):
        """Get awx organization

        :param organization: organization id
        :return: organization
        :raise AwxError:
        """
        res = self.http_get('organizations/%s/' % organization)
        self.logger.debug('get organization: %s' % truncate(res))
        return res

    def get_users(self, orgid):
        """get awx users in organization id

        :param orgid: organization id
        :return: list of organization's users
        :raise AwxError:
        """
        res = self.http_list('organizations/%s/users/' % orgid)
        self.logger.debug('get organization %s users' % orgid)
        return res

    # def organizations_link_user(self, **params):
    #     """link awx user to organization
    #
    #     :param organizationid: awx organization id
    #     :param userid: userid to link
    #     :param is_admin: true/false
    #     :return: True
    #     :raise AwxError:
    #     """
    #     if not 'organizationid' in params.keys():
    #         raise AwxError("missing organizationid parameter")
    #     else:
    #         organizationid = params['organizationid']
    #         org = str(organizationid)
    #     if not 'userid' in params.keys():
    #         raise AwxError("missing userid parameter")
    #     else:
    #         userid = params['userid']
    #     if not 'is_admin' in params.keys():
    #         raise AwxError("missing is_admin parameter")
    #     else:
    #         is_admin = params['is_admin']
    #     if is_admin == 'true':
    #         uri = self.awx_base_uri + "/api/v2/organizations/" + org + "/admins/"
    #     else:
    #         uri = self.awx_base_uri + "/api/v2/organizations/" + org + "/users/"
    #
    #     heady = {'Authorization': 'Bearer ' + self.token, 'content-type': 'application/json'}
    #     id = int(userid)
    #     payload = {'id': id}
    #     res = requests.post(uri, data=jsonDumps(payload), headers=heady)
    #     result = str(res)
    #     if result == '<Response [204]>':
    #         return True
    #     else:
    #         return res
    #
    # def organizations_unlink_user(self, **params):
    #     """unlink awx user to organization
    #
    #     :param organizationid: awx organization id
    #     :param userid: userid to unlink
    #     :param is_admin: true/false
    #     :return: organization or message error
    #     :raise AwxError:
    #     """
    #     if not 'organizationid' in params.keys():
    #         raise AwxError("missing organizationid parameter")
    #     else:
    #         organizationid = params['organizationid']
    #         org = str(organizationid)
    #     if not 'userid' in params.keys():
    #         raise AwxError("missing userid parameter")
    #     else:
    #         userid = params['userid']
    #     if not 'is_admin' in params.keys():
    #         raise AwxError("missing is_admin parameter")
    #     else:
    #         is_admin = params['is_admin']
    #     if is_admin == 'true':
    #         uri = self.awx_base_uri + "/api/v2/organizations/" + org + "/admins/"
    #     else:
    #         uri = self.awx_base_uri + "/api/v2/organizations/" + org + "/users/"
    #
    #     heady = {'Authorization': 'Bearer ' + self.token, 'content-type': 'application/json'}
    #     id = int(userid)
    #     payload = {'id': id, 'disassociate': 'true'}
    #     res = requests.post(uri, data=jsonDumps(payload), headers=heady)
    #     result = str(res)
    #     if result == '<Response [204]>':
    #         return 'OK'
    #     else:
    #         return res
    #
    # def show_organizations_admins(self, **params):
    #     """get admins of an organization
    #
    #     :param organizationid: awx organization id
    #     :return: list of organizations admin dict or message error
    #     :raise AwxError:
    #     """
    #     if not 'organizationid' in params.keys():
    #         raise AwxError("missing organizationid parameter")
    #     else:
    #         organizationid = params['organizationid']
    #         org = str(organizationid)
    #     uri = self.awx_base_uri + "/api/v2/organizations/" + org + "/admins"
    #     heady = {'Authorization': 'Bearer ' + self.token}
    #     res = requests.get(uri, headers=heady)
    #     output = res.json()
    #     try:
    #         message = output
    #         return message
    #     except:
    #         message = output
    #         return message
