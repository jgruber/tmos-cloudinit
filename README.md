# tmos-cloudinit
### Cloudinit Modules and Patching for F5  TMOS ###

F5 TMOS is a secured and close operating system which can not take advantage of the linux community's work to standardize cloud virtual machine onboarding through the cloudinit project.

Starting with TMOS v13, an order version of cloudinit was included with TMOS, but had only the following modules available:

- bootcmd
- write_file
- runcmd

Through the use of these cloudinit modules, various combinates of `bash`, `javascript`, and `python` onboard scripting evolved within specific cloud ecosystems. The templating depended on the environment and what orchestration systems were available. 

In an attempt to standardize these efforsts, F5 launched a set of declarative `iControl LX` extensions which are used to configure TMOS and provision BIG-IP services. These extensions, marketed as the Automation and Orchestration (A & O) toolchain, can be installed on TMOS devices and then called through RESTful interfaces. These extensions do not come preinstalled nor do the take advantage of the configuration metadata provided by cloud environments to virtual machines instances through cloudinit. The cloudinit modules in this repository tie cloudinit userdata and the F5 A & O toolchain together.

The cloudinit modules included in this repository need to be file-injected into standard TMOS images before they can be used.

## Patching TMOS VE Images Using an Ubuntu OpenStack Instance ##

This repository comes with a simple `bash` script to patch OpenStack qcow2 contained images. In the future, F5 intends to release an image bakery tools which will formalize how to patch TMOS VE images for all supported container types.

To build a host which can run the simple OpenStack image build script, start an Ubuntu server 18.04 LTS OpenStack cloud instance. Make sure the cloud instance can route traffic requests to your OpenStack cloud Glance services. The script will upload your patched images to your OpenStack cloud. 

Most of the functions performed in the patch script require root level access within your virtual machine. You can open a root login session from `sudo` with `sudo -l`. Simply terminate the VM instance when you are finished patching your images.

Install require packages.

```
root@tmosimagebuilder:~# apt update
root@tmosimagebuilder:~# apt install qemu-utils python-openstackclient git
```

Download this repository

```
root@tmosimagebuilder:~# git clone https://github.com/jgruber/tmos-cloudinit.git
Cloning into 'tmos-cloudinit'...
remote: Enumerating objects: 122, done.
remote: Counting objects: 100% (122/122), done.
remote: Compressing objects: 100% (73/73), done.
remote: Total 122 (delta 49), reused 90 (delta 29), pack-reused 0
Receiving objects: 100% (122/122), 52.64 KiB | 2.11 MiB/s, done.
Resolving deltas: 100% (49/49), done.
root@tmosimagebuilder:~# cd tmos-cloudinit/
root@tmosimagebuilder:~/tmos-cloudinit# 
```

Download predownloaded stock TMOS images from downloads.f5.com to the virtual machine. 

```
root@tmosimagebuilder:~/tmos-cloudinit# mkdir TMOSImages
root@tmosimagebuilder:~/tmos-cloudinit# cd TMOSImages
root@tmosimagebuilder:~/tmos-cloudinit# curl http://192.168.0.65/F5Downloads/BIGIP-14.1.0.1-0.0.7.ALL_1SLOT.qcow2
root@tmosimagebuilder:~/tmos-cloudinit# curl http://192.168.0.65/F5Downloads/BIGIP-14.1.0.1-0.0.7.LTM_1SLOT.qcow2
root@tmosimagebuilder:~/tmos-cloudinit# cd ..
```

Download any iControl LX extensions you wish to install in your image.

```
root@tmosimagebuilder:~/tmos-cloudinit# mkdir iControlLXExtensions
root@tmosimagebuilder:~/tmos-cloudinit# cd iControlLXExtensions
root@tmosimagebuilder:~/tmos-cloudinit# curl -s -O -L https://github.com/F5Networks/f5-declarative-onboarding/blob/master/dist/f5-declarative-onboarding-1.4.0-1.noarch.rpm
root@tmosimagebuilder:~/tmos-cloudinit# curl -s -O -L https://github.com/F5Networks/f5-appsvcs-extension/releases/download/v3.11.0/f5-appsvcs-3.11.0-3.noarch.rpm
root@tmosimagebuilder:~/tmos-cloudinit# cd ..
```

