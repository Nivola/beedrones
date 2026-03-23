# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2026 CSI-Piemonte

from netapp_ontap.resources.aggregate import Aggregate
from beecell.types.type_string import truncate
from beedrones.ontapp.client import OntapEntity, make_request


class OntapAggregate(OntapEntity):
    """OntapAggregate"""

    resclass = Aggregate

    def list_with_disk_info(self, **kwargs):
        """list aggregates

        :param kwargs:
        :return:
        """
        kwargs.setdefault("fields", ("name", "uuid", "block_storage.primary"))
        kwargs.setdefault("order_by", "name asc")
        return self.list(**kwargs)

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
        fields = kwargs.pop("fields")
        return self.list_entities(OntapAggregate.resclass, fields, **kwargs)

    @make_request
    def get(self, aggregate_id):
        """get aggregate

        :param aggregate_id: aggregate id
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
