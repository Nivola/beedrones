# beedrones
__beedrones__ is a project that contains all the base platform client used by the nivola cmp platform. Platform client
are developed to simplify interaction with platform api exposed with http(s) protocol and rest or some xml input and 
output format.
Different platforms are integrated in clients, from bind to manage dns key to openstack to manage keystone, nova and
neutron api, to vsphere and nsx-v.
Some clients are written from scratch using library like requests or httpclient, other use existing python client and
wrap it in more simple commands.

The main clients developed are:
- [awx](https://github.com/ansible/awx) client - [api reference](https://docs.ansible.com/ansible-tower/2.3.0/html/towerapi/intro.html)
- [camunda]() client - [api reference]()
- [bind]() client - [api reference]()
- [graphite]() client - [api reference]()
- [guacamole]() client - [api reference]()
- [openstack](https://www.openstack.org/) client - [api reference](https://docs.openstack.org/api-quick-start/)
- [trilio](https://www.trilio.io/) client - [api reference]()
- [syncthing](https://syncthing.net/) client - [api reference](https://docs.syncthing.net/dev/rest.html)
- [veeam]() client - [api reference]()
- [libvirt](https://github.com/libvirt/libvirt-python) client - [api reference](https://libvirt.org/docs/libvirt-appdev-guide-python/en-US/html/)
- [vSphere](https://github.com/vmware/pyvmomi) client - [api reference](https://code.vmware.com/apis/968/vsphere)
- [zabbix](https://www.zabbix.com/) client - [api reference](https://www.zabbix.com/zabbix_api)

## Packages

### Awx client

Awx client use rest api to manage fundamental entities like inventory, credential, project, job template.

**Tested on**: Awx 14.1.0

#### How to use

Connect and login to awx:

```python
from beedrones.awx.client import AwxManager

uri = http://localhost:80/api/v2/
client = AwxManager(uri=uri)
client.authorize(user='admin', pwd='mypass')
```

Ping engine:

```python
client.ping()
```

Get inventories:

```python
client.inventory.list()
```

Create a project with a git credential:

```python
cred = client.credential.add_git('gitlab.csi.it-cred', 1, 'ansible', 'xxx')
cred_id = cred['id']
client.project.add('prova_prj', scm_type='git', scm_url='https://localhost/project',
                   scm_branch='master', credential=cred_id)
```
Create and launch a template job:

```python
playbook = 'zabbix-agent.yml'
project = client.project.list(name='prova_prj')[0]['id']
inventory = client.inventory.add('nivola_cmp_stage_inventory, organization)['id']
credential = client.credential.list(name='prova_template_cred')

client.job_template.add('prova_template', 'run', inventory, project, playbook,
                        ask_credential_on_launch=True, ask_variables_on_launch=True, 
                        ask_limit_on_launch=True)
            

limit = 'server.localdomain'
extra_vars = {}
params = {'credentials': [credential[0]['id']], 'extra_vars': extra_vars, 'limit': limit}
job = client.job_template.launch(job_template[0]['id'], **params)                        
```

### Bind client

Bind client use [dnspython](https://www.dnspython.org/) package to manage dns zones, recorda and record cname. 

**Tested on**: Bind 

#### How to use

Connect to bind:

```python
from beedrones.dns.client import DnsManager

serverdns = {'resolver': ['dns_ip_1', 'dns_ip_2'], 'update': ['up_dns_ip_1', 'up_dns_ip_2']}
key = {'key': 'value'}
client = DnsManager(serverdns, zones=[], dnskey=key)
```

Query dns zone:

```python
zone = 'localdomain'
client.query_nameservers(zone)
client.query_authority(zone)
```

Create and query recorda:

```python
zone = 'localdomain'
ip_addr = '10.100.1.2'
host_name = 'test'
client.add_record_A(ip_addr, host_name, zone, ttl=3600)
client.query_record_A(host_name)
```

### Graphite client

Graphite client use rest api to query collected data.

**Tested on**: Graphite 0.9.16

#### How to use

Connect and Graphite:

```python
from beedrones.graphite.client import GraphiteManager

host =  'localhost.localdomain'
client = GraphiteManager(host, 'test')
```

Query metrics:

```python
client.set_search_path('test.vmware.tst-open-graphite')
res = client.get_virtual_node_metrics('vsphere', 'vm-3870', 15)
client.format_metrics('vm-3870', res, 'vsphere')
```

### Guacamole client

Guacamole client is in development.

**Tested on**: 

### Openstack client

Openstack client connect to module rest api like keystone, nova, nutron, manila and cinder to manage entities like
project, network, server and volume.

**Tested on**: Openstack Stein

#### How to use

Connect and login to Openstack:

```python
from beedrones.openstack.client import OpenstackManager

uri = http://localhost:5000/v3
client = OpenstackManager(uri=uri, default_region='RegionOne')
client.authorize('admin', 'mypass', project='admin', domain='Default', key=None)
```

Ping engine:

```python
client.ping()
```

Get hypervisors:

```python
client.system.compute_hypervisors()
```

Create and list projects:

```python
client.project.create('prova-project', 'default', False, parent_id=None)
client.project.list()
```

Create and list servers:

```python
name = 'server-test'
image = client.image.get(name='centos7')['id']
flavor = client.flavor.get(2)['id']
networks = [{'uuid': self.client.network.get(name='net1')['id']}]
res = client.server.create(name, flavor, networks=networks, adminpass='mypass', description='test',
                           image=image, security_groups=['default'])
client.server.list()
```

### Trilio client

Trilio client is in development.

**Tested on**: 

### Syncthing client

Syncthing client is in development.

**Tested on**: 

### Veeam client

Veeam client is in development.

**Tested on**: 

### Libvirt client

Libvirt client use [python libvirt](https://libvirt.org/python.html) to query libvirt deamon on a server where are 
running some domains.

**Tested on**: Libvirt 4.5.0

#### How to use

Connect and login to awx:

```python
from beedrones.virt.manager import VirtManager

host = 'localhost'
user = 'root'
keyfile = '/tmp/id_rsa'
client = VirtManager('virt1', host, user=user, key=keyfile)
client.connect()
```

Ping engine:

```python
client.ping()
```

Get domains:

```python
status = 1
server.get_domains(status=status)
```

### vSphere client

Vsphere client is based on pyVmomi. pyVmomi is the Python SDK for the VMware vSphere API that allows you to manage 
ESX, ESXi, and vCenter. is the Python SDK for the VMware vSphere API that allows you to manage ESX, ESXi, and vCenter.
Vsphere client manage vCenter entities like folder, server, dvpg, ...
Vsphere client also interact with nsx api to manage network virtualization entities like dfw, edge, logical switch, ..

**Tested on**: vSphere vCenter 6.5 and Nsx 6.3.5

#### How to use

Connect and login to Vsphere:

```python
from beedrones.vsphere.client import VsphereManager

vcenter = {'host': 'localhost', 'port': 443, 'user': 'admin.local', 'pwd': 'mypass', 'verified': False, 'timeout': 5}
nsxmanager = {'host': 'localhost', 'port': 443, 'user': 'admin', 'pwd': 'mypass', 'verified': False, 'timeout': 5}
client = VsphereManager(vcenter, nsxmanager, key=None)
client.authorize('admin', 'mypass', project='admin', domain='Default', key=None)
```

Ping engine:

```python
client.ping()
```

Get datacenters, clusters and folders:

```python
client.datacenter.list()
client.cluster.list()
client.folder.list()
```

Create and list servers:

```python
name = 'server_test'
guest_id = 'windows9Server64Guest'
folder = client.folder.get('group-v3')
datastore = client.datastore.get('datastore-48').name        
resource_pool = client.cluster.resource_pool.get('resgroup-42')
network = client.network.get_network('dvportgroup-66')
task = client.server.create(name, guest_id, resource_pool, datastore, folder, network, memory_mb=2048,
                            cpu=2, core_x_socket=1, disk_size_gb=40, version='vmx-13')
client.server.list()
```

### Zabbix client

Zabbix client use Zabbix api to manage group, host, template, alerts, ...

**Tested on**: Zabbix 4

#### How to use

Connect and login to Zabbix:

```python
from beedrones.zabbix.client import ZabbixManager

uri = http://localhostzabbix
client = ZabbixManager(uri=uri)
client.authorize('Admin', 'mypass')
```

Ping engine:

```python
client.ping()
```

Get hosts:

```python
client.host.list()
```

Get alerts:

```python
d = datetime.strptime('21/09/2019', '%d/%m/%Y')
time_from = mktime(d.timetuple())
res = client.alert.list(time_from=time_from)
```

## Installing

### Install requirements
First of all you have to install some package and create a python virtual env:

```
$ sudo apt -y install gcc python-dev sshpass rsync mariadb-client git libldap2-dev libffi-dev libssl-dev libsasl2-dev pkg-config libvirt-dev
$ python3 -m venv /tmp/py3-test-env
$ source /tmp/py3-test-env/bin/activate
```

### Install python packages

Public packages:

```
$ pip3 install -U git+https://github.com/Nivola/beecell.git
$ pip3 install -U git+https://github.com/Nivola/beedrones.git
```

CSI Internal packages:

```
$ pip3 install -U git+https://gitlab.csi.it/nivola/cmp2/beecell.git@devel
$ pip3 install -U git+https://gitlab.csi.it/nivola/cmp2/beedrones.git@devel
```

## Running the tests
Activate virtual env:

```
$ source /tmp/py3-test-env/bin/activate
```

Open tests directory __/tmp/py3-test-env/lib/python3.x/site-packages/beedrones/tests__

Copy file beedrones.yml in your home directory. Open the file and set correctly all the <BLANK> variables.

Test log can be seen as /tmp/test.log

Open test, set internal query and manage options and run:

```
$ python awx/client.py
$ python dns/client.py
$ python graphite/client.py
$ python dns/openstack.py
$ python dns/trilio.py
$ python dns/vsphere.py
$ python dns/virt.py
$ python dns/zabbix.py
```

## Versioning
We use Semantic Versioning for versioning. (https://semver.org)

## Authors and Contributors
See the list of contributors who participated in this project in the file AUTHORS.md contained in each specific project.

## Copyright
CSI Piemonte - 2018-2021

## License
See the LICENSE.txt file for details