Download your OpenStack RC environment file and import.

```
root@tmosimagebuilder:~/tmos-cloudinit# . admin-openrc.sh
root@tmosimagebuilder:~/tmos-cloudinit# openstack image list
+--------------------------------------+------------------------------------------+--------+
| ID                                   | Name                                     | Status |
+--------------------------------------+------------------------------------------+--------+
| dbd0e31f-56da-4eae-8499-a74d17dec12f | cirros                                   | active |
| ecf217ab-3685-451c-8ae3-240b4a8868e9 | ubuntu-18-04-server                      | active |
+--------------------------------------+------------------------------------------+--------+
```

Edit the `rebuild_qcow2_image.sh` script, updating the location of your OpenStack RC environment file and iControl LX extensions.

```
root@tmosimagebuilder:~/tmos-cloudinit# sed -i '/os_rc_file=/cos_rc_file="${wd}/admin-openrc.sh"' rebuild_qcow2_image.sh 
root@tmosimagebuilder:~/tmos-cloudinit# sed -i '/icontrollx_rpm_injection_path=/cicontrollx_rpm_injection_path="${wd}/iControlLXExtensions"' rebuild_qcow2_image.sh
```

Patch your images.

```
root@tmosimagebuilder:~/tmos-cloudinit# ./rebuild_qcow2_image.sh ./TMOSImages/BIGIP-14.1.0.1-0.0.7.LTM_1SLOT.qcow2 
initializing imaging patching
copying ./TMOSImages/BIGIP-14.1.0.1-0.0.7.LTM_1SLOT.qcow2 as base image for OpenStack_BIGIP-14.1.0.1-0.0.7.LTM_1SLOT.qcow2
mounting OpenStack_BIGIP-14.1.0.1-0.0.7.LTM_1SLOT.qcow2 base image
finding TMOS volume groups within base image
patching cloud-init resources
injecting python modules into python 2.7 system path
injecting cloud-init.tmpl
inserting iControl LX install packages
injecting /root/tmos-cloudinit/iControlLXExtensions/f5-appsvcs-3.11.0-3.noarch.rpm
injecting /root/tmos-cloudinit/iControlLXExtensions/f5-declarative-onboarding-1.4.0-1.noarch.rpm
closing patched volumes
uploading patched OpenStack_BIGIP-14.1.0.1-0.0.7.LTM_1SLOT.qcow2 to OpenStack
+------------------+------------------------------------------------------+
| Field            | Value                                                |
+------------------+------------------------------------------------------+
| checksum         | c54ded7f5a17b57a041fb91b3924546f                     |
| container_format | bare                                                 |
| created_at       | 2019-05-15T03:47:04Z                                 |
| disk_format      | qcow2                                                |
| file             | /v2/images/0b3ee03d-267e-4f42-85c5-b5da3c9657a6/file |
| id               | 0b3ee03d-267e-4f42-85c5-b5da3c9657a6                 |
| min_disk         | 0                                                    |
| min_ram          | 0                                                    |
| name             | OpenStack_BIGIP-14.1.0.1-0.0.7.LTM_1SLOT             |
| owner            | 14910e1a2ed544f7aef81c5019d43f4a                     |
| protected        | False                                                |
| schema           | /v2/schemas/image                                    |
| size             | 5061869568                                           |
| status           | active                                               |
| tags             |                                                      |
| updated_at       | 2019-05-15T03:53:20Z                                 |
| virtual_size     | None                                                 |
| visibility       | shared                                               |
+------------------+------------------------------------------------------+
removing patched image file from local disk
```

