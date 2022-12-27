# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beedrones.bee_orchestrator.client import BeeOrchestrator
from beedrones.tests.test_util import BeedronesTestCase, runtest


tests = [
    'test_get_available_configs',

]


class CmpClientTestCase(BeedronesTestCase):
    @classmethod
    def setUpClass(cls):
        BeedronesTestCase.setUpClass()

        authparams = {'type': 'keyauth', 'user': 'admin@local', 'pwd': 'beehive_test'}
        cls.client = BeeOrchestrator('/home/beehive3/pkgs/beehive-mgmt/post-install/')

    def tearDown(self):
        BeedronesTestCase.tearDown(self)

    def test_get_available_configs(self):
        self.client.get_available_configs()


if __name__ == '__main__':
    runtest(CmpClientTestCase, tests)
