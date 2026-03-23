# Changelog

## Version 1.18.2 (2026-03-12)

Rilascio nuove funzionalità
* Aggiunto
  - ontap volume delete
* Risolto
  - Extract task state evaluation into _evaluate_task_state()
  - Extract update parsing into _iter_state_changes()
  - Isolate filter destruction via _destroy_filter()
  - Improve timeout and retry handling with optional wait hook
  - Reorder parameters (wait before timeout)
  - Replace polling-based task wait with event-driven PropertyCollector The new implementation eliminates sleep-based polling cycles and leverages vSphere's native push notification mechanism for immediate state updates.
  - Event-driven notifications instead of repeated polling loops
  - Isolated PropertyCollector per task for thread/greenlet safety
  - Automatic recovery from socket/SSL timeouts
  - Significantly reduced API calls and CPU usage
  - Better scalability for concurrent task monitoring
  - Event-driven notifications instead of repeated polling loops
  - Isolated PropertyCollector per task for thread/greenlet safety
  - Automatic recovery from socket/SSL timeouts
  - Significantly reduced API calls and CPU usage
  - Better scalability for concurrent task monitoring
  - Replace expensive inventory search in `get_by_morid` with direct ManagedObject instantiation (`get_vm_object`). This avoids traversing the entire folder tree to find a VM by ID.
  - Cache nested properties (config, guest, hardware) into local variables within loops and methods to minimize repeated attribute lookups and potential SOAP calls.
  - Improve robustness in hardware parsing by using `getattr` for optional fields like `backing` and `connectable`.
  - Remove unused methods and dead code in `guest_utils.py` (e.g., fault_tolerance, clone placeholders).
  - Fix mutable default arguments in `nsx_call` and `call` methods to avoid potential side effects across calls.
  - Modernize string formatting using f-strings and logging placeholders to resolve linter warnings (E713, W1203).

## Version 1.18.1 (2026-02-12)

Rilascio nuove funzionalità
* Aggiunto
  - Update licensing header
* Risolto
  - Fix OpenStack server list pagination to retrieve all instances

## Version 1.18.0 (2026-01-22)

Rilascio nuove funzionalità
* Aggiunto
  - ontap aggregate information while querying volumeand list policies filters
  - ontap volume optional snaplock filter
  - type hints
* Risolto
  - updated python version, labraries and dependencies
  - Fix typos
  - fix kibana import_dashboard write file in /tmp
  - fix error handling socket timeout vsphere
  - fix openstack update_quota
* Rimosso
  - camunda client
  - some duplicate method
  - six direct usage

## Version 1.17.13 (2025-12-11)

Rilascio nuove funzionalità

## Version 1.17.12 (2025-11-27)

Rilascio nuove funzionalità
* Aggiunto
  - staas_ontap_v2 goldencopy management for shared volumes
  - nsx dfw section update
  - GrafanaFolder log list
  - ontap get_by_svm_name

## Version 1.17.11 (2025-11-06)

Rilascio nuove funzionalità
* Aggiunto
  - hard poweroff and misc imports fix
* Risolto
  - map[minor:increase timeout creating openstack volume]

## Version 1.17.10 (2025-10-09)

Rilascio nuove funzionalità
* Risolto
  - map[Manila:avoid error in case turn off]
  - vpc ip availability commit

## Version 1.17.7 (2025-08-05)

Rilascio nuove funzionalità
* Aggiunto
  - SecurityGroup rule apply to NSX security group not to NSX distribuited firewall
* Risolto
  - wait_task, added optional raise on error
  - Add mgmt of appliedTo and direction options in dfw rule update
  - Update update_rule method
  - Set default rule logging value to True
  - Update dfw rule update method
  - Update rule with enable/disable log option

## Version 1.17.6 (2025-06-10)

Rilascio nuove funzionalità
* Risolto
  - some feature in ontap snapmirror and to retrieve snapmirror policies
  - some comments

## Version 1.17.4 ()

Rilascio nuove funzionalità
* Risolto
  - veeam list job

