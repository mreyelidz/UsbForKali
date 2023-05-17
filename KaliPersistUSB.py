import os
import glob
import time
import pyudev
import sys

def poll_usb():
    '''
    Polls for USB Device and returns device object
    '''
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context, "udev")
    monitor.filter_by(subsystem="block", device_type="disk")
    print("Waiting for a USB drive to be connected...")
    for device in iter(monitor.poll, None):
        if device.action == "add":
            if 'ID_BUS' in device and device['ID_BUS'] == 'usb':
                usb_device = "/dev/{}".format(device.sys_name)
                print("USB drive {} connected!".format(device.sys_name))
                return usb_device

def check_persistence(usb_device):
    '''
    Checks for persistence.conf file and determines if persistence is enabled
    '''
    if os.path.exists("{}/live/persistence.conf".format(usb_device)):
        with open("{}/live/persistence.conf".format(usb_device), "r") as f:
            content = f.read()
            if "/live/cow" in content:
                print("Found an existing usable Kali Linux installation with persistence on the USB drive.")
                time.sleep(5)
                device_name = glob.glob("/dev/{}*".format(os.path.basename(usb_device)))[0]
                return device_name
            else:
                print("Found an existing Kali Linux installation on the USB drive, but it does not support persistence.")

def download_kali():
    '''
    Downloads the Kali Linux ISO if it does not exist, returns the filename
    '''
    if len(glob.glob("*.iso")) > 0:
        iso_file = glob.glob("*.iso")[0]
        print(f"Skipping ISO download since {iso_file} exists.")
    else:
        print("Continuing with the ISO download.")
        os.system("sudo apt-get install -y curl")
        os.system("curl -L -O https://cdimage.kali.org/kali-2023.1/kali-linux-2023.1-live-amd64.iso")
        iso_file = "kali-linux-2023.1-live-amd64.iso"
    return iso_file

def create_persistent_partition(usb_device, persistence_size):
    '''
    Create ext4 partition for Kali Linux persistence 
    '''
    print("Creating a new partition on the USB drive...")
    os.system("echo -e 'n\np\n2\n\n+{}G\nw' | sudo fdisk {}".format(persistence_size, usb_device))

    print("Formatting the new partition as ext4...")
    os.system("sudo mkfs.ext4 {}2".format(usb_device))

def install_kali_usb(iso_file, device_name):
    '''
    Installs Kali Linux to the USB device
    '''
    print("Creating a bootable USB drive...")
    os.system(f"sudo dd if={iso_file} of={device_name} bs=4M status=progress")

    print("Mounting the new partition...")
    os.system("sudo mkdir -p /mnt/my_usb")
    os.system("sudo mount {}2 /mnt/my_usb".format(device_name))

    print("Running the Kali Linux installer...")
    os.system("sudo /mnt/my_usb/live-installer/installer.sh")

def restart_computer():
    '''
    Reboots computer and boots to Persistent Kali Linux on USB
    '''
    print("Rebooting the computer and selecting the Persistent boot option...")
    os.system("sudo reboot")

def main():
    usb_device = poll_usb()
    if usb_device:
        device_name = check_persistence(usb_device)
        if not device_name:
            iso_file = download_kali()
            partition_size = int(os.popen("sudo fdisk -l {} | grep Disk | awk '{{print $5}}'".format(usb_device)).read().strip()) // 1024 // 1024 // 1024
            persistence_size = partition_size - 4 if partition_size > 4 else partition_size
            create_persistent_partition(usb_device, persistence_size)
            device_name = f"{usb_device}2"
            install_kali_usb(iso_file, device_name)
            restart_computer()
    else:
        print("No USB devices found. Exiting.")
        sys.exit(1)

if __name__ == '__main__':
    main()
