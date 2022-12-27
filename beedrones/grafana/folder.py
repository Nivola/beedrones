# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte

from beecell.simple import truncate
from beedrones.grafana.client_grafana import GrafanaEntity


class GrafanaFolder(GrafanaEntity):
    def get(self, folder_uid=None):
        """Get grafana folder

        :param folder_uid: folder_uid
        :return: folder
        :raise GrafanaError:
        """
        # res = self.manager.grafanaFace.folder.get_folder_by_id(folder_id) # numeric id
        res = self.manager.grafanaFace.folder.get_folder(folder_uid)
        self.logger.debug('get folder: %s' % truncate(res))
        return res

    def search(self, folder_name=None):
        """Get grafana folder

        :param folder_name: folder_name
        :return: folder
        :raise GrafanaError:
        """
        # res = self.manager.grafanaFace.search.search_dashboards(query=folder_name, type_='dash-folder')
        res = self.search_ext(query=folder_name, type_='dash-folder')
        self.logger.debug('search folder: %s' % truncate(res))
        return res

    def list(self):
        """List grafana folder

        :return: folder
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.folder.get_all_folders()
        self.logger.debug('get folders: %s' % truncate(res))
        return res

    def add(self, folder_name, **params):
        """Add grafana folder

        :param str folder_name: Name of this folder.
        :return: folder
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.folder.create_folder(title=folder_name)
        self.logger.debug('add folder: %s' % truncate(res))

        folder_uid = res['uid']
        folder_id = res['id']
        self.logger.debug('folder_name: %s - uid: %s - id: %s' % (folder_name, folder_uid, folder_id))
        return res

    def delete(self, folder_uid):
        """Delete grafana folder

        :param folder_uid: grafana folder_uid
        :return: True
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.folder.delete_folder(uid=folder_uid)
        return True

    # def add_dashboard(self, space_id_from, dashboard_to_search, space_id_to, index_pattern=None):
    #     dashboard_id = self.find_dashboard(space_id_from, dashboard_to_search)
    #     str_dashboard = self.export_dashboard(dashboard_id)

    #     if index_pattern is not None:
    #         # replace filebeat-* con filebeat-*-logtype-*-account_name
    #         str_dashboard = str_dashboard.replace('filebeat-*', index_pattern)

    #     self.import_dashboard(space_id_to, str_dashboard)
    #     return

    def add_permission(self, folder_uid, team_id_viewer=None, team_id_editor=None, **params):
        """Add grafana folder

        :param str folder_name: Name of this folder.
        :return: folder
        :raise GrafanaError:
        """
        items = []
        if team_id_viewer is not None:
            items.append({ "teamId": team_id_viewer, "permission": 1})
        if team_id_editor is not None:
            items.append({ "teamId": team_id_editor, "permission": 2})

        data_items = { 
            "items": items
        }
        self.logger.debug('add permission - data_items: %s' % truncate(data_items))
        res = self.manager.grafanaFace.folder.update_folder_permissions(uid=folder_uid, items=data_items)
        self.logger.debug('add permission - res: %s' % truncate(res))
        return res

    def get_permissions(self, folder_uid=None):
        """Get grafana folder permission

        :param folder_uid: folder_uid
        :return: folder
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.folder.get_folder_permissions(folder_uid)
        self.logger.debug('get folder permission: %s' % truncate(res))
        return res