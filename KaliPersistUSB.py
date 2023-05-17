Kali USB persistence

import os
import glob
import time
import pyudev

# set the name of the Kali Linux ISO file
iso_file = "kali-linux-2023.1-amd64.iso"

# get the first connected USB device
context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by('block')
print("Waiting for a USB drive to be connected...")
for device in iter(monitor.poll, None):
    if 'ID_BUS' in device and device['ID_BUS'] == 'usb':
        usb_device = "/dev/{}".format(device.sys_name)
        print("USB drive {} connected!".format(device.sys_name))
        break

# calculate the size of the Persistence partition
partition_size = int(os.popen("sudo fdisk -l {} | grep Disk | awk '{{print $5}}'".format(usb_device)).read().strip()) // 1024 // 1024 // 1024
persistence_size = partition_size - 4 if partition_size > 4 else partition_size

# create the bootable USB drive
print("Creating a bootable USB drive...")
os.system("sudo dd if={} of={} bs=4M status=progress".format(iso_file, usb_device))

# identify the device name of the USB drive
time.sleep(5)
device_name = glob.glob("/dev/{}*".format(device.sys_name))[0]

# create a new partition on the USB drive
print("Creating a new partition on the USB drive...")
os.system("echo -e 'n\np\n2\n\n+{}G\nw' | sudo fdisk {}".format(persistence_size, device_name))

# format the new partition as ext4
print("Formatting the new partition as ext4...")
os.system("sudo mkfs.ext4 {}2".format(device_name))

# mount the new partition
print("Mounting the new partition...")
os.system("sudo mkdir -p /mnt/my_usb")
os.system("sudo mount {}2 /mnt/my_usb".format(device_name))

# run the Kali Linux installer in Live mode with Persistence
print("Running the Kali Linux installer...")
os.system("sudo /mnt/my_usb/live-installer/installer.sh")

# reboot the computer and select the Persistent boot option
print("Rebooting the computer and selecting the Persistent boot option...")
os.system("sudo reboot")
