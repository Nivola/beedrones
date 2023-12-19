# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import truncate
from beedrones.grafana.client_grafana import GrafanaEntity


class GrafanaTeam(GrafanaEntity):
    def get(self, team_id=None):
        """Get grafana team

        :param team_id: team_id
        :return: team
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.teams.get_team(team_id)
        self.logger.debug("get team: %s" % truncate(res))
        return res

    def get_by_name(self, team_name):
        """Get grafana team

        :param team_id: team_name
        :return: team
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.teams.get_team_by_name(team_name)
        self.logger.debug("get team by name: %s" % truncate(res))
        return res

    def list(self, page=1, size=None):
        """List grafana teams

        :return: teams
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.teams.search_teams(page=page, perpage=size)
        self.logger.debug("get teams: %s" % truncate(res))
        return res

    def add(self, team_name, **params):
        """Add grafana team

        :param str team_name: Name of this team.
        :return: team
        :raise GrafanaError:
        """
        data_team = {
            "name": team_name,
            # "email": "email@test.com"
        }
        res = self.manager.grafanaFace.teams.add_team(team=data_team)
        self.logger.debug("add team: %s" % truncate(res))

        team_id = res["teamId"]
        self.logger.debug("team_name: %s - id: %s" % (team_name, team_id))
        return res

    def delete(self, team_id):
        """Delete grafana team

        :param team_id: grafana team_id
        :return: True
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.teams.delete_team(team_id=team_id)
        return True

    def add_user(self, team_id, user_id, **params):
        """Add grafana team

        :param team_id: team id.
        :param user_id: user id.
        :return: message
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.teams.add_team_member(team_id, user_id)
        self.logger.debug("add user to team: %s" % truncate(res))
        message = res["message"]
        self.logger.debug("add_user - team_id: %s - user_id: %s - message: %s" % (team_id, user_id, message))
        return message

    def get_users(self, team_id, **params):
        """Add grafana team

        :param team_id: team id.
        :return: team users
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.teams.get_team_members(team_id)
        self.logger.debug("get_users - get user of team: %s" % truncate(res))
        return res

    def del_user(self, team_id, user_id, **params):
        """Delete grafana user from team

        :param team_id: team id.
        :param user_id: user id.
        :return: team
        :raise GrafanaError:
        """
        self.logger.debug("del_users - team_id: %s - user_id: %s" % (team_id, user_id))
        res = self.manager.grafanaFace.teams.remove_team_member(team_id, user_id)
        message = res["message"]
        self.logger.debug("del_users - team_id: %s - user_id: %s - message: %s" % (team_id, user_id, message))
        return message
