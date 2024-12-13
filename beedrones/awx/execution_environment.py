# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from beedrones.awx.client import AwxEntity
from beecell.simple import jsonDumps, truncate


class AwxExecutionEnvironments(AwxEntity):
    """ """

    def list(self, **params):
        """Get awx execution_environments

        :return: list of execution_environments
        :raise AwxError:
        """
        res = self.http_list("execution_environments/", **params)
        self.logger.debug("list execution_environments: %s" % truncate(res))
        return res

    def get(self, execution_environment):
        """Get awx execution environment

        :param execution environment: execution environment id
        :return: execution environment
        :raise AwxError:
        """
        res = self.http_get("execution_environments/%s/" % execution_environment)
        self.logger.debug("get execution environment: %s" % truncate(res))
        return res

    def delete(self, execution_environment):
        """Delete awx execution environment

        :param execution environment: awx execution environment id
        :return: True
        :raise AwxError:
        """
        self.http_delete("execution_environments/%s/" % execution_environment)
        return True
