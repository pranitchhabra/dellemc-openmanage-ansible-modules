#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 2.1.1
# Copyright (C) 2018-2020 Dell Inc. or its subsidiaries. All Rights Reserved.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: idrac_syslog
short_description: Enable or disable the syslog on iDRAC.
version_added: "2.9.11"
description:
  - This module allows to enable or disable the iDRAC syslog.
options:
    idrac_ip:
        required: True
        type: str
        description: iDRAC IP Address.
    idrac_user:
        required: True
        type: str
        description: iDRAC username.
    idrac_password:
        required: True
        type: str
        description: iDRAC user password.
        aliases: ['idrac_pwd']
    idrac_port:
        required: False
        type: int
        description: iDRAC port.
        default: 443
    share_name:
        required: True
        type: str
        description: Network share or a local path.
    share_user:
        required: False
        type: str
        description: Network share user name. Use the format 'user@domain' or 'domain\\user' if user is part of a domain.
            This option is mandatory for CIFS share.
    share_password:
        required: False
        type: str
        description: Network share user password. This option is mandatory for CIFS share.
        aliases: ['share_pwd']
    share_mnt:
        required: False
        type: str
        description: Local mount path of the network share with read-write permission for ansible user.
            This option is mandatory for network shares.
    syslog:
        description: Enables or disables an iDRAC syslog.
        choices: [Enabled, Disabled]
        default: Enabled
        type: str
requirements:
    - "omsdk"
    - "python >= 2.7.5"
author:
  - "Felix Stephen (@felixs88)"
  - "Anooja Vardhineni (@anooja-vardhineni)"
"""

EXAMPLES = """
---
- name: Enable iDRAC syslog
  idrac_syslog:
       idrac_ip:  "192.168.0.1"
       idrac_user:  "user_name"
       idrac_password:  "user_password"
       share_name:  "192.168.0.2:/share"
       share_password:  "share_user_pwd"
       share_user:  "share_user_name"
       share_mnt:  "/mnt/share"
       syslog:  "Enabled"

- name: Disable iDRAC syslog
  idrac_syslog:
       idrac_ip:  "192.168.0.1"
       idrac_user:  "user_name"
       idrac_password:  "user_password"
       share_name:  "192.168.0.2:/share"
       share_password:  "share_user_pwd"
       share_user:  "share_user_name"
       share_mnt:  "/mnt/share"
       syslog:  "Disabled"
"""

RETURNS = """
msg:
    description: Job details of the syslog operation.
    returned: success
    type: dict
    sample: {
        "@odata.context": "/redfish/v1/$metadata#DellJob.DellJob",
        "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_852940632485",
        "@odata.type": "#DellJob.v1_0_2.DellJob",
        "CompletionTime": "2020-03-27T02:27:45",
        "Description": "Job Instance",
        "EndTime": null,
        "Id": "JID_852940632485",
        "JobState": "Completed",
        "JobType": "ImportConfiguration",
        "Message": "Successfully imported and applied Server Configuration Profile.",
        "MessageArgs": [],
        "MessageArgs@odata.count": 0,
        "MessageId": "SYS053",
        "Name": "Import Configuration",
        "PercentComplete": 100,
        "StartTime": "TIME_NOW",
        "Status": "Success",
        "TargetSettingsURI": null,
        "retval": true
    }
error_info:
  description: Details of the HTTP Error.
  returned: on HTTP error
  type: dict
  sample: {
    "error": {
      "code": "Base.1.0.GeneralError",
      "message": "A general error has occurred. See ExtendedInfo for more information.",
      "@Message.ExtendedInfo": [
        {
          "MessageId": "GEN1234",
          "RelatedProperties": [],
          "Message": "Unable to process the request because an error occurred.",
          "MessageArgs": [],
          "Severity": "Critical",
          "Resolution": "Retry the operation. If the issue persists, contact your system administrator."
        }
      ]
    }
  }
"""


import json
from ansible.module_utils.remote_management.dellemc.dellemc_idrac import iDRACConnection
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError

try:
    from omsdk.sdkfile import file_share_manager
    from omsdk.sdkcreds import UserCredentials
except ImportError:
    pass


def run_setup_idrac_syslog(idrac, module):
    idrac.use_redfish = True
    upd_share = file_share_manager.create_share_obj(share_path=module.params['share_name'],
                                                    mount_point=module.params['share_mnt'],
                                                    isFolder=True,
                                                    creds=UserCredentials(
                                                        module.params['share_user'],
                                                        module.params['share_password']))
    idrac.config_mgr.set_liason_share(upd_share)
    if module.check_mode:
        if module.params['syslog'] == 'Enabled':
            idrac.config_mgr.enable_syslog(apply_changes=False)
        elif module.params['syslog'] == 'Disabled':
            idrac.config_mgr.disable_syslog(apply_changes=False)
        msg = idrac.config_mgr.is_change_applicable()
    else:
        if module.params['syslog'] == 'Enabled':
            msg = idrac.config_mgr.enable_syslog()
        elif module.params['syslog'] == 'Disabled':
            msg = idrac.config_mgr.disable_syslog()
    return msg


def main():
    module = AnsibleModule(
        argument_spec={
            "idrac_ip": {"required": True, "type": 'str'},
            "idrac_user": {"required": True, "type": 'str'},
            "idrac_password": {"required": True, "type": 'str', "aliases": ['idrac_pwd'], "no_log": True},
            "idrac_port": {"required": False, "default": 443, "type": 'int'},
            "share_name": {"required": True, "type": 'str'},
            "share_user": {"required": False, "type": 'str'},
            "share_password": {"required": False, "type": 'str', "aliases": ['share_pwd'], "no_log": True},
            "share_mnt": {"required": False, "type": 'str'},
            "syslog": {"required": False, "choices": ['Enabled', 'Disabled'], "default": 'Enabled'}
        },
        supports_check_mode=True)

    try:
        with iDRACConnection(module.params) as idrac:
            msg = run_setup_idrac_syslog(idrac, module)
            changed = False
            if msg.get('Status') == "Success":
                changed = True
                if msg.get('Message') == "No changes found to commit!":
                    changed = False
    except HTTPError as err:
        module.fail_json(msg=str(err), error_info=json.load(err))
    except URLError as err:
        module.exit_json(msg=str(err), unreachable=True)
    except (RuntimeError, SSLValidationError, ConnectionError, KeyError,
            ImportError, ValueError, TypeError) as e:
        module.fail_json(msg=str(e))
    module.exit_json(msg=msg, changed=changed)


if __name__ == '__main__':
    main()
