# tmos-cloudinit
### Cloudinit Modules and Patching for F5  TMOS ###

F5 TMOS is a secured operating system designed for deployment as a network appliance. While TMOS utilizes a CentOS based kernel and linux based control processes to bootstrap and configure distributed networking microkernels, it has been highly customized from typical linux distributions.  

Linux distributions use a standard bootstrapping agent known as cloudinit to integrate cloud infrastructure metadata with the systems init processes.

Starting with TMOS v13, TMOS inluded a version of cloudinit, but due to TMOS customizations, only the following cloudinit modules were enabled available:

- bootcmd
- write_file
- runcmd

Through the use of these cloudinit modules, various combinates of `bash`, `javascript`, and `python` onboard scripting evolved within specific cloud ecosystems. TMOS onboarding templates were created for various IaaS environments. The templates created the necessary provisioning scripts gleaning instance metadata from source unique to each IaaS environment. 

In an attempt to standardize TMOS orchestration efforts, F5 created an extensible service framework capable of extending TMOS' REST provisioning called iControl LX. Supported iControl LX extensions which provided base TMOS system provisioning (f5-declarative-onboaring) and TMM service provisioning (f5-appsvcs-extension) are constantly evolving to support a catalog of deployment use cases. These and other extensions make up the F5 Automation and Orchestration (A & O) toolchain.

The cloudinit modules found in this repository unity TMOS cloudinit agent support with iControl LX extensions. Each of these modules support the publishing and installation of iControl LX extensions for use in TMOS orchestration. There are experimental cloudinit modules to extend TMOS support for static management interface provisioning, provisioning of TMM interfaces through DHCPv4, and total system network provisioning gleaned from TMOS standard network_data.json metadata.  

The cloudinit modules included in this repository need to be file-injected into standard TMOS v13+ images before they can be used.

## Patching TMOS VE Images to Install Cloudinit Modules - Using a Docker Instance ##

This repository includes a Dockerfile and patch scripts which can build a Docker instance capable of patching standard images from `downloads.f5.com` to include additional cloudinit modules and iControl LX extensions.

Download the images you wish to patch with this repositories' cloudinit modules, and optionally iControl LX extension, to a directories available as a volume to your docker instance.

```
ls /data/BIGIP-14.1
BIGIP-14.1.0.5-0.0.5.ALL_1SLOT-ide.ova
BIGIP-14.1.0.5-0.0.5.ALL_1SLOT.qcow2.zip
BIGIP-14.1.0.5-0.0.5.ALL_1SLOT-scsi.ova
BIGIP-14.1.0.5-0.0.5.ALL_1SLOT.vhd.zip
BIGIP-14.1.0.5-0.0.5.LTM_1SLOT-ide.ova
BIGIP-14.1.0.5-0.0.5.LTM_1SLOT-scsi.ova
BIGIP-14.1.0.5-0.0.5.LTM_1SLOT.qcow2.zip
BIGIP-14.1.0.5-0.0.5.LTM_1SLOT.vhd.zip
```

You can also prepare a directory which can container iControl LX packag `rpm` files.

```
$ ls /data/iControlLXLatestBuild
f5-appsvcs-3.11.0-3.noarch.rpm
f5-declarative-onboarding-1.4.0-1.noarch.rpm
```

#### Note: do not remove the disk images from their archive containers (zip or ova) ####

You can build the docker image from the `tmos_image_patcher` Dockerfile.

```
$ docker build -t tmos_image_patcher:latest tmos_image_patcher
```

After the build process completes, you should have a docker image available to you locally.

```
$ docker images | grep tmos_image_patcher
tmos_image_patcher    latest    3416ed456cfe    22 seconds ago    1.38GB
```

Patched images can then be build by creating a `tmos_image_builder` docker instance based on your image.

#### Expected Docker Volume Mounts ####

Make sure you create the mounts as specified below. Your TMOS image archives folder should be mounted as a volume to `/TMOSImages` and any 
iControl LX extensions you want injected into your image shuld be mounted to the instances' `/iControlLXPackages` directory.

| Docker Volume Mount | Required | Description |
| --------------------- | ----- | ---------- |
| /TMOSImages   | Yes | Path to the directory with the TMOS Virtual Edition archives to patch |
| /iControlLXPackages   | No | Path to the directory with optional iControl LX RPM packages to inject into the images |

#### Example Mounts ####

`
-v /data/BIGIP-14.1:/TMOSImages -v /data/iControlLXLatestBuild:/iControlLXPackages
`

You can run the image patch script as a Docker contianer with the Docker `run` command.

