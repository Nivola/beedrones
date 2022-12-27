# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from logging import getLogger
from kubernetes import client
from urllib3 import disable_warnings

from beecell.types.type_dict import dict_get

disable_warnings()


class k8sError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return "k8sError: %s" % self.value

    def __str__(self):
        return "k8sError: %s" % self.value


class k8sEntity(object):
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.manager = manager
        self.as_dict = True

    @property
    def client(self):
        return self.manager.client

    @property
    def timeout(self):
        return self.manager.timeout

    @property
    def default_namespace(self):
        return self.manager.default_namespace

    @property
    def all_namespaces(self):
        if self.default_namespace == '*':
            return True
        return False

    def print_dict(self, as_dict):
        """If set to True print list and get result as dict

        :param as_dict: True or False
        :return: None
        """
        self.as_dict = as_dict

    def get_dict(self, obj):
        """return as dict or as python object

        :param obj: object to convert
        :param as_dict: if True return dict
        :return: dict or python object
        """
        if self.as_dict is True:
            return obj.to_dict()
        return obj

    def convert_date(self, data):
        data['metadata']['creation_timestamp'] = str(data['metadata']['creation_timestamp'])
        for field in dict_get(data, 'metadata.managed_fields', default=[]):
            field['time'] = str(field['time'])
        return data


def api_request(method):
    def inner(ref, *args, **kwargs):
        try:
            res = method(ref, *args, **kwargs)
        except k8sError as ex:
            ref.logger.error(ex, exc_info=True)
            raise
        except Exception as ex:
            ref.logger.error(ex, exc_info=True)
            raise k8sError(str(ex))
        return res
    return inner


class k8sManager(object):
    """k8sManager

    :param key: [optional] fernet key used to decrypt encrypted password
    """

    def __init__(self, host, token, port=80, proto='http', path='', timeout=5.0, cert_file=None, key_file=None,
                 key=None):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.host = host
        self.port = port
        self.proto = proto
        self.token = token
        self.cert_file = cert_file
        self.key_file = key_file
        self.timeout = timeout
        self.key = key
        self.path = path

        # k8s client instance
        self.client = None
        self.client_config = None
        self._namespace = None

        self.__configure()
        self.__set_entities()

    def __set_entities(self):
        from .node import K8sNode
        from .namespace import K8sNamespace
        from .pod import K8sPod
        from .service import K8sService
        from .configmap import K8sConfigMap
        from .ingress import K8sIngress
        from .deploy import K8sDeploy
        from .secret import K8sSecret
        from .cronjob import K8sCronJob
        from .job import K8sJob
        from .gitrepo import K8sGitRepo

        self.node = K8sNode(self)
        self.namespace = K8sNamespace(self)
        self.pod = K8sPod(self)
        self.service = K8sService(self)
        self.configmap = K8sConfigMap(self)
        self.ingress = K8sIngress(self)
        self.deploy = K8sDeploy(self)
        self.secret = K8sSecret(self)
        self.cronjob = K8sCronJob(self)
        self.job = K8sJob(self)
        self.gitrepo = K8sGitRepo(self)

    def __configure(self):
        # Create a configuration object
        configuration = client.Configuration()

        # Specify the endpoint of your Kube cluster
        configuration.host = '%s://%s:%s%s' % (self.proto, self.host, self.port, self.path)

        # Security part.
        # In this simple example we are not going to verify the SSL certificate of
        # the remote cluster (for simplicity reason)
        configuration.verify_ssl = False
        # Nevertheless if you want to do it you can with these 2 parameters
        # configuration.verify_ssl=True
        # ssl_ca_cert is the filepath to the file that contains the certificate.
        # configuration.ssl_ca_cert="certificate"

        k8s_token = self.token
        cert_file = self.cert_file
        key_file = self.key_file
        if k8s_token is not None:
            configuration.api_key = {'authorization': 'Bearer ' + k8s_token}
        elif key_file is not None and cert_file is not None:
            configuration.cert_file = cert_file
            configuration.key_file = key_file

        # Create a ApiClient with our config
        self.client_config = client.ApiClient(configuration)
        self.client = client

    @property
    def core_api(self):
        return self.client.CoreV1Api(self.client_config)

    @property
    def apis_api(self):
        return self.client.ApisApi(self.client_config)

    @property
    def apps_api(self):
        return self.client.AppsV1Api(self.client_config)

    @property
    def networking_api(self):
        return self.client.NetworkingV1Api(self.client_config)

    @property
    def networking_beta_api(self):
        return self.client.NetworkingV1beta1Api(self.client_config)

    @property
    def batch_api(self):
        return self.client.BatchV1Api(self.client_config)

    @property
    def batch_beta_api(self):
        return self.client.BatchV1beta1Api(self.client_config)

    @property
    def custom_api(self):
        return self.client.CustomObjectsApi(self.client_config)

    @property
    def default_namespace(self):
        return self._namespace

    def set_default_namespace(self, namespace):
        """set default namespace where search

        :param namespace: namespace name. If set * search is done in all the namespace
        :return:
        """
        self._namespace = namespace

    def set_timeout(self, timeout):
        self.timeout = timeout

    def ping(self):
        """Ping k8s cluster node

        :return: True or False
        """
        try:
            self.apis_api.get_api_versions()
            return True
        except:
            return False

    def version(self):
        """Get k8s cluster node version

        :return: version
        """
        try:
            res = self.apis_api.get_api_versions()
            return res
        except:
            raise k8sError('error while get k8s api version')

    def api_discover(self):
        """Discover k8s cluster apis

        :return: api list
        """
        res = []
        try:
            for api in self.apis_api.get_api_versions().groups:
                versions = []
                for v in api.versions:
                    name = ""
                    if v.version == api.preferred_version.version and len(
                            api.versions) > 1:
                        name += "*"
                    name += v.version
                    versions.append(name)
                res.append({'name': api.name, 'version': ','.join(versions)})
            return res
        except:
            raise k8sError('error while discover k8s apis')