```
root@tmosimagebuilder:~/tmos-cloudinit# ./rebuild_qcow2_image.sh ./TMOSImages/BIGIP-14.1.0.1-0.0.7.ALL_1SLOT.qcow2 
initializing imaging patching
copying ./TMOSImages/BIGIP-14.1.0.1-0.0.7.ALL_1SLOT.qcow2 as base image for OpenStack_BIGIP-14.1.0.1-0.0.7.ALL_1SLOT.qcow2
mounting OpenStack_BIGIP-14.1.0.1-0.0.7.ALL_1SLOT.qcow2 base image
finding TMOS volume groups within base image
patching cloud-init resources
injecting python modules into python 2.7 system path
injecting cloud-init.tmpl
inserting iControl LX install packages
injecting /root/tmos-cloudinit/iControlLXExtensions/f5-appsvcs-3.11.0-3.noarch.rpm
injecting /root/tmos-cloudinit/iControlLXExtensions/f5-declarative-onboarding-1.4.0-1.noarch.rpm
closing patched volumes
uploading patched OpenStack_BIGIP-14.1.0.1-0.0.7.ALL_1SLOT.qcow2 to OpenStack
+------------------+------------------------------------------------------+
| Field            | Value                                                |
+------------------+------------------------------------------------------+
| checksum         | 4c7daf28602f84037dd1e17b7c2ea193                     |
| container_format | bare                                                 |
| created_at       | 2019-05-15T03:54:21Z                                 |
| disk_format      | qcow2                                                |
| file             | /v2/images/65446750-fc58-46d7-af93-3ff02ee08d9d/file |
| id               | 65446750-fc58-46d7-af93-3ff02ee08d9d                 |
| min_disk         | 0                                                    |
| min_ram          | 0                                                    |
| name             | OpenStack_BIGIP-14.1.0.1-0.0.7.ALL_1SLOT             |
| owner            | 14910e1a2ed544f7aef81c5019d43f4a                     |
| protected        | False                                                |
| schema           | /v2/schemas/image                                    |
| size             | 5123735552                                           |
| status           | active                                               |
| tags             |                                                      |
| updated_at       | 2019-05-15T04:00:52Z                                 |
| virtual_size     | None                                                 |
| visibility       | shared                                               |
+------------------+------------------------------------------------------+
removing patched image file from local disk
```

# Using the Cloudinit Modules #

The modules all include an `enabled` attribute which must be set to `true` for any onboard configuration to take place. For the most part these modules are mutually exclusive from each other, meaning you should only use the one that fits your deployment environment.

All modules log to the common `/config/cloud/f5-cloudinit.log` log file. 

## tmos_static_mgmt ##

This cloudinit module extents TMOS to allow for static address assignment provided through cloudinit userdata.

This cloudinit module writes and executes onboarding scripts in the `/config/cloud/tmos_static_mgmt` directory.

| Module Attribute | Default | Description|
| --------------------- | -----------| ---------------|
| enabled              | false      | Activates ths module|
| ip         | none (required)        | The management IP address or CIDR |
| netmask | none | The management IP netmask, only required if ip is not CIDR |
| gw | none | The management default gateway IP address |
| mtu | 1500 | The management link MTU |
| icontrollx_package_urls | none | List of URLs to download and install iControl LX extension packages before onboarding |
| post_onboard_enabled | false | Enabled the attempt to run a list of commands after onboarding completes |
| post_onboard_commands | list | List of CLI commands to run in order. Execution will halt at the point a CLI command fails. |
| phone_home_url | url | Reachable URL to report completion of this modules onboarding. |


### usage ###

```
#cloud-config
tmos_static_mgmt:
  enabled: true
  ip: 192.168.245.100
  netmask: 255.255.255.0
  gw: 192.168.245.1
  mtu: 1450
  icontrollx_package_urls:
    - https://github.com/F5Networks/f5-declarative-onboarding/raw/master/dist/f5-declarative-onboarding-1.3.0-4.noarch.rpm
    - https://github.com/F5Networks/f5-appsvcs-extension/raw/master/dist/latest/f5-appsvcs-3.10.0-5.noarch.rpm
    - https://github.com/F5Networks/f5-telemetry-streaming/raw/master/dist/f5-telemetry-1.2.0-1.noarch.rpm
  post_onboard_enabled: true
  post_onboard_commands:
    - tmsh modify sys db ui.advisory.color { value orange }
    - tmsh modify sys db ui.advisory.text { value  'Onboarded with OpenStack Metadata' }
    - tmsh modify sys db ui.advisory.enabled { value true }
    - tmsh modify sys db provision.extramb { value 500 }
    - tmsh modify sys global-settings gui-setup disabled
    - tmsh modify sys provision ltm level minimum
    - tmsh modify sys provision asm level minimum
    - /usr/local/bin/SOAPLicenseClient --basekey KALCE-AHJBL-RFJSD-GGNFG-MFJCDYX
  phone_home_url: https://webhook.site/5f8cd8a7-b051-4648-9296-8f6afad34c93
```

