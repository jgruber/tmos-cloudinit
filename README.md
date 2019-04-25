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

The modules all include an `enabled` attribute which must be set to `true` for any onboard configuration to take place. For the most part these modules are mutually exclusive from each other, meaning you should only use the one that fits your deployment environment.

## tmos_static_mgmt ##

This cloudinit module extents TMOS to allow for static address assignment provided through cloudinit userdata.

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
This cloudinit module requries the use of a ConfigDrive data source and OpenStack file formatted meta_data.json and network_data.json metadata files. This module extents TMOS functionality to include static provisioning off all interfaces (manaement and TMM) via either network metadata or the use of DHCPv4 or DHCPv6. This interface includes the ability to augment the configuration data retrieved via metadata and DHCP with additional f5-declarative-onboarding and f5-appsvc-3 declarations. Any supplied f5-declarative-onboarding declarations will overwrite or be merged with configuration declarations defined via metadata resource resolution. This modules support both 1NIC and nNIC deployments.

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


## tmos_dhcp_tmm ##

This cloudinit module resolves configuration data for all interfaces (management and TMM) through DHCPv4 or DHCPv6. All interfaces should be connected to networks with DHCP services. This modules support both 1NIC and nNIC deployments.

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

This module assumes the management interface provisioning completes via the default method (DHCPv4), but that all other onboard configurations should be handled through f5-declarative-onboarding and f5-appsvcs-3 declarations. 

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


