#!/bin/bash
source /data/F5Download/admin-openrc.sh
iControlLXPackagesDir=/data/iControlLXNoBuilds
imagesDir=/data/F5Download/BIGIP-TEST
version=14.1.0.5-0.0.5
external_network_name=public
management_network_name=management
cluster_network_name=HA
internal_network_name=internal
vip_network_name=external
ltm_1slot_flavor=LTM.1SLOT
all_1slot_flavor=ALL.1SLOT
phone_home_url_view='https://webhook.site/#!/5a5310ff-648d-4dfc-97e3-6bbe9d88d111/9c8aeb41-0440-47da-b94e-75b2052aa6a2/1'
phone_home_url='https://webhook.site/5a5310ff-648d-4dfc-97e3-6bbe9d88d111'
openstack flavor list | grep LTM.1SLOT | cut -d' ' -f2

echo "docker run --rm -it -v ${imagesDir}:/TMOSImages -v ${iControlLXPackagesDir}:/iControlLXPackages tmos_image_patcher:latest"
docker run --rm -it -v "${imagesDir}":/TMOSImages -v "${iControlLXPackagesDir}":/iControlLXPackages tmos_image_patcher:latest

openstack image delete OpenStack_BIGIP-${version}.ALL_1SLOT.qcow2
openstack image create --container-format bare --disk-format qcow2 --file $imagesDir/BIGIP-${version}.ALL_1SLOT.qcow2/BIGIP-${version}.qcow2  OpenStack_BIGIP-${version}.ALL_1SLOT.qcow2
openstack image delete OpenStack_BIGIP-${version}.LTM_1SLOT.qcow2
openstack image create --container-format bare --disk-format qcow2 --file $imagesDir/BIGIP-${version}.LTM_1SLOT.qcow2/BIGIP-${version}.qcow2  OpenStack_BIGIP-${version}.LTM_1SLOT.qcow2

allimage=$(openstack image list | grep OpenStack_BIGIP-${version}.ALL_1SLOT.qcow2 | cut -d' ' -f2)
echo "ALL image is: ${allimage}"
ltmimage=$(openstack image list | grep OpenStack_BIGIP-${version}.LTM_1SLOT.qcow2 | cut -d' ' -f2)
echo "LTM image is: ${ltmimage}"
rtdir=$(pwd)
scriptdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${scriptdir}/demo/openstack/heat/
sed -i "/ tmos_image/c\  tmos_image: ${ltmimage}" *do_only_env.yaml
sed -i "/ tmos_image/c\  tmos_image: ${allimage}" *waf_env.yaml

os_networks=$(openstack network list)
external_network=$(echo "${os_networks}" | grep ${external_network_name} | cut -d' ' -f2)
management_network=$(echo "${os_networks}" | grep ${management_network_name} | cut -d' ' -f2)
cluster_network=$(echo "${os_networks}" | grep ${cluster_network_name} | cut -d' ' -f2)
internal_network=$(echo "${os_networks}" | grep ${internal_network_name} | cut -d' ' -f2)
vip_network=$(echo "${os_networks}" | grep ${vip_network_name} | cut -d' ' -f2)
vip_subnet_line=$(echo "${os_networks}" | grep ${vip_network_name})
vip_subnet=$(echo ${vip_subnet_line} | cut -d' ' -f6)


sed -i "/ external_network/c\  external_network: ${external_network}" *_env.yaml
sed -i "/ management_network/c\  management_network: ${management_network}" *_env.yaml
sed -i "/ cluster_network/c\  cluster_network: ${cluster_network}" *_env.yaml
sed -i "/ internal_network/c\  internal_network: ${internal_network}" *_env.yaml
sed -i "/ vip_network/c\  vip_network: ${vip_network}" *_env.yaml
sed -i "/ vip_subnet/c\  vip_subnet: ${vip_subnet}" *_env.yaml

ltm_1slot_flavor_id=$(openstack flavor list | grep ${ltm_1slot_flavor} | cut -d' ' -f2)
all_1slot_flavor_id=$(openstack flavor list | grep ${all_1slot_flavor} | cut -d' ' -f2)

sed -i "/ tmos_flavor/c\  tmos_flavor: ${ltm_1slot_flavor_id}" *do_only_env.yaml
sed -i "/ tmos_flavor/c\  tmos_flavor: ${all_1slot_flavor_id}" *waf_env.yaml

sed -i "/ monitor at/c\  # monitor at: ${phone_home_url_view}" *_env.yaml
sed -i "/ phone_home_url/c\  phone_home_url: ${phone_home_url}" *_env.yaml

cd ${rtdir}