## tmos_configdrive_openstack ##
This cloudinit module requries the use of a ConfigDrive data source and OpenStack file formatted meta_data.json and network_data.json metadata files. This module extents TMOS functionality to include static provisioning off all interfaces (manaement and TMM) via either network metadata or the use of DHCPv4. This interface includes the ability to augment the configuration data retrieved via metadata and DHCP with additional f5-declarative-onboarding and f5-appsvc-3 declarations. Any supplied f5-declarative-onboarding declarations will overwrite or be merged with configuration declarations defined via metadata resource resolution. This modules support both 1NIC and nNIC deployments.

There are implicit declarations of the TMM intefaces names to use for the data plane default route and the configuration sychronization interfaces. If these declarations are omitted, the module will attempt to assign them dynamically based on available network configuration data.

This cloudinit module writes and executes onboarding scripts in the `/config/cloud/openstack` directory.

This cloudinit module optionally composes f5-declarative-onboarding declarations in the `/config/cloud/f5-declarative-onboarding` directory.

This cloudinit module optionally composes f5-appsvcs-extension declarations in the `/config/cloud/f5-appsvcs-extension` directory.


| Module Attribute | Default | Description|
| --------------------- | -----------| ---------------|
| enabled              | false      | Activates ths module|
| rd_enabled         | true        | Automatically create route domains when needed |
| configsync_interface | 1.1 | Sets the TMM interface name to use for configsync |
| default_route_interface | none | Explicitly define the TMM interface to use for the default route. Otherwise one will be determined automatically |
| dhcp_timeout | 120 | Seconds to wait for a DHCP response when using DHCP for resource discovery |
| inject_routes | true | Creates static routes from discovered route resources |
| icontrollx_package_urls | none | List of URLs to download and install iControl LX extension packages before onboarding |
| do_enable | true | Enables attempt to create a f5-declarative-onboarding declaration from discovered resources. If enabled, an asynchronous attempt to declare resouces via f5-declarative-onboarding will be made. If the initial request fails, non-declarative onboarding will resumse |
| do_declaration | none |  YAML formatted f5-declarative-onboarding declaration. This declaration will augment or overwrite the declaration created by resource discovery |
| as3_enabled | true | Enables attempt to declare an application services configuration with f5-appsvcs-extension|
| as3_declaration | none | The f5-appsvcs-extension declaration to declare if enabled |
| post_onboard_enabled | false | Enabled the attempt to run a list of commands after onboarding completes |
| post_onboard_commands | list | List of CLI commands to run in order. Execution will halt at the point a CLI command fails. |
| phone_home_url | url | Reachable URL to report completion of this modules onboarding. |

#### Warning: f5-declarative-onboarding and f5-appsvcs-extension do not support the use of route domains at this time. You should disable route domain support when attempting to use f5-declarative-onboarding and f5-appsvcs-extension declarations 

SSH keys found in the OpenStack meta_data.json file will also be injected as authorized_keys for the root account.

If f5-declarative-onboarding is disbaled, done by setting `do_eabled` to false, the device onboarding configuration will contine as described in the OpenStack meta_data.json and network_data.json files. f5-appsvcs-extension declarations can be applied with or without f5-declarative-onboarding being enabled.

