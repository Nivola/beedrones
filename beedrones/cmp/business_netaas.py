# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.password import random_password
from urllib.parse import urlencode
from beecell.simple import truncate
from beecell.types.type_dict import dict_get
from beecell.types.type_string import str2bool
from beedrones.cmp.business import CmpBusinessAbstractService
from beedrones.cmp.client import CmpBaseService, CmpApiManagerError, CmpApiClientError
from beedrones.cmp.business_service import CmpBusinessServiceInstanceService, CmpBusinessServiceLinkService
from beedrones.cmp.business_cpaas import CmpBusinessCpaasInstanceService


class CmpBusinessNetaasService(CmpBusinessAbstractService):
    """Cmp business compute service"""

    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        self.backup = None
        self.vpc = CmpBusinessNetaasVpcService(self.manager)
        self.sg = CmpBusinessNetaasSecurityGroupService(self.manager)
        self.internet_gateway = CmpBusinessNetaasGatewayService(self.manager)
        self.health_monitor = CmpBusinessNetaasLoadBalancerHealthMonitorService(self.manager)
        self.target_group = CmpBusinessNetaasLoadBalancerTargetGroupService(self.manager)
        self.listener = CmpBusinessNetaasLoadBalancerListenerService(self.manager)
        self.load_balancer = CmpBusinessNetaasLoadBalancerService(self.manager)


class CmpBusinessNetaasVpcService(CmpBusinessAbstractService):
    """Cmp business network service - vpc"""

    VERSION = "v2.0"

    def list(self, *args, **kwargs):
        """get vpcs

        :param accounts: list of account id comma separated
        :param page: list page
        :param size: list page size
        :param tags: list of tag comma separated
        :param states: list of state comma separated
        :param ids: list of vpc id comma separated
        :param name: list of vpc id comma separated
        :return: list of vpcs {'count':.., 'page':.., 'total':.., 'sort':.., 'vpcs':..}
        :raise CmpApiClientError:
        """
        params = ["accounts", "states", "tags", "ids"]
        mappings = {
            "tags": lambda x: x.split(","),
            "ids": lambda x: x.split(","),
            "states": lambda x: x.split(","),
        }
        aliases = {
            "accounts": "owner-id.N",
            "ids": "instance-id.N",
            "tags": "tag-value.N",
            "states": "state.N",
            "size": "Nvl_MaxResults",
            "page": "Nvl_NextToken",
        }
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri("networkservices/vpc/describevpcs", preferred_version=self.VERSION, **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, "DescribeVpcsResponse")
        res = {
            "count": len(res.get("vpcSet")),
            "page": kwargs.get("NextToken", 0),
            "total": res.get("nvl-vpcTotal"),
            "sort": {"field": "id", "order": "asc"},
            "vpcs": res.get("vpcSet"),
        }
        self.logger.debug("get vpcs: %s" % truncate(res))
        return res

    def get(self, oid, **kwargs):
        """get vpc

        :param oid: vpc id or uuid
        :return: vpc
        :raise CmpApiClientError:
        """
        if self.is_uuid(oid):
            kwargs.update({"vpc-id.N": [oid]})
        params = ["vpc-id.N"]
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri("computeservices/vpc/describevpcs", preferred_version="v1.0", **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, "DescribeVpcsResponse.vpcSet", default=[])
        if len(res) > 0:
            res = res[0]
        else:
            raise CmpApiManagerError("vpc %s does not exist" % oid)
        self.logger.debug("get vpc%s: %s" % (oid, truncate(res)))
        return res


class CmpBusinessNetaasSubnetService(CmpBusinessAbstractService):
    """Cmp business network service - subnet"""

    VERSION = "v1.0"


