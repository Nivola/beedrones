# Changelog

## Version 1.16.0 (2024-03-26)

Rilascio nuove funzionalità
* Added
  - vsphere customization
  - vsphere clone
  - Debian 11 support

## Version 1.15.3 (2024-03)
Rilscio conrrettive

* Added
  - no changes
* Fixed
  - no changes

## Version 1.15.0 (2025-10-12)

Rilascio nuove funzionalità
* Added
  - zabbix client improvements
  - veeam client improvements
  - grafana add dashboard from json
  - import load balancer
  - delete load balancer and fairwall rules
  - vsphere resume server after suspend
* Fixed
  - timeout
  - minor fixes

## Version 1.14.0 (2023-06-22)

Rilascio nuove funzionalità
* Added
  - veeam client improvements
  - ssh gateway client improvement
  - vsphere client improvements
* Fixed
  - firewall rule update
  - openstack client

## Version 1.13.0 (2023-02-24)

Rilascio nuove funzionalità
* Added
  - nsx client improvements
  - vsphere client improvements
  - openstack client improvements
  - ssh gateway
* Fixed
  - timeout
  - openstack volume-group-snapshot-get
  - minor fixes

## Version 1.12.0 (2023-01-27)

Rilascio nuove funzionalità
* Added
  - openstack client improvements
  - elasticsearch client improvements
  - grafana client improvements
* Fixed
  - minor fixes
  - timeout

## Version 1.11.0 (2022-10-11)

Rilascio nuove funzionalità
* Added
  - add grafana client
  - add kibana client
  - Various bugfixes

## Version 1.8.0 (2022)

Rilascio nuove funzionalità
* Added
  - add method to vsphere dfw add_item_to_exclusion_list and remove_item_from_exclusion_list
  - add cmp client ssh section
* Fixed
  - configuration of network and admin pass for vsphere server with so oracle linux
  - correct bug in method openstack server get_state
  - correct bug in vsphere dfw rule add with cidr:0.0.0.0/0 and nsx version 6.4.10

## Version 1.7.0 (2022-02-11)

Rilascio nuove funzionalità
* Added
  - add openstack aggregates and flavor extra spec
  - update cmp api client
  - add method server.get_console_esxi_uri in vsphere client to get console token
  - add zabbix client proxy management
  - add ontap netapp client
  - add zabbix client trigger and it_service
  - add k8s client
  - add trilio snapshot wait_for_status method
  - add haproxy client
  - add vsphere server support for ubuntu linux customization
* Fixed
  - fix keystone uri with version in openstack client
  - moved jwtclient from beehive in cmp api client
  - upgrade reference in openstack project to cinderv3
  - correct bug in dns client. It must be specified keyalgorithm=HMAC_MD5 in key and update
  - correct bug in openstack volume snapshots list. Only the first 1000 were returned
  - correct various bug in trilio client
  - correct bug in openstack client api methods
  - correct bug in vsphere server guest_setup_network with redhat linux os

## Version 1.6.0 (2021-06-11)

Rilascio nuove funzionalità
* Added
  - cmp api client initial version
  - datadomain api client initial version
  - add group management method to awx client
  - add OpenstackserverGroup in openstack client
  - add OpenstackserverGroup in openstack client
  - add openstack http client forbidden management on error
  - add disable proxy in yum.conf in vsphere server if no_proxy is set to True
  - improved nat_rule_add with some fields
  - add limit management in openstack flavor object
  - add support for filter in awx job event list
* Fixed
  - update management of http proxy in some type of vm
  - correct bug that affect openstack image list. Only 20 items were returned by default. Increased to 500
  - correct bug that affect openstack server list. Only 1000 servers were listed

## Version 1.5.1 (2021-02-05)

Rilascio nuove funzionalità
* Added
  - add openstack method to manage volume
  - add itemNotFound in openstack client error parsing
* Fixed
  - add param noproxy in OpenstackServer.user_data to disable yum proxy setting in centos7 using cloud_init
  - update openstack image client to support glance
  - correct various bug in openstack client

## Version 1.5.0 (2020-12-31)

Rilascio nuove funzionalità
* Added
  - added volume clone method in openstack client
  - added volume list all method in openstack client. It permit to list all the volume beyond limit of 1000
  - add client how to in README.md
  - add itemNotFound in openstack client error parsing
* Fixed
  - fixed volume v3 list in openstack client. It was limited to 1000 output item. Now you can paginate query
  - complete review of libvirt client
  - correct bug in openstack Network.create. mtu set to 1450 to enable vxlan network creation.
  - update copyright
  - update test unit

## Version 1.4.2 (2020-10-23)

Rilascio nuove funzionalità
* Added
  - added list of ipv4 ip in vsphere server get and list
  - added support in openstack client for api microversion
  - added support for cinder v3 api in openstack client, volume package, snapshot, volume group, volume group snapshot
  - added method add_security_group and remove_security_group to openstack network port
  - added class OpenstackManilaShareNetwork in openstack manila client
  - added class OpenstackManilaShareServer in openstack manila client
  - added class OpenstackManilaShare export location list and get in openstack manila client
  - add vsphere server hardware method guest_disable_firewall
  - add parameter timeout=30.0 in AwxManager
* Fixed
  - Vsphere server delete_hard_disk. virtual_hdd_device now is located using unitNumber and not deviceInfo.label
  - removed os- in classes OpenstackManilaXXXX

## Version 1.4.1 (2020-08-21)

Rilascio nuove funzionalità
* Added
  - added nsx edge method for sslvpn
  - added filter by ip and subnet in openstack port list
* Fixed
  - correct bug in vsphere and openstack client
  - correct import bug in camunda engine

## Version 1.4.0 (2020-06-21)

Rilascio nuove funzionalità
* Added
  - Update awx client
  - Update zabbix client
  - New Vsphere client edge method
  - New method in vsphere nsx edge
* Fixed
  - correct bug in vsphere and openstack client

## Version 1.3.0 (2019-09-04)

Rilascio nuove funzionalità
* Added
  - Created awx client
  - Created syncthig client
  - Added method customize to vsphere server
* Fixed
  - method OpenstackPorject.get_members changed using keystone api role_assignemnts

## Version 1.2.0 (2019-05-24)

Rilascio nuove funzionalità
* Added
  - OpenstackVolume Aggiunto metodo snapshot.revert_to
  - OpenstackImage Aggiunto metodo get_metadata
* Fixed
  - Revisione complessiva del client openstack

## Version 1.1.0 (2019-01-13)

Rilascio nuove funzionalità
* Added
  - vsphere client inizio client per la gestione dei load balancer su nsx edge
  - openstack client aggiunta gestione volumi

## Version 1.0.0 (2018-07-31)

Rilascio nuove funzionalità
* Added
  - First production preview release.

## Version 0.1.0 (2016-04-18)

Rilascio nuove funzionalità
* Added
  - First private preview release.
