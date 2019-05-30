#!/usr/bin/env python

# coding=utf-8
# pylint: disable=broad-except,unused-argument,line-too-long, unused-variable
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
This module contains the logic to create a configdrive compliant ISO image
provided either user-data YAML or DO and ASM declarations.
"""

import os
import sys
import logging
import tempfile
import yaml

import pycdlib

LOG = logging.getLogger('tmos_image_patcher')
LOG.setLevel(logging.DEBUG)
FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOGSTREAM = logging.StreamHandler(sys.stdout)
LOGSTREAM.setFormatter(FORMATTER)
LOG.addHandler(LOGSTREAM)


def create_configdrive(userdata, configdrive_file,
                       metatdata=None, vendordata=None, networkdata=None):
    """ create the ISO9660 configdrive containing only the user-data """
    if not userdata:
        LOG.error('can not create a ISO9660 configdrive without userdata')
        return False
    if not configdrive_file:
        LOG.error('can not create tmos_declared configdrive wihtout output file')
        return False
    md_prefix = '/openstack/latest'
    tmpdir = '%s%s' % (tempfile.mkdtemp(), md_prefix)
    try:
        os.makedirs(tmpdir)
        iso = pycdlib.PyCdlib()
        iso.new(interchange_level=3,
                joliet=True,
                sys_ident='LINUX',
                pub_ident_str='F5 Application and Orchestration PM Team',
                app_ident_str='tmos_configdrive_builder',
                rock_ridge='1.09',
                vol_ident='config-2')
        iso.add_directory('/OPENSTACK', rr_name='openstack')
        iso.add_directory('/OPENSTACK/LATEST', rr_name='latest')
        with open('%s/user_data' % tmpdir, 'w+') as ud_file:
            ud_file.write(userdata)
        iso.add_file(
            '%s/user_data' % tmpdir,
            '%s/USER_DATA.;1' % md_prefix.upper(),
            rr_name='user_data')
        if metatdata:
            with open('%s/meta_data.json' % tmpdir, 'w+') as md_file:
                md_file.write(metatdata)
            iso.add_file(
                '%s/meta_data.json' % tmpdir,
                '%s/META_DATA.JSON;1' % md_prefix.upper(),
                rr_name='meta_data.json')
        if vendordata:
            with open('%s/vendor_data.json' % tmpdir, 'w+') as vd_file:
                vd_file.write(vendordata)
            iso.add_file(
                '%s/vendor_data.json' % tmpdir,
                '%s/VENDOR_DATA.JSON;1' % md_prefix.upper(),
                rr_name='vendor_data.json')
        if networkdata:
            with open('%s/network_data.json' % tmpdir, 'w+') as nd_file:
                nd_file.write(networkdata)
            iso.add_file(
                '%s/network_data.json' % tmpdir,
                '%s/NETWORK_DATA.JSON;1' % md_prefix.upper(),
                rr_name='network_data.json')
        iso.write(configdrive_file)
        iso.close()
        clean_tmpdir(tmpdir)
    except TypeError as type_error:
        LOG.error('error creating ISO file: %s', type_error)
        clean_tmpdir(tmpdir)
        return False
    return True


def clean_tmpdir(tmpdir):
    """ clean out temporary directory """
    for tmp_file in os.listdir(tmpdir):
        os.remove('%s/%s' % (tmpdir, tmp_file))
    system_temp_dir = tempfile.gettempdir()
    path, directory = os.path.split(tmpdir)
    while not path == system_temp_dir:
        os.rmdir("%s" % os.path.join(path, directory))
        path, directory = os.path.split(path)
    os.rmdir("%s" % os.path.join(path, directory))


def build_configdrive_from_files(userdata_file=None, configdrive_file=None,
                                 metadata_file=None, vendordata_file=None,
                                 networkdata_file=None):
    """ Read data from files and build configdrive """
    userdata = None
    if userdata_file:
        with open(userdata_file) as ud_file:
            userdata = ud_file.read()
    metadata = None
    if metadata_file:
        with open(metadata_file) as md_file:
            metadata = md_file.read()
            LOG.info(
                'building ISO9660 configdrive meta_data.json from %s', metadata_file)
    vendordata = None
    if vendordata_file:
        with open(vendordata_file) as vd_file:
            vendordata = vd_file.read()
            LOG.info(
                'building ISO9660 configdrive vendor_data.json from %s', vendordata_file)
    networkdata = None
    if networkdata_file:
        with open(networkdata_file) as nd_file:
            networkdata = nd_file.read()
            LOG.info(
                'building ISO9660 configdrive network_data.json from %s', networkdata_file)
    return create_configdrive(userdata, configdrive_file, metadata, vendordata, networkdata)


def build_configdrive_from_decs(do_declaration_file=None,
                                as3_declaration_file=None,
                                configdrive_file=None,
                                phone_home_url=None,
                                phone_home_cli=None):
    """ Read declaration files and build configdrive """
    do_obj = None
    if do_declaration_file:
        do_declaration = None
        with open(do_declaration_file) as do_file:
            do_declaration = do_file.read()
        do_obj = load_declaration(do_declaration)

    as3_obj = None
    if as3_declaration_file:
        as3_declaration = None
        with open(do_declaration_file) as as3_file:
            as3_declaration = as3_file.read()
        as3_obj = load_declaration(as3_declaration)
    userdata_obj = {
        'tmos_declared': {
            'enabled': True
        }
    }
    if do_obj:
        LOG.info('adding f5-declarative-onboarding declaration to user_data')
        userdata_obj['tmos_declared']['do_declaration'] = do_obj
    if as3_obj:
        LOG.info('adding f5-appsvcs-extensions declaration to user_data')
        userdata_obj['tmos_declared']['as3_declaration'] = as3_obj
    if phone_home_url:
        LOG.info('adding phone_home_url to user_data')
        userdata_obj['tmos_declared']['phone_home_url'] = phone_home_url
    if phone_home_cli:
        LOG.info('adding phone_home_cli to user_data')
        userdata_obj['tmos_declared']['phone_home_cli'] = phone_home_cli
    userdata = to_yaml(userdata_obj)
    userdata = "#cloud-config\n%s" % userdata
    return create_configdrive(userdata, configdrive_file, None, None, None)


def load_declaration(string):
    """ loads the declaration """
    try:
        obj = yaml.safe_load(string)
        return obj
    except ValueError:
        return False


def to_yaml(obj):
    """ creates a YAML document from an object """
    try:
        return yaml.dump(obj, default_flow_style=False, width=float("inf"))
    except ValueError:
        return False


if __name__ == "__main__":
    USERDATA_FILE = os.getenv('USERDATA_FILE', '/declarations/user_data')
    METADATA_FILE = os.getenv('METADATA_FILE', '/declarations/meta_data.json')
    VENDORDATA_FILE = os.getenv(
        'VENDORDATA_FILE', '/declarations/vendor_data.json')
    NETWORKDATA_FILE = os.getenv(
        'NETWORKDATA_FILE', '/declarations/network_data.json')

    DO_DECLARATION_FILE = os.getenv(
        'DO_DECLARATION_FILE', '/declarations/do_declaration.json')
    AS3_DECLARATION_FILE = os.getenv(
        'AS3_DECLARATION_FILE', '/declarations/as3_declaration.json')
    PHONE_HOME_CLI = os.getenv('PHONE_HOME_CLI', None)
    PHONE_HOME_URL = os.getenv('PHONE_HOME_URL', None)

    CONFIGDRIVE_FILE = os.getenv(
        'CONFIGDRIVE_FILE', '/configdrives/configdrive.iso')

    if os.path.exists(USERDATA_FILE):
        LOG.info('building ISO9660 configdrive user_data from %s', USERDATA_FILE)
        if not os.path.exists(METADATA_FILE):
            METADATA_FILE = None
        if not os.path.exists(VENDORDATA_FILE):
            VENDORDATA_FILE = None
        if not os.path.exists(NETWORKDATA_FILE):
            NETWORKDATA_FILE = None
        BUILT = build_configdrive_from_files(
            USERDATA_FILE, CONFIGDRIVE_FILE, METADATA_FILE,
            VENDORDATA_FILE, NETWORKDATA_FILE)
        if not BUILT:
            LOG.error('could not build ISO9660 configdrive')
            if os.path.exists(CONFIGDRIVE_FILE):
                os.remove(CONFIGDRIVE_FILE)
            sys.exit(1)
    else:
        HAVE_DO = False
        if os.path.exists(DO_DECLARATION_FILE):
            HAVE_DO = True
        HAVE_AS3 = False
        if os.path.exists(AS3_DECLARATION_FILE):
            HAVE_AS3 = True
        if HAVE_DO or HAVE_AS3:
            LOG.info('building ISO9660 for tmos_declared module with declarations')
            BUILT = build_configdrive_from_decs(
                DO_DECLARATION_FILE, AS3_DECLARATION_FILE,
                CONFIGDRIVE_FILE, PHONE_HOME_URL, PHONE_HOME_CLI)
            if not BUILT:
                LOG.error('could not build ISO9660 configdrive')
                if os.path.exists(CONFIGDRIVE_FILE):
                    os.remove(CONFIGDRIVE_FILE)
                sys.exit(1)
        else:
            LOG.error('no cloudinit userdata file or f5 declarations files found')
            sys.exit(1)
    LOG.info('output IS09660 file: %s', CONFIGDRIVE_FILE)
