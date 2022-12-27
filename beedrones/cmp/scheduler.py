# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.types.type_string import truncate
from beedrones.cmp.client import CmpBaseService, CmpApiClientError


class CmpSchedulerAbstractService(CmpBaseService):
    """Cmp scheduler service
    """
    SUBSYSTEM = 'auth'
    PREFIX = 'nas'
    VERSION = 'v2.0'
    ENDPOINTS = {
        'auth': {'prefix': 'nas', 'version': 'v2.0'},
        'catalog': {'prefix': 'ncs', 'version': 'v2.0'},
        'event': {'prefix': 'nes', 'version': 'v2.0'},
        'resource': {'prefix': 'nrs', 'version': 'v2.0'},
        'ssh': {'prefix': 'gas', 'version': 'v2.0'},
        'service': {'prefix': 'nws', 'version': 'v2.0'},
    }

    def setup_subsystem(self, subsystem):
        endpoint = self.ENDPOINTS.get(subsystem, None)
        if endpoint is None:
            raise CmpApiClientError('subsystem is wrong')
        self.SUBSYSTEM = subsystem
        self.PREFIX = endpoint.get('prefix')
        self.VERSION = endpoint.get('version')

    def get_uri(self, uri):
        return '/%s/%s/%s' % (self.VERSION, self.PREFIX, uri)


class CmpSchedulerService(CmpSchedulerAbstractService):
    """Cmp scheduler service
    """
    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        self.task = CmpSchedulerTaskService(self.manager)
        self.schedule = CmpSchedulerScheduleService(self.manager)


class CmpSchedulerTaskService(CmpSchedulerAbstractService):
    """Cmp scheduler task service
    """
    def list(self, *args, **kwargs):
        """get task instances

        :param name: task instance name
        :param objid: task instance objid
        :return: list of task instances
        :raise CmpApiClientError:
        """
        params = ['name', 'objid']
        mappings = {'name': lambda n: '%' + n + '%'}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('worker/tasks')
        res = self.api_get(uri, data=data)
        self.logger.debug('get task instances: %s' % truncate(res))
        return res

    def get(self, oid):
        """get task instance

        :param oid: task instance id
        :return: task instance
        :raise CmpApiClientError:
        """
        uri = self.get_uri('worker/tasks/%s' % oid)
        res = self.api_get(uri).get('task_instance', {})
        self.logger.debug('get task instance %s: %s' % (oid, truncate(res)))
        return res

    def get_trace(self, oid):
        """get task instance trace

        :param oid: task instance id
        :return: task instance trace
        :raise CmpApiClientError:
        """
        uri = self.get_uri('worker/tasks/%s/trace' % oid)
        res = self.api_get(uri).get('task_trace', {})
        self.logger.debug('get task instance %s trace: %s' % (oid, truncate(res)))
        return res

    def get_log(self, oid, **kwargs):
        """get task instance log

        :param oid: task instance id
        :param kwargs.size: number of lines to print
        :param kwargs.page: number of page of lines to print
        :return: task instance log
        :raise CmpApiClientError:
        """
        params = ['size', 'page']
        mappings = {}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('worker/tasks/%s/log' % oid)
        res = self.api_get(uri, data=data).get('task_log', {})
        self.logger.debug('get task instance %s log: %s' % (oid, truncate(res)))
        return res

    def get_definitions(self):
        """get task definitions

        :return: task definitions
        :raise CmpApiClientError:
        """
        uri = self.get_uri('worker/tasks/definitions')
        res = self.api_get(uri).get('task_definitions', {})
        self.logger.debug('get task definitions: %s' % truncate(res))
        return res

    def get_status(self, oid):
        """get task status

        :param oid: task instance id
        :return: task definitions
        :raise CmpApiClientError:
        """
        uri = self.get_uri('worker/tasks/%s/status' % oid)
        res = self.api_get(uri).get('task_instance', {})
        self.logger.debug('get task instance %s status: %s' % (oid, truncate(res)))
        return res

    def run_test1(self):
        """run test task

        :return: task result
        :raise CmpApiClientError:
        """
        uri = self.get_uri('worker/tasks/test')
        data = {'x': 2, 'y': 234, 'numbers': [2, 78, 45, 90], 'mul_numbers': []}
        res = self.api_post(uri, data=data)
        self.logger.debug('run test task 1: %s' % truncate(res))
        return res

    def run_test2(self):
        """run test task 2

        :return: task result
        :raise CmpApiClientError:
        """
        uri = self.get_uri('worker/tasks/test2')
        data = ''
        res = self.api_post(uri, data=data)
        self.logger.debug('run test task 2: %s' % truncate(res))
        return res

    def run_test3(self):
        """run test task 3

        :return: task result
        :raise CmpApiClientError:
        """
        uri = self.get_uri('worker/tasks/test3')
        data = {'x': 2, 'y': 234}
        res = self.api_post(uri, data=data)
        self.logger.debug('run test task 3: %s' % truncate(res))
        return res


class CmpSchedulerScheduleService(CmpSchedulerAbstractService):
    """Cmp scheduler schedule service
    """
    def list(self, *args, **kwargs):
        """get schedule entries

        :param name: entry name
        :return: list of entities
        :raise CmpApiClientError:
        """
        params = ['name']
        mappings = {'name': lambda n: '%' + n + '%'}
        data = self.format_paginated_query(kwargs, params, mappings=mappings)
        uri = self.get_uri('scheduler/entries')
        res = self.api_get(uri, data=data)
        self.logger.debug('get schedule entries: %s' % truncate(res))
        return res

    def get(self, oid):
        """get schedule entry

        :param oid: container id or uuid
        :return: container
        :raise CmpApiClientError:
        """
        uri = self.get_uri('scheduler/entries/%s' % oid)
        res = self.api_get(uri).get('schedule', {})
        self.logger.debug('get schedule entry %s: %s' % (oid, truncate(res)))
        return res

    def add(self, name, task, schedule, args, **kwargs):
        """add schedule entry

        :param name: schedule name
        :param task: task name. Ex. beehive_service.task_v2.metrics.acquire_metric_task
        :param dict schedule: schedule params. Can be timedelta or crontab.
            Ex. {"type": "timedelta", "minutes": 30}
            Ex. {"type": "crontab", "day_of_month": "*", "minute": "15", "day_of_week": "*", "hour": "01",
                 "month_of_year": "*"  }
        :param dict args: params to send to task.
            Ex. {"objid": "*", user": "task_manager", "server": "localhost", "identity": "", "api_id" : "",
                 "alias": "AcquireMetric", "sync" : false}
        :return: schedule
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'name': name,
            'task': task,
            'schedule': schedule,
            'args': [args, '*']
        }
        uri = self.get_uri('containers')
        res = self.api_post(uri, data={'schedule': data})
        self.logger.debug('Create schedule entry %s' % res.get('name'))
        return res

    def delete(self, oid):
        """delete schedule entry

        :param oid: schedule name
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('scheduler/entries/%s' % oid)
        self.api_delete(uri, data='')
        self.logger.debug('delete schedule entry %s' % oid)