## Version 1.17.3 (2025-03-28)

Rilascio nuove funzionalità
* Aggiunto
  - openstack volume debug create
  - ontap connection increased timeout
* Risolto
  - openstack ping msg

## Version 1.17.2 (2025-03-12)

Rilascio nuove funzionalità

## Version 1.17.1 (Thu Mar 6 14:29:25 2025 +0100)

Rilascio nuove funzionalità
* Risolto
  - nsx etag for delete_rule, section

## Version 1.17.0 (2025-02-24)
rilascio funzionalità

* Aggiunto
  - new staas on_tap v2
  - type hints
* Risolto
  - awx execution environments client
  - Check on security group
  - Check on vsphere when non ipv4 or and ipvs
  - cleaned up in order tu publishing code
  - Correct bug in method returning vsphere edge ipsec config
  - Correct bug in nsx edge load balancer config get
  - Default is True if False, delete hard disk virtual device without remove
  - delete_hard_disk add optional param delete_backing_file
  - Fix bug in aggregates count
  - Fix platform vsphere list template
  - Fix possible unvalid content
  - Fix setup after "deprecation"
  - Fix some import in test after bee_client new project
  - fix vcenter session (vim.fault.NotAuthenticated)
  - fix vsHost.info error when some value were None
  - Patch vsphere details mathod when managedBy if not None
  - Patchset to print some output when ask get on a vm WITHOUT GUEST TOOLS
  - split aggregate list in two separate functions due to output incompatibilities
  - Split different class in different files
  - temporary fix vsphere doesn't return anymore just one result when using search ip filter
  - the backing file alias the vsphere volume in vdmk format
  - this is done because pg11 and 12 are broken and not able easily ignore
  - openstack server optional filter by ip or power_state and other minor fixes
  - vsphere refactoring
* Rimosso
  - Remove obsolete code unused import
  - cmp client

## Version 1.16.9 (2024-03-26)
rilascio correttive

* Risolto
  - map[elk:delete dashboard, return errors in add dashboard]

## Version 1.16.8 (2024-03-26)
rilascio correttive

* Aggiunto
  - awx execution environments client
* Risolto
  - setting on unknown distro in order to support rhel9 and derivatives on prod.
  - grafana update dashboard
  - grafana delete_dashboard

## Version 1.16.0 (2024-03-26)

Rilascio nuove funzionalità
* Aggiunto
  - vsphere customization
  - vsphere clone
  - Debian 11 support

## Version 1.15.3 (2024-03)
Rilscio correttive

* Aggiunto
  - no changes
* Risolto
  - no changes

## Version 1.15.0 (2025-10-12)

Rilascio nuove funzionalità
* Aggiunto
  - zabbix client improvements
  - veeam client improvements
  - grafana add dashboard from json
  - import load balancer
  - delete load balancer and fairwall rules
  - vsphere resume server after suspend
* Risolto
  - timeout
  - minor fixes

## Version 1.14.0 (2023-06-22)

Rilascio nuove funzionalità
* Aggiunto
  - veeam client improvements
  - ssh gateway client improvement
  - vsphere client improvements
* Risolto
  - firewall rule update
  - openstack client

## Version 1.13.0 (2023-02-24)

Rilascio nuove funzionalità
* Aggiunto
  - nsx client improvements
  - vsphere client improvements
  - openstack client improvements
  - ssh gateway
* Risolto
  - timeout
  - openstack volume-group-snapshot-get
  - minor fixes

## Version 1.12.0 (2023-01-27)

Rilascio nuove funzionalità
* Aggiunto
  - openstack client improvements
  - elasticsearch client improvements
  - grafana client improvements
* Risolto
  - minor fixes
  - timeout

## Version 1.11.0 (2022-10-11)

Rilascio nuove funzionalità
* Aggiunto
  - add grafana client
  - add kibana client
  - Various bugfixes

## Version 1.8.0 (2022)

Rilascio nuove funzionalità
* Aggiunto
  - add method to vsphere dfw add_item_to_exclusion_list and remove_item_from_exclusion_list
  - add cmp client ssh section