```
$ docker run --rm -it -v /data/BIGIP-14.1:/TMOSImages -v /data/iControlLXLatestBuild:/iControlLXPackages tmos_image_patcher

2019-05-29 22:43:48,133 - tmos_image_patcher - DEBUG - process start time: Wednesday, May 29, 2019 10:43:48
2019-05-29 22:43:48,133 - tmos_image_patcher - INFO - Scanning for images in: /TMOSImages
2019-05-29 22:43:48,133 - tmos_image_patcher - INFO - TMOS cloudinit modules sourced from: /tmos-cloudinit
2019-05-29 22:43:48,133 - tmos_image_patcher - INFO - Copying iControl LX install packages from: /iControlLXPackages
2019-05-29 22:43:48,133 - tmos_image_patcher - INFO - Patching TMOS /usr file system from: /tmos-cloudinit/image_patch_files/usr
2019-05-29 22:43:48,133 - tmos_image_patcher - DEBUG - extracting /TMOSImages/BIGIP-14.1.0.5-0.0.5.ALL_1SLOT.vhd.zip to /TMOSImages/BIGIP-14.1.0.5-0.0.5.ALL_1SLOT.vhd
2019-05-29 22:44:41,790 - tmos_image_patcher - DEBUG - extracting /TMOSImages/BIGIP-14.1.0.5-0.0.5.LTM_1SLOT.vhd.zip to /TMOSImages/BIGIP-14.1.0.5-0.0.5.LTM_1SLOT.vhd
2019-05-29 22:45:41,653 - tmos_image_patcher - DEBUG - extracting /TMOSImages/BIGIP-14.1.0.5-0.0.5.LTM_1SLOT-ide.ova to /TMOSImages/BIGIP-14.1.0.5-0.0.5.LTM_1SLOT-ide
...

```

Each TMOS image archive will be expanded into a folder containing your newly patched image. The folder will have the same name as the archive file without the extension. The patched image, in the expanedd folder, will be in the same format as the original. You can utilize your patched images just as you would the originals.

<pre>
> $ tree /data/BIGIP-14.1
/data/BIGIP-14.1
├── BIGIP-14.1.0.5-0.0.5.ALL_1SLOT-ide
│   └── <b>BIGIP-14.1.0.5-0.0.5.ALL_1SLOT-ide.ova</b>
├── BIGIP-14.1.0.5-0.0.5.ALL_1SLOT-ide.ova
├── BIGIP-14.1.0.5-0.0.5.ALL_1SLOT.qcow2
│   └── <b>BIGIP-14.1.0.5-0.0.5.qcow2</b>
├── BIGIP-14.1.0.5-0.0.5.ALL_1SLOT.qcow2.zip
├── BIGIP-14.1.0.5-0.0.5.ALL_1SLOT-scsi
│   └── <b>BIGIP-14.1.0.5-0.0.5.ALL_1SLOT-scsi.ova</b>
├── BIGIP-14.1.0.5-0.0.5.ALL_1SLOT-scsi.ova
├── BIGIP-14.1.0.5-0.0.5.ALL_1SLOT.vhd
│   └── <b>BIGIP-14.1.0.5-0.0.5.vhd</b>
├── BIGIP-14.1.0.5-0.0.5.ALL_1SLOT.vhd.zip
├── BIGIP-14.1.0.5-0.0.5.LTM_1SLOT-ide
│   └── <b>BIGIP-14.1.0.5-0.0.5.LTM_1SLOT-ide.ova</b>
├── BIGIP-14.1.0.5-0.0.5.LTM_1SLOT-ide.ova
├── BIGIP-14.1.0.5-0.0.5.LTM_1SLOT.qcow2
│   └── <b>BIGIP-14.1.0.5-0.0.5.qcow2</b>
├── BIGIP-14.1.0.5-0.0.5.LTM_1SLOT.qcow2.zip
├── BIGIP-14.1.0.5-0.0.5.LTM_1SLOT-scsi
│   └── <b>BIGIP-14.1.0.5-0.0.5.LTM_1SLOT-scsi.ova</b>
├── BIGIP-14.1.0.5-0.0.5.LTM_1SLOT-scsi.ova
├── BIGIP-14.1.0.5-0.0.5.LTM_1SLOT.vhd
│   └── <b>BIGIP-14.1.0.5-0.0.5.vhd</b>
└── BIGIP-14.1.0.5-0.0.5.LTM_1SLOT.vhd.zip
</pre>

As an example, your patched image could be uploaded directly to OpenStack Glance.

```
$ openstack image create --disk-format qcow2 --container-format bare --file /data/BIGIP-14.1/BIGIP-14.1.0.5-0.0.5.LTM_1SLOT.qcow2/BIGIP-14.1.0.5-0.0.5.qcow2 OpenStack_BIGIP-14.1.0.5-0.0.5.LTM_1SLOT
+------------------+------------------------------------------------------+
| Field            | Value                                                |
+------------------+------------------------------------------------------+
| checksum         | 4929021d0f045eb91f928f4cf26aeca9                     |
| container_format | bare                                                 |
| created_at       | 2019-05-29T23:23:29Z                                 |
| disk_format      | qcow2                                                |
| file             | /v2/images/c8692af7-66a7-4dd0-8b0a-81506b0b3b74/file |
| id               | c8692af7-66a7-4dd0-8b0a-81506b0b3b74                 |
| min_disk         | 0                                                    |
| min_ram          | 0                                                    |
| name             | OpenStack_BIGIP-14.1.0.5-0.0.5.LTM_1SLOT             |
| owner            | 14910e1a2ed544f7aef81c5019d43f4a                     |
| protected        | False                                                |
| schema           | /v2/schemas/image                                    |
| size             | 5069668352                                           |
| status           | active                                               |
| tags             |                                                      |
| updated_at       | 2019-05-29T23:24:14Z                                 |
| virtual_size     | None                                                 |
| visibility       | shared                                               |
+------------------+------------------------------------------------------+

```

