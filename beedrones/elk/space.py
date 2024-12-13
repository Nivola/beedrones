# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
# (C) Copyright 2018-2024 CSI-Piemonte

import random
import string
from beecell.simple import jsonDumps

from beecell.simple import truncate
from beedrones.elk.client_kibana import KibanaEntity


class KibanaSpace(KibanaEntity):
    """ """

    def list(self, **params):
        """Get kibana spaces

        :return: list of spaces
        :raise KibanaError:
        """
        res = self.http_list("api/spaces/space", **params)
        self.logger.debug("KibanaSpace - list spaces: %s" % truncate(res))
        return res

    def get(self, space_id):
        """Get kibana space

        :param space: space id
        :return: space
        :raise KibanaError:
        """
        res = self.http_get("api/spaces/space/%s" % space_id)
        self.logger.debug("KibanaSpace - get space: %s" % truncate(res))
        return res

    def add(self, space_id, name, description="", color=None, initials=None, **params):
        """Add kibana space

        :param str name: Name of this space.
        :param str description: Optional description of this space. [default=""]
        :param str color: (field, default=None)
        :param str initials: (field, default=None)
        :return: space
        :raise KibanaError:
        """
        params.update({"id": space_id, "name": name})

        if description is not None:
            params.update({"description": description})

        if color is not None:
            params.update({"color": color})

        if initials is not None:
            params.update({"initials": initials})

        res = self.http_post("api/spaces/space", data=params)
        self.logger.debug("KibanaSpace - add space: %s" % truncate(res))
        return res

    def delete(self, space_id):
        """Delete kibana space

        :param space_id: kibana space id
        :return: True
        :raise KibanaError:
        """
        self.http_delete("api/spaces/space/%s" % space_id)
        self.logger.debug("KibanaSpace - delete - space_id: %s" % space_id)
        return True

    #
    # dashboard
    #
    def get_dashboard(self, space_id, search="*", size=20, page=0, *args, **kwargs):
        """get kibana dashboard

        :param space_id: space id
        :param search: dashboard to search
        :param size: query page items [default=20]
        :param page: query page [default=0]
        :return: dashboard id
        :raise KibanaError:
        """
        params = {
            "type": "dashboard",
            "search_fields": ["id", "title"],
            "search": search,
            "fields": ["id", "title"],
            "default_search_operator": None,
            "per_page": size,
            "page": page + 1,
        }

        if space_id is None or space_id == "default":
            uri = "api/saved_objects/_find"
        else:
            uri = "s/%s/api/saved_objects/_find" % space_id

        res = self.http_get(uri, **params)
        resp = {
            "page": res.get("page"),
            "count": res.get("per_page"),
            "total": res.get("total"),
            "sort": {"field": "id", "order": "asc"},
            "dashboards": res.get("saved_objects", []),
        }
        self.logger.debug("KibanaSpace - get dashboard: %s" % truncate(resp))

        return resp

    def add_dashboard(self, space_id_from, dashboard_to_search, space_id_to, index_pattern=None):
        dashboard_id = self.find_dashboard(space_id_from, dashboard_to_search)
        str_dashboard = self.export_dashboard(dashboard_id)

        if index_pattern is not None:
            # replace filebeat-* con filebeat-*-logtype-*-account_name
            str_dashboard = str_dashboard.replace("filebeat-*", index_pattern)

        self.import_dashboard(space_id_to, str_dashboard)
        return

    def find_dashboard(self, space_id, dashboard_to_search="default"):
        """Find kibana dashboard

        :param space_id: space id
        :param dashboard_to_search: dashboard to search [default='default']
        :return: dashboard id
        :raise KibanaError:
        """
        dashboard_id = None
        params = {
            "type": "dashboard",
            "search_fields": ["id", "title"],
            "search": dashboard_to_search,
            "fields": ["id", "title"],
            "default_search_operator": None,
            "per_page": 100,
            "page": 1,
        }

        if space_id is None or space_id == "default":
            uri = "api/saved_objects/_find"
        else:
            uri = "s/%s/api/saved_objects/_find" % space_id

        res = self.http_get(uri, **params)

        dashboards = res["saved_objects"]
        for item in dashboards:
            dashboard_id = item["id"]
            break

        self.logger.debug("KibanaSpace - get dashboard_id: %s" % dashboard_id)

        return dashboard_id

    def export_dashboard(self, dashboard_id, **params):
        """Export kibana dashboard

        :param dashboard_id: dashboard id
        :return: json
        :raise KibanaError:
        """
        self.logger.debug("KibanaSpace - export_dashboard - dashboard_id: %s" % dashboard_id)

        params.update(
            {
                "objects": [{"type": "dashboard", "id": dashboard_id}],
                "includeReferencesDeep": True,
            }
        )

        url_export = "api/saved_objects/_export"
        res = self.http_post(url_export, data=params)
        self.logger.debug("KibanaSpace - export_dashboard - res: %s" % truncate(res, size=4000))

        # res in questo caso è una stringa con vari json all'interno!
        iExportedCount = res.rindex("exportedCount")
        self.logger.debug("KibanaSpace - export_dashboard - iExportedCount: %s" % iExportedCount)
        iLastGraffa = res.rindex("}", 0, iExportedCount)
        self.logger.debug("KibanaSpace - export_dashboard - iLastGraffa: %s" % iLastGraffa)

        # stringa con solo il primo json
        str_dashboard = res[0 : iLastGraffa + 1]
        # il json della dashboard è molto grande
        # self.logger.debug('export_dashboard - str_dashboard: %s' % str_dashboard)

        return str_dashboard

    def import_dashboard(self, space_id, str_dashboard):
        """Export kibana dashboard

        :param dashboard_id: dashboard id
        :param str_dashboard: dashboard data
        :return: json
        :raise KibanaError:
        """
        letters = string.ascii_letters
        str_random = "".join(random.choice(letters) for i in range(10))

        filename = "dashboard-temp" + str_random + ".ndjson"
        with open(filename, "w") as text_file:
            print(str_dashboard, file=text_file)
        myFile = open(filename, "rb")
        files = {"file": myFile}

        url_export = "s/%s/api/saved_objects/_import?createNewCopies=true"
        res = self.http_post(url_export % space_id, files=files)
        self.logger.debug("KibanaSpace - import_dashboard - res: %s" % res)

        myFile.close()

        # remove file dashboard
        import os

        os.remove(filename)