class CmpBusinessNetaasSecurityGroupService(CmpBusinessAbstractService):
    """Cmp business network service - security group"""

    VERSION = "v1.0"

    def list(self, *args, **kwargs):
        """get security groups

        :param accounts: list of account id comma separated
        :param ids: list of security group id comma separated
        :param vpcs: list of vpc id comma separated
        :param tags: list of tag comma separated
        :param page: list page
        :param size: list page size
        :return: list of security groups {'count':.., 'page':.., 'total':.., 'sort':.., 'security_groups':..}
        :raise CmpApiClientError:
        """
        params = ["accounts", "ids", "tags", "vpcs"]
        mappings = {
            "tags": lambda x: x.split(","),
            "vpcs": lambda x: x.split(","),
            "ids": lambda x: x.split(","),
        }
        aliases = {
            "accounts": "owner-id.N",
            "ids": "group-id.N",
            "tags": "tag-key.N",
            "vpcs": "vpc-id.N",
            "size": "MaxResults",
            "page": "NextToken",
        }
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri(
            "computeservices/securitygroup/describesecuritygroups",
            preferred_version="v1.0",
            **kwargs,
        )
        res = self.api_get(uri, data=data)
        res = dict_get(res, "DescribeSecurityGroupsResponse")
        res = {
            "count": len(res.get("securityGroupInfo")),
            "page": kwargs.get("page", 0),
            "total": res.get("nvl-securityGroupTotal"),
            "sort": {"field": "id", "order": "asc"},
            "security_groups": res.get("securityGroupInfo"),
        }
        self.logger.debug("get security groups: %s" % truncate(res))
        return res

    def get(self, oid, **kwargs):
        """get security group

        :param oid: security group id or uuid
        :return: security groups
        :raise CmpApiClientError:
        """
        args = {"GroupName.N": [oid]}
        params = ["GroupName.N", "name.N"]
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri(
            "computeservices/securitygroup/describesecuritygroups",
            preferred_version="v1.0",
            **args,
        )
        res = self.api_get(uri, data=data)
        res = dict_get(res, "DescribeSecurityGroupsResponse.securityGroupInfo", default=[])
        if len(res) > 0:
            res = res[0]
        else:
            raise CmpApiManagerError("security group %s does not exist" % oid)
        self.logger.debug("get security group %s: %s" % (oid, truncate(res)))
        return res

    def add(self, name, vpc, template=None, **kwargs):
        """Add security group

        :param str name: security group name
        :param str vpc: parent vpc id
        :param str template: security group template id [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {"GroupName": name, "VpcId": vpc}
        sg_type = template
        if sg_type is not None:
            data["GroupType"] = sg_type

        uri = self.get_uri("computeservices/securitygroup/createsecuritygroup")
        res = self.api_post(uri, data={"security_group": data})
        res = dict_get(res, "CreateSecurityGroupResponse.groupId")
        self.logger.debug("Create security group %s" % res)
        return res

    def delete(self, oid):
        """Delete security group

        :param oid: id of the security group
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri("computeservices/securitygroup/deletesecuritygroup")
        self.api_delete(uri, data={"security_group": {"GroupName": oid}})
        self.logger.debug("delete security group %s" % oid)

    def add_rule(self, oid, rule_type, proto=None, port=None, dest=None, source=None):
        """add security group rule

        :param oid: id of the security group
        :param rule_type: egress or ingress. For egress rule the destination. For ingress rule specify the source
        :param proto: protocol. can be tcp, udp, icmp or -1 for all. [optional]
        :param port: can be an integer between 0 and 65535 or a range with start and end in the same interval. Range
            format is <start>-<end>. Use -1 for all ports. Set subprotocol if proto is icmp (8 for ping). [optional]
        :param dest: rule destination. Syntax <type>:<value>. Destination type can be SG, CIDR. For SG value must be
            <sg_id>. For CIDR value should like 10.102.167.0/24. [optional]
        :param source: rule source. Syntax <type>:<value>. Source type can be SG, CIDR. For SG value must be <sg_id>.
            For CIDR value should like 10.102.167.0/24. [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        from_port = -1
        to_port = -1
        if port is not None:
            port = str(port)
            port = port.split("-")
            if len(port) == 1:
                from_port = to_port = port[0]
            else:
                from_port, to_port = port

        if proto is None:
            proto = "-1"

        if rule_type not in ["ingress", "egress"]:
            raise CmpApiClientError("rule type must be ingress or egress")
        if rule_type == "ingress":
            if source is None:
                raise CmpApiClientError("ingress rule require source")
            dest = source.split(":")
        elif rule_type == "egress":
            if dest is None:
                raise CmpApiClientError("egress rule require destination")
            dest = dest.split(":")
        if dest[0] not in ["SG", "CIDR"]:
            raise CmpApiClientError("source/destination type must be SG or CIDR")
        data = {
            "GroupName": oid,
            "IpPermissions.N": [{"FromPort": from_port, "ToPort": to_port, "IpProtocol": proto}],
        }
        if dest[0] == "SG":
            data["IpPermissions.N"][0]["UserIdGroupPairs"] = [{"GroupName": dest[1]}]
        elif dest[0] == "CIDR":
            data["IpPermissions.N"][0]["IpRanges"] = [{"CidrIp": dest[1]}]
        else:
            raise Exception("Wrong rule type")

        if rule_type == "egress":
            uri = self.get_uri("computeservices/securitygroup/authorizesecuritygroupegress")
            self.task_key = "AuthorizeSecurityGroupEgressResponse.nvl-activeTask"
        elif rule_type == "ingress":
            uri = self.get_uri("computeservices/securitygroup/authorizesecuritygroupingress")
            self.task_key = "AuthorizeSecurityGroupIngressResponse.nvl-activeTask"
        res = self.api_post(uri, data={"rule": data})
        self.logger.debug("create security group %s rule" % oid)
        return res

    def del_rule(self, oid, rule_type, proto=None, port=None, dest=None, source=None):
        """delete security group rule

        :param oid: id of the security group
        :param rule_type: egress or ingress. For egress rule the destination. For ingress rule specify the source
        :param proto: protocol. can be tcp, udp, icmp or -1 for all. [optional]
        :param port: can be an integer between 0 and 65535 or a range with start and end in the same interval. Range
            format is <start>-<end>. Use -1 for all ports. Set subprotocol if proto is icmp (8 for ping). [optional]
        :param dest: rule destination. Syntax <type>:<value>. Destination type can be SG, CIDR. For SG value must be
            <sg_id>. For CIDR value should like 10.102.167.0/24. [optional]
        :param source: rule source. Syntax <type>:<value>. Source type can be SG, CIDR. For SG value must be <sg_id>.
            For CIDR value should like 10.102.167.0/24. [optional]
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        from_port = -1
        to_port = -1
        if port is not None:
            port = str(port)
            port = port.split("-")
            if len(port) == 1:
                from_port = to_port = port[0]
            else:
                from_port, to_port = port

        if proto is None:
            proto = "-1"

        if rule_type not in ["ingress", "egress"]:
            raise Exception("rule type must be ingress or egress")
        if rule_type == "ingress":
            if source is None:
                raise Exception("ingress rule require source")
            dest = source.split(":")
        elif rule_type == "egress":
            if dest is None:
                raise Exception("egress rule require destination")
            dest = dest.split(":")
        if dest[0] not in ["SG", "CIDR"]:
            raise Exception("source/destination type must be SG or CIDR")
        data = {
            "GroupName": oid,
            "IpPermissions.N": [{"FromPort": from_port, "ToPort": to_port, "IpProtocol": proto}],
        }
        if dest[0] == "SG":
            data["IpPermissions.N"][0]["UserIdGroupPairs"] = [{"GroupName": dest[1]}]
        elif dest[0] == "CIDR":
            data["IpPermissions.N"][0]["IpRanges"] = [{"CidrIp": dest[1]}]
        else:
            raise Exception("wrong rule type")

        if rule_type == "egress":
            uri = self.get_uri("computeservices/securitygroup/revokesecuritygroupegress")
            self.task_key = "RevokeSecurityGroupEgressResponse.nvl-activeTask"
        elif rule_type == "ingress":
            uri = self.get_uri("computeservices/securitygroup/revokesecuritygroupingress")
            self.task_key = "RevokeSecurityGroupIngressResponse.nvl-activeTask"
        self.api_delete(uri, data={"rule": data})
        self.logger.debug("delete security group %s rule" % oid)


