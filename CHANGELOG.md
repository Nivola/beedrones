# Changelog

## Version 1.11.0 (oct 11, 2022)
* Added ...
    * add grafana client
    * add kibana client
* Various bugfixes

## Version 1.8.0 (, 2022)

* Added ...
    * add method to vsphere dfw add_item_to_exclusion_list and remove_item_from_exclusion_list
    * add cmp client ssh section
* Fixed ...
    * configuration of network and admin pass for vsphere server with so oracle linux
    * correct bug in method openstack server get_state
    * correct bug in vsphere dfw rule add with cidr:0.0.0.0/0 and nsx version 6.4.10
* Integrated ...

* Various bugfixes

## Version 1.7.0 (feb 11, 2022)

* Added ...
    * add openstack aggregates and flavor extra spec
    * update cmp api client
    * add method server.get_console_esxi_uri in vsphere client to get console token
    * add zabbix client proxy management
    * add ontap netapp client
    * add zabbix client trigger and it_service
    * add k8s client
    * add trilio snapshot wait_for_status method
    * add haproxy client
    * add vsphere server support for ubuntu linux customization
* Fixed ...
    * fix keystone uri with version in openstack client
    * moved jwtclient from beehive in cmp api client
    * upgrade reference in openstack project to cinderv3
    * correct bug in dns client. It must be specified keyalgorithm=HMAC_MD5 in key and update
    * correct bug in openstack volume snapshots list. Only the first 1000 were returned
* Integrated ...
* Various bugfixes
    * correct various bug in trilio client
    * correct bug in openstack client api methods
    * correct bug in vsphere server guest_setup_network with redhat linux os


## Version 1.6.0 (jun 11, 2021)

* Added ...
    * cmp api client initial version
    * datadomain api client initial version
    * add group management method to awx client
    * add OpenstackserverGroup in openstack client 
* Fixed ...
    * update management of http proxy in some type of vm
* Integrated ...
    * add disable proxy in yum.conf in vsphere server if no_proxy is set to True
    * improved nat_rule_add with some fields
    * add limit management in openstack flavor object
    * add support for filter in awx job event list
* Various bugfixes
    * correct bug that affect openstack image list. Only 20 items were returned by default. Increased to 500
    * correct bug that affect openstack server list. Only 1000 servers were listed
    * add openstack http client forbidden management on error

## Version 1.5.1 (Feb 05, 2021)

* Added ...
    * add openstack method to manage volume  
* Fixed ...
    * add param noproxy in OpenstackServer.user_data to disable yum proxy setting in centos7 using cloud_init
    * update openstack image client to support glance
* Integrated ...
    * add itemNotFound in openstack client error parsing
* Various bugfixes
    * correct various bug in openstack client

## Version 1.5.0 (Dec 31, 2020)

* Added ...
    * added volume clone method in openstack client
    * added volume list all method in openstack client. It permit to list all the volume beyond limit of 1000
    * add client how to in README.md
* Fixed ...
    * fixed volume v3 list in openstack client. It was limited to 1000 output item. Now you can paginate query
    * complete review of libvirt client
    * correct bug in openstack Network.create. mtu set to 1450 to enable vxlan network creation.
    * update copyright
    * update test unit
* Integrated ...
    * add itemNotFound in openstack client error parsing
* Various bugfixes

## Version 1.4.2 (Oct 23, 2020)

* Added ...
    * added list of ipv4 ip in vsphere server get and list
    * added support in openstack client for api microversion
    * added support for cinder v3 api in openstack client, volume package, snapshot, volume group, volume group snapshot
    * added method add_security_group and remove_security_group to openstack network port
    * added class OpenstackManilaShareNetwork in openstack manila client
    * added class OpenstackManilaShareServer in openstack manila client
    * added class OpenstackManilaShare export location list and get in openstack manila client
    * add vsphere server hardware method guest_disable_firewall
* Fixed ...
    * Vsphere server delete_hard_disk. virtual_hdd_device now is located using unitNumber and not deviceInfo.label
    * removed os- in classes OpenstackManilaXXXX
* Integrated ...
    * add parameter timeout=30.0 in AwxManager
* Various bugfixes

## Version 1.4.1 (Aug 21, 2020)

* Added ...
    * added nsx edge method for sslvpn
    * added filter by ip and subnet in openstack port list
* Fixed ...
* Integrated ...
* Various bugfixes
    * correct bug in vsphere and openstack client
    * correct import bug in camunda engine

## Version 1.4.0 (Jun 21, 2020)

* Added ...
    * Update awx client
    * Update zabbix client
    * New Vsphere client edge method
    * New method in vsphere nsx edge
* Fixed ...
* Integrated ...
* Various bugfixes
    * correct bug in vsphere and openstack client

## Version 1.3.0 (Sep 04, 2019)

* Added ...
    * Created awx client
    * Created syncthig client
    * Added method customize to vsphere server
* Fixed ...
    * method OpenstackPorject.get_members changed using keystone api role_assignemnts
* Integrated ...
* Various bugfixes


## Version 1.2.0 (May 24, 2019)

* Added ...
    * **OpenstackVolume**: Aggiunto metodo snapshot.revert_to
    * **OpenstackImage**: Aggiunto metodo get_metadata
* Fixed ...
    * Revisione complessiva del client openstack
* Integrated ...
* Various bugfixes


## Version 1.1.0 (January 13, 2019)

* Added ...
    * **vsphere client**: inizio client per la gestione dei load balancer su nsx edge
* Fixed ...
* Integrated ...
    * **openstack client**: aggiunta gestione volumi
* Various bugfixes

## Version 1.0.0 (July 31, 2018)

First production preview release.

## Version 0.1.0 (April 18, 2016)

First private preview release.