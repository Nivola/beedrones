# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from requests.auth import HTTPBasicAuth

#var_url="https://10.138.176.90/config/getcfg?pkey=no&src=txt"
#var_url="https://10.138.176.90/config/AgLastSyncInfoTable"
#var_url="https://10.138.176.90/config/SlbOperEnhRealServerTable"
#var_url="https://10.138.176.90"
var_url="https://10.138.176.90/monitor?prop=agApplyPending,agSavePending,agSyncNeeded,vrrpInfoHAState"
#var_url="https://10.138.176.90/config/AgSyslogMsgTable"
#var_url="https://10.138.176.90/config/VlanNewCfgTable"
var_user="admin"
var_password="admin"
from pprint import pprint
#var_url="https://10.138.176.90/config/VrrpNewCfgVirtRtrTable"
client_session = requests.Session()

res = client_session.get(var_url, auth=HTTPBasicAuth(var_user, var_password), verify=False)
#print res
data=json.loads(res.text)
client_session.close()