Once your patched images are available to your virtualized environment, you can use cloudinit userdata to handle initial device and service provisioning.

## Creating OpenStack Formatted Cloudinit ConfigDrive ISOs - Using a Docker Instance ##

While IaaS clouds already support mechanisms to supply cloudinit userdata to declare guest instances configurations, TMOS VE is supported in sparser virtualization environments which might not. For those environments, an ISO CDROM image can be attached to TMOS VE guest prior to booting it. If the ISO CDROM image is properly formatted as a cloudinit ConfigDrive data source, cloudinit modules can still be used.

As an example, VMWare Workstation can be use to create a TMOS VE instance from a patched TMOS OVA archive. It will suitably build the instance attributes per the F5 defined OVF, but will then wait for the end user to start the instance. Prior to starting the instance, the user can add an IDE CDROM drivce device and attach a ConfigDrive ISO file.

TMOS supports cloudinit OpenStack ConfigDrive. The ISO CDROM attached has to have a volume label of `config-2` and must follow a specific layout of files, containing a specific JSON file with a specific attribute defined.

<pre>
/iso (volume label config-2)
└── openstack
    └── latest
        ├── meta_data.json
        ├───────────────────> {"uuid": "a7481585-ee3f-432b-9f7e-ddc7e5b02c27"}
        ├── user_data
        └───────────────────> THIS CAN CONTAIN ANY USERDATA YOU WANT
</pre>

If you generate an ISO9660 files system with Rock Ridge extensions to allow TMOS cloudinit to mount your device and act on your userdata, you can treat any virtualization environment like a properly declared IaaS. You can use any ISO9660 filesystem generation tool you want, as long as it conforms to the standard for the OpenStack ConfigDrive cloudinit data source.

This repository includes a Dockerfile and an ISO9660 generation script which will create the appropriate CDROM ISO image file provided proper inputs. 

You can build the docker image from the `tmos_configdrive_builder` Dockerfile.

```
$ docker build -t tmos_configdrive_builder:latest tmos_configdrive_builder
```

After the build process completes, you should have a docker image available to you locally.

```
$ docker images|grep tmos_configdrive_builder
tmos_configdrive_builder     latest     23c1d99efdd5     17 seconds ago     274MB
```

The script was designed to take inputs as environment variables, rather then command line arguments, to make use via `docker` easier for the end user. Any content, like your declarations or whole JSON dictionaries, are made available via files in specific directories. This too was done to make them available to Docker instances via volume mounts.

The CDROM is built to be use in two modes:

1. `tmos_declared` mode - which builds f5-declarative-onboarding and optionally f5-appsvcs-extensions declarations, `phone_home_url` and `phone_home_cli` variables, into a CDROM ISO usable with the `tmos_declared` cloudinit module.

2. Fully explicit mode - which builds a CDROM ISO from a fully defined set of `user_data`, and optionally `meta_data.json`, `vendor_data.json`, and `network_data.json` files. This allows for the construction of any settings in your `user_data` you want. This can be used to work with any of the modules defined in this repository.

#### tmos_declared Mode Environment Variables and Files ####

Here is a list of environment variables to set which will determine how CDROM ISO is built:

| Environment Variable | Required | Default | Description|
| --------------------- | ----- | ---------- | ---------------|
| DO_DECLARATION_FILE   | Yes | /declarations/do_declaration.json | Your f5-declarative-onboarding declaration in a text file. The declaration can be in JSON or YAML format. |
| AS3_DECLARATION_FILE  | No | /declarations/as3_declaration.json | Your f5-appsvcs-extension declaration in a text file. The declaration can be in JSON or YAML format. |
| PHOME_HOME_URL | No | None | The URL to use as the `phone_home_url` attributed of the `tmos_declared` declaration. |
| PHOME_HOME_CLI | No | None | The URL to use as the `phone_home_url` attributed of the `tmos_declared` declaration. |
| CONFIGDRIVE_FILE | Yes | /configdrives/configdrive.iso | The output ISO file. |

The files specified above must be available to the Docker instance, so should be the volume mount paths as seen from within the Docker instance.

If you have a local subfolder `declarations` directory containing both `do_declaration.json` and `as3_declaration.json`, you could create your basic CDROM ISO in the current directory wih the following bash shell command.