class CmpBusinessNetaasGatewayService(CmpBusinessAbstractService):
    """Cmp business network service - gateway"""

    VERSION = "v1.0"

    def list(self, *args, **kwargs):
        """Get internet gateways

        :param kwargs:
        :return:
        """
        params = ["accounts", "ids"]
        mappings = {"ids": lambda x: x.split(",")}
        aliases = {
            "accounts": "owner-id.N",
            "ids": "InternetGatewayId.N",
            "size": "MaxResults",
            "page": "NextToken",
        }
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri("networkservices/gateway/describeinternetgateways", preferred_version=self.VERSION, **kwargs)
        res = self.api_get(uri, data=data)
        res = dict_get(res, "DescribeInternetGatewaysResponse.internetGatewaySet", default=[])
        return res

    def get(self, oid, **kwargs):
        """get internet gateway

        :param oid: internet gateway id or uuid
        :return: dict of internet gateway details
        :raise CmpApiClientError:
        """
        if self.is_uuid(oid):
            kwargs.update({"InternetGatewayId.N": [oid]})
        params = ["InternetGatewayId.N"]
        data = self.format_paginated_query(kwargs, params)
        uri = self.get_uri(
            "networkservices/gateway/describeinternetgateways",
            preferred_version="v1.0",
            **kwargs,
        )
        res = self.api_get(uri, data=data)
        res = dict_get(res, "DescribeInternetGatewaysResponse.internetGatewaySet", default=[])
        if len(res) > 0:
            res = res[0]
        else:
            raise CmpApiManagerError("Internet gateway %s does not exist" % oid)
        self.logger.debug("Get internet gateway %s: %s" % (oid, truncate(res)))
        return res


