# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

import unittest
from beecell.simple import truncate
from beedrones.cmp.platform import CmpPlatformAbstractService
# from beedrones.cmp.business_common import CmpPlatformAuthService
from beedrones.cmp.client import CmpBaseService
from sys import path
from beecell.simple import dynamic_import
from os import listdir


class CmpPlatformTestService(CmpPlatformAbstractService):
    """Cmp business div
    """
    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)
        
        # self.auth = CmpPlatformTestAuthService(self.manager)


    def get(self, local_package_path, package, plan):
        res = None
        if package is not None and plan is not None:
            prj = package.replace('_', '-')
            # path.append('%s/%s' % (self.app.config.get('beehive', 'local_package_path'), prj))
            path.append('%s/%s' % (local_package_path, prj))
            test_run = dynamic_import('%s.regression.%s' % (package, plan))
            test_groups = filter(lambda x: x.find('tests_') == 0, dir(test_run))
            res = [{'package': package, 'test-plan': plan, 'test-group': i} for i in test_groups]

        self.logger.debug('res: %s' % res)

        # uri = self.get_uri('organizations/%s' % oid)
        # res = self.api_get(uri)
        # self.logger.debug('get organization %s: %s' % (oid, truncate(res)))
        return res


    def run(self, local_package_path, package, plan, group=None, test=None, config=None, extra_config=None, validate=False, user='test1', max=2, endpointsForced=None, report_file=None) -> unittest.result.TestResult:
        # package = self.app.pargs.package
        # plan = self.app.pargs.plan
        # group = self.app.pargs.group
        # test = self.app.pargs.test
        # tests = self.app.pargs.list
        # config = self.app.pargs.mainconf
        # extra_config = self.app.pargs.conf
        # validate = self.app.pargs.validate
        # user = self.app.pargs.user
        # max = self.app.pargs.concurrency

        if config is None:
            # config = '%s/beehive-tests/beehive_tests/configs/test/beehive.yml' % \
            #          self.app.config.get('beehive', 'local_package_path')
            config = '%s/beehive-tests/beehive_tests/configs/test/beehive.yml' % local_package_path

        args = {
            'conf': config,
            'exconf': extra_config,
            'validate': validate,
            'user': user,
            'max': int(max),
            'endpointsForced': endpointsForced,
            'stream': "custom",
            'report_file': report_file,
            'skip_log_config': True
        }

        prj = package.replace('_', '-')
        # test_file = '%s/%s/%s/regression' % (self.app.config.get('beehive', 'local_package_path'), prj, package)
        test_file = '%s/%s/%s/regression' % (local_package_path, prj, package)
        file_list = [f.replace('.py', '') for f in listdir(test_file)]
        if plan not in file_list:
            raise Exception('Test %s is not available' % plan)
        else:
            # path.append('%s/%s' % (self.app.config.get('beehive', 'local_package_path'), prj))
            path.append('%s/%s' % (local_package_path, prj))
            test_run = dynamic_import('%s.regression.%s' % (package, plan))
            self.logger.debug('run - test_run: %s' % test_run)

            if group is not None:
                if tests is not None:
                    idxs = tests.split(',')
                    all_tests = getattr(test_run, group)
                    tests = []
                    for idx in idxs:
                        tests.append(all_tests[int(idx)])
                    test_run.tests = tests
                else:
                    test_run.tests = getattr(test_run, group)
            elif test is not None:
                test_run.tests = [test]
            print('run tests:')
            for item in test_run.tests:
                self.logger.debug('run - item: %s' % item)
                print('- %s' % item)

            self.logger.debug('run - args: %s' % args)
            return test_run.run(args)


# class CmpPlatformTestAuthService(CmpPlatformAuthService):
#     """Cmp tests
#     """
#     common_name = 'testsss'