```
docker run --rm -it -v $(pwd)/declarations:/declarations -v $(pwd):/configdrives tmos_configdrive_builder
2019-05-30 20:00:59,009 - tmos_image_patcher - INFO - building ISO9660 for tmos_declared module with declarations
2019-05-30 20:00:59,029 - tmos_image_patcher - INFO - adding f5-declarative-onboarding declaration to user_data
2019-05-30 20:00:59,029 - tmos_image_patcher - INFO - adding f5-appsvcs-extensions declaration to user_data
2019-05-30 20:00:59,042 - tmos_image_patcher - INFO - generating OpenStack mandatory ID
2019-05-30 20:00:59,046 - tmos_image_patcher - INFO - output IS09660 file: /configdrives/configdrive.iso
ls ./configdrive.iso
configdrive.iso
```

If you are not comfortable with, or can not use bash expansion, just fully defined your file paths.

To define `phone_home_url` or `phone_home_cli` attributes in your `tmos_declared` declaration, simply add them as Docker environment variables.

#### Expected Docker Volume Mounts ####

There are two mount paths the configdrive ISO builder script expects to have available. One is a file path to your declarations, either default or explicitly defined by environment variables. The other is the directory to write your ISO file.

| Docker Volume Mount | Required | Description |
| --------------------- | ----- | ---------- |
| /declarations   | Yes | Path to the directory containing your declarations |
| /configdrives   | Yes | Path to the directory to write your ISO files |

As an example, to create an `configdrive.iso` file in the current directory which would creeate metadata for the `tmos_declared` cloudint module, taking declarations files from the `./declarations` directory, while explicitly defining a `phone_home_url`, the Docker `run` syntax would look like the following.


```
docker run --rm -it -e PHONE_HOME_URL=https://webhook.site/5f8cd8a7-b051-4648-9296-8f6afad34c93 -v $(pwd)/declarations:/declarations -v $(pwd):/configdrives tmos_configdrive_builder
```

#### Explicit Mode Environment Variables and Files ####

If the script has a `USERDATA_FILE` or finds a `/declarations/user_data` file, it will automatically prefer explicit mode. 

The other defined optional files `METADATA_FILE`, `VENDORDATA_FILE`, and `NETWORKDATA_FILE`, should conform to the OpenStack metadata standards for use with cloudinit.

| Environment Variable | Required | Default | Description|
| --------------------- | ----- | ---------- | ---------------|
| USERDATA_FILE   | Yes | /declarations/user_data | Your fully defined user_data to include. |
| METADATA_FILE   | No | /declarations/meta_data.json | Your fully defined instance meta_data to include in JSON format. |
| VENDOR_FILE   | No | /declarations/vendor_data.json | Your fully defined instance vendor_data to include in JSON format. |
| NETWORKDATA_FILE   | No | /declarations/network_data.json | Your fully defined instance network_data to include in JSON format. |
| CONFIGDRIVE_FILE | Yes | /configdrives/configdrive.iso | The output ISO file. |

```
docker run --rm -it -e USERDATA_FILE=/declarations/instance2224 -v $(pwd)/declarations:/declarations -v $(pwd):/configdrives tmos_configdrive_builder
2019-05-30 20:04:12,158 - tmos_image_patcher - INFO - building ISO9660 configdrive user_data from /declarations/instance2224
2019-05-30 20:04:12,158 - tmos_image_patcher - INFO - generating OpenStack mandatory ID
2019-05-30 20:04:12,163 - tmos_image_patcher - INFO - output IS09660 file: /configdrives/configdrive.iso
ls ./configdrive.iso
configdrive.iso
```

# Using F5 TMOS Cloudinit Modules #

The modules all include an `enabled` attribute which must be set to `true` for any onboard configuration to take place. For the most part these modules are mutually exclusive from each other, meaning you should only use the one that fits your deployment environment.

All modules log to the common `/var/log/f5-cloudinit.log` log file. 


## Which Cloudinit Module Should You Use? ##

Each module handles very specific use cases. Each use case aquires the per-instance configuration data from different resources.

| Module | Aquires Per-Instance Config From | Provisions |
| --------------------- | ----------------- | ---------- |
| tmos_static_mgmt   | cloudinit YAML declaration | Provisions the management interface statically from cloudinit YAML, and then optionally installs iControl LX extensions. |
| tmos_declared   | cloudinit YAML declaration | Optionally installs iControl LX extensions and then makes f5-declarative-onboarding and f5-appsvcs-extention declarations. |
| tmos_configdrive_openstack  | OpenStack metadata, and cloudinit YAML declaration | Provisions the management interface from OpenStack metadata, then optionally installs iControl LX extensions. An f5-declarative-onboarding declaration is constructed from OpenStack metadata. Any f5-declarative-onboarding declaration made in the cloudinit YAML is merged with the declaration created from OpenStack metadata. Any attributes defined in the declaration in the cloud YAML overwrites any attribute constructed from the OpenStack metadata. After f5-declarative-onboarding is complete, optionally an f5-appsvcs-extension declaration from the cloudinit YAML delcaration is made. |
| tmos_dhcpv4_tmm   | DHCPv4 requests on all interfaces, and cloudinit YAML declaration | Provisions the management interface from DHCPv4 lease information, then optionally installs iControl LX extensions. An f5-declarative-onboarding declaration is constructed from DHCPv4 lease information. Any f5-declarative-onboarding declaration made in the cloudinit YAML is merged with the declaration created from DHCPv4 lease information. Any attributes defined in the declaration in the cloud YAML overwrites any attributes constructed from DHCPv4 information. After f5-declarative-onboarding is complete, optionally an f5-appsvcs-extension declaration from the cloudinit YAML delcaration is made.|

