# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from itertools import islice
from netapp_ontap.resources import Aggregate
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapAggregate(OntapEntity):
    """OntapAggregate"""

    def list_with_node(self, **kwargs):
        """list aggregates

        :param kwargs:
        :return:
        """
        kwargs.setdefault("fields", ("name", "uuid", "node"))
        kwargs.setdefault("order_by", "name asc")
        return self.list(**kwargs)

    def list_with_space(self, **kwargs):
        """list aggregates

        :param kwargs:
        :return:
        """
        kwargs.setdefault("fields", ("name", "uuid", "space.block_storage"))
        kwargs.setdefault("order_by", "space.block_storage.available desc")
        return self.list(**kwargs)

    @make_request
    def list(self, **kwargs):
        """list aggregates
        field agnostic. do not call directly
        """
        max_records = kwargs.pop("max_records", None)
        if max_records:
            # if given, it means we want paginated
            page = kwargs.pop("page", 0)
            # if offset given, use it, otherwise calculate it
            offset = kwargs.pop("offset", None)
            if not offset:
                offset = page * max_records
            total = Aggregate.count_collection(connection=self.client)
            res = Aggregate.get_collection(connection=self.client, offset=offset, max_records=max_records, **kwargs)
            res = islice(res, max_records)
            records = [aggregate.to_dict() for aggregate in res]
            count = len(records)
            resp = {"total": total, "page": page, "count": count, "records": records}
            resp["order_by"] = kwargs.get("order_by", "N/A N/A")
        else:
            # list all (without pagination, for compatibility with past implementations)
            res = Aggregate.get_collection(connection=self.client, **kwargs)
            resp = [aggregate.to_dict() for aggregate in res]

        self.logger.debug("list aggregates: %s" % truncate(resp))
        return resp

    @make_request
    def get(self, aggregate_id):
        """get aggregate

        :param kwargs:
        :return:
        """
        # fields = ( TODO in case specific fields are needed )
        fields = None
        aggregate = Aggregate(uuid=aggregate_id)
        aggregate.set_connection(self.client)
        aggregate.get(fields=fields)
        resp = aggregate.to_dict()
        self.logger.debug("get aggregate: %s" % truncate(resp))
        return resp
