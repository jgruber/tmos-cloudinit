#!/bin/bash

wd=$(pwd)

system_pyton_path_files="${wd}/image_patch_files/system_python_path"
icontrollx_rpm_injection_path="/data/iControlLXLatestBuild"
template_path="${wd}/image_patch_files/usr/share/defaults/config/templates"

os_rc_file="/data/F5Download/admin-openrc.sh"


function init() {
    modprobe nbd max_part=8
    qemu-nbd -d /dev/nbd0 > /dev/null 2>&1
    qemu-nbd -d /dev/nbd0 > /dev/null 2>&1
    sleep 2
    pvscan_out=$(pvscan|grep 'No matching'|wc -l)
    if [ $pvscan_out -ne "1" ]; then
        echo "volumes still attached from last image build.. please fix"
	    exit 1
    fi
}


function cp_src_to_dst() {
    cp $1 $2
    if [ $? -ne 0 ]; then
        echo "could not copy $1 to $2"
	    exit 1
    fi
}


function clean_up_volumes() {
    vgchange -an > /dev/null 2>&1
    sleep 2
    qemu-nbd -d /dev/nbd0 > /dev/null 2>&1
    qemu-nbd -d /dev/nbd0 > /dev/null 2>&1
    qemu-nbd -d /dev/nbd0 > /dev/null 2>&1
    qemu-nbd -d /dev/nbd0 > /dev/null 2>&1
    sleep 2
    pvscan_out=$(pvscan|grep 'No matching'|wc -l)
    if [ $pvscan_out -ne "1" ]; then
        echo "disk did not detach properly... please fix"
        exit 1
    fi
}


function mount_dst_image_file() {
    qemu-nbd -c /dev/nbd0 $1
    if [ $? -eq 0 ]; then
        sleep 2
        pvscan > /dev/null 2>&1
        if [ $? -eq 0 ]; then
	    vgchange -ay > /dev/null 2>&1
	    sleep 2
        else
	    echo "scan for volumes was not successful"
	    clean_up_volumes
        fi
	    sleep 2
    else
        echo "could not mount image as a block device"
        exit 1
    fi
}


function clean_up_volumes() {
    vgchange -an > /dev/null 2>&1
    sleep 2
    qemu-nbd -d /dev/nbd0 > /dev/null 2>&1
    qemu-nbd -d /dev/nbd0 > /dev/null 2>&1
    sleep 2
    qemu-nbd -d /dev/nbd0 > /dev/null 2>&1
    qemu-nbd -d /dev/nbd0 > /dev/null 2>&1
    pvscan_out=$(pvscan|grep 'No matching'|wc -l)
    if [ $pvscan_out -ne "1" ]; then
        echo "disk did not detach properly... please fix"
        exit 1
    fi
}


function validate_volume_group() {
    vg_dev=$(ls -d /dev/vg-db*|head -n 1| tr -d '\n')
    vol_found=$(ls ${vg_dev}/set.1._usr | wc -l)
    if [ $vol_found -ne "1" ]; then
        echo "mounted disk is not a TMOS VE image"
	clean_up_volumes
    fi
}


function cp_cloudinit_parts() {
    mount_point='/tmp/bigip_usr'
    mkdir -p $mount_point
    vg_dev=$(ls -d /dev/vg-db*|head -n 1| tr -d '\n')
    mount $vg_dev/set.1._usr $mount_point
    if [ -d $mount_point/lib/python2.7 ]; then
        echo "injecting python modules into python 2.7 system path"
        cp --recursive $system_pyton_path_files/* $mount_point/lib/python2.7/
    fi
    if [ -d $mount_point/lib/python2.6 ]; then
        echo "injecting python modules into python 2.6 system path"
        cp --recursive $system_pyton_path_files/* $mount_point/lib/python2.6/
    fi
    echo "injecting cloud-init.tmpl"
    cp $template_path/cloud-init.tmpl $mount_point/share/defaults/config/templates/cloud-init.tmpl
    umount $mount_point
}


function cp_icontrollx_rpms() {
    mount_point='/tmp/bigip_config'
    mkdir -p $mount_point
    vg_dev=$(ls -d /dev/vg-db*|head -n 1| tr -d '\n')
    mount "${vg_dev}"/set.1._config $mount_point
    mkdir -p $mount_point/icontrollx_installs
    for rpm_file in $icontrollx_rpm_injection_path/*.rpm; do
	echo "injecting $rpm_file"
        cp $rpm_file $mount_point/icontrollx_installs/
    done
    umount $mount_point
}


function upload_image_to_glance() {
    source $os_rc_file
    image_name=$(echo $1 | awk 'BEGIN{FS=OFS="."} NF--')
    image_ext=$(echo $1 | awk -F . '{print $NF}')
    openstack image delete $image_name > /dev/null 2>&1
    openstack image create --disk-format $image_ext --container-format bare --file $1 $image_name
}


function rm_dst_image_file() {
    rm -rf $1
    if [ $? -ne 0 ]; then
        echo "could not remove patched image file $1"
    fi
}


function main() {
    src_image_file=$1
    dst_image_file="OpenStack_"$(basename $1)
    echo "initializing imaging patching"
    init
    if [ $? -ne 0 ]; then exit 1; fi
    echo "copying $src_image_file as base image for $dst_image_file"
    cp_src_to_dst $src_image_file $dst_image_file
    if [ $? -ne 0 ]; then exit 1; fi
    echo "mounting $dst_image_file base image"
    mount_dst_image_file $dst_image_file
    if [ $? -ne 0 ]; then exit 1; fi
    echo "finding TMOS volume groups within base image"
    validate_volume_group
    if [ $? -ne 0 ]; then exit 1; fi
    echo "patching cloud-init resources"
    cp_cloudinit_parts
    echo "inserting iControl LX install packages"
    cp_icontrollx_rpms
    echo "closing patched volumes" 
    clean_up_volumes
    if [ $? -ne 0 ]; then exit 1; fi
    echo "uploading patched $dst_image_file to OpenStack"
    upload_image_to_glance $dst_image_file
    echo "removing patched image file from local disk"
    rm_dst_image_file $dst_image_file
}


main "$@"
