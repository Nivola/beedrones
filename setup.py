#!/usr/bin/env python
# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from setuptools import setup
from setuptools.command.install import install as _install


class install(_install):
    def pre_install_script(self):
        pass

    def post_install_script(self):
        pass

    def run(self):
        self.pre_install_script()

        _install.run(self)

        self.post_install_script()


def load_requires():
    with open('./MANIFEST.md') as f:
        requires = f.read()
    return requires


def load_version():
    with open('./beedrones/VERSION') as f:
        version = f.read()
    return version


if __name__ == '__main__':
    version = load_version()
    setup(
        name='beedrones',
        version=version,
        description='Platform client',
        long_description='Platform client',
        author='CSI Piemonte',
        author_email='nivola.engineering@csi.it',
        license='EUPL-1.2',
        url='',
        scripts=[],
        packages=[
            'beedrones',
            'beedrones.awx',
            'beedrones.backup',
            'beedrones.bee_orchestrator',
            'beedrones.camunda',
            'beedrones.cmp',
            'beedrones.datadomain',
            'beedrones.dns',
            'beedrones.elk',
            'beedrones.grafana',
            'beedrones.graphite',
            'beedrones.guacamole',
            'beedrones.haproxy',
            'beedrones.k8s',
            'beedrones.ontapp',
            'beedrones.openstack',
            'beedrones.radware',
            'beedrones.rancher',
            'beedrones.ssh_gateway',
            'beedrones.syncthing',
            'beedrones.tests',
            'beedrones.tests.awx',
            'beedrones.tests.bee_orchestrator',
            'beedrones.tests.camunda',
            'beedrones.tests.camunda.bpmn_example_processes',
            'beedrones.tests.cmp',
            'beedrones.tests.datadomain',
            'beedrones.tests.dns',
            'beedrones.tests.elk',
            'beedrones.tests.grafana',
            'beedrones.tests.graphite',
            'beedrones.tests.guacamole',
            'beedrones.tests.openstack',
            'beedrones.tests.rancher',
            'beedrones.tests.syncthing',
            'beedrones.tests.trilio',
            'beedrones.tests.veeam',
            'beedrones.tests.virt',
            'beedrones.tests.vsphere',
            'beedrones.tests.zabbix',
            'beedrones.trilio',
            'beedrones.veeam',
            'beedrones.virt',
            'beedrones.vsphere',
            'beedrones.winapi',
            'beedrones.zabbix',
        ],
        namespace_packages=[],
        py_modules=[
            'beedrones.__init__'
        ],
        classifiers=[
            'Development Status :: %s' % version,
            'Programming Language :: Python'
        ],
        entry_points={},
        data_files=[],
        package_dir={
            'beedrones': 'beedrones'
        },
        package_data={
            'beedrones': ['VERSION']
        },
        install_requires=load_requires(),
        dependency_links=[],
        zip_safe=True,
        cmdclass={'install': install},
        keywords='',
        python_requires='',
        obsoletes=[],
    )




