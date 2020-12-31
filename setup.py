#!/usr/bin/env python
# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

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
        license='GPL v3',
        url='',
        scripts=[],
        packages=[
            'beedrones',
            'beedrones.awx',
            'beedrones.camunda',
            'beedrones.dns',
            'beedrones.graphite',
            'beedrones.guacamole',
            'beedrones.openstack',
            'beedrones.radware',
            'beedrones.syncthing',
            'beedrones.trilio',
            'beedrones.veeam',
            'beedrones.virt',
            'beedrones.vsphere',
            'beedrones.zabbix',
            'beedrones.tests',
            'beedrones.tests.awx',
            'beedrones.tests.camunda',
            'beedrones.tests.dns',
            'beedrones.tests.graphite',
            'beedrones.tests.guacamole',
            'beedrones.tests.openstack',
            'beedrones.tests.syncthing',
            'beedrones.tests.trilio',
            'beedrones.tests.veeam',
            'beedrones.tests.virt',
            'beedrones.tests.vsphere',
            'beedrones.tests.zabbix',
        ],
        namespace_packages=[],
        py_modules=[
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