```
#cloud-config
tmos_configdrive_openstack:
  enabled: true
  rd_enabled: false
  configsync_interface: 1.1
  default_route_interface: 1.3
  dhcp_timeout: 120
  inject_routes: true
  icontrollx_package_urls:
    - https://github.com/F5Networks/f5-declarative-onboarding/raw/master/dist/f5-declarative-onboarding-1.3.0-4.noarch.rpm
    - https://github.com/F5Networks/f5-appsvcs-extension/raw/master/dist/latest/f5-appsvcs-3.10.0-5.noarch.rpm
    - https://github.com/F5Networks/f5-telemetry-streaming/raw/master/dist/f5-telemetry-1.2.0-1.noarch.rpm
  post_onboard_enabled: false
  do_enabled: true
  do_declaration:
    Common:
      class: Tenant
      licenseKey:
        class: License
        licenseType: regKey
        regKey: GJKDM-UJTJH-OJZVX-ZJPEG-XTJIAHI
      provisioningLevels:
        class: Provision
        ltm: nominal
        asm: minimum
  as3_enabled: true
  as3_declaration:
    class: AS3
    action: deploy
    persist: true
    declaration:
      class: ADC
      schemaVersion: 3.0.0
      ...
  phone_home_url: https://webhook.site/5f8cd8a7-b051-4648-9296-8f6afad34c93
```

In addition to the delcared elements, this module also supports `cloud-config` delcarations for `ssh_authorized_keys`. Any declared keys will be authorized for the TMOS root account.

```
#cloud-config
ssh_authorized_keys:
  - ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEA3FSyQwBI6Z+nCSjUUk8EEAnnkhXlukKoUPND/RRClWz2s5TCzIkd3Ou5+Cyz71X0XmazM3l5WgeErvtIwQMyT1KjNoMhoJMrJnWqQPOt5Q8zWd9qG7PBl9+eiH5qV7NZ mykey@host
```


## tmos_dhcpv4_tmm ##

This cloudinit module resolves configuration data for all interfaces (management and TMM) through DHCPv4. All interfaces should be connected to networks with DHCPv4 services. This modules support both 1NIC and nNIC deployments.

There are implicit declarations of the TMM intefaces names to use for the data plane default route and the configuration sychronization interfaces. If these declarations are omitted, the module will attempt to assign them dynamically based on available network configuration data.

This cloudinit module writes and executes onboarding scripts in the `/config/cloud/tmos_dhcpv4_tmm` directory.

This cloudinit module optionally composes f5-declarative-onboarding declarations in the `/config/cloud/f5-declarative-onboarding` directory.

This cloudinit module optionally composes f5-appsvcs-extension declarations in the `/config/cloud/f5-appsvcs-extension` directory.

| Module Attribute | Default | Description|
| --------------------- | -----------| ---------------|
| enabled              | false      | Activates ths module|
| rd_enabled         | true        | Automatically create route domains when needed |
| configsync_interface | 1.1 | Sets the TMM interface name to use for configsync |
| default_route_interface | none | Explicitly define the TMM interface to use for the default route. Otherwise one will be determined automatically |
| dhcp_timeout | 120 | Seconds to wait for a DHCP response when using DHCP for resource discovery |
| inject_routes | true | Creates static routes from discovered route resources |
| icontrollx_package_urls | none | List of URLs to download and install iControl LX extension packages before onboarding |
| do_enable | true | Enables attempt to create a f5-declarative-onboarding declaration from discovered resources. If enabled, an asynchronous attempt to declare resouces via f5-declarative-onboarding will be made. If the initial request fails, non-declarative onboarding will resumse |
| do_declaration | none |  YAML formatted f5-declarative-onboarding declaration. This declaration will augment or overwrite the declaration created by resource discovery |
| as3_enabled | true | Enables attempt to declare an application services configuration with f5-appsvcs-extension|
| as3_declaration | none | The f5-appsvcs-extension declaration to declare if enabled |
| post_onboard_enabled | false | Enabled the attempt to run a list of commands after onboarding completes |
| post_onboard_commands | list | List of CLI commands to run in order. Execution will halt at the point a CLI command fails. |
| phone_home_url | url | Reachable URL to report completion of this modules onboarding. |

#### Warning: f5-declarative-onboarding and f5-appsvcs-extension do not support the use of route domains at this time. You should disable route domain support when attempting to use f5-declarative-onboarding and f5-appsvcs-extension declarations 

If f5-declarative-onboarding is disbaled, done by setting `do_eabled` to false, the device onboarding configuration will contine as described in the OpenStack meta_data.json and network_data.json files. f5-appsvcs-extension declarations can be applied with or without f5-declarative-onboarding being enabled.

