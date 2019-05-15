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

## Build On Ubuntu OpenStack Instance ##

Start an Ubuntu server 18.04 LTS OpenStack cloud instance. Make sure the cloud instance can route traffic requests to your OpenStack cloud Glance services. 

Most of these functions require root level access within your virtual machine. You can open a root login session from `sudo` with `sudo -l`.

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

The modules all include an `enabled` attribute which must be set to `true` for any onboard configuration to take place. For the most part these modules are mutually exclusive from each other, meaning you should only use the one that fits your deployment environment.

## tmos_static_mgmt ##

This cloudinit module extents TMOS to allow for static address assignment provided through cloudinit userdata.

| Module Attribute | Default | Description|
| --------------------- | -----------| ---------------|
| enabled              | false      | Activates ths module|
| ip         | none (required)        | The management IP address or CIDR |
| netmask | none | The management IP netmask, only required if ip is not CIDR |
| gw | none | The management default gateway IP address |
| mtu | 1500 | The management link MTU |
| post_onboard_enabled | false | Enabled the attempt to run a list of commands after onboarding completes |
| post_onboard_commands | list | List of CLI commands to run in order. Execution will halt at the point a CLI command fails. |


### usage ###

```
#cloud-config
tmos_static_mgmt:
  enabled: true
  ip: 192.168.245.100
  netmask: 255.255.255.0
  gw: 192.168.245.1
  mtu: 1450
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
    - /usr/bin/curl https://webhook.site/d52ba6d9-653d-4817-b34e-4f927026a639
```

## tmos_configdrive_openstack ##
This cloudinit module requries the use of a ConfigDrive data source and OpenStack file formatted meta_data.json and network_data.json metadata files. This module extents TMOS functionality to include static provisioning off all interfaces (manaement and TMM) via either network metadata or the use of DHCPv4. This interface includes the ability to augment the configuration data retrieved via metadata and DHCP with additional f5-declarative-onboarding and f5-appsvc-3 declarations. Any supplied f5-declarative-onboarding declarations will overwrite or be merged with configuration declarations defined via metadata resource resolution. This modules support both 1NIC and nNIC deployments.

There are implicit declarations of the TMM intefaces names to use for the data plane default route and the configuration sychronization interfaces. If these declarations are omitted, the module will attempt to assign them dynamically based on available network configuration data.

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
| as3_enabled | true | Enables attempt to declare an application services configuration with f5-appsvcs-3|
| as3_declaration | none | The f5-appsvcs-3 declaration to declare if enabled |
| post_onboard_enabled | false | Enabled the attempt to run a list of commands after onboarding completes |
| post_onboard_commands | list | List of CLI commands to run in order. Execution will halt at the point a CLI command fails. |

#### Warning: f5-declarative-onboarding and f5-appsvcs-3 do not support the use of route domains at this time. You should disable route domain support when attempting to use f5-declarative-onboarding and f5-appsvcs-3 declarations 

SSH keys found in the OpenStack meta_data.json file will also be injected as authorized_keys for the root account.

If f5-declarative-onboarding is disbaled, done by setting `do_eabled` to false, the device onboarding configuration will contine as described in the OpenStack meta_data.json and network_data.json files. f5-appsrvs-3 declarations can be applied with or without f5-declarative-onboarding being enabled.

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
| as3_enabled | true | Enables attempt to declare an application services configuration with f5-appsvcs-3|
| as3_declaration | none | The f5-appsvcs-3 declaration to declare if enabled |
| post_onboard_enabled | false | Enabled the attempt to run a list of commands after onboarding completes |
| post_onboard_commands | list | List of CLI commands to run in order. Execution will halt at the point a CLI command fails. |

#### Warning: f5-declarative-onboarding and f5-appsvcs-3 do not support the use of route domains at this time. You should disable route domain support when attempting to use f5-declarative-onboarding and f5-appsvcs-3 declarations 

If f5-declarative-onboarding is disbaled, done by setting `do_eabled` to false, the device onboarding configuration will contine as described in the OpenStack meta_data.json and network_data.json files. f5-appsrvs-3 declarations can be applied with or without f5-declarative-onboarding being enabled.

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
    - /usr/bin/curl https://webhook.site/d52ba6d9-653d-4817-b34e-4f927026a639
```

In addition to the delcared elements, this module also supports `cloud-config` delcarations for `ssh_authorized_keys`. Any declared keys will be authorized for the TMOS root account.

```
#cloud-config
ssh_authorized_keys:
  - ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEA3FSyQwBI6Z+nCSjUUk8EEAnnkhXlukKoUPND/RRClWz2s5TCzIkd3Ou5+Cyz71X0XmazM3l5WgeErvtIwQMyT1KjNoMhoJMrJnWqQPOt5Q8zWd9qG7PBl9+eiH5qV7NZ mykey@host
```


## tmos_declared ##

This module assumes the management interface provisioning completes via the default method (DHCPv4 or DHCPv6), but that all other onboard configurations should be handled through f5-declarative-onboarding and f5-appsvcs-3 declarations. 

### Warning: DHCPv6 does not include interface-mtu support, meaning your access to your management interface might not be reliable. IPv6 requires the mgmt interface be set to a minumum of 1280 bytes, but SDN tunnel types might limit it to below the standard 1500 bytes. ###


The declarations must be coherent with the deployment environment. As an example, the f5-declarative-onboarding declaration would need to include the `internal` VLAN and the `self_1nic` SelfIP classes to properly declare a 1NIC deployment.

| Module Attribute | Default | Description|
| --------------------- | -----------| ---------------|
| enabled              | false      | Activates ths module|
| icontrollx_package_urls | none | List of URLs to download and install iControl LX extension packages before onboarding |
| do_declaration | none |  YAML formatted f5-declarative-onboarding declaration. This declaration will augment or overwrite the declaration created by resource discovery |
| as3_declaration | none | The f5-appsvcs-3 declaration to declare if enabled |

```
#cloud-config
tmos_declared:
  enabled: True
  icontrollx_package_urls:
    - https://github.com/F5Networks/f5-declarative-onboarding/raw/master/dist/f5-declarative-onboarding-1.3.0-4.noarch.rpm
    - https://github.com/F5Networks/f5-appsvcs-extension/raw/master/dist/latest/f5-appsvcs-3.10.0-5.noarch.rpm
    - https://github.com/F5Networks/f5-telemetry-streaming/raw/master/dist/f5-telemetry-1.2.0-1.noarch.rpm
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
      ...
  as3_declaration:
    class: AS3
    action: deploy
    persist: true
    declaration:
      class: ADC
      schemaVersion: 3.0.0
      ...
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


