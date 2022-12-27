# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from time import sleep

from kubernetes.stream import stream
from six import ensure_text
from beecell.types.type_string import truncate
from beedrones.k8s.client import k8sEntity, api_request


class K8sPod(k8sEntity):
    """K8sPod
    """
    @property
    def api(self):
        return self.manager.core_api

    @api_request
    def list(self, name=None):
        """list pods in a namespace

        :param name: name filter
        :return: list of pods
        """
        if self.all_namespaces is True:
            pods = self.api.list_pod_for_all_namespaces()
        else:
            pods = self.api.list_namespaced_pod(self.default_namespace)

        res = pods.to_dict().get('items', [])

        # pods = self.api.list_namespaced_pod(self.default_namespace).items
        # res = []
        # for pod in pods:
        #     if name is None or (name is not None and pod.metadata.name.find(name) >= 0):
        #         res.append(self.get_dict(pod))

        self.logger.debug('list pods: %s' % truncate(res))
        return res

    @api_request
    def get(self, name):
        """get pod

        :param name: name of the pod
        :return:
        """
        pod = self.api.read_namespaced_pod(name, self.default_namespace)
        res = self.get_dict(pod)
        self.logger.debug('get pod: %s' % truncate(res))
        return res

    @api_request
    def delete(self, name):
        res = self.api.delete_namespaced_pod(name, self.default_namespace)
        return res

    def __get_stream(self, pod, print_line):
        for line in self.api.read_namespaced_pod_log(pod, self.default_namespace, follow=True, tail_lines=100,
                                                     _preload_content=False).stream():
            line = ensure_text(line).rstrip()
            print_line(line)

    def __wait_pod_running(self, name, maxtime=10.0):
        delta = 0.5
        elapsed = 0.0
        while elapsed < maxtime:
            pod = self.api.read_namespaced_pod(name, self.default_namespace)
            if pod.status.phase == 'Running':
                break
            sleep(delta)
            elapsed += delta
        if pod.status.phase != 'Running':
            raise Exception('pod %s does not go in Running status' % name)

    @api_request
    def get_log(self, oid=None, name=None, tail_lines=100, follow=False, print_line=None):
        """get pod log

        :param oid: pod id
        :param name: pod name
        :param tail_lines: number of tail line to show
        :param follow: if True follow log data from stream
        :param print_line: function used to print log. Signature
            def print_line(line):
                ...
        :return:
        """
        namespace = self.default_namespace
        if oid is not None:
            if follow is True:
                self.__get_stream(oid)
            else:
                log = self.api.read_namespaced_pod_log(oid, namespace, tail_lines=tail_lines)
                for line in log.split('\n'):
                    print_line(line)
        elif name is not None:
            pods = self.api.list_namespaced_pod(namespace).items
            log_pods = []
            for pod in pods:
                if pod.metadata.name.find(name) >= 0:
                    log_pods.append(pod.metadata.name)

            for log_pod in log_pods:
                self.__wait_pod_running(log_pod)

                if follow is True:
                    self.__get_stream(log_pod, print_line)
                else:
                    log = self.api.read_namespaced_pod_log(log_pod, namespace, tail_lines=tail_lines)
                    # click.echo('-------------------------- %s --------------------------' % log_pod)
                    for line in log.split('\n'):
                        log_type = print_line(line)

    def get_console(self, pod):
        namespace = self.default_namespace

        # Calling exec interactively
        exec_command = ['/bin/bash']
        console = stream(self.api.connect_get_namespaced_pod_exec,
                         pod,
                         namespace,
                         command=exec_command,
                         stderr=True, stdin=True,
                         stdout=True, tty=True,
                         _preload_content=False)
        return console