class CmpBusinessNetaasLoadBalancerAbstractService(CmpBusinessAbstractService):
    """Cmp business network service - abstract load balancer"""

    VERSION = "v1.0"
    PREFIX = "nws/"

    def __init__(self, manager):
        CmpBusinessAbstractService.__init__(self, manager)
        self.serv_instance = CmpBusinessServiceInstanceService(self.manager)
        self.cpaas_instance = CmpBusinessCpaasInstanceService(self.manager)
        self.link = CmpBusinessServiceLinkService(self.manager)

    def do_check(self, account, inst_name, inst_type):
        data = {"account_id": account, "plugintype": inst_type, "name": inst_name, "flag_container": False, "size": -1}
        instances = self.serv_instance.list(**data).get("serviceinsts", [])
        if len(instances) > 0:
            return instances[0].get("uuid")
        return None


class CmpBusinessNetaasLoadBalancerHealthMonitorService(CmpBusinessNetaasLoadBalancerAbstractService):
    """Cmp business network service - load balancer/health monitor"""

    TYPE = "NetworkHealthMonitor"

    def list(self, account, **kwargs):
        """Get health monitors

        :param account:
        :param kwargs:
        :return:
        """
        params = ["accounts", "ids", "tags"]
        mappings = {
            "accounts": account,
            "ids": lambda x: x.split(","),
            "tags": lambda x: x.split(","),
        }
        aliases = {
            "accounts": "owner-id.N",
            "ids": "HealthMonitorId.N",
            "tags": "tag-key.N",
            "size": "MaxResults",
            "page": "Nvl-NextToken",
        }
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri(
            "networkservices/loadbalancer/healthmonitor/describehealthmonitors",
            preferred_version=self.VERSION,
            **kwargs,
        )
        res = self.api_get(uri, data=data)
        res = res.get("DescribeHealthMonitorsResponse", {})
        return res

    def get(self, oid, **kvargs):
        """Get health monitor

        :param oid: health monitor id or uuid
        :return: health monitor details
        :raise CmpApiClientError:
        """
        data = {"HealthMonitorId.N": [oid]}
        uri = self.get_uri(
            "networkservices/loadbalancer/healthmonitor/describehealthmonitors",
            preferred_version=self.VERSION,
            **kvargs,
        )
        res = self.api_get(uri, data=urlencode(data, doseq=True))
        res = dict_get(res, "DescribeHealthMonitorsResponse.healthMonitorSet")
        if len(res) != 1:
            raise CmpApiManagerError("Health monitor %s does not exist or is not unique" % oid)
        res = res[0]
        self.logger.debug("get health monitor %s: %s" % (oid, truncate(res)))
        return res

    def load(self, account, **kvargs):
        """Import health monitor

        :param account:
        :param kvargs:
        :return:
        """
        hm_name = kvargs.get("name")
        hm_id = self.do_check(account, hm_name, self.TYPE)
        if hm_id is not None:
            raise Exception("health monitor %s already exists in account %s" % (hm_name, account))
        hm_data = {
            "owner-id": account,
            "Name": hm_name,
            "Protocol": kvargs.get("type").upper(),
            "Interval": kvargs.get("interval"),
            "Timeout": kvargs.get("timeout"),
            "MaxRetries": kvargs.get("maxRetries"),
            "Method": kvargs.get("method"),
            "RequestURI": kvargs.get("url"),
            "Expected": kvargs.get("expected"),
        }
        uri = self.get_uri(
            "networkservices/loadbalancer/healthmonitor/createhealthmonitor", preferred_version=self.VERSION, **kvargs
        )
        res = self.api_post(uri, data={"health_monitor": hm_data})
        hm_id = dict_get(res, "CreateHealthMonitorResponse.HealthMonitor.healthMonitorId")
        print("imported health monitor: %s" % hm_id)
        return hm_id


