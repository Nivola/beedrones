# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte

import json
from beecell.simple import jsonDumps, truncate
from beedrones.grafana.client_grafana import GrafanaEntity


class GrafanaDashboard(GrafanaEntity):
    def get(self, dashboard_uid=None):
        """Get grafana dashboard

        :param dashboard_uid: dashboard_uid
        :return: dashboard
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.dashboard.get_dashboard(dashboard_uid)
        self.logger.debug('get dashboard: %s' % truncate(res, 1000))
        return res

    def add(self, data_dashboard, **params):
        """Add grafana dashboard

        :param str dashboard_name: Name of this dashboard.
        :return: dashboard
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.dashboard.update_dashboard(dashboard=data_dashboard)
        self.logger.debug('add dashboard: %s' % truncate(res))

        url = res['url']
        uid = res['uid']
        self.logger.debug('dashboard_name: %s - id: %s' % (url, uid))
        return res

    def delete(self, dashboard_uid):
        """Delete grafana dashboard

        :param dashboard_uid: grafana dashboard_uid
        :return: True
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.dashboard.delete_dashboard(dashboard_uid=dashboard_uid)
        return True

    def list(self, folder_id=None, search='', size=20, page=1, *args, **kwargs):
        """get grafana dashboard

        :param folder_uid: folder uid
        :param folder_id: folder id
        :param search: dashboard to search
        :param size: query page items [default=20]
        :param page: query page [default=1]
        :return: dashboard id
        :raise GrafanaError:
        """

        # res = self.manager.grafanaFace.search.search_dashboards(
        res = self.search_ext(query=search, type_='dash-db', folder_ids=folder_id, limit=size, page=page)
        self.logger.debug('list: %s' % truncate(res))

        resp = {
            'page': page,
            'count': size,
            'total': -1,
            'sort': {'field': 'id', 'order': 'asc'},
            'dashboards': res
        }
        self.logger.debug('GrafanaSpace - list dashboard: %s' % truncate(resp))

        return resp

    def add_dashboard(self, dashboard_to_search, folder_id_to, organization, division, account, dash_tag=None):
        # dashboard_uid = self.find_dashboard(space_id_from, dashboard_to_search)
        folder_general = '0' # general grafana folder
        res_dashboard = self.search_ext(query=dashboard_to_search, type_='dash-db', folder_ids=folder_general)
        self.logger.debug('add_dashboard: %s' % truncate(res_dashboard))

        if len(res_dashboard) == 0:
            # raise Exception('add_dashboard - dashboard not found: %s' % dashboard_to_search)
            self.logger.error('add_dashboard - dashboard not found: %s' % dashboard_to_search)

        elif len(res_dashboard) > 1:
            # raise Exception('add_dashboard - %s dashboard found: %s' % (len(res_dashboard), dashboard_to_search))
            res_dashboard_new = []
            for dashboard_item in res_dashboard:
                title: str = dashboard_item['title']
                if title.startswith(dashboard_to_search):
                    res_dashboard_new.append(dashboard_item)

            if len(res_dashboard_new) > 1:
                raise Exception('add_dashboard - %s dashboard found starting with: %s' % (len(res_dashboard_new), dashboard_to_search))
            else:
                res_dashboard = res_dashboard_new

        if len(res_dashboard) == 1:
            dashboard_uid = res_dashboard[0]['uid']
            self.logger.debug('add_dashboard - dashboard_uid: %s' % dashboard_uid)
            dashboard = self.get(dashboard_uid)
            json_dashboard = dashboard['dashboard']

            title_new = dashboard_to_search + '-' + organization + '.' + division + '.' + account

            tags = [organization, division, account]
            if dash_tag is not None:
                tag_array = dash_tag.split(",")
                for tag_item in tag_array:
                    tags.append(tag_item)

            json_dashboard.update({
                'id': None,
                'uid': None,
                'title': title_new,
                'tags': [x for x in tags]
                # "tags": [
                #     # "Account",
                #     organization,
                #     division,
                #     account
                # ],
            })

            # replace templating "text": "XXXXX", "value": "XXXXX"
            triplet = '%s.%s.%s' % (organization, division, account)
            str_dashboard = jsonDumps(json_dashboard)
            str_dashboard = str_dashboard.replace('XXXXX', triplet)
            json_dashboard = json.loads(str_dashboard)

            data_dashboard = {
                "dashboard": json_dashboard,
                "folderid": folder_id_to
            }
            self.logger.debug('add_dashboard - data_dashboard: %s' % data_dashboard)
            res = self.add(data_dashboard)
            return res

        return
