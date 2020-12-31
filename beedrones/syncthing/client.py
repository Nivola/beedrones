# SPDX-License-Identifier: GPL-3.0-or-later
#
# (C) Copyright 2018-2019 CSI-Piemonte
# (C) Copyright 2019-2020 CSI-Piemonte
# (C) Copyright 2020-2021 CSI-Piemonte

from logging import getLogger
import urllib3
import requests
import ujson as json

urllib3.disable_warnings()


class SyncthingError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)

    def __repr__(self):
        return 'SyncthingError: %s' % self.value

    def __str__(self):
        return 'SyncthingError: %s' % self.value


class SyncthingManager(object):
    """

    """
    def __init__(self, ipaddr, apikey, port=8384):
        self.logger = getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self.apikey = apikey
        self.ipaddr = ipaddr
        self.headers = {'X-API-Key': apikey}
        self.uri = 'https://%s:%s/rest' % (ipaddr, port)
        self.qr_uri = 'https://%s:%s/qr' % (ipaddr, port)
        self.system_uri = self.uri + '/system'
        self.db_uri = self.uri + '/db'
        self.event_uri = self.uri + '/events'
        self.stat_uri = self.uri + '/stats'
        self.misc_uri = self.uri + '/svc'

    def qr(self):
        uri = self.qr_uri
        r = requests.get(uri, headers=self.headers, verify=False)
        res = True
        self.logger.debug('Get agent %s: %s' % (self.ipaddr, res))
        return res

    def restart(self):
        uri = self.system_uri + '/restart'
        r = requests.get(uri, headers=self.headers, verify=False)
        res = True
        self.logger.debug('Restart agent %s: %s' % (self.ipaddr, res))
        return res

    def pause(self):
        uri = self.system_uri + '/pause'
        r = requests.get(uri, headers=self.headers, verify=False)
        res = True
        self.logger.debug('Pause agent %s: %s' % (self.ipaddr, res))
        return res

    def resume(self):
        uri = self.system_uri + '/resume'
        r = requests.get(uri, headers=self.headers, verify=False)
        res = True
        self.logger.debug('Resume agent %s: %s' % (self.ipaddr, res))
        return res

    def ping(self):
        uri = self.system_uri + '/ping'
        r = requests.get(uri, headers=self.headers, verify=False)
        res = r.json()
        self.logger.debug('Ping agent %s: %s' % (self.ipaddr, res))
        return res

    def status(self):
        uri = self.system_uri + '/status'
        r = requests.get(uri, headers=self.headers, verify=False)
        res = r.json()
        self.logger.debug('Status of agent %s: %s' % (self.ipaddr, res))
        return res

    def log(self):
        uri = self.system_uri + '/log'
        r = requests.get(uri, headers=self.headers, verify=False)
        res = r.json()
        self.logger.debug('Status of agent %s: %s' % (self.ipaddr, res))
        return res

    def events(self):
        uri = self.event_uri
        r = requests.get(uri, headers=self.headers, verify=False)
        res = r.json()
        self.logger.debug('Events of agent %s: %s' % (self.ipaddr, res))
        return res

    def debug(self, enable='', disable=''):
        uri = self.system_uri + '/debug'
        config = {'enable': enable, 'disable': disable}
        r = requests.post(uri, headers=self.headers, verify=False, data=config)
        res = True
        self.logger.debug('Events of agent %s: %s' % (self.ipaddr, res))
        return res

    def get_config(self):
        uri = self.system_uri + '/config'
        r = requests.get(uri, headers=self.headers, verify=False)
        res = r.json()
        self.logger.debug('Get agent %s config: %s' % (self.ipaddr, res))
        return res

    def set_config(self, new_config={}):
        uri = self.system_uri + '/config'
        r = requests.get(uri, headers=self.headers, verify=False)
        config = r.json()
        config.update(new_config)
        config = json.dumps(config)
        r = requests.post(uri, headers=self.headers, verify=False, data=config)
        self.logger.debug('Set agent %s config' % (self.ipaddr))
        self.restart()
        return True

    def get_devices(self):
        conf = self.get_config()
        res = conf.get('devices')
        return res

    def get_device(self, devid):
        conf = self.get_config()
        res = {c.get('deviceID'): c for c in conf.get('devices')}
        device = res.get(devid, None)
        if device is None:
            raise SyncthingError('Device %s was not found in remote devices list' % devid)
        return device

    def get_device_id(self):
        uri = self.system_uri + '/ping'
        r = requests.get(uri, headers=self.headers, verify=False)
        res = r.headers.get('X-Syncthing-Id')
        self.logger.debug('Get agent %s device id: %s' % (self.ipaddr, res))
        return res

    def get_device_name(self):
        res = self.get_devices()[0].get('name')
        return res

    def add_device(self, device_id, address, port=22000, auto_accept=False):
        config = self.get_config()
        device = {
          "deviceID": device_id,
          # "name": name,
          "addresses": [
            "tcp://%s:%s" % (address, port)
          ],
          "compression": "metadata",
          "certName": "",
          "introducer": False,
          "skipIntroductionRemovals": False,
          "introducedBy": "",
          "paused": False,
          "allowedNetworks": [],
          "autoAcceptFolders": auto_accept,
          "maxSendKbps": 0,
          "maxRecvKbps": 0,
          "ignoredFolders": [],
          "pendingFolders": [],
          "maxRequestKiB": 0
        }
        config.get('devices').append(device)
        self.set_config(new_config=config)

    def get_folders(self):
        conf = self.get_config()
        res = conf.get('folders')
        return res

    def get_folders_stats(self):
        uri = self.stat_uri + '/folder'
        r = requests.get(uri, headers=self.headers, verify=False)
        res = r.json()
        self.logger.debug('Get agent %s folders stats: %s' % (self.ipaddr, res))
        return res

    def add_folder(self, path, shared_to=None):
        config = self.get_config()
        folder = {
            'autoNormalize': True,
            'copiers': 0,
            'copyOwnershipFromParent': True,
            'devices': [{
                'deviceID': self.get_device_id(),
                'introducedBy': ''}
            ],
            'disableSparseFiles': False,
            'disableTempIndexes': False,
            'filesystemType': 'basic',
            'fsWatcherDelayS': 10,
            'fsWatcherEnabled': True,
            'hashers': 0,
            'id': path,
            'ignoreDelete': False,
            'ignorePerms': False,
            'label': '',
            'markerName': '.stfolder',
            'maxConflicts': 10,
            'minDiskFree': {'unit': '%', 'value': 1},
            'order': 'random',
            'path': path,
            'paused': False,
            'pullerMaxPendingKiB': 0,
            'pullerPauseS': 0,
            'rescanIntervalS': 3600,
            'scanProgressIntervalS': 0,
            'type': 'sendreceive',
            'useLargeBlocks': True,
            'versioning': {'params': {}, 'type': ''},
            'weakHashThresholdPct': 25
        }
        if shared_to is not None:
            self.get_device(shared_to)
            folder['devices'].append({
                'deviceID': shared_to,
                'introducedBy': ''
            })

        config.get('folders').append(folder)
        self.set_config(new_config=config)

    def delete_folder(self, path):
        config = self.get_config()
        folders = config.pop('folders')
        idx = 0
        for folder in folders:
            if folder.get('path') == path:
                folders.pop(idx)
                break
            idx += 1
        config['folders'] = folders
        self.set_config(new_config=config)

    def get_discovery(self):
        uri = self.system_uri + '/discovery'
        r = requests.get(uri, headers=self.headers, verify=False)
        res = r.json()
        self.logger.debug('get discovery agent cache %s config: %s' % (self.ipaddr, res))
        return res

    def set_discovery(self, device_id, device_addr):
        uri = self.system_uri + '/discovery'
        params = {'device': device_id, 'add': device_addr}
        r = requests.post(uri, headers=self.headers, verify=False, params=params)
        res = True
        self.logger.debug('Set discovery agent cache %s config: %s' % (self.ipaddr, res))
        return res

    def get_connections(self):
        uri = self.system_uri + '/connections'
        r = requests.get(uri, headers=self.headers, verify=False)
        res = r.json()
        self.logger.debug('Get agent %s connections: %s' % (self.ipaddr, res))
        return res

    def get_db_completion(self, device, folder):
        uri = self.db_uri + '/completion'
        params = {'device': device, 'folder': folder}
        r = requests.get(uri, headers=self.headers, verify=False, params=params)
        res = r.json()
        self.logger.debug('Get agent %s db completion: %s' % (self.ipaddr, res))
        return res

    def get_db_status(self, folder):
        uri = self.db_uri + '/status'
        params = {'folder': folder}
        r = requests.get(uri, headers=self.headers, verify=False, params=params)
        res = r.json()
        self.logger.debug('Get agent %s db status: %s' % (self.ipaddr, res))
        return res