class CmpBusinessNetaasLoadBalancerTargetGroupService(CmpBusinessNetaasLoadBalancerAbstractService):
    """Cmp business network service - load balancer/target group"""

    TYPE = "NetworkTargetGroup"

    def load(self, account, **kvargs):
        """Import target group

        :param account:
        :param kvargs:
        :return:
        """
        tg_name = kvargs.get("name")
        tg_id = self.do_check(account, tg_name, self.TYPE)
        if tg_id is not None:
            raise Exception("target group %s already exists in account %s" % (tg_name, account))
        tg_data = {
            "owner-id": account,
            "Name": kvargs.get("name"),
            "Description": kvargs.get("description", tg_name),
            "BalancingAlgorithm": kvargs.get("algorithm"),
            "TargetType": kvargs.get("type", "vm"),
            "HealthMonitor": kvargs.get("health_monitor"),
            "Transparent": kvargs.get("transparent"),
        }
        uri = self.get_uri(
            "networkservices/loadbalancer/targetgroup/createtargetgroup", preferred_version=self.VERSION, **kvargs
        )
        res = self.api_post(uri, data={"target_group": tg_data})
        tg_id = dict_get(res, "CreateTargetGroupResponse.TargetGroup.targetGroupId")
        print("imported target group: %s" % tg_id)
        return tg_id

    def register_targets(self, account, oid, members, **kvargs):
        """

        :param account:
        :param oid:
        :param members:
        :param kvargs:
        :return:
        """
        print("registering targets with target group ...")
        if not isinstance(members, list):
            members = [members]
        targets_data = {"TargetGroupId": oid, "Targets": []}
        target_ids = []
        for member in members:
            target_name = member.get("name")
            data = {"accounts": account, "name": target_name, "size": -1}
            instances = self.cpaas_instance.list(**data).get("instances")
            if len(instances) > 0:
                instance = instances[0]
                target = {
                    "Id": instance.get("instanceId"),
                    "LbPort": member.get("port"),
                    "HmPort": member.get("monitorPort"),
                }
                targets_data["Targets"].append(target)
                target_ids.append(instance.get("instanceId"))
        uri = self.get_uri(
            "networkservices/loadbalancer/targetgroup/registertargets", preferred_version=self.VERSION, **kvargs
        )
        res = self.api_put(uri, data={"target_group": targets_data})
        if len(target_ids) == 0:
            print("no target to register")
        else:
            print("targets registered")
        return target_ids

    def get_health_monitor(self, oid):
        """Get health monitor linked to target group

        :param oid: target group id
        :return:
        """
        data = {"type": "tg-hm", "start_service": oid}
        bu_links = self.link.list(**data)
        bu_link_id = None
        hm_id = None
        if len(bu_links) > 0:
            bu_link = bu_links[0]
            bu_link_id = bu_link.get("id")
            hm_id = dict_get(bu_link, "details.end_service.id")
        return bu_link_id, hm_id

    def delete(self, oid, **kvargs):
        """Delete target group

        :param oid: target group id
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri(
            "networkservices/loadbalancer/targetgroup/deletetargetgroup", preferred_version=self.VERSION, **kvargs
        )
        self.api_delete(uri, data={"targetGroupId": str(oid)})
        self.logger.debug("delete lb target group %s" % oid)


class CmpBusinessNetaasLoadBalancerListenerService(CmpBusinessNetaasLoadBalancerAbstractService):
    """Cmp business network service - load balancer/listener"""

    TYPE = "NetworkListener"

    def list(self, account, **kwargs):
        """Get listeners

        :param account:
        :param kwargs:
        :return:
        """
        params = ["accounts", "ids", "tags"]
        mappings = {
            "accounts": account,
            "ids": lambda x: x.split(","),
            "tags": lambda x: x.split(","),
        }
        aliases = {
            "accounts": "owner-id.N",
            "ids": "ListenerId.N",
            "tags": "tag-key.N",
            "size": "MaxResults",
            "page": "Nvl-NextToken",
        }
        data = self.format_paginated_query(kwargs, params, mappings=mappings, aliases=aliases)
        uri = self.get_uri(
            "networkservices/loadbalancer/listener/describelisteners", preferred_version=self.VERSION, **kwargs
        )
        res = self.api_get(uri, data=data)
        res = res.get("DescribeListenersResponse", {})
        return res

    def get(self, oid, **kvargs):
        """Get listener

        :param oid: listener id or uuid
        :return: listener details
        :raise CmpApiClientError:
        """
        data = {"ListenerId.N": [oid]}
        uri = self.get_uri(
            "networkservices/loadbalancer/listener/describelisteners", preferred_version=self.VERSION, **kvargs
        )
        res = self.api_get(uri, data=urlencode(data, doseq=True))
        res = dict_get(res, "DescribeListenersResponse.listenerSet")
        if len(res) != 1:
            raise CmpApiManagerError("listener %s does not exist or is not unique" % oid)
        res = res[0]
        self.logger.debug("get listener %s: %s" % (oid, truncate(res)))
        return res

    def load(self, account, **kvargs):
        """Import listener

        :param account:
        :param kvargs:
        :return:
        """
        li_name = kvargs.get("name")
        li_name = li_name.replace("_", "-")
        li_id = self.do_check(account, li_name, self.TYPE)
        if li_id is not None:
            raise Exception("listener %s already exists in account %s" % (li_name, account))
        li_data = {
            "owner-id": account,
            "Name": li_name,
            "Description": kvargs.get("description", li_name),
            "TrafficType": kvargs.get("template").lower(),
            "Persistence": dict_get(kvargs, "persistence.method"),
            "CookieName": dict_get(kvargs, "persistence.cookieName"),
            "CookieMode": dict_get(kvargs, "persistence.cookieMode"),
            "ExpireTime": dict_get(kvargs, "persistence.expire"),
            "InsertXForwardedFor": str2bool(kvargs.get("insertXForwardedFor")),
        }
        http_redirect = kvargs.get("httpRedirect")
        if http_redirect is not None:
            li_data.update({"URLRedirect": http_redirect.get("to")})
        uri = self.get_uri(
            "networkservices/loadbalancer/listener/createlistener", preferred_version=self.VERSION, **kvargs
        )
        res = self.api_post(uri, data={"listener": li_data})
        li_id = dict_get(res, "CreateListenerResponse.Listener.listenerId")
        print("imported listener: %s" % li_id)
        return li_id

    def delete(self, oid, **kwargs):
        """Delete listener

        :param oid: id of the listener
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri(
            "networkservices/loadbalancer/listener/deletelistener", preferred_version=self.VERSION, **kwargs
        )
        self.api_delete(uri, data={"listenerId": str(oid)})
        self.logger.debug("delete lb listener %s" % oid)


