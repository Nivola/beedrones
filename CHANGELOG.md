# Changelog

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