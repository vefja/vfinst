import os
import sys


# Check for root
if os.geteuid() != 0:
    exit("You must run chemical as root!")

# Check for internet
if os.system("ping archlinux.org -c 1") != 0:
    exit("You must be connected to the internet to use chemical.")

if os.path.isdir("/sys/firmware/efi/efivars/") is True:
    efi = True
else:
    efi = False

if sys.argv[1:]:
    if sys.argv[1] == "atomic":
        atomic = True
else:
    atomic = False

def install():
    os.system("pacman -Sy git wget curl --noconfirm")
    os.system("clear")
    print("Welcome to Nitrogen Installer!")
    print()
    print("Partition Disks")
    print("Which disk would you like to use?")
    os.system("lsblk -d")
    disk = input("/dev/")
    os.system("cfdisk /dev/" + disk)

    os.system("clear")

    if atomic is False:
        print("Chemical 1.0")
    else:
        print("Chemical 1.0(Atomic install)")

    def im_sure_the_partitions_are_right():
        os.system("lsblk /dev/" + disk)
        print("Are you sure the partitions are correctly created?")
        sure = input("Y/n ")
        if sure in ["y", "Y", "yes", "yeah"]:
            pass
        elif sure in ["n", "N", "no", "nope"]:
            im_sure_the_partitions_are_right()
        else:
            print(sure + ": Command not understood")
            im_sure_the_partitions_are_right()
    im_sure_the_partitions_are_right()

    print("Formatting partitions")
    print("Select root partition")
    root = input("/dev/" + disk)
    print("Select swap(empty for none)")
    swap = input("/dev/" + disk)

    if efi is True:
        print("Select EFI Partition")
        efi_part = input("/dev/" + disk)

    print("Are you sure you want to continue? Continuing will remove every file from the selected partitions.")
    removal_prompt = input("Y/n ")

    if removal_prompt == "n":
        sys.exit(1)
    else:
        pass

    os.system("mkfs.btrfs -f /dev/" + disk + root)

    if len(swap) != 0:
        os.system("mkswap /dev/" + disk + swap)

    if efi is True:
        os.system("mkfs.vfat -F32 /dev/" + disk + efi_part)

    print("Mounting file systems")
    os.system("mount /dev/" + disk + root + " /mnt")
    os.system("swapon -a")
    if efi is True: 
        os.system("mkdir /mnt/boot/efi")
        os.system("mount /dev/" + disk + efi_part + " /mnt/boot/efi")
        print("/dev/" + disk + efi_part)

    print("Installing Nitrogen Base")
    os.system("pacstrap /mnt base linux-lts linux-firmware base-devel sof-firmware python btrfs-progs")
    os.system("genfstab -U /mnt >> /mnt/etc/fstab")
    print("Configuring Nitrogen")
    print("Select Region")
    region_right = False
    city_right = False
    os.system("ls /mnt/usr/share/zoneinfo/")
    while region_right is False:
        region = input("Region: ")
        if os.system("ls /mnt/usr/share/zoneinfo/" + region + " > /dev/null") == 0:
            region_right = True
        else:
            pass

    print("Select City")
    os.system("ls /mnt/usr/share/zoneinfo/" + region)
    while city_right is False:
        city = input("City: ")
        if os.system("ls /mnt/usr/share/zoneinfo/" + region + "/" + city + " > /dev/null") == 0:
            city_right = True
        else:
            pass

    os.system("ln -s /mnt/usr/share/zoneinfo/" + region + "/" + city + " /mnt/etc/localtime")
    os.system("echo LANG=en_US.UTF-8 >> /mnt/etc/locale.conf")    
    os.system("echo 'en_US.UTF-8 UTF-8' >> /mnt/etc/locale.gen")
    os.system("arch-chroot /mnt/ locale-gen")
    os.system("arch-chroot /mnt/ hwclock --systohc")

    print("Select hostname(empty for default)")
    hostname = input("Hostname: ")
    if len(hostname) == 0:
        os.system("echo nitrogen > /mnt/etc/hostname")
    else:
        os.system("echo " + hostname + " > /mnt/etc/hostname")

    print("Password for root")
    correct_passwd = False
    while correct_passwd is False:
        c_passwd_answer = os.system("arch-chroot /mnt/ passwd root")
        if c_passwd_answer == 0:
            correct_passwd = True
            pass


    print("Creating a user")
    username = input("New user's name: ")
    os.system("arch-chroot /mnt/ useradd -m -G wheel " + username)
    os.system("arch-chroot /mnt/ passwd " + username)
    correct_passwd = False
    while correct_passwd is False:
        c_passwd_answer = os.system("arch-chroot /mnt/ passwd " + username)
        if c_passwd_answer == 0:
            correct_passwd = True
            pass

    os.system("pacstrap /mnt grub")

    print("Installing Boot Loader")
    if efi is True:
        # TODO: add efi grub installer
        os.system("pacstrap /mnt efibootmgr dosfstools os-prober mtools")
        os.system("mkdir /mnt/boot/efi")
        os.system("arch-chroot /mnt/ grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=Nitrogen")
    else:
        os.system("arch-chroot /mnt/ grub-install --target=i386-pc /dev/" + disk)
    os.system("arch-chroot /mnt/ grub-mkconfig -o /boot/grub/grub.cfg")
    
    print("Configuring Nitrogen pt 2")
    os.system("curl https://raw.githubusercontent.com/NitrogenLinux/chemical/main/os-release > /mnt/etc/os-release")
    os.system("curl https://raw.githubusercontent.com/NitrogenLinux/chemical/main/os-release > /mnt/usr/lib/os-release")

    print("Installing Elements")
    os.system("pacstrap /mnt wget")
    os.system("wget https://github.com/NitrogenLinux/elements/raw/stable/lmt")
    os.system("mv -v lmt /mnt/usr/bin")
    os.system("mkdir -p /mnt/etc/elements/repos/")
    os.system("git clone https://github.com/NitrogenLinux/elements-repo.git /mnt/etc/elements/repos/")
    os.system("wget https://github.com/tekq/elements-search/raw/main/search")
    os.system("wget https://github.com/tekq/elements-search/raw/main/search-repo")
    os.system("mv -v search* /mnt/etc/elements/")
    os.system("chmod a+x /usr/bin/lmt")
    os.system("chmod a+x /etc/elements/search*")

    if atomic is True:
        print("Will you be using iwd NetworkManager or wpa_supplicant?")
        print("1. iwd")
        print("2. NetworkManager")
        print("3. wpa_supplicant")
        network_supplier = int(input())
        if network_supplier == 1:
            os.system("pacstrap /mnt iwd")
            os.system("arch-chroot /mnt/ systemctl enable iwd")
        elif network_supplier == 2:
            os.system("pacstrap /mnt networkmanager")
            os.system("arch-chroot /mnt/ systemctl enable NetworkManager")
        elif network_supplier == 3:
            os.system("pacstrap /mnt wpa_supplicant wpa_cli")
            os.system("arch-chroot /mnt/ systemctl enable wpa_supplicant")

    else:
        print("Installing desktop environment")
        os.system("pacstrap /mnt networkmanager gnome gdm")
        os.system("arch-chroot /mnt/ systemctl enable gdm")
        os.system("arch-chroot /mnt/ systemctl enable NetworkManager")


    print("")
    print("")
    print("")

    print("Do you want to reboot?")
    reboot_y_n = input("Y/n")
    if reboot_y_n == "y":
        os.system("reboot")
    else:
        pass


# Run Installer
install()