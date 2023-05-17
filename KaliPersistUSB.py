import os
import glob
import time
import pyudev

context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by('block')
print("Waiting for a USB drive to be connected...")
for device in iter(monitor.poll, None):
    if 'ID_BUS' in device and device['ID_BUS'] == 'usb':
        usb_device = "/dev/{}".format(device.sys_name)
        print("USB drive {} connected!".format(device.sys_name))
        break

if os.path.exists("{}/live/persistence.conf".format(usb_device)):
    with open("{}/live/persistence.conf".format(usb_device), "r") as f:
        content = f.read()
        if "/live/cow" in content:
            print("Found an existing usable Kali Linux installation with persistence on the USB drive.")
            time.sleep(5)
            device_name = glob.glob("/dev/{}*".format(device.sys_name))[0]
            break
        else:
            print("Found an existing Kali Linux installation on the USB drive, but it does not support persistence.")

if 'iso_file' not in locals():
    iso_files = glob.glob("*.iso")
    if len(iso_files) == 0:
        print("No .iso files found in the current directory. Exiting.")
        sys.exit(1)
    iso_file = iso_files[0]

if 'device_name' in locals() or 'iso_file' in locals():
    if 'device_name' in locals():
        print("Skipping ISO download since a usable Kali Linux installation was found on the USB drive.")
    else:
        print("Continuing with the ISO download.")
        os.system("sudo apt-get install -y curl")
        os.system("curl -L -O https://cdimage.kali.org/kali-2021.3/kali-linux-2023.1-live-amd64.iso")
        iso_file = "kali-linux-2023.1-live-amd64.iso"

    partition_size = int(os.popen("sudo fdisk -l {} | grep Disk | awk '{{print $5}}'".format(usb_device)).read().strip()) // 1024 // 1024 // 1024
    persistence_size = partition_size - 4 if partition_size > 4 else partition_size

    print("Creating a bootable USB drive...")
    os.system("sudo dd if={} of={} bs=4M status=progress".format(iso_file, usb_device))

    time.sleep(5)
    device_name = glob.glob("/dev/{}*".format(device.sys_name))[0]

    print("Creating a new partition on the USB drive...")
    os.system("echo -e 'n\np\n2\n\n+{}G\nw' | sudo fdisk {}".format(persistence_size, device_name))

    print("Formatting the new partition as ext4...")
    os.system("sudo mkfs.ext4 {}2".format(device_name))

    print("Mounting the new partition...")
    os.system("sudo mkdir -p /mnt/my_usb")
    os.system("sudo mount {}2 /mnt/my_usb".format(device_name))

    print("Running the Kali Linux installer...")
    os.system("sudo /mnt/my_usb/live-installer/installer.sh")

    print("Rebooting the computer and selecting the Persistent boot option...")
    os.system("sudo reboot")
else:
    print("No usable Kali Linux installation or Kali Linux ISO file found.")