You should use the module which matches your sources of per-instance configuration data.

## The tmos_static_mgmt Cloudinit Module ##

This cloudinit module extents TMOS to allow for static address assignment provided through cloudinit userdata.

This modules create initialization scripts containing TMOS `tmsh` commands to fulfill the specified configurations. The generated initialization scripts are created in the `/opt/cloud/tmos_static_mgmt` directory on the device.

| Module Attribute | Default | Description|
| --------------------- | -----------| ---------------|
| enabled              | false      | Activates ths module|
| ip         | none (required)        | The management IP address or CIDR. |
| netmask | none | The management IP netmask, only required if ip is not CIDR. |
| gw | none | The management default gateway IP address. |
| mtu | 1500 | The management link MTU. |
| hostname | none | The hostname in FQDN format (host and domain) to assign. |
| nameservers | list | List of DNS server IP addresses. |
| searchdomain | none | A single search domain to assign. |
| ntpservers | list | List of NTP server FQDNs or IP addresses. | 
| icontrollx_trusted_sources | true | Only install iControl LX RPMs which are signed by TMOS trusted keys. |
| icontrollx_package_urls | none | List of URLs to download and install iControl LX extension packages before onboarding. |
| post_onboard_enabled | false | Enabled the attempt to run a list of commands after onboarding completes. |
| post_onboard_commands | list | List of CLI commands to run in order. Execution will halt at the point a CLI command fails. |
| phone_home_url | url | Reachable URL to report completion of this modules onboarding. |
| phone_home_url_verify_tls | true | If the phone_home_url uses TLS, verify the host certificate. |
| phone_home_cli | cli command | CLI command to run when this modules completes successfully. |

#### Note: The `tmos_static_mgmt` module can be used in conjuction with the `tmos_declared` module to add managment interface provisioning before iControl LX extension declarations are made. ####


### userdata usage ###

```
#cloud-config
tmos_static_mgmt:
  enabled: true
  ip: 192.168.245.100
  netmask: 255.255.255.0
  gw: 192.168.245.1
  mtu: 1450
  icontrollx_trusted_sources: false
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
  phone_home_cli: "curl -i -X POST -H 'X-Auth-Token: gAAAAABc5UscwS1py5XfC3yPcyN8KcgD7hYtEZ2-xHw95o4YIh0j5IDjAu9qId3JgMOp9hnHwP42mYA7oPPP0yl-OQXvCaCS3OezKlO7MsS-ZCTJzuS3sSysIMHTA78fGsXbMgCQZCi5G-evLG9xUNrYp5d3blhMnpHR0dlHPz6VMacNkPhyrQI' -H 'Content-Type: application/json' -H 'Accept: application/json' http://192.168.0.121:8004/v1/d3779c949b57403bb7f703016e91a425/stacks/demo_waf/3dd6ce45-bb8c-400d-a48c-87ac9e46e60e/resources/wait_handle/signal"
```

## The tmos_declared Cloudinit Module ##

This module assumes the management interface provisioning completes via the default method (DHCPv4 or DHCPv6), but that all other onboard configurations should be handled through f5-declarative-onboarding and f5-appsvcs-extension declarations. 

### Warning: DHCPv6 does not include interface-mtu support, meaning your access to your management interface might not be reliable. IPv6 requires the mgmt interface be set to a minumum of 1280 bytes, but SDN tunnel types might limit it to below the standard 1500 bytes. Use the `tmos_static_mgmt` in your cloudinit YAML if you need to provision your management interface to make it accessible. ###

The declarations must be coherent with the deployment environment. As an example, the f5-declarative-onboarding declaration would need to include the `internal` VLAN and the `self_1nic` SelfIP classes to properly declare a 1NIC deployment.

This cloudinit module optionally composes f5-declarative-onboarding declarations in the `/var/lib/cloud/f5-declarative-onboarding` directory. This declaration is in JSON format.

This cloudinit module optionally composes f5-appsvcs-extension declarations in the `/var/lib/cloud/f5-appsvcs-extension` directory. This declaration is in JSON format.

| Module Attribute | Default | Description|
| --------------------- | -----------| ---------------|
| enabled              | false      | Activates ths module|
| icontrollx_trusted_sources | true | Only install iControl LX RPMs which are signed by TMOS trusted keys |
| icontrollx_package_urls | none | List of URLs to download and install iControl LX extension packages before onboarding |
| do_declaration | none |  YAML formatted f5-declarative-onboarding declaration. This declaration will augment or overwrite the declaration created by resource discovery |
| as3_declaration | none | The f5-appsvcs-extension declaration to declare if enabled |
| phone_home_url | url | Reachable URL to report completion of this modules onboarding. |
| phone_home_url_verify_tls | true | If the phone_home_url uses TLS, verify the host certificate. |
| phone_home_cli | cli command | CLI command to run when this modules completes successfully. |

