# tmos-cloudinit
### OpenStack HEAT templates using f5-declarative-onboarding and f5-appsrvcs-extension ###

OpenStack HEAT represents a great way to lifecycle manage OpenStack resources. Where we get into trouble with HEAT is when we try to manage non-OpenStack resources, meaning resources not defined by the OpenStack community. HEAT is extensible and vendors can make their customer resources available to their customers, but they must be maintained through the changes between OpenStack releases. In addition, if testing of a vendor Heat resource functionality required non-open components, upstreaming into community really did not address any vendor plugin quality issues. Vendor supplied and installed Heat plugins quickly became frowned upon by customers.

F5 Automation Toolchain extensions are developed in two week sprints. Features are added and made available on a very rapid basis. To that end, the cloud-init modules in this repository support the dynamic installation and use of F5 Automation Toolchain extensions into your OpenStack instances. The declarative nature makes for a natural fit wih OpenStack HEAT.

In the past F5 published both vendor specific Heat resources and complex composed HEAT templates. These proved hard to customize and quickly fell behind OpenStack release testing. In an attempt to better serve our customers, and let them move at the pace they want, we changed philosphies and now support declarations made against the released Automation Toolchain extensions. This repository contains example HEAT templates which make those declarations through OpenStack compute userdata. These templates use only OpenStack community resources without any advanced composition. They are simple YAML which can be customized by any customer. What F5 stands behind is the declarations made by HEAT templates to the Automation Toolchain extensions. You get the ability to customize your infrastructure deployment lifecycles with Heat and simple YAML declarations which unlock all the enterprise and provider features of your F5 TMOS instances. You get the world class support of the TMOS instances you are used to because of the Automation Toolchain extensions. To add features, simply change the declarations made to the Automation Toolchain extensions in your Heat YAML templates.

