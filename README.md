# tmos-cloudinit
###Cloudinit Modules and Patching for F5  TMOS###

F5 TMOS is a secured and close operating system which can not take advantage of the linux community's work to standardize cloud virtual machine onboarding through the cloud-init project.

Starting with TMOS v13, an order version of cloud-init was included with TMOS, but had only the following modules available:

- bootcmd
- write_file
- runcmd

Through the use of these cloud-init modules, various combinates of `bash`, `javascript`, and `python` onboard scripting evolved within specific cloud ecosystems. The specifcs depended on the environment and what orchestration systems were available. 

In an attempt to standardize these efforsts, F5 launched a set of declarative `iControl LX` extensions which can be used to configure TMOS and provision BIG-IP services. These extensions, marketed as the Automation and Orchestration (A & O) toolchain, can be installed on TMOS devices and then called through RESTful interfaces. The problem was these extensions do not come preinstalled nor do the take advantage of the configuration metadata provided by cloud environments to virtual machines instances. 

The cloud-init modules need to be file-injected into standard TMOS images before they can be used.

The modules all include an `enabled` attribute which must be set to `true` for any onboard configuration to take place. For the most part these modules are mutually exclusive from each other, meaning you should only use the one that fits your deployment environment.

## tmos_static_mgmt ##

This cloud-init module extents TMOS to allow for static address assignment provided through cloud-init userdata. This modules support both 1NIC and nNIC deployments.

### usage ###

```
#cloud-config
tmos_static_mgmt:
  enabled: true
  ip: 192.168.245.100/24
  gw: 192.168.245.1
  mtu: 1450
```

## tmos_configdrive_openstack ##
This cloud-init module requries the use of a configdrive data source and OpenStack file format meta_data.json and network_data.json. This module extents TMOS functionality to include static provisioning off all interfaces (manaement and TMM) via either static network metadata or the use of DHCPv4 or DHCPv6. This interface includes the ability to augment the configuration data retrieved via metadata and DHCP with additiona f5-declarative-onboarding and f5-appsvc-3 declarations. Any f5-declarative-onboarding declarations will overwrite or be merged with configuration declarations defined via metadata resource resolution.

There are implicit declarations of the TMM intefaces names to use for the data plane default route and the configuration sychronization interfaces. If these declarations are omitted, the module will attempt to assign them dynamically based on available network configuration data.


####Warning: f5-declarative-onboarding does not support the use of route domains at this time. 

SSH keys found in the OpenStack meta_data.json file will also be injected as authorized_keys for the root account.

If f5-declarative-onboarding is disbaled, but setting `do_eabled`  to false,  the device onboarding configuration will contine as described in the OpenStack meta_data.json and network_data.json files. f5-appsrvs-3 declarations can be applied without f5-declarative-onboarding being enabled. Be aware the f5-appsvcs-3 does not yet support route domains either.

```
tmos_configdrive_openstack:
  enabled: true
  rd_enabled: false
  do_enabled: true
  configsync_interface: 1.1
  default_route_interface: 1.3
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
  as3_declaration:
    class: AS3
    action: deploy
    persist: true
    declaration:
      class: ADC
      schemaVersion: 3.0.0
      ...

```

## tmos_dhcp_tmm ##

This cloud-init module resolves configuration data for all interfaces (management and TMM) through DHCPv4 or DHCPv6. All interfaces should be connected to networks with DHCP services.

There are implicit declarations of the TMM intefaces names to use for the data plane default route and the configuration sychronization interfaces. If these declarations are omitted, the module will attempt to assign them dynamically based on available network configuration data.

This module similarly support both f5-declarative-onboarding and f5-appsvcs-3 declarations.

Unlike the OpenStack metadata module, no source of SSH keys for injection is assume. SSH keys can be explicitly declared via the standard cloud-init `ssh_authorized_keys` syntax.


```
#cloud-config
ssh_authorized_keys:
  - ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEA3FSyQwBI6Z+nCSjUUk8EEAnnkhXlukKoUPND/RRClWz2s5TCzIkd3Ou5+Cyz71X0XmazM3l5WgeErvtIwQMyT1KjNoMhoJMrJnWqQPOt5Q8zWd9qG7PBl9+eiH5qV7NZ mykey@host

tmos_dhcp_tmm:
  enabled: True
  rd_enabled: False
  do_enabled: True
  configsync_interface: 1.1
  default_route_interface: 1.3
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
  as3_declaration:
    class: AS3
    action: deploy
    persist: true
    declaration:
      class: ADC
      schemaVersion: 3.0.0
     ...
```

##tms_declared##

This module assumes the management interface provision happens in the default method (DHCPv4), but that all other onboard configurations should be handled through f5-declarative-onboarding and f5-appsvcs-3 declarations.

The `ssh_autorized_key` functionality is included as f5-declarative-onboarding does not support SSH key injection at this time.

```
#cloud-config
tmos_configdrive_openstack:
  enabled: True
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
  as3_declaration:
    class: AS3
    action: deploy
    persist: true
    declaration:
      class: ADC
      schemaVersion: 3.0.0
      ...
```

The patched cloud-init configuration template has been alterred to support the cloud-init `set_password` module. You can cahnge the built in TMOS `admin` and  `root` passwords using the following declarations.


```
#cloud-config
chpasswd:
  list: |
    root:f5str0ngPa$$word
    admin:f5str0ngPa$$word
  expire: False
```