#### Note: It is often simplier to use the `set-password` cloudinit module (referenced below) to change the default `admin` and `root` passwords rather than the f5-declarative-onboarding declaration to change user passwords. Both ways work as designed. ####

### userdata usage ###

```
#cloud-config
tmos_declared:
  enabled: true
  icontrollx_trusted_sources: false
  icontrollx_package_urls:
    - "https://github.com/F5Networks/f5-declarative-onboarding/raw/master/dist/f5-declarative-onboarding-1.3.0-4.noarch.rpm"
    - "https://github.com/F5Networks/f5-appsvcs-extension/raw/master/dist/latest/f5-appsvcs-3.10.0-5.noarch.rpm"
    - "https://github.com/F5Networks/f5-telemetry-streaming/raw/master/dist/f5-telemetry-1.2.0-1.noarch.rpm"
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
          url: "https://raw.githubusercontent.com/f5devcentral/f5-asm-policy-template-v13/master/owasp_ready_template/owasp-no-autotune.xml"
          ignoreChanges: true
  post_onboard_enabled: true
  post_onboard_commands:
    - "echo 'curl -s http://monitors.internal.local/rebooted' >> /config/startup"
  phone_home_url: "https://webhook.site/5f8cd8a7-b051-4648-9296-8f6afad34c93"
  phone_home_cli: "curl -i -X POST -H 'X-Auth-Token: gAAAAABc5UscwS1py5XfC3yPcyN8KcgD7hYtEZ2-xHw95o4YIh0j5IDjAu9qId3JgMOp9hnHwP42mYA7oPPP0yl-OQXvCaCS3OezKlO7MsS-ZCTJzuS3sSysIMHTA78fGsXbMgCQZCi5G-evLG9xUNrYp5d3blhMnpHR0dlHPz6VMacNkPhyrQI' -H 'Content-Type: application/json' -H 'Accept: application/json' http://192.168.0.121:8004/v1/d3779c949b57403bb7f703016e91a425/stacks/demo_waf/3dd6ce45-bb8c-400d-a48c-87ac9e46e60e/resources/wait_handle/signal"
```

The `phone_home_url` must take a `POST` reqeust. The `POST` body will be a JSON object with the following format:


```
{
  "id": "a67d1edb-0a4a-4101-afd1-2fbf04713cfa",
  "version": "14.1.0.1-0.0.7.0",
  "product": "BIGIP",
  "hostname": "waf1primary.local",
  "management": "192.168.245.119/24",
  "installed_extensions": ["f5-service-discovery", "f5-declarative-onboarding", "f5-appsvcs"],
  "as3_enabled": true,
  "do_enabled": true,
  "status": "SUCCESS"
}
```

The `phone_home_cli` will only be called if the module runs succesfully, to the degree the provisioning can be synchronized. The `phone_home_cli` command execution allows for OpenStack Heat and AWS CFT type wait condition resources to be use with their auto generated curl CLI notifications.

## The tmos_configdrive_openstack Cloudinit Module ##

This cloudinit module requries the use of a ConfigDrive data source and OpenStack file formatted meta_data.json and network_data.json metadata files. This module extents TMOS functionality to include static provisioning off all interfaces (manaement and TMM) via either network metadata or the use of DHCPv4. This interface includes the ability to augment the configuration data retrieved via metadata and DHCP with additional f5-declarative-onboarding and f5-appsvc-3 declarations. Any supplied f5-declarative-onboarding declarations will overwrite or be merged with configuration declarations defined via metadata resource resolution. This modules support both 1NIC and nNIC deployments.

There are implicit declarations of the TMM intefaces names to use for the data plane default route and the configuration sychronization interfaces. If these declarations are omitted, the module will attempt to assign them dynamically based on available network configuration data.

This modules create initialization scripts containing TMOS `tmsh` commands to fulfill the specified configurations. The generated initialization scripts are created in the `/opt/cloud/tmos_configdrive_openstack` directory on the device.

This cloudinit module optionally composes f5-declarative-onboarding declarations in the `/var/lib/cloud/f5-declarative-onboarding` directory. This declaration is in JSON format.

Any attributes in the `do_declaration` attriute of the cloudinit YAML will be merged into the f5-declarative-onboarding declaration composed from OpenStack metadata. Any declaration attribute defined in the cloudinit YAML will overwrite the same attribute, if present, in the composed declaration.

This cloudinit module optionally composes f5-appsvcs-extension declarations in the `/var/lib/cloud/f5-appsvcs-extension` directory. This declaration is in JSON format.


