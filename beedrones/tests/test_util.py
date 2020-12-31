# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

import os

import logging
import sys
import unittest
import pprint
import time
import json

import yaml

from beecell.logger import LoggerHelper
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from yaml import load
from beecell.simple import str2uni
from datetime import datetime
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from celery.utils.log import ColorFormatter as CeleryColorFormatter
from celery.utils.term import colored


class ColorFormatter(CeleryColorFormatter):
    #: Loglevel -> Color mapping.
    COLORS = colored().names
    colors = {'DEBUG': COLORS['blue'], 
              'WARNING': COLORS['yellow'],
              'WARN': COLORS['yellow'],
              'ERROR': COLORS['red'], 
              'CRITICAL': COLORS['magenta'],
              'TEST': COLORS['green'],
              'TESTPLAN': COLORS['cyan']
              }


class BeedronesTestCase(unittest.TestCase):
    """To execute this test you need a mysql instance, a user and a 
    database associated to the user.
    """    
    logger = logging.getLogger('beedrones.test')
    logging.addLevelName(60, 'TESTPLAN')
    logging.addLevelName(70, 'TEST')
    pp = pprint.PrettyPrinter(width=200)
    
    @classmethod
    def setUpClass(cls):
        cls.logger.log(60, '==================== Testplan %s - START ====================' % cls.__name__)
        self = cls

        # load config
        try:
            home = os.path.expanduser('~')
            self.config = self.load_file('%s/beedrones.yml' % home, frmt='yaml')
            self.logger.info('get beedrones test configuration')
        except Exception as ex:
            raise Exception('Error loading config file beedrones.yml. Search in user home. %s' % ex)

        # load fernet key
        try:
            home = os.path.expanduser('~')
            self.fernet = self.load_file('%s/beedrones.fernet' % home, frmt='yaml')
            self.logger.info('get beedrones test fernet key')
        except Exception as ex:
            raise Exception('Error loading config file beedrones.fernet. Search in user home. %s' % ex)

        self.platform = self.config.get('platform')

    @classmethod
    def tearDownClass(cls):
        cls.logger.log(60, '==================== Testplan %s - STOP ====================' % cls.__name__)

    @classmethod
    def load_file(cls, file_config, frmt='json'):
        f = open(file_config, 'r')
        config = f.read()
        if frmt == 'json':
            config = json.loads(config)
        elif frmt == 'yaml':
            config = load(config, Loader=Loader)
        f.close()
        return config

    def load_yaml(self, file_name):
        data = self.load_file(file_name, frmt='yaml')
        data = yaml.dump(data)
        return data

    def setUp(self):
        self.logger.log(70, '#################### %s ####################' % self.id()[9:])
        self.start = time.time()
        
    def tearDown(self):
        elapsed = round(time.time() - self.start, 4)
        self.logger.log(70, '#################### %s #################### : %ss' % (self.id()[9:], elapsed))
    
    def open_mysql_session(self, db_uri):
        engine = create_engine(db_uri)
        db_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return db_session
    
    def convert_timestamp(self, timestamp):
        """
        """
        timestamp = datetime.fromtimestamp(timestamp)
        return str2uni(timestamp.strftime('%d-%m-%Y %H:%M:%S.%f'))


def runtest(testcase_class, tests):
    log_file = '/tmp/test.log'
    watch_file = '/tmp/test.watch'

    logging.captureWarnings(True)

    # setting logger
    # frmt = "%(asctime)s - %(levelname)s - %(process)s:%(thread)s - %(message)s"
    frmt = '%(asctime)s - %(levelname)s - %(message)s'
    loggers = [
        logging.getLogger('beedrones'),
        logging.getLogger('beecell'),
        logging.getLogger('requests'),
        logging.getLogger('urllib3'),
    ]
    LoggerHelper.file_handler(loggers, logging.DEBUG, log_file, frmt=frmt, formatter=ColorFormatter)
    '''loggers = [
        logging.getLogger('beecell.perf'),
    ]
    LoggerHelper.file_handler(loggers, logging.DEBUG, watch_file, frmt='%(message)s', formatter=ColorFormatter)

    loggers = [
        logging.getLogger('beehive.test.run'),
    ]
    LoggerHelper.file_handler(loggers, logging.INFO, run_file, frmt='%(message)s', formatter=ColorFormatter)'''

    # run test suite
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(unittest.TestSuite(map(testcase_class, tests)))
