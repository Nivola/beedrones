# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2023 CSI-Piemonte
from six import ensure_text

from beecell.simple import truncate, get_attrib
from beedrones.vsphere.client import VsphereObject, VsphereError


class VsphereNetworkDfw(VsphereObject):
    """Distributed Firewall Helper"""

    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def query_status(self):
        """Get firewall configuration status

        :return:
        """
        res = self.call("/api/4.0/firewall/globalroot-0/status", "GET", "")
        res = res["firewallStatus"]

        return res

    def query_section_status(self, section):
        """Get firewall Layer3 status

        :param section: section id
        :return:
        """
        res = self.call(
            "/api/4.0/firewall/globalroot-0/status/layer3sections/%s" % section,
            "GET",
            "",
        )
        res = res["firewallStatus"]

        return res

    def get_config(self):
        """ """
        res = self.call("/api/4.0/firewall/globalroot-0/config", "GET", "")
        return res["firewallConfiguration"]

    def get_sections(self, rule_type="LAYER2"):
        """Get list of section with rules.

        :param rule_type: rule type. Can be LAYER3, L3REDIRECT. If
                          not specify return all the sections [optional]
        :return:
        """
        res = self.call("/api/4.0/firewall/globalroot-0/config?ruleType=%s" % rule_type, "GET", "")
        res = res["filteredfirewallConfiguration"]

        return res

    def get_layer3_section(self, sectionid=None, name=None):
        """
        :param sectionid: section id
        :param name: section name
        :return: json string

        Return example:

            .. code-block:: python

                {
                    "@name": "Default Section Layer3",
                    "@timestamp": "1472659441651",
                    "@generationNumber": "1472659441651",
                    "@id": "1031",
                    "@type": "LAYER3"
                    "rule": [
                        {
                            "direction": "inout",
                            "name": "Default Rule",
                            "precedence": "default",
                            "sectionId": "1031",
                            "@logged": "true",
                            "@disabled": "false",
                            "action": "deny",
                            "appliedToList": {
                                "appliedTo": {
                                    "isValid": "true",
                                    "type": "DISTRIBUTED_FIREWALL",
                                    "name": "DISTRIBUTED_FIREWALL",
                                    "value": "DISTRIBUTED_FIREWALL"
                                }
                            },
                            "packetType": "any",
                            "@id": "133087"
                        },..
                    ]
                }
        """
        if sectionid is not None:
            res = self.call(
                "/api/4.0/firewall/globalroot-0/config/layer3sections/%s" % sectionid,
                "GET",
                "",
            )
            return res["section"]
        elif name is not None:
            res = self.call(
                "/api/4.0/firewall/globalroot-0/config/layer3sections?name=%s" % name,
                "GET",
                "",
            )
            return res["sections"]["section"]

    def get_rule(self, sectionid, ruleid):
        """
        :param sectionid: section id
        :param ruleid: rule id
        :return: json string

        Return example:

            .. code-block:: python

                {
                    "direction": "inout",
                    "name": "Default Rule",
                    "precedence": "default",
                    "@logged": "true",
                    "@disabled": "false",
                    "action": "deny",
                    "appliedToList": {
                        "appliedTo": {
                            "isValid": "true",
                            "type": "DISTRIBUTED_FIREWALL",
                            "name": "DISTRIBUTED_FIREWALL",
                            "value": "DISTRIBUTED_FIREWALL"
                        }
                    },
                    "packetType": "any",
                    "@id": "133087"
                }
        """
        uri = "/api/4.0/firewall/globalroot-0/config/layer3sections/%s/rules/%s" % (
            sectionid,
            ruleid,
        )
        res = self.call(uri, "GET", "").get("rule", {})
        if res.get("sectionId", None) != sectionid:
            res = {}
        return res

    def filter_rules(self, security_groups=None):
        """Get list of rules that respect filter fields

        :param security_groups: list of security group mor_id
        """
        res = []
        data = self.call("/api/4.0/firewall/globalroot-0/config?action=allow", "GET", "")
        data = data.get("firewallConfiguration", {}).get("layer3Sections", [])
        sections = data.get("section", [])
        if type(sections) is not list:
            sections = [sections]
        for section in sections:
            rules = section.get("rule", [])
            if type(rules) is not list:
                rules = [rules]
            if len(rules) > 0:
                for rule in rules:
                    source = rule.get("sources", {}).get("source", {})
                    if type(source) is list:
                        source = source[0]
                    dest = rule.get("destinations", {}).get("destination", {})
                    if type(dest) is list:
                        dest = dest[0]
                    if source.get("type") == "SecurityGroup" and source.get("value") in security_groups:
                        res.append(rule)
                    if dest.get("type") == "SecurityGroup" and dest.get("value") in security_groups:
                        res.append(rule)
        self.logger.debug(("Found dfw rules: %s" % truncate(res)))
        return res

    def index_rules(self, security_groups=None):
        """Get index of rules with key the filter field

        :param security_groups: list of security group mor_id
        """
        res = {}
        data = self.call("/api/4.0/firewall/globalroot-0/config", "GET", "")
        data = data.get("firewallConfiguration", {}).get("layer3Sections", [])
        sections = data.get("section", [])
        if type(sections) is not list:
            sections = [sections]
        for section in sections:
            rules = section.get("rule", [])
            if type(rules) is not list:
                rules = [rules]
            if len(rules) > 0:
                for rule in rules:
                    source = rule.get("sources", {}).get("source", {})
                    if type(source) is list:
                        source = source[0]
                    dest = rule.get("destinations", {}).get("destination", {})
                    if type(dest) is list:
                        dest = dest[0]
                    if source.get("type") == "SecurityGroup" and source.get("value") in security_groups:
                        try:
                            res[source.get("value")].append(rule)
                        except:
                            res[source.get("value")] = [rule]
                    elif dest.get("type") == "SecurityGroup" and dest.get("value") in security_groups:
                        try:
                            res[source.get("value")].append(rule)
                        except:
                            res[source.get("value")] = [rule]
        self.logger.debug(("Found dfw rules: %s" % truncate(res)))
        return res

    def print_sections(self, sections, print_rules=True, table=True):
        """Print pretty all the firewall rules and section

        :param print_rules: if True print rules detail
        """
        l3sections = sections["layer3Sections"]["section"]
        if type(l3sections) is not list:
            l3sections = [l3sections]
        for l3section in l3sections:
            if print_rules is True:
                self.print_section(l3section, table)
            else:
                self.logger.info("%-10s%-70s%15s" % (l3section["@id"], l3section["@name"], l3section["@timestamp"]))
        l2sections = sections["layer2Sections"]["section"]
        if type(l2sections) is not list:
            l2sections = [l2sections]
        for l2section in l2sections:
            if print_rules is True:
                self.print_section(l2section, table)
            else:
                self.logger.info("%-10s%-70s%15s" % (l3section["@id"], l3section["@name"], l3section["@timestamp"]))

    def print_section(self, l3section, table=True):
        """Print pretty all the firewall rules and section"""
        self.logger.info("".join(["#" for i in range(120)]))
        self.logger.info("%-10s%-70s%15s" % (l3section["@id"], l3section["@name"], l3section["@timestamp"]))
        self.logger.info("".join(["#" for i in range(120)]))

        if table is True:
            tmpl = "%-8s%-20s%-9s%-9s%-10s%-8s%20s%20s%20s%20s"
            title = (
                "id",
                "name",
                "logged",
                "disabled",
                "direction",
                "action",
                "sources",
                "destinations",
                "services",
                "appliedto",
            )
            self.logger.info(tmpl % title)
            self.logger.info("".join(["-" for i in range(150)]))

        rules = l3section["rule"]
        if type(rules) is not list:
            rules = [rules]

        for rule in rules:
            if table is True:
                # sources
                sources = []
                try:
                    source = rule["sources"]
                    infos = source["source"]
                    if type(infos) is not list:
                        infos = [infos]
                    for info in infos:
                        try:
                            name = info["name"]
                        except:
                            name = ""
                        sources.append(name)
                except:
                    sources.append("* any")

                # destinations
                destinations = []
                try:
                    source = rule["destinations"]
                    infos = source["destination"]
                    if type(infos) is not list:
                        infos = [infos]
                    for info in infos:
                        try:
                            name = info["name"]
                        except:
                            name = ""
                        destinations.append(name)
                except:
                    destinations.append("* any")

                # services
                services = []
                try:
                    source = rule["services"]
                    infos = source["service"]
                    if type(infos) is not list:
                        infos = [infos]
                    for info in infos:
                        try:
                            name = truncate(info["name"], 5)
                        except:
                            name = ""
                        services.append(name)
                except:
                    services.append("* any")

                # appliedToList
                appliedto = []
                try:
                    source = rule["appliedToList"]
                    infos = source["appliedTo"]
                    if type(infos) is not list:
                        infos = [infos]
                    for info in infos:
                        try:
                            name = truncate(info["name"], 9)
                        except:
                            name = ""
                        appliedto.append(name)
                except:
                    appliedto.append("* any")

                row = (
                    rule["@id"],
                    rule["name"],
                    rule["@logged"],
                    rule["@disabled"],
                    rule["direction"],
                    rule["action"],
                    ",".join(sources),
                    ",".join(destinations),
                    ",".join(services),
                    ",".join(appliedto),
                )
                self.logger.info(tmpl % row)
            else:
                self.print_rule(rule)
                self.logger.info("  " + "".join(["-" for i in range(100)]))

    def print_rule(self, rule):
        """Print pretty all the firewall rules and section"""
        tmpl = "   %-15s:%20s"
        self.logger.info(tmpl % ("id", rule["@id"]))
        self.logger.info(tmpl % ("name", rule["name"]))
        self.logger.info(tmpl % ("logged", rule["@logged"]))
        self.logger.info(tmpl % ("disabled", rule["@disabled"]))
        self.logger.info(tmpl % ("direction", rule["direction"]))
        self.logger.info(tmpl % ("action", rule["action"]))

        # sources
        self.logger.info(tmpl % ("sources:", ""))
        try:
            source = rule["sources"]
            infos = source["source"]
            if type(infos) is not list:
                infos = [infos]
            for info in infos:
                name = info.get("name", "")
                self.logger.info("%20s %s : %s : %s" % ("", name, info["value"], info["type"]))
        except Exception:
            self.logger.info("%20s %s %s" % ("", "*", "any"))

        # destinations
        self.logger.info(tmpl % ("destinations:", ""))
        try:
            source = rule["destinations"]
            infos = source["destination"]
            if type(infos) is not list:
                infos = [infos]
            for info in infos:
                name = info.get("name", "")
                self.logger.info("%20s %s : %s : %s" % ("", name, info["value"], info["type"]))
        except Exception:
            self.logger.info("%20s %s %s" % ("", "*", "any"))

        # services
        self.logger.info(tmpl % ("services:", ""))
        try:
            source = rule["services"]
            infos = source["service"]
            if type(infos) is not list:
                infos = [infos]
            for info in infos:
                name = info.get("name", "")
                self.logger.info("%20s %s : %s : %s" % ("", name, info["value"], info["type"]))
        except Exception:
            self.logger.info("%20s %s %s" % ("", "*", "any"))

        # appliedToList
        self.logger.info(tmpl % ("applied to:", ""))
        try:
            source = rule["appliedToList"]
            infos = source["appliedTo"]
            if type(infos) is not list:
                infos = [infos]
            for info in infos:
                name = info.get("name", "")
                self.logger.info("%20s %s : %s : %s" % ("", name, info["value"], info["type"]))
        except Exception:
            self.logger.info("%20s %s %s" % ("", "*", "any"))

    def _append_rule_attribute(self, tag, value, rtype, name=None):
        """Append rule internal tag like source, destination and
        appliedToList

        :param tag: tag can be source, destination, appliedTo and service
        :param name: rule name
        :param value: for certain rule contains morId
        :param rtype: type
        :return: list with rule structure
        """
        data = ["<%s>" % tag]

        if name is not None:
            data.append("<name>%s</name>" % name)

        data.extend(
            [
                "<value>%s</value>" % value,
                "<type>%s</type>" % rtype,
                "<isValid>true</isValid>",
                "</%s>" % tag,
            ]
        )
        return data

    def _append_rule_service_attribute(self, value):
        """Append rule internal tag service.

        :param value: contains service morId
        :param rtype: type
        :return: list with rule structure
        """
        data = ["<service><value>%s</value></service>" % value]
        return data

    def _append_rule_definition(self, tags, tag, data):
        res = []
        if data is not None:
            if tags in ["sources", "destinations"]:
                res.append('<%s excluded="false">' % tags)
            else:
                res.append("<%s>" % tags)
            for s in data:
                if s["type"] == "Ipv4Address" and s["value"] == "0.0.0.0/0":
                    if len(data) == 1:
                        return []
                    continue
                res.extend(self._append_rule_attribute(tag, s["value"], s["type"], name=s["name"]))
            res.append("</%s>" % tags)
        return res

    def _append_rule_service(self, data):
        """Append service configuration to rule

        Ex. [{'port':'*', 'protocol':'*'}] -> *:*
            [{'port':'*', 'protocol':6}] -> tcp:*
            [{'port':80, 'protocol':6}] -> tcp:80
            [{'port':80, 'protocol':17}] -> udp:80
            [{'protocol':1, 'subprotocol':8}] -> icmp:echo request
        """
        res = ["<services>"]
        if data is not None:
            for s in data:
                if "value" in s:
                    res.extend("<service><value>%s</value></service>" % s["value"])
                elif not (s["protocol"] == "*" and s["port"] == "*"):
                    # else:
                    if "subprotocol" not in s:
                        s["subprotocol"] = s["protocol"]
                    res.extend("<service>")
                    if "port" not in s or s["port"] == "*":
                        port = ""
                    else:
                        port = s["port"]

                    res.extend("<destinationPort>%s</destinationPort>" % port)
                    res.extend("<protocol>%s</protocol>" % s["protocol"])
                    if s["subprotocol"] != "*":
                        res.extend("<subProtocol>%s</subProtocol>" % s["subprotocol"])
                    res.extend("</service>")
        res.append("</services>")
        return res

    def create_section(self, name, action="allow", logged="false"):
        """Create new section

        :param name: section name
        :param action: new action value. Ie: allow, deny, reject [default=allow]
        :param logged: if True rule is logged [default=false]
        """
        data = ['<section name="%s">' % name, "</section>"]
        data = "".join(data)
        res = self.call(
            "/api/4.0/firewall/globalroot-0/config/layer3sections",
            "POST",
            data,
            headers={
                "Content-Type": "application/xml",
                "If-Match": self.manager.nsx["etag"],
            },
        )
        return res["section"]

    def create_rule(
        self,
        sectionid,
        name,
        action,
        direction="inout",
        logged="false",
        sources=None,
        destinations=None,
        services=None,
        appliedto=None,
        precedence="default",
    ):
        """Create new rule

        :param sectionid: section id
        :param name: rule name
        :param action: new action value. Ie: allow, deny, reject [optional]
        :param logged: if 'true' rule is logged
        :param direction: rule direction: in, out, inout
        :param sources: List like [{'name':, 'value':, 'type':, }] [optional]
            Ex: [{'name':'db-vm-01', 'value':'vm-84', 'type':'VirtualMachine'}]
            Ex: [{'name':None, 'value':'10.1.1.0/24', 'type':'Ipv4Address'}]
            Ex: [{'name':'WEB-LS', 'value':'virtualwire-9',
                  'type':'VirtualWire'}]
            Ex: [{'name':'APP-LS', 'value':'virtualwire-10',
                  'type':'VirtualWire'}]
            Ex: [{'name':'SG-WEB2', 'value':'securitygroup-22',
                  'type':'SecurityGroup'}]
            Ex: [{'name':'PAN-app-vm2-01 - Network adapter 1',
                  'value':'50031300-ad53-cc80-f9cb-a97254336c01.000',
                  'type':'vnic'}]
        :param destinations: List like [{'name':, 'value':, 'type':, }] [optional]
            Ex: [{'name':'WEB-LS', 'value':'virtualwire-9',
                  'type':'VirtualWire'}]
            Ex: [{'name':'APP-LS', 'value':'virtualwire-10',
                  'type':'VirtualWire'}]
            Ex: [{'name':'SG-WEB-1', 'value':'securitygroup-21',
                  'type':'SecurityGroup'}]
        :param services: List like [{'name':, 'value':, 'type':, }] [optional]
            Ex: [{'name':'ICMP Echo Reply', 'value':'application-337',
                  'type':'Application'}]
            Ex: [{'name':'ICMP Echo', 'value':'application-70',
                  'type':'Application'}]
            Ex: [{'name':'SSH', 'value':'application-223',
                  'type':'Application'}]
            Ex: [{'name':'DHCP-Client', 'value':'application-223',
                  'type':'Application'},
                 {'name':'DHCP-Server', 'value':'application-223',
                  'type':'Application'}]
            Ex: [{'name':'HTTP', 'value':'application-278',
                  'type':'Application'},
                 {'name':'HTTPS', 'value':'application-335',
                  'type':'Application'}]
            Ex. [{'port':'*', 'protocol':'*'}] -> *:*
                [{'port':'*', 'protocol':6}] -> tcp:*
                [{'port':80, 'protocol':6}] -> tcp:80
                [{'port':80, 'protocol':17}] -> udp:80
                [{'protocol':1, 'subprotocol':8}] -> icmp:echo request

            Get id from https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
            For icmp Summary of Message Types:
                0  Echo Reply
                3  Destination Unreachable
                4  Source Quench
                5  Redirect
                8  Echo
               11  Time Exceeded
               12  Parameter Problem
               13  Timestamp
               14  Timestamp Reply
               15  Information Request
               16  Information Reply
        :param appliedto: List like [{'name':, 'value':, 'type':, }] [optional]
            Ex: [{'name':'DISTRIBUTED_FIREWALL',
                  'value':'DISTRIBUTED_FIREWALL',
                  'type':'DISTRIBUTED_FIREWALL'}]
            Ex: [{'name':'ALL_PROFILE_BINDINGS',
                  'value':'ALL_PROFILE_BINDINGS',
                  'type':'ALL_PROFILE_BINDINGS'}]
            Ex: [{'name':'db-vm-01', 'value':'vm-84', 'type':'VirtualMachine'}]
            Ex: [{'name':'SG-WEB-1', 'value':'securitygroup-21',
                  'type':'SecurityGroup'},
                 {'name':'SG-WEB2', 'value':'securitygroup-22',
                  'type':'SecurityGroup'}]
        """

        data = [
            '<rule id="0" disabled="false" logged="%s">' % logged,
            "<name>%s</name>" % name,
            "<action>%s</action>" % action,
            "<precedence>%s</precedence>" % precedence,
            "<direction>%s</direction>" % direction,
            "<sectionId>%s</sectionId>" % sectionid,
            "<notes></notes>",
            "<packetType>any</packetType>",
        ]

        data.extend(self._append_rule_definition("sources", "source", sources))
        data.extend(self._append_rule_definition("destinations", "destination", destinations))
        data.extend(self._append_rule_service(services))
        data.extend(self._append_rule_definition("appliedToList", "appliedTo", appliedto))

        data.append("</rule>")

        data = "".join(data)
        res = self.call(
            "/api/4.0/firewall/globalroot-0/config/layer3sections/%s/rules" % sectionid,
            "POST",
            data,
            headers={
                "Content-Type": "application/xml",
                "If-Match": self.manager.nsx["etag"],
            },
        )
        self.logger.debug("Create dfw rule: %s" % res)
        return res["rule"]

    def update_rule(self, sectionid, ruleid, new_action=None, new_disable=None, new_name=None):
        """
        :param sectionid: section id
        :param ruleid: rule id
        :param new_name: new rule name
        :param new_action: new action value. Ie: allow, deny, reject [optional]
        :param new_disable: 'true' if rule is disabled [optional]
        """
        data = self.call(
            "/api/4.0/firewall/globalroot-0/config/layer3sections/%s/rules/%s" % (sectionid, ruleid),
            "GET",
            "",
            parse=False,
        )

        import xml.etree.ElementTree as etree

        root = etree.fromstring(data)

        if new_action is not None:
            action = root.find("action")
            action.text = new_action

        if new_disable is not None:
            root.set("disabled", new_disable)

        if new_name is not None:
            name = root.find("name")
            name.text = new_name

        data = ensure_text(etree.tostring(root))
        res = self.call(
            "/api/4.0/firewall/globalroot-0/config/layer3sections/%s/rules/%s" % (sectionid, ruleid),
            "PUT",
            data,
            headers={
                "Content-Type": "application/xml",
                "If-Match": self.manager.nsx["etag"],
            },
        )

        return res["rule"]

    def move_rule(self, sectionid, ruleid, ruleafter=None):
        """
        :param sectionid: section id
        :param ruleid: rule id
        :param ruleafter: rule id, put rule after this.
        """
        data = self.call(
            "/api/4.0/firewall/globalroot-0/config/layer3sections/%s" % sectionid,
            "GET",
            "",
            parse=False,
        )

        import xml.etree.ElementTree as etree

        root = etree.fromstring(data)
        rule = root.findall("./rule[@id='%s']" % ruleid)
        if len(rule) <= 0:
            raise VsphereError("Rule %s not found" % ruleid)

        rule = rule[0]
        root.remove(rule)
        # insert rule on the top
        if ruleafter is None:
            root.insert(0, rule)

        # insert rule in the given postion
        rules = root.findall("./rule")
        pos = 0
        for r in rules:
            oid = r.get("id")
            pos += 1
            if oid == ruleafter:
                break
        root.insert(pos, rule)

        data = etree.tostring(root)
        res = self.call(
            "/api/4.0/firewall/globalroot-0/config/layer3sections/%s" % sectionid,
            "PUT",
            data,
            headers={
                "Content-Type": "application/xml",
                "If-Match": self.manager.nsx["etag"],
            },
        )

        return res

    def delete_section(self, sectionid):
        """
        :param sectionid: section id
        """
        res = self.call(
            "/api/4.0/firewall/globalroot-0/config/layer3sections/%s" % sectionid,
            "DELETE",
            "",
            headers={
                "Content-Type": "application/xml",
                "If-Match": self.manager.nsx["etag"],
            },
        )
        return res

    def delete_rule(self, sectionid, ruleid):
        """delete rule

        :param sectionid: section id
        :param ruleid: rule id
        """
        res = self.call(
            "/api/4.0/firewall/globalroot-0/config/layer3sections/%s/rules/%s" % (sectionid, ruleid),
            "DELETE",
            "",
            headers={
                "Content-Type": "application/xml",
                "If-Match": self.manager.nsx["etag"],
            },
        )
        return True

    #
    # exclusion_list
    #
    def get_exclusion_list(self):
        res = self.call("/api/2.1/app/excludelist", "GET", "")
        return res["VshieldAppConfiguration"]["excludeListConfiguration"]

    def add_item_to_exclusion_list(self, member_id):
        """add item from exclusion list

        :param member_id: member id
        """
        res = self.call(
            "/api/2.1/app/excludelist/%s" % member_id,
            "PUT",
            "",
            headers={"Content-Type": "application/xml"},
        )
        return True

    def remove_item_from_exclusion_list(self, member_id):
        """remove item from exclusion list

        :param member_id: member id
        """
        res = self.call(
            "/api/2.1/app/excludelist/%s" % member_id,
            "DELETE",
            "",
            headers={"Content-Type": "application/xml"},
        )
        return True
