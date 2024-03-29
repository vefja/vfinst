#!/sbin/python3
import os
import sys

# Check for root
if os.geteuid() != 0:
    sys.exit("You must run chemical as root!")

# Check for internet
if os.system("ping -c1 voidlinux.org") != 0:
    sys.exit("You must be connected to the internet to use chemical.")

efi = os.path.isdir("/sys/firmware/efi/efivars/") is True

if sys.argv[1:]:
    if sys.argv[1] == "atomic":
        atomic = True
else:
    atomic = False


def install():
    os.system("xbps-install -Sy git wget curl")
    os.system("clear")

    if atomic is False:
        print("Chemical 0.9")
    else:
        print("Chemical 0.9(Atomic install)")

    print()
    print("Partition Disks")
    print("Which disk would you like to use?")
    os.system("lsblk -d")
    disk = input("/dev/")

    while os.system("ls /dev/" + disk + " >> /dev/null") != 0:
        print("That doesn't seem right, try again")
        disk = input("/dev/")

    os.system("cfdisk /dev/" + disk)

    os.system("clear")

    def confirm_partitions():
        os.system("lsblk /dev/" + disk)
        print("Are you sure the partitions are correctly created?")
        sure = input("Y/n ")
        if sure in ["y", "Y", "yes", "yeah"]:
            pass
        elif sure in ["n", "N", "no", "nope"]:
            os.system("cfdisk /dev/" + disk)
            confirm_partitions()
        else:
            print(sure + ": Command not understood")
            confirm_partitions()

    confirm_partitions()

    print("Formatting partitions")
    print("Select root partition")
    root = input("/dev/" + disk)
    if len(root) < 1:
        while len(str(root)) < 1:
            print("That doesn't seem right, try again")
            root = input("/dev/" + disk)
    else:
        while os.system("blkid /dev/" + disk + root + " >> /dev/null") != 0:
            print("That doesn't seem right, try again")
            os.system("lsblk /dev/" + disk)
            root = input("/dev/" + disk)
        while os.system("ls /dev/" + disk + root + " >> /dev/null") != 0:
            print("That doesn't seem right, try again")
            os.system("lsblk /dev/" + disk)
            root = input("/dev/" + disk)

    print("Swap partition?", end=" ")
    swap_existence = str(input("Y/n "))
    if swap_existence in ["y", "Y"]:
        print("Select swap partition: ", end=" ")
        swap = input("/dev/" + disk)
    else:
        swap = ""

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
        os.system("mkdir /mnt/boot/EFI -p")
        os.system("mount /dev/" + disk + efi_part + " /mnt/boot/EFI")

    print("Installing Nitrogen Base")
    os.system(
        "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt base-system grub os-prober nano btrfs-progs void-repo-nonfree")
    os.system("for dir in dev proc sys run; do mount --rbind /$dir /mnt/$dir; mount --make-rslave /mnt/$dir; done")
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
    os.system('echo "LANG=en_US.UTF-8" > /mnt/etc/locale.conf')
    os.system('echo "en_US.UTF-8 UTF-8" >> /mnt/etc/default/libc-locales')
    os.system("chroot /mnt xbps-reconfigure -f glibc-locales")

    print("Select hostname(empty for default)")
    hostname = input("Hostname: ")
    if len(hostname) == 0:
        os.system("echo Nitrogen > /mnt/etc/hostname")
    else:
        os.system("echo " + hostname + " > /mnt/etc/hostname")

    print("Password for root")
    correct_passwd = False
    while correct_passwd is False:
        c_passwd_answer = os.system("chroot /mnt/ passwd root")
        if c_passwd_answer == 0:
            correct_passwd = True

    print("Creating a user")
    os.system("chroot /mnt groupadd sudo")
    username = input("New user's name: ")
    os.system("chroot /mnt/ useradd -m -G sudo,users " + username)
    correct_passwd = False
    while correct_passwd is False:
        if os.system("chroot /mnt/ passwd " + username) == 0:
            correct_passwd = True

    print("Installing drivers")
    print("Which GPU are you using?")
    print("1. NVIDIA")
    print("2. AMD")
    print("3. Intel")
    print("4. None/VM")

    gpu = int(input("GPU Manufacturer: "))
    if gpu == 1:
        print("GPU Model(only number; ex: 2060, 2080, 1650)", end=": ")
        nvidia_model = int(input())
        if nvidia_model >= 800:
            os.system(
                "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt nvidia nvidia-libs-32bit")
        elif nvidia_model == 700:
            os.system(
                "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt nvidia470 nvidia470-libs-32bit")
        elif nvidia_model == 600:
            os.system(
                "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt nvidia470 nvidia470-libs-32bit")
        elif nvidia_model <= 500:
            os.system(
                "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt nvidia390 nvidia470-libs-32bit")

    elif gpu == 2:
        os.system(
            "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt mesa-dri vulkan-loader mesa-vulkan-radeon amdvlk")
    elif gpu == 3:
        os.system(
            "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt mesa-dri linux-firmware-intel mesa-vulkan-intel vulkan-loader")
    elif gpu == 4:
        pass

    # TODO: add laptop software
    print("Would you like to install Laptop-specific packages?")
    laptop = input("Y/n ")
    if str(laptop) in ["y", "Y"]:
        os.system(
            "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt tlp powertop")
        os.system("chroot /mnt/ ln -sv /etc/sv/tlp /var/service")
    else:
        pass

    print("Installing and Configuring Boot Loader")
    if efi is True:
        os.system("chroot /mnt/ grub-install --target=x86_64-efi --bootloader-id=Nitrogen")  # GRUB UEFI Installation
    else:
        print("Installing Grub")
        os.system("chroot /mnt/ grub-install --target=i386-pc /dev/" + disk)  # Grub BIOS installation

    os.system("chroot /mnt/ grub-mkconfig -o /boot/grub/grub.cfg")  # Generate grub.cfg
    os.system("chroot /mnt/ xbps-reconfigure -fa")  # configure everything

    print("Tweaking Nitrogen")  # Configure system
    os.system(
        "curl https://raw.githubusercontent.com/NitrogenLinux/chemical/main/os-release > /mnt/etc/os-release")  # Replace Void's os-release with Nitrogen's
    os.system(
        "curl https://raw.githubusercontent.com/NitrogenLinux/chemical/main/os-release > /mnt/usr/lib/os-release")  # Replace Void's os-release with Nitrogen's
    os.system(
        "curl https://raw.githubusercontent.com/NitrogenLinux/chemical/main/lsb_release > /mnt/usr/bin/lsb_release")  # Replace Void's lsb_release with Nitrogen's

    print("Installing Elements")  # Install elements
    os.system(
        "xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt wget git curl snapper >> /dev/null")  # Install wget, git, python, python-pip
    os.system(
        "curl -s https://api.github.com/repos/NitrogenLinux/Elements/releases/latest | grep 'browser_download_url.*lmt' | cut -d : -f 2,3 | tr -d \" | wget -qi -")  # Download Elements
    os.system("mv -v lmt /mnt/usr/bin/lmt")  # Move Elements to /usr/bin
    os.system("mkdir -p /mnt/etc/elements/repos/")  # Create elements repo directory
    os.system("mkdir -pv /mnt/etc/elements/tools/ /mnt/etc/elements/.sys_files") # Create elements secret folder :p
    os.system("curl https://raw.githubusercontent.com/NitrogenLinux/elements/main/tools/find_opt.sh > /mnt/etc/elements/tools/find_opt.sh")
    os.system("chmod 755 /mnt/etc/elements/tools")
    os.system("touch /mnt/etc/elements/.sys_files/.pkg.db")
    os.system("curl https://raw.githubusercontent.com/NitrogenLinux/elements/main/lmt.conf > /mnt/etc/elements/lmt.conf")
    os.system(
        "git clone https://github.com/NitrogenLinux/elements-repo.git /mnt/etc/elements/repos/nitrogen")  # Clone elements repo
    os.system(
        "git clone https://github.com/NitrogenLinux/elements-repo.git /mnt/etc/elements/repos/.old_nitrogen")  # Clone elements repo
    os.system("mkdir -p /mnt/etc/elements/.sys_files")
    os.system("touch /mnt/etc/elements/.sys_files/.pkg.db")
    os.system("chmod a+x /mnt/usr/bin/lmt")  # Make lmt executable
    os.system("chmod a+x -R /mnt/etc/elements/repos/Nitrogen")  # Make packages executable

    if atomic is True:
        print("Will you be using iwd NetworkManager or wpa_supplicant?")  # NetworkManager or wpa_supplicant or iwd
        print("1. iwd")
        print("2. NetworkManager")
        print("3. wpa_supplicant")
        network_supplier = int(input("1/2/3: "))
        if network_supplier == 1:
            os.system(
                "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt iwd")  # Install iwd
            os.system("chroot /mnt/ ln -s /etc/sv/iwd /var/service/")  # Enable iwd
        elif network_supplier == 2:
            os.system(
                "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt NetworkManager")  # Install NetworkManager
            os.system("chroot /mnt/ ln -s /etc/sv/NetworkManager /var/service/")
        elif network_supplier == 3:
            os.system(
                "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt wpa_supplicant wpa_cli")
            os.system("chroot /mnt/ ln -s /etc/sv/wpa_supplicant /var/service/")

    else:
        print("Installing desktop environment")
        os.system(
            "XBPS_ARCH=x86_64 xbps-install -Sy -R https://alpha.de.repo.voidlinux.org/current -r /mnt NetworkManager gnome-core xorg wayland gdm python3-dbus gnome-terminal firefox")
        os.system("chroot /mnt/ ln -sv /etc/sv/gdm /var/service/")
        os.system("chroot /mnt/ ln -sv /etc/sv/dbus /var/service/")
        os.system("chroot /mnt/ ln -sv /etc/sv/NetworkManager /var/service/")
        os.system("chroot /mnt/ ln -sv /etc/sv/dhcpcd /var/service/")
        print("Set sudo perms")
        os.system('echo "%sudo ALL=(ALL:ALL) ALL" > /mnt/etc/sudoers')
        os.system(
            'echo "root ALL=(ALL:ALL) ALL" >> /mnt/etc/sudoers')  # let root use sudo(for obvious reasons) as well as the user

    print("")
    print("")

    print("Do you want to reboot?")
    reboot_choice = input("Y/n ")
    if reboot_choice == "y":
        os.system("reboot")
    else:
        pass


# Run Installer
install()