```
#cloud-config
tmos_dhcp_tmm:
  enabled: true
  rd_enabled: false
  configsync_interface: 1.1
  default_route_interface: 1.3
  dhcp_timeout: 120
  inject_routes: true
  icontrollx_package_urls:
    - https://github.com/F5Networks/f5-declarative-onboarding/raw/master/dist/f5-declarative-onboarding-1.3.0-4.noarch.rpm
    - https://github.com/F5Networks/f5-appsvcs-extension/raw/master/dist/latest/f5-appsvcs-3.10.0-5.noarch.rpm
    - https://github.com/F5Networks/f5-telemetry-streaming/raw/master/dist/f5-telemetry-1.2.0-1.noarch.rpm
  do_enabled: false
  as3_enabled: false
  post_onboard_enabled: true
  post_onboard_commands:
    - tmsh modify sys global-settings gui-setup disabled
    - tmsh modify sys db ui.advisory.color { value orange }
    - tmsh modify sys db ui.advisory.text { value  'Onboarded with OpenStack Metadata' }
    - tmsh modify sys db ui.advisory.enabled { value true }
    - tmsh modify sys db provision.extramb { value 500 }
    - tmsh modify sys provision ltm level minimum
    - tmsh modify sys provision asm level minimum
    - /usr/local/bin/SOAPLicenseClient --basekey KALCE-AHJBL-RFJSD-GGNFG-MFJCDYX
  phone_home_url: https://webhook.site/5f8cd8a7-b051-4648-9296-8f6afad34c93
```

In addition to the delcared elements, this module also supports `cloud-config` delcarations for `ssh_authorized_keys`. Any declared keys will be authorized for the TMOS root account.

```
#cloud-config
ssh_authorized_keys:
  - ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEA3FSyQwBI6Z+nCSjUUk8EEAnnkhXlukKoUPND/RRClWz2s5TCzIkd3Ou5+Cyz71X0XmazM3l5WgeErvtIwQMyT1KjNoMhoJMrJnWqQPOt5Q8zWd9qG7PBl9+eiH5qV7NZ mykey@host
```


## tmos_declared ##

This module assumes the management interface provisioning completes via the default method (DHCPv4 or DHCPv6), but that all other onboard configurations should be handled through f5-declarative-onboarding and f5-appsvcs-extension declarations. 

### Warning: DHCPv6 does not include interface-mtu support, meaning your access to your management interface might not be reliable. IPv6 requires the mgmt interface be set to a minumum of 1280 bytes, but SDN tunnel types might limit it to below the standard 1500 bytes. ###

The declarations must be coherent with the deployment environment. As an example, the f5-declarative-onboarding declaration would need to include the `internal` VLAN and the `self_1nic` SelfIP classes to properly declare a 1NIC deployment.

This cloudinit module optionally composes f5-declarative-onboarding declarations in the `/config/cloud/f5-declarative-onboarding` directory.

This cloudinit module optionally composes f5-appsvcs-extension declarations in the `/config/cloud/f5-appsvcs-extension` directory.

| Module Attribute | Default | Description|
| --------------------- | -----------| ---------------|
| enabled              | false      | Activates ths module|
| icontrollx_package_urls | none | List of URLs to download and install iControl LX extension packages before onboarding |
| do_declaration | none |  YAML formatted f5-declarative-onboarding declaration. This declaration will augment or overwrite the declaration created by resource discovery |
| as3_declaration | none | The f5-appsvcs-extension declaration to declare if enabled |
| phone_home_url | url | Reachable URL to report completion of this modules onboarding. |

