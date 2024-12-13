# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from itertools import islice
from netapp_ontap.resources import QuotaReport

# from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapUsage(OntapEntity):
    """
    OntapUsage
    """

    @make_request
    def list_usage_svm(self, svm_uuid):
        """
        :param svm_uuid: uuid of svm
        :return: list of dict
        """
        params = {"svm.uuid": svm_uuid}
        return self._list_usage_x(**params)

    @make_request
    def list_usage_volume(self, volume_uuid):
        """
        :param volume_uuid: uuid of volume
        :return: list of dict
        """
        # e.g.
        # space: {'hard_limit': 54975581388800, 'used': {'total': 0, 'hard_limit_percent': 0}}
        # files: {'used': {'total': 1}}
        # aatype: "tree"

        params = {"volume.uuid": volume_uuid}
        return self._list_usage_x(**params)

    @make_request
    def list_usage_qtree(self, volume_uuid, qtree_id):
        """
        :param volume_uuid: uuid of volume
        :param qtree_id: id of qtree on volume
        :return: list of dict
        """
        params = {"volume.uuid": volume_uuid, "id": qtree_id}
        return self._list_usage_x(**params)

    def _list_usage_x(self, max_records: int = None, fields: str = "", **kwargs):
        """
        generic method to list quota usage of svm, volume, qtree, etc.
        :param max_records:
        :param kwargs:
        :return:
        """
        res = QuotaReport.get_collection(connection=self.client, max_records=20, fields=fields, **kwargs)
        if max_records:
            res = islice(res, max_records)

        resp = [quota.to_dict() for quota in res]
        return resp

    @make_request
    def get_usage(self):
        """
        TODO params
        """
        quota = QuotaReport(volume={"uuid": "f5cb101d-590a-11ec-b166-d039ea34650a"}, index=2305843013508661248)
        quota.set_connection(self.client)
        # import pdb
        # pdb.set_trace()
        quota.get()
        return quota.to_dict()

    def _get_x(self, **kwargs):
        pass

    @make_request
    def list_all(self):
        fields = {}
        # params = {"volume.uuid": "f5cb101d-590a-11ec-b166-d039ea34650a", "qtree.id":1}
        # params = {"svm.uuid": "5fdf33f3-58e8-11ec-b166-d039ea34650a"}
        # total = QuotaReport.count_collection(connection=self.client, fields=fields, **params)
        # print(total)
        res = QuotaReport.get_collection(connection=self.client, max_records=20, fields=fields)  # , **params)
        tmp = islice(res, 20)
        resp = []
        for item in tmp:
            resp.append(item.do_dict())
        return resp
        # quota = QuotaReport(volume={"uuid": "f5cb101d-590a-11ec-b166-d039ea34650a"},index=2305843013508661248)
        # quota.set_connection(self.client)
        # quota.get()

        # import pdb
        # pdb.set_trace()