* Risolto
  - configuration of network and admin pass for vsphere server with so oracle linux
  - correct bug in method openstack server get_state
  - correct bug in vsphere dfw rule add with cidr:0.0.0.0/0 and nsx version 6.4.10

## Version 1.7.0 (2022-02-11)

Rilascio nuove funzionalità
* Aggiunto
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
* Risolto
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
* Aggiunto
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
* Risolto
  - update management of http proxy in some type of vm
  - correct bug that affect openstack image list. Only 20 items were returned by default. Increased to 500
  - correct bug that affect openstack server list. Only 1000 servers were listed

## Version 1.5.1 (2021-02-05)

Rilascio nuove funzionalità
* Aggiunto
  - add openstack method to manage volume
  - add itemNotFound in openstack client error parsing
* Risolto
  - add param noproxy in OpenstackServer.user_data to disable yum proxy setting in centos7 using cloud_init
  - update openstack image client to support glance
  - correct various bug in openstack client

## Version 1.5.0 (2020-12-31)

Rilascio nuove funzionalità
* Aggiunto
  - added volume clone method in openstack client
  - added volume list all method in openstack client. It permit to list all the volume beyond limit of 1000
  - add client how to in README.md
  - add itemNotFound in openstack client error parsing
* Risolto
  - fixed volume v3 list in openstack client. It was limited to 1000 output item. Now you can paginate query
  - complete review of libvirt client
  - correct bug in openstack Network.create. mtu set to 1450 to enable vxlan network creation.
  - update copyright
  - update test unit

## Version 1.4.2 (2020-10-23)

Rilascio nuove funzionalità
* Aggiunto
  - added list of ipv4 ip in vsphere server get and list
  - added support in openstack client for api microversion
  - added support for cinder v3 api in openstack client, volume package, snapshot, volume group, volume group snapshot
  - added method add_security_group and remove_security_group to openstack network port
  - added class OpenstackManilaShareNetwork in openstack manila client
  - added class OpenstackManilaShareServer in openstack manila client
  - added class OpenstackManilaShare export location list and get in openstack manila client
  - add vsphere server hardware method guest_disable_firewall
  - add parameter timeout=30.0 in AwxManager
* Risolto
  - Vsphere server delete_hard_disk. virtual_hdd_device now is located using unitNumber and not deviceInfo.label
  - removed os- in classes OpenstackManilaXXXX

## Version 1.4.1 (2020-08-21)

Rilascio nuove funzionalità
* Aggiunto
  - added nsx edge method for sslvpn
  - added filter by ip and subnet in openstack port list
* Risolto
  - correct bug in vsphere and openstack client
  - correct import bug in camunda engine

## Version 1.4.0 (2020-06-21)

Rilascio nuove funzionalità
* Aggiunto
  - Update awx client
  - Update zabbix client
  - New Vsphere client edge method
  - New method in vsphere nsx edge
* Risolto
  - correct bug in vsphere and openstack client

## Version 1.3.0 (2019-09-04)

Rilascio nuove funzionalità
* Aggiunto
  - Created awx client
  - Created syncthig client
  - Added method customize to vsphere server
* Risolto
  - method OpenstackPorject.get_members changed using keystone api role_assignemnts

## Version 1.2.0 (2019-05-24)

Rilascio nuove funzionalità
* Aggiunto
  - OpenstackVolume Aggiunto metodo snapshot.revert_to
  - OpenstackImage Aggiunto metodo get_metadata
* Risolto
  - Revisione complessiva del client openstack

## Version 1.1.0 (2019-01-13)

Rilascio nuove funzionalità
* Aggiunto
  - vsphere client inizio client per la gestione dei load balancer su nsx edge
  - openstack client aggiunta gestione volumi

## Version 1.0.0 (2018-07-31)

Rilascio nuove funzionalità
* Aggiunto
  - First production preview release.

## Version 0.1.0 (2016-04-18)

Rilascio nuove funzionalità
* Aggiunto
  - First private preview release.