```
#cloud-config
tmos_declared:
  enabled: true
  icontrollx_package_urls:
    - https://github.com/F5Networks/f5-declarative-onboarding/raw/master/dist/f5-declarative-onboarding-1.3.0-4.noarch.rpm
    - https://github.com/F5Networks/f5-appsvcs-extension/raw/master/dist/latest/f5-appsvcs-3.10.0-5.noarch.rpm
    - https://github.com/F5Networks/f5-telemetry-streaming/raw/master/dist/f5-telemetry-1.2.0-1.noarch.rpm
  do_declaration:
    schemaVersion: 1.0.0
    class: Device
    async: true
    label: Cloudinit Onboarding
    Common:
      class: Tenant
      provisioningLevels:
        class: Provision
        ltm: nominal
        asm: nominal
      poolLicense:
        class: License
        licenseType: licensePool
        bigIqHost: licensor.example.openstack.com
        bigIqUsername: admin
        bigIqPassword: admin
        licensePool: BIGIPVEREGKEYS
        reachable: true
        bigIpUsername: admin
        bigIpPassword: admin
      dnsServers:
        class: DNS
        nameServers:
          - 8.8.8.8
        search:
          - example.openstack.com
      ntpServers:
        class: NTP
        servers:
          - 0.pool.ntp.org
          - 1.pool.ntp.org
          - 2.pool.ntp.org
      HA:
        class: VLAN
        mtu: 1450
        interfaces:
          - name: 1.1
            tagged: false
      HA-self:
        class: SelfIp
        address: 1.1.1.106/24
        vlan: HA
        allowService: all
        trafficGroup: traffic-group-local-only
      configsync:
        class: ConfigSync
        configsyncIp: /Common/HA-self/address
      internal:
        class: VLAN
        mtu: 1450
        interfaces:
          - name: 1.2
            tagged: false
      internal-self:
        class: SelfIp
        address: 192.168.40.51/24
        vlan: internal
        allowService: default
        trafficGroup: traffic-group-local-only
      external:
        class: VLAN
        mtu: 1450
        interfaces:
          - name: 1.3
            tagged: false
      external-self:
        class: SelfIp
        address: 192.168.80.56/24
        vlan: external
        allowService: none
        trafficGroup: traffic-group-local-only
      default:
        class: Route
        gw: 192.168.80.1
        network: default
        mtu: 1500
      dbvars:
        class: DbVariables
        ui.advisory.enabled: true
        ui.advisory.color: orange
        ui.advisory.text: This device is under centralized management.
  as3_declaration:
    class: ADC
    schemaVersion: 3.0.0
    label: ASM_VS1
    remark: ASM_VS1
    Sample_app_sec_01:
      class: Tenant
      HTTP_Service:
        class: Application
        template: http
        serviceMain:
          class: Service_HTTP
          virtualAddresses:
            - 192.168.80.51
          snat: auto
          pool: Pool1
          policyWAF:
            use: WAFPolicy
        Pool1:
          class: Pool
          monitors:
            - http
          members:
            - servicePort: 8001
              serverAddresses:
                - 10.10.10.143
            - servicePort: 8002
              serverAddresses:
                - 10.10.10.144
        WAFPolicy:
          class: WAF_Policy
          url: https://raw.githubusercontent.com/f5devcentral/f5-asm-policy-template-v13/master/owasp_ready_template/owasp-no-autotune.xml
          ignoreChanges: true
  phone_home_url: https://webhook.site/5f8cd8a7-b051-4648-9296-8f6afad34c93
```

The phone_home_url must take a `POST` reqeust. The `POST` body will be a JSON object with the following format:

```
{
	"id": "a67d1edb-0a4a-4101-afd1-2fbf04713cfa",
  "version": "14.1.0.1-0.0.7.0",
  "management": "192.168.245.119/24",
	"installed_extensions": ["f5-service-discovery", "f5-declarative-onboarding", "f5-appsvcs"],
	"as3_enabled": true,
	"do_enabled": true,
  "status": "COMPLETE"
}
```

In addition to the delcared elements, this module also supports `cloud-config` delcarations for `ssh_authorized_keys`. Any declared keys will be authorized for the TMOS root account.

```
#cloud-config
ssh_authorized_keys:
  - ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEA3FSyQwBI6Z+nCSjUUk8EEAnnkhXlukKoUPND/RRClWz2s5TCzIkd3Ou5+Cyz71X0XmazM3l5WgeErvtIwQMyT1KjNoMhoJMrJnWqQPOt5Q8zWd9qG7PBl9+eiH5qV7NZ mykey@host
```

The patched cloudinit configuration template has been alterred to support the standard cloudinit `set_password` module. You can cahnge the built-in TMOS `admin` and  `root` passwords using the following declarations.


```
#cloud-config
chpasswd:
  list: |
    root:f5str0ngPa$$word
    admin:f5str0ngPa$$word
  expire: False
```