| Module Attribute | Default | Description|
| --------------------- | -----------| ---------------|
| enabled              | false      | Activates ths module|
| rd_enabled         | true        | Automatically create route domains when needed |
| configsync_interface | 1.1 | Sets the TMM interface name to use for configsync |
| default_route_interface | none | Explicitly define the TMM interface to use for the default route. Otherwise one will be determined automatically |
| dhcp_timeout | 120 | Seconds to wait for a DHCP response when using DHCP for resource discovery |
| inject_routes | true | Creates static routes from discovered route resources |
| icontrollx_trusted_sources | true | Only install iControl LX RPMs which are signed by TMOS trusted keys |
| icontrollx_package_urls | none | List of URLs to download and install iControl LX extension packages before onboarding |
| do_enable | true | Enables attempt to create a f5-declarative-onboarding declaration from discovered resources. If enabled, an asynchronous attempt to declare resouces via f5-declarative-onboarding will be made. If the initial request fails, non-declarative onboarding will resumse |
| do_declaration | none |  YAML formatted f5-declarative-onboarding declaration. This declaration will augment or overwrite the declaration created by resource discovery |
| as3_enabled | true | Enables attempt to declare an application services configuration with f5-appsvcs-extension|
| as3_declaration | none | The f5-appsvcs-extension declaration to declare if enabled |
| post_onboard_enabled | false | Enabled the attempt to run a list of commands after onboarding completes |
| post_onboard_commands | list | List of CLI commands to run in order. Execution will halt at the point a CLI command fails. |
| phone_home_url | url | Reachable URL to report completion of this modules onboarding. |
| phone_home_url_verify_tls | true | If the phone_home_url uses TLS, verify the host certificate. |
| phone_home_cli | cli command | CLI command to run when this modules completes successfully. |

#### Warning: f5-declarative-onboarding and f5-appsvcs-extension do not support the use of route domains at this time. You should disable route domain support when attempting to use f5-declarative-onboarding and f5-appsvcs-extension declarations 

SSH keys found in the OpenStack meta_data.json file will also be injected as authorized_keys for the root account.

If f5-declarative-onboarding is disbaled, done by setting `do_eabled` to false, the device onboarding configuration will contine as described in the OpenStack meta_data.json and network_data.json files. f5-appsvcs-extension declarations can be applied with or without f5-declarative-onboarding being enabled.

### userdata usage ###

```
#cloud-config
tmos_configdrive_openstack:
  enabled: true
  rd_enabled: false
  configsync_interface: 1.1
  default_route_interface: 1.3
  dhcp_timeout: 120
  inject_routes: true
  icontrollx_trusted_sources: false
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
  phone_home_cli: "curl -i -X POST -H 'X-Auth-Token: gAAAAABc5UscwS1py5XfC3yPcyN8KcgD7hYtEZ2-xHw95o4YIh0j5IDjAu9qId3JgMOp9hnHwP42mYA7oPPP0yl-OQXvCaCS3OezKlO7MsS-ZCTJzuS3sSysIMHTA78fGsXbMgCQZCi5G-evLG9xUNrYp5d3blhMnpHR0dlHPz6VMacNkPhyrQI' -H 'Content-Type: application/json' -H 'Accept: application/json' http://192.168.0.121:8004/v1/d3779c949b57403bb7f703016e91a425/stacks/demo_waf/3dd6ce45-bb8c-400d-a48c-87ac9e46e60e/resources/wait_handle/signal"
```

In addition to the delcared elements, this module also supports `cloud-config` delcarations for `ssh_authorized_keys`. Any declared keys will be authorized for the TMOS root account.

```
#cloud-config
ssh_authorized_keys:
  - ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEA3FSyQwBI6Z+nCSjUUk8EEAnnkhXlukKoUPND/RRClWz2s5TCzIkd3Ou5+Cyz71X0XmazM3l5WgeErvtIwQMyT1KjNoMhoJMrJnWqQPOt5Q8zWd9qG7PBl9+eiH5qV7NZ mykey@host
```

## The tmos_dhcpv4_tmm Cloudinit Module ##

This cloudinit module resolves configuration data for all interfaces (management and TMM) through DHCPv4. All interfaces should be connected to networks with DHCPv4 services. This modules support both 1NIC and nNIC deployments.

There are implicit declarations of the TMM intefaces names to use for the data plane default route and the configuration sychronization interfaces. If these declarations are omitted, the module will attempt to assign them dynamically based on available network configuration data.

This modules create initialization scripts containing TMOS `tmsh` commands to fulfill the specified configurations. The generated initialization scripts are created in the `/opt/cloud/tmos_dhcpv4_tmm` directory on the device.

This cloudinit module optionally composes f5-declarative-onboarding declarations in the `/var/lib/cloud/f5-declarative-onboarding` directory. This declaration is in JSON format.

Any attributes in the `do_declaration` attriute of the cloudinit YAML will be merged into the f5-declarative-onboarding declaration composed from DHCPv4 lease information. Any declaration attribute defined in the cloudinit YAML will overwrite the same attribute, if present, in the composed declaration.

This cloudinit module optionally composes f5-appsvcs-extension declarations in the `/var/lib/cloud/f5-appsvcs-extension` directory. This declaration is in JSON format.