class CmpBusinessNetaasLoadBalancerService(CmpBusinessNetaasLoadBalancerAbstractService):
    """Cmp business network service - load balancer"""

    TYPE = "NetworkLoadBalancer"

    def get(self, oid, **kvargs):
        """Get load balancer

        :param oid: load balancer id or uuid
        :return: load balancer details
        :raise CmpApiClientError:
        """
        data = {"LoadBalancerId.N": [oid]}
        uri = self.get_uri(
            "networkservices/loadbalancer/describeloadbalancers", preferred_version=self.VERSION, **kvargs
        )
        res = self.api_get(uri, data=urlencode(data, doseq=True))
        res = dict_get(res, "DescribeLoadBalancersResponse.loadBalancerSet")
        if len(res) > 0:
            res = res[0]
        else:
            raise CmpApiManagerError("load balancer %s not found" % oid)
        self.logger.debug("get load balancer %s: %s" % (oid, truncate(res)))
        return res

    def load(self, account, **kvargs):
        """Import load balancer

        :param account:
        :param kvargs:
        :return:
        """
        lb_name = kvargs.get("name")
        lb_id = self.do_check(account, lb_name, self.TYPE)
        if lb_id is not None:
            raise Exception("load balancer %s already exists in account %s" % (lb_name, account))
        lb_data = {
            "owner-id": account,
            "Name": lb_name,
            "Template": kvargs.get("template"),
            "Protocol": kvargs.get("protocol").upper(),
            "Port": kvargs.get("port"),
            "VirtualIpAddress": kvargs.get("ipAddress"),
            "isVIPStatic": kvargs.get("is_vip_static"),
            "Listener": kvargs.get("listener"),
            "TargetGroup": kvargs.get("target_group"),
            "MaxConnections": kvargs.get("connectionLimit"),
            "MaxConnectionRate": kvargs.get("connectionRateLimit"),
            "ResourceId": kvargs.get("resource_id"),
            "DeploymentEnvironment": kvargs.get("deployment_env"),
        }
        uri = self.get_uri("networkservices/loadbalancer/importloadbalancer", preferred_version=self.VERSION, **kvargs)
        res = self.api_post(uri, data={"load_balancer": lb_data})
        lb_id = dict_get(res, "ImportLoadBalancerResponse.LoadBalancer.loadBalancerId")
        print("imported load balancer: %s" % lb_id)
        return lb_id

    def delete(self, oid, no_linked_objs=False, **kvargs):
        """Delete load balancer

        :param oid: load balancer id or uuid
        :param no_linked_objs:
        :return: load balancer details
        :raise CmpApiClientError:
        """
        uri = self.get_uri("networkservices/loadbalancer/deleteloadbalancer", preferred_version=self.VERSION, **kvargs)
        self.api_delete(uri, data={"loadBalancerId": str(oid), "no_linked_objs": no_linked_objs})
        self.logger.debug("delete load balancer %s" % oid)

    def get_listener(self, oid):
        """Get listener linked to load balancer

        :param oid: load balancer id
        :return:
        """
        data = {"type": "lb-li", "start_service": oid}
        bu_links = self.link.list(**data)
        bu_link = bu_links[0]
        bu_link_id = bu_link.get("id")
        li_id = dict_get(bu_link, "details.end_service.id")
        return bu_link_id, li_id

    def get_target_group(self, oid):
        """Get target group linked to load balancer

        :param oid: load balancer id
        :return:
        """
        data = {"type": "lb-tg", "start_service": oid}
        bu_links = self.link.list(**data)
        bu_link = bu_links[0]
        bu_link_id = bu_link.get("id")
        tg_id = dict_get(bu_link, "details.end_service.id")
        return bu_link_id, tg_id
