# coding=utf-8
# pylint: disable=broad-except
# Copyright (c) 2016-2018, F5 Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
This module supplies general onboarding utility functions
"""
import json
import logging
import os
import re
import socket
import subprocess
import time
import requests

from cloudinit import util
from cloudinit import ssh_util
from cloudinit import log as logging

LOG = logging.getLogger(__name__)

OUT_DIR = '/config/cloud'

DO_DECLARATION_DIR = OUT_DIR + '/f5-declarative-onboarding'
AS3_DECLARATION_DIR = OUT_DIR + '/f5-appsrvs-3'

DHCP_LEASE_DIR = OUT_DIR + '/dhclient'

RPM_INSTALL_DIR = '/config/icontrollx_installs'

DO_DECLARATION_FILE = DO_DECLARATION_DIR + '/do_declaration.json'
AS3_DECLARATION_FILE = AS3_DECLARATION_DIR + '/as3_declaration.json'

PROGRESS_FILE = OUT_DIR + '/cloudinit.log'
RPM_INSTALL_PROGRESS_FLAG_FILE_PREFIX = OUT_DIR + 'ICONTROL_LX_INSTALL_'

SSH_KEY_FILE = '/root/.ssh/authorized_keys'
DEFAULT_DNS_SERVERS = ['8.8.8.8', '8.8.4.4']
DEFAULT_NTP_SERVERS = ['0.pool.ntp.org', '1.pool.ntp.org']
DEFAULT_TIMEZONE = 'UTC'
DEFAULT_CONFIGSYNC_INTERFACE = '1.1'

REMOVE_DHCP_LEASE_FILES = False


# inject discovered SSH keys, we don't use the ssh_keys cloud-init module
# because it uses SELinuxGuard, which we don't know will always be
# safe with TMOS versions
def inject_public_ssh_keys(keys):
    """Injects discovered and metadata supplied SSH keys into the root account"""
    keys_to_add = {}
    parser = ssh_util.AuthKeyLineParser()
    for k in keys:
        authkeyline = parser.parse(str(k))
        keys_to_add[authkeyline.base64] = k
    existing_keys = ssh_util.parse_authorized_keys(SSH_KEY_FILE)
    for existing_key in existing_keys:
        if existing_key.base64 in keys_to_add:
            del keys_to_add[existing_key.base64]
    with open(SSH_KEY_FILE, 'a+') as keyfile:
        for k in keys_to_add:
            keyfile.write(keys_to_add[k] + '\n')


def is_v6(address):
    """Determines if the supplied address is a valid IPv6 address"""
    try:
        socket.inet_pton(socket.AF_INET6, address)
        return True
    except socket.error:
        return False


def is_v4(address):
    """Determines if the supplied address is a valid IPv4 address"""
    try:
        socket.inet_pton(socket.AF_INET, address)
        return True
    except socket.error:
        return False


def is_mcpd():
    """Determines if the TMOS master control process is running"""
    running = subprocess.Popen(
        "tmsh -a show sys mcp-state field-fmt | grep running | wc -l",
        stdout=subprocess.PIPE, shell=True
    ).communicate()[0].replace('\n', '')
    if int(running) == 1:
        return True
    return False


def wait_for_mcpd():
    """Blocks until the TMOS master control process is running"""
    waiting_on_mcpd = 120
    while waiting_on_mcpd > 0:
        waiting_on_mcpd -= 1
        if is_mcpd():
            return True
        time.sleep(2)
    return False


def is_tmm():
    """Determines if the TMOS dataplane microkernels are running"""
    tmm_running = int(subprocess.Popen("ps -ef|grep /usr/bin/tmm|grep -v grep|wc -l| tr -d ';\n'",
                                       stdout=subprocess.PIPE, shell=True).communicate()[0])
    if tmm_running == 1:
        return True
    return False


def force_tmm_down():
    """Forces all TMOS dataplane microkernels down"""
    fnull = open(os.devnull, 'w')
    subprocess.call(['/bin/pkill', 'tmm'], stdout=fnull)
    subprocess.call(['/bin/bigstart', 'stop', 'tmm'], stdout=fnull)
    subprocess.call(['/bin/pkill', 'tmm'], stdout=fnull)
    time.sleep(2)


def stop_tmm():
    """Stops TMOS dataplane microkernels"""
    fnull = open(os.devnull, 'w')
    subprocess.call(['/bin/bigstart', 'stop', 'tmm'], stdout=fnull)
    time.sleep(5)


def start_tmm():
    """Starts TMOS dataplane microkernels"""
    fnull = open(os.devnull, 'w')
    subprocess.call(['/bin/bigstart', 'start', 'tmm'], stdout=fnull)
    time.sleep(5)


def is_icontrol():
    """Determines if the TMOS control plane iControl REST service is running"""
    try:
        return requests.get(
            'http://localhost:8100/shared/echo',
            auth=('admin', '')
        ).json()['stage'] == 'STARTED'
    except Exception:
        return False


def wait_for_icontrol():
    """Blocks until the TMOS control plane iControl REST service is running"""
    waiting_on_icontrol = 120
    while waiting_on_icontrol > 0:
        waiting_on_icontrol -= 1
        if is_icontrol():
            return True
        time.sleep(2)
    return False


def is_rest_worker(workerpath):
    """Determines if the TMOS control plane iControl REST worker path exists"""
    try:
        return requests.get(
            'http://localhost:8100' + workerpath,
            auth=('admin', '')
        ).status_code != 404
    except Exception:
        return False


def wait_for_rest_worker(workerpath):
    """Blocks until the TMOS control plane iControl REST worker path exists"""
    task_url = 'http://localhost:8100' + workerpath
    waiting_on_url = 120
    while waiting_on_url > 0:
        waiting_on_url -= 1
        try:
            response = requests.get(task_url, auth=('admin', ''))
            if response.status_code < 400:
                return True
        except Exception:
            return False
    return False


def is_icontrollx():
    """Determines if the TMOS control plane iControl REST service is running"""
    try:
        response = requests.get(
            'http://localhost:8100/mgmt/shared/echo-js',
            auth=('admin', '')
        )
        if response.status_code < 400:
            return True
        return False
    except Exception:
        return False


def wait_for_icontrollx():
    """Blocks until the TMOS control plane iControl Node service is running"""
    waiting_on_icontrol = 120
    while waiting_on_icontrol > 0:
        waiting_on_icontrol -= 1
        if is_icontrollx():
            return True
        time.sleep(2)
    return False


def is_onenic():
    """Determines if the TMOS deployment is a 1NIC deployment"""
    if is_mcpd():
        fnull = open(os.devnull, 'w')
        is_1nic = subprocess.call(
            ['/usr/bin/tmsh', 'list', 'net', 'interface', '1.0'], stdout=fnull, stderr=fnull)
        if is_1nic == 0:
            return True
        return False
    else:
        interfaces = subprocess.Popen(
            "ip link | egrep 'eth[1-9]' | cut -d':' -f2 | tr -d ' '",
            stdout=subprocess.PIPE, shell=True
        ).communicate()[0].split('\n')
        if 'eth1' in interfaces:
            return False
        return True


def dhcp_lease_dir_exists():
    """Ensures DHCP lease file copy directory exists"""
    if not os.path.isdir(DHCP_LEASE_DIR):
        os.makedirs(DHCP_LEASE_DIR)


def make_dhcp4_request(interface, timeout=120):
    """Makes DHCPv4 queries out a linux link device"""
    dhcp_lease_dir_exists()
    tmp_conf_file = DHCP_LEASE_DIR + '/dhclient.conf'
    lease_file = DHCP_LEASE_DIR + '/' + interface + '.lease'
    tmp_lease_file = '/tmp/' + interface + '.lease'
    fnull = open(os.devnull, 'w')
    dhclient_cf = open(tmp_conf_file, 'w')
    dhclient_cf.write(
        "\nrequest subnet-mask, broadcast-address, time-offset, routers,\n")
    dhclient_cf.write(
        "        domain-name, domain-name-servers, domain-search, host-name,\n")
    dhclient_cf.write(
        "        root-path, interface-mtu, classless-static-routes;\n")
    dhclient_cf.close()
    if os.path.isfile(lease_file):
        util.del_file(lease_file)
    subprocess.call(['/bin/pkill', 'dhclient'], stdout=fnull)
    subprocess.call(['/sbin/dhclient',
                     '-lf',
                     tmp_lease_file,
                     '-cf',
                     tmp_conf_file,
                     '-1',
                     '-timeout',
                     str(timeout),
                     '-pf',
                     '/tmp/dhclient.' + interface + '.pid',
                     '-sf',
                     '/bin/echo',
                     interface], stdout=fnull)
    if os.path.getsize(tmp_lease_file) > 0:
        util.copy(tmp_lease_file, lease_file)
        subprocess.call(['/bin/pkill', 'dhclient'], stdout=fnull)
        util.del_file('/tmp/dhclient.' + interface + '.pid')
        util.del_file(tmp_lease_file)
        return True
    else:
        subprocess.call(['/bin/pkill', 'dhclient'], stdout=fnull)
        util.del_file('/tmp/dhclient.' + interface + '.pid')
        util.del_file(tmp_lease_file)
    return False


def process_dhcp4_lease(interface, return_options=None):
    """Parses dhclient v4 lease file format for metadata"""
    if not return_options:
        return_options = ['subnet-mask',
                          'routers',
                          'domain-name-servers',
                          'interface-mtu',
                          'classless-static-routes',
                          'host-name',
                          'domain-name']
    return_data = {}

    lease_file = DHCP_LEASE_DIR + '/' + interface + '.lease'
    if os.path.isfile(interface):
        lease_file = interface

    for line in open(lease_file):
        if 'fixed-address' not in return_data and "fixed-address" in line:
            # format: fixed-address 1.1.1.110;
            test_fixed_address = 'fixed-address '
            lidx = line.index(test_fixed_address)
            return_data['fixed-address'] = \
                line[lidx + len(test_fixed_address):].replace(';\n', '')
        for option in return_options:
            test_option = option + ' '
            if (option not in return_data) and (test_option in line):
                # format: option routers 1.1.1.1;
                lidx = line.index(test_option)
                return_data[option] = \
                    line[lidx + len(test_option):].replace(
                        ';\n', '').replace('"', '').replace("'", '')
    return return_data


def process_dhcp4_routes(static_routes):
    """Processes dhclient v4 static routes metadata"""
    dhcp_routes = []
    if static_routes:
        static_route_list = static_routes.split(',')
        for static_route in static_route_list:
            rap = static_route.split(' ')
            route = process_dhcp4_route(rap[0], rap[1])
            if route:
                dhcp_routes.append(route)
    return dhcp_routes


def process_dhcp4_route(static_route, gateway):
    """Parse single dhclient v4 route entry into a dictionary"""
    if not static_route == '0':
        route = {}
        route['network'] = static_route[static_route.find('.') + 1:]
        if len(route['network']) == 3:
            route['network'] = route['network'] + '.0.0.0'
        if route['network'].find('.') > 0:
            dots = route['network'].count('.')
            if dots == 1:
                route['network'] = route['network'] + '.0.0'
            if dots == 2:
                route['network'] = route['network'] + '.0'
        route['netmask'] = static_route[0:static_route.find('.')]
        route['gateway'] = gateway
        route['route_name'] = "route_%s_%s" % (
            route['network'], route['netmask'])
        route['route_name'] = route['route_name'].replace(
            '.', '_').replace(':', '_').replace('/', '_')
        # we don't forward to local or link local in a gateway
        if route['network'].startswith('127'):
            return None
        elif route['network'].startswith('169.254'):
            return None
        elif route['network'].lower().startswith('fe80'):
            return None
        return route
    return None


def ipv4_cidr_from_netmask(netmask):
    """Convert IPv4 netmask to CIDR bits"""
    return sum([bin(int(x)).count('1') for x in netmask.split('.')])


def do_declaration_dir_exists():
    """Ensures f5-declarative-onboarding declaration copy directory exists"""
    if not os.path.isdir(DO_DECLARATION_DIR):
        os.makedirs(DO_DECLARATION_DIR)


def persist_do_declaration(declaration, additional_declarations):
    """Write the f5-declarative-onboarding declaration to file"""
    do_declaration_dir_exists()
    if os.path.isfile(DO_DECLARATION_FILE):
        util.del_file(DO_DECLARATION_FILE)
    if additional_declarations:
        # top level merge
        for key, value in additional_declarations['Common'].iteritems():
            declaration['Common'][key] = value
    util.write_file(DO_DECLARATION_FILE, json.dumps(declaration))


def do_declare():
    """Makes a f5-declarative-onboarding declaration from the generated file"""
    if is_rest_worker('/mgmt/shared/declarative-onboarding') and os.path.isfile(DO_DECLARATION_DIR):
        dec_file = open(DO_DECLARATION_FILE, 'r')
        declaration = dec_file.read()
        dec_file.close()
        json.loads(declaration)
        dec_url = 'http://localhost:8100/mgmt/shared/declarative-onboarding'
        response = requests.post(dec_url, auth=('admin', ''), data=declaration)
        # initial request
        if response.status_code < 400:
            return True
    return False


def get_do_declaration():
    """Gets the current f5-declarative-onboarding declaration"""
    return requests.get(
        'http://localhost:8100/mgmt/shared/declarative-onboarding',
        auth=('admin', '')
    )


def as3_declaration_dir_exists():
    """Ensures f5-appsvcs-3 declaration copy directory exists"""
    if not os.path.isdir(AS3_DECLARATION_DIR):
        os.makedirs(AS3_DECLARATION_DIR)


def persist_as3_declaration(declaration):
    """Write the f5-appsvcs-3 declaration to file"""
    as3_declaration_dir_exists()
    if os.path.isfile(AS3_DECLARATION_FILE):
        util.del_file(AS3_DECLARATION_FILE)
    util.write_file(AS3_DECLARATION_FILE, json.dumps(declaration))


def as3_declare():
    """Makes an f5-appsvcs-3 declaration from the supplied metadata"""
    if is_rest_worker('/mgmt/shared/appsvcs/declare') and os.path.isfile(AS3_DECLARATION_FILE):
        as3df = open(AS3_DECLARATION_FILE, 'r')
        declaration = as3df.read()
        as3df.close()
        json.loads(declaration)
        d_url = 'http://localhost:8100/mgmt/shared/appsvcs/declare'
        response = requests.post(d_url, auth=('admin', ''), data=declaration)
        # initial request
        if response.status_code < 400:
            return True
    return False


def get_as3_declaration():
    """Gets the existing f5-appsvcs-3 declaration"""
    return requests.get(
        'http://localhost:8100/mgmt/shared/appsvcs/declare',
        auth=('admin', '')
    )


def create_install_task(rpm_file_path):
    """Issues an iControl LX install task"""
    install_url = 'http://localhost:8100/mgmt/shared/iapp/package-management-tasks'
    install_json = '{ "operation": "INSTALL", "packageFilePath": "%s" }' % rpm_file_path
    response = requests.post(install_url, auth=(
        'admin', ''), data=install_json)
    if response.status_code < 400:
        response_json = response.json()
        return response_json['id']
    return False


def create_uninstall_task(package_name):
    """Issues an iControl LX uninstall task"""
    install_url = 'http://localhost:8100/mgmt/shared/iapp/package-management-tasks'
    install_json = '{ "operation": "UNINSTALL", "packageName": "%s" }' % package_name
    response = requests.post(install_url, auth=(
        'admin', ''), data=install_json)
    if response.status_code < 400:
        response_json = response.json()
        return response_json['id']
    return False


def create_query_extensions_task():
    """Issues an iControl LX query task"""
    query_url = 'http://localhost:8100/mgmt/shared/iapp/package-management-tasks'
    query_json = '{ "operation": "QUERY" }'
    response = requests.post(query_url, auth=(
        'admin', ''), data=query_json)
    if response.status_code < 400:
        response_json = response.json()
        return response_json['id']
    return False


def get_task_status(task_id, log_progress=None):
    """Queries the task status of an iControl LX task"""
    task_url = 'http://localhost:8100/mgmt/shared/iapp/package-management-tasks/' + task_id
    response = requests.get(task_url, auth=('admin', ''))
    if response.status_code < 400:
        response_json = response.json()
        if log_progress:
            log_progress('task %s returned status %s' %
                         (task_id, response_json['status']))
        if response_json['status'] == 'FAILED':
            if 'errorMessage' in response_json and log_progress:
                log_progress('task %s failed: %s' %
                             (task_id, response_json['errorMessage']))
        return response_json['status']
    return False


def query_task_until_finished(task_id, log_progress=None):
    """Blocks until an iControl LX task finishes or fails"""
    max_attempts = 60
    while max_attempts > 0:
        max_attempts -= 1
        status = get_task_status(task_id, log_progress)
        if status and status == 'FINISHED':
            return True
        elif status == 'FAILED':
            return False
        time.sleep(2)


def return_package_task(task_id):
    """Returns the content of an iControl LX task"""
    task_url = 'http://localhost:8100/mgmt/shared/iapp/package-management-tasks/' + task_id
    response = requests.get(task_url, auth=('admin', ''))
    if response.status_code < 400:
        response_json = response.json()
        if 'queryResponse' in response_json:
            return response_json['queryResponse']
        return response_json
    return False


def get_installed_extensions():
    """Queries installed iControl LX extensions"""
    task_id = create_query_extensions_task()
    query_task_until_finished(task_id)
    return return_package_task(task_id)


def uninstall_extension(package_name_prefix, log_progress=None):
    """Uninstalls an iControl LX extension"""
    packages = get_installed_extensions()
    for package in packages:
        if package['name'].startswith(package_name_prefix):
            task_id = create_uninstall_task(package['packageName'])
            query_task_until_finished(task_id, log_progress)


def download_extension(extension_url):
    """Downloads an iControl LX RPM package prior to installation processing"""
    tmp_file_name = '/tmp/download_file.part'
    dest_file = os.path.basename(extension_url)
    if os.path.isfile(tmp_file_name):
        util.del_file(tmp_file_name)
    resp = requests.get(extension_url, stream=True, allow_redirects=True)
    resp.raise_for_status()
    cont_disp = resp.headers.get('content-disposition')
    if cont_disp:
        cont_disp_fn = re.findall('filename=(.+)', cont_disp)
        if cont_disp_fn > 0:
            dest_file = cont_disp_fn[0]
    with open(tmp_file_name, 'wb') as out_file:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                out_file.write(chunk)
    if os.path.isfile(tmp_file_name):
        dest_file = RPM_INSTALL_DIR + '/' + dest_file
        util.copy(tmp_file_name, dest_file)
        return True
    return False


def install_extensions(log_progress):
    """Install iControl LX package RPMs found in the RPM_INSTALL_DIR directory"""
    for rpm in os.listdir(RPM_INSTALL_DIR):
        if wait_for_mcpd() and wait_for_rest_worker('/mgmt/shared/iapp/package-management-tasks/'):
            if log_progress:
                log_progress('installing icontrol LX rpm: ' + rpm)
            install_task_id = create_install_task(
                RPM_INSTALL_DIR + '/' + rpm)
            if log_progress:
                log_progress('install task is: ' + install_task_id)
            rpm_installed = False
            if install_task_id:
                rpm_installed = query_task_until_finished(
                    install_task_id, log_progress)
            if rpm_installed:
                if log_progress:
                    log_progress('icontrol LX rpm %s installed' % rpm)
            else:
                if log_progress:
                    log_progress(
                        'icontrol LX rpm %s did not install properly' % rpm)
    wait_for_rest_worker('/mgmt/shared/echo-js')


def clean():
    """Remove any onboarding artifacts"""
    if REMOVE_DHCP_LEASE_FILES:
        lease_files = os.listdir(DHCP_LEASE_DIR)
        for lease_file in lease_files:
            util.del_file("%s/%s" % (DHCP_LEASE_DIR, lease_file))