| Module Attribute | Default | Description|
| --------------------- | -----------| ---------------|
| enabled              | false      | Activates ths module|
| rd_enabled         | true        | Automatically create route domains when needed |
| configsync_interface | 1.1 | Sets the TMM interface name to use for configsync |
| default_route_interface | none | Explicitly define the TMM interface to use for the default route. Otherwise one will be determined automatically |
| dhcp_timeout | 120 | Seconds to wait for a DHCP response when using DHCP for resource discovery |
| inject_routes | true | Creates static routes from discovered route resources |
| icontrollx_trusted_sources | true | Only install iControl LX RPMs which are signed by TMOS trusted keys |
| icontrollx_package_urls | none | List of URLs to download and install iControl LX extension packages before onboarding |
| do_enable | true | Enables attempt to create a f5-declarative-onboarding declaration from discovered resources. If enabled, an asynchronous attempt to declare resouces via f5-declarative-onboarding will be made. If the initial request fails, non-declarative onboarding will resumse |
| do_declaration | none |  YAML formatted f5-declarative-onboarding declaration. This declaration will augment or overwrite the declaration created by resource discovery |
| as3_enabled | true | Enables attempt to declare an application services configuration with f5-appsvcs-extension|
| as3_declaration | none | The f5-appsvcs-extension declaration to declare if enabled |
| post_onboard_enabled | false | Enabled the attempt to run a list of commands after onboarding completes |
| post_onboard_commands | list | List of CLI commands to run in order. Execution will halt at the point a CLI command fails. |
| phone_home_url | url | Reachable URL to report completion of this modules onboarding. |
| phone_home_url_verify_tls | true | If the phone_home_url uses TLS, verify the host certificate. |
| phone_home_cli | cli command | CLI command to run when this modules completes successfully. |

#### Warning: f5-declarative-onboarding and f5-appsvcs-extension do not support the use of route domains at this time. You should disable route domain support when attempting to use f5-declarative-onboarding and f5-appsvcs-extension declarations 

If f5-declarative-onboarding is disbaled, done by setting `do_eabled` to false, the device onboarding configuration will contine as described in the OpenStack meta_data.json and network_data.json files. f5-appsvcs-extension declarations can be applied with or without f5-declarative-onboarding being enabled.

### userdata usage ###

```
#cloud-config
tmos_dhcpv4_tmm:
  enabled: true
  rd_enabled: false
  configsync_interface: 1.1
  default_route_interface: 1.3
  dhcp_timeout: 120
  inject_routes: true
  icontrollx_trusted_sources: false
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
  phone_home_cli: "curl -i -X POST -H 'X-Auth-Token: gAAAAABc5UscwS1py5XfC3yPcyN8KcgD7hYtEZ2-xHw95o4YIh0j5IDjAu9qId3JgMOp9hnHwP42mYA7oPPP0yl-OQXvCaCS3OezKlO7MsS-ZCTJzuS3sSysIMHTA78fGsXbMgCQZCi5G-evLG9xUNrYp5d3blhMnpHR0dlHPz6VMacNkPhyrQI' -H 'Content-Type: application/json' -H 'Accept: application/json' http://192.168.0.121:8004/v1/d3779c949b57403bb7f703016e91a425/stacks/demo_waf/3dd6ce45-bb8c-400d-a48c-87ac9e46e60e/resources/wait_handle/signal"
```

In addition to the delcared elements, this module also supports `cloud-config` delcarations for `ssh_authorized_keys`. Any declared keys will be authorized for the TMOS root account.

```
#cloud-config
ssh_authorized_keys:
  - ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEA3FSyQwBI6Z+nCSjUUk8EEAnnkhXlukKoUPND/RRClWz2s5TCzIkd3Ou5+Cyz71X0XmazM3l5WgeErvtIwQMyT1KjNoMhoJMrJnWqQPOt5Q8zWd9qG7PBl9+eiH5qV7NZ mykey@host
```

# TMOS Cloudinit Modules Support for SSH Keys and Passwords #

In addition to the delcared elements, these modules also supports `cloud-config` delcarations for `ssh_authorized_keys` using the standard cloudinit `cloud-config` declaration syntax. Any declared keys will be authorized for the TMOS root account.

### additional userdata ###

```
#cloud-config
ssh_authorized_keys:
  - ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEA3FSyQwBI6Z+nCSjUUk8EEAnnkhXlukKoUPND/RRClWz2s5TCzIkd3Ou5+Cyz71X0XmazM3l5WgeErvtIwQMyT1KjNoMhoJMrJnWqQPOt5Q8zWd9qG7PBl9+eiH5qV7NZ mykey@host
```

### Support Cloudinit set-password ###

The patched VE image cloudinit configurations template has been alterred to support the standard cloudinit `set_password` module as well. You can cahnge the built-in TMOS `admin` and  `root` passwords using the following cloudinit `cloud-config` declarations.


```
#cloud-config
chpasswd:
  list: |
    root:f5str0ngPa$$word
    admin:f5str0ngPa$$word
  expire: False
```