These templates expect you to customize the `env` files, pre-populating them with OpenStack, image, flavor, and networking IDs, but you could choose to customize these templates to create all the resources they need access to. They also utilize F5 BIG-IQ pool based licensing, but a simply change to the f5-declarative-onboarding declaration can be migrate these templates to BYOL (bring your own license) REGKEY based activations. ( [see the f5-declarative-onboarding clouddocs](https://clouddocs.f5.com/products/extensions/f5-declarative-onboarding/latest/) )

This repository contains Heat environment and template YAML files for the following F5 cloudinit modules:

- `tmos_configdrive_openstack_*` which create the Automation Toolchain f5-declarative-onboarding declaration classes from the OpenStack instance metadata and network_data.json files present on a cloudinit ConfigDrive data source.
- `tmos_dhcpv4_tmm_*` which create the Automation Toolchain f5-declarative-onboarding declaration classes from DHCPv4 queries to all network ports associated with your OpenStack instance.
- `tmos_declared_*` which fully declare all Automation Toolchain classes explicitly without use of any OpenStack instance metadata.

Each set of templates come with `do_only` and `waf` examples. The `do_only` templates demonstrate Heat using only f5-declarative-onboarding declarations. The `waf` examples demonstrate Heat using both f5-declarative-onboarding and f5-appsvcs-extension declarations to fully define a WAF network function. These example templates can be customized to provide any network function capabale with the Automation Toolchain extensions.

## f5-declarative-onboarding only templates ###

The templates marked `do_only` only make f5-declarative-onboarding declarations through the F5 cloudinit modules. What you can do with f5-declarative-onboarding is defined here:

[f5-declarative-onboarding cloud docs](https://clouddocs.f5.com/products/extensions/f5-declarative-onboarding/latest/)

f5-declarative-onboarding supports defining TMOS network interfaces, licensing, clustering, and much more.

To use one of the example templates, customize the `env` file associated with a template and launch an OpenStack HEAT stack.

As an example, let's consider a 4 network interface BIG-IP which will learn its networking provisioning data from the OpenStack `network_data.json` metadata file. That means we will use the `tmos_configdrive_openstack` cloudinit module.

The assoiciated `env` file would be `tmos_configdrive_openstack_4_nic_do_only.env.yaml`. The contents of that HEAT YAML env file look like this:

```
parameters:
  tmos_image: 20f68ec9-e5ee-44a8-9091-e2b62b8e7452 <- BIG-IP LTM-1SLOT image patch with the tmos_configdive_openstack cloudinit module 
  tmos_flavor: 61b6b513-4a74-4d8d-8365-a7b712b40aa0 <- Flavor defined for BIG-IP LTM-1SLOT
  tmos_root_password: f5c0nfig
  tmos_admin_password: f5c0nfig
  license_host: 192.168.245.114 <- BIG-IQ licensing host
  license_username: admin
  license_password: admin
  license_pool: BIGIPVEREGKEYS <- BIG-IQ license pool 
  # monitor at: https://webhook.site/#!/7af00208-313d-42e9-b0f9-d0e88d631989/2a06b288-fd01-4f1c-a33e-097ef81712cb/1
  phone_home_url: https://webhook.site/7af00208-313d-42e9-b0f9-d0e88d631989 <- What URL to call when all your declarations have been made
  external_network: 9c74eb83-ae4d-4b51-82fa-df0084cc8f6b <- network to create a Floating IP to your management interface
  management_network: d0a2306c-31bb-46ef-8abf-6b622639c01a <- managment interface network
  cluster_network: e185645b-7fbd-4b2b-9ea1-a551fed55cb6 <- network for config-sync and failover heartbeats
  internal_network: 8b1cf4ca-012d-4164-ae7d-68e2670caf7a <- internal servers network 
  vip_network: 5eaa04e7-efe1-47e9-a6a4-dad7e5465f32 <- client access network
  vip_subnet: 55ff861a-1dbf-45b4-b7b8-31006f1f9f20 <- subnet to get a fixed IP for your virtual service address
  heat_timeout: 1800
```

This environment can be used with the following templates:

`tmos_configdrive_openstack_4_nic_do_only.template.yaml` <- standalone BIG-IP
`tmos_configdrive_openstack_4_nic_do_only_active_standby.template.yaml` <- HA cluster of 2 BIG-IPs

Once you have the correct resource IDs populated in the `env` file, you launch the template using the OpenStack HEAT client.

```
opensack heat create BIGIPHACluster01 \
   -e tmos_configdrive_openstack_4_nic_do_only.env.yaml \
   -t tmos_configdrive_openstack_4_nic_do_only_active_standby.template.yaml
```

From the template file you can see how easy it is to make an F5 Automation Toolchain declaration in OpenStack HEAT. The F5 Automation Toolchain declaration is simply embedded YAML issued as part of your OpenStack compute instance userdata.

```
adc_instance:
    type: OS::Nova::Server
    depends_on: [tmos_mgmt_port, tmos_cluster_port, tmos_internal_port, tmos_vip_port]
    properties:
      image: { get_param: tmos_image }
      flavor: { get_param: tmos_flavor }
      config_drive: true
      key_name: admin
      networks:
        - port: { get_resource: tmos_mgmt_port }
        - port: { get_resource: tmos_cluster_port }
        - port: { get_resource: tmos_internal_port }
        - port: { get_resource: tmos_vip_port }
      user_data_format: RAW
      user_data:
        str_replace:
          params:
            __root_password__: { get_param: tmos_root_password }
            __admin_password__: { get_param: tmos_admin_password }
            __bigiq_host__: { get_param: license_host }
            __bigiq_username__: { get_param: license_username }
            __bigiq_password__: { get_param: license_password }
            __license_pool__: { get_param: license_pool }
            __phone_home_url__: { get_param: phone_home_url }
            __wc_notify__: { get_attr: ['wait_handle', 'curl_cli'] }
          template: |
            #cloud-config
            chpasswd:
              expire: false
              list: |
                root:__root_password__
                admin:__admin_password__
            tmos_configdrive_openstack:
              enabled: true
              rd_enabled: false
              configsync_interface: 1.1
              default_route_interface: 1.3
              inject_routes: true
              do_enabled: true
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
                  poolLicense:
                    class: License
                    licenseType: licensePool
                    bigIqHost: __bigiq_host__
                    bigIqUsername: __bigiq_username__
                    bigIqPassword: __bigiq_password__
                    licensePool: __license_pool__
                    reachable: true
                    bigIpUsername: admin
                    bigIpPassword: __admin_password__
                  dbvars:
                    class: DbVariables
                    ui.advisory.enabled: true
                    ui.advisory.color: orange
                    ui.advisory.text: This device is under centralized management.
              as3_enabled: false
              phone_home_url: "__phone_home_url__"
              phone_home_cli: "__wc_notify__"
              post_onboard_enabled: false
```

## f5-declarative-onboarding and f5-appsvcs-extension declaration templates ###

While f5-declarative-onboarding sets up the TMOS instance to match your infrastructure, f5-appsvcs-extension provides a declarative way to define TMOS virtual servies. 

What you can do with f5-declarative-onboarding is defined here:

[f5-appsvcs-extension cloud docs](https://clouddocs.f5.com/products/extensions/f5-appsvcs-extension/latest/)

You can not only declare the services, you can declaratively alter the services as operational conditions change. With f5-appsvcs-extension, you can onboard a catalog of advanced services and modify them through a simple declarative REST API. Once you have your infrastructure defined and managed by HEAT, your CI/CD interaction moves to the purpose designed f5-appsvcs-extension REST schema to operationalize your TMOS devices throughout your cloud.

As an example of using the tmos_configdrive_openstack cloudinit module to declare both f5-declarative-onboarding and f5-appsvcs-extension, there are example templates which provision either standalone or HA cluster WAF (web application firewall) network functions ( the block in NFV) out of TMOS deviecs.



