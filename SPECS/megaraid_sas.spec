%define name megaraid_sas
%define version 07.711.04.00
%define release 1
%define kernel 4.19.0+1
Summary: LSI Megaraid drivers
Name: %{name}
Version: %{version}
Release: %{release}
Vendor: LSI Corporation
License: GPL
Group: System Environment/Kernel
Source0: %{name}-%{version}.tar.gz
Source1: Module.supported
URL: http://www.lsi.com
Distribution: LSI Coporation
BuildRoot: /var/tmp/%{name}-buildroot


%description
Drivers for (i686, x86_64, ia64, ppc64 and updates) for the
LSI Corporation Megaraid_sas  Architecture 

# prep #########################################################################
%prep
echo prep %{version}
%setup -c -b 0
cp %_sourcedir/Module.supported drivers/scsi/megaraid_sas/Module.supported


# build ########################################################################
%build
echo build %{version}
%bcond_with retpoline
%if %{with retpoline}
	export KCFLAGS='-mindirect-branch=thunk-inline -mindirect-branch-register'
	find . -name *.c -print0 | xargs -0 sed -i '/MODULE_LICENSE(/a MODULE_INFO(retpoline, "Y");'
%endif
make build  KERNEL=%{kernel};

# install ######################################################################
%install
echo install %{version}
echo "%defattr(-,root,root)" > $RPM_BUILD_DIR/file.list.%{name}

kernel_ver=%{kernel}
MEGARAIDLINUX_IPATH=/lib/modules/%{kernel}/weak-updates/megaraid_sas

if modinfo megaraid_sas -n |xargs file |grep -c "compressed" >> /dev/null; then
	driver_bin="megaraid_sas.ko.xz"
elif [ `find /lib/modules/${kernel_ver}/ -name megaraid_sas.ko.xz*` ]; then
	driver_bin="megaraid_sas.ko.xz"
else
	driver_bin="megaraid_sas.ko"
fi

mkdir -p $RPM_BUILD_ROOT/lib/modules/%{kernel}/weak-updates/megaraid_sas

# create the file list used in %files to indicate which files are in package
echo "$MEGARAIDLINUX_IPATH/${driver_bin}.new" >> $RPM_BUILD_DIR/file.list.%{name}

make install PREFIX=$RPM_BUILD_ROOT KERNEL=%{kernel}
if [ ${driver_bin} == "megaraid_sas.ko.xz" ]; then
	xz $RPM_BUILD_ROOT/$MEGARAIDLINUX_IPATH/megaraid_sas.ko
fi
mv -f $RPM_BUILD_ROOT/$MEGARAIDLINUX_IPATH/${driver_bin} \
	$RPM_BUILD_ROOT/$MEGARAIDLINUX_IPATH/${driver_bin}.new


# pre #########################################################################
%pre
echo pre %{version}
system_arch=`uname -m`
if [ %{_target_cpu} != ${system_arch} ]; then
	echo "ERROR: Failed installing this rpm!!!!"
	echo "This rpm is intended for %{_target_cpu} platform. It seems your system is ${system_arch}.";
	exit 1;
fi;

# post #########################################################################
%post
echo post %{version}

kernel_ver=%{kernel}
if modinfo megaraid_sas -n |xargs file |grep -c "compressed" >> /dev/null; then
	driver_bin="megaraid_sas.ko.xz"
elif [ `find /lib/modules/${kernel_ver}/ -name megaraid_sas.ko.xz*` ]; then
	driver_bin="megaraid_sas.ko.xz"
else
	driver_bin="megaraid_sas.ko"
fi

if [ ! -e /boot/vmlinuz-%{kernel} ] && [ ! -e /boot/vmlinux-%{kernel} ]; then
	continue;
fi;

MEGARAIDLINUX_IPATH=/lib/modules/%{kernel}/weak-updates/megaraid_sas
if [ ! -e $MEGARAIDLINUX_IPATH/${driver_bin}.new ]; then
	continue;
fi;

MEGARAIDLINUX_ORIG_IPATH=/lib/modules/%{kernel}/kernel/drivers/scsi/megaraid
echo "The megaraid driver for kernel %{kernel} is now version %{version}";
cp -f $MEGARAIDLINUX_IPATH/${driver_bin}.new $MEGARAIDLINUX_IPATH/${driver_bin}

# Remake the initrd image
MEGARAIDLINUX_IPATH=/lib/modules/%{kernel}/kernel/drivers/scsi/megaraid
if [ -e $MEGARAIDLINUX_IPATH/${driver_bin} ]; then
	mv $MEGARAIDLINUX_IPATH/${driver_bin} \
		$MEGARAIDLINUX_IPATH/${driver_bin}.orig
fi;

MEGARAIDLINUX_IPATH=/lib/modules/%{kernel}/updates
if [ -e $MEGARAIDLINUX_IPATH/${driver_bin} ]; then
	mv $MEGARAIDLINUX_IPATH/${driver_bin} \
		$MEGARAIDLINUX_IPATH/${driver_bin}.orig
fi;

MEGARAIDLINUX_IPATH=/lib/modules/%{kernel}/extra/megaraid_sas
if [ -e $MEGARAIDLINUX_IPATH/${driver_bin} ]; then
	mv $MEGARAIDLINUX_IPATH/${driver_bin} \
		$MEGARAIDLINUX_IPATH/${driver_bin}.orig
fi;

bootpart=/boot;
depmod -v %{kernel} > /dev/null 2>&1;

#   By default mkinitramfs command includes only those modules present in kernel/driver/ path
#   in to the initrd image. So inorder to include ${driver_bin} module which is present in weak-update
#   directory in to initrd image then append "megaraid_sas" line to /etc/initramfs-tools/modules.   
#   /etc/initramfs-tools/modules stores those modules that we want to include in our initramfs.

if which mkinitramfs |grep -c "mkinitramfs" >> /dev/null; then
	if which mkinitramfs |grep -c "no mkinitramfs" >> /dev/null ; then
		module_init_tool="unknown"
	else
		module_init_tool="mkinitramfs"
		mkinitramfs_modules=/etc/initramfs-tools/modules
		pattern=`grep -R "megaraid_sas" ${mkinitramfs_modules}`
		if [ $? -ne 0 ]; then
			echo "megaraid_sas" >> ${mkinitramfs_modules} 
		else
			sed -e s/"$pattern"/megaraid_sas/ ${mkinitramfs_modules} > /tmp/mkinitramfs_modules
			mv /tmp/mkinitramfs_modules ${mkinitramfs_modules}
		fi;

		mkinitramfs -k -o ${bootpart}/initrd.img-%{kernel} %{kernel}
		echo -e "${module_init_tool} post Install Done."
		exit 0;
	fi
fi

if which mkinitrd |grep -c "mkinitrd" >> /dev/null; then
	if which mkinitrd |grep -c "no mkinitrd" >> /dev/null ; then
		module_init_tool="unknown"
	else
		module_init_tool="mkinitrd"
		mkinitrd -f /boot/initramfs-%{kernel}.img %{kernel}
		ln -s initrd-%{kernel}.img  initramfs-%{kernel}.img
		echo -e "${module_init_tool} post Install Done."
		exit 0;
	fi
fi
		
echo -e "post Install Done."

# postun #######################################################################
%postun
echo postun %{version}

kernel_ver=%{kernel}
if modinfo megaraid_sas -n |xargs file |grep -c "compressed" >> /dev/null; then
	driver_bin="megaraid_sas.ko.xz"
elif [ `find /lib/modules/${kernel_ver}/ -name megaraid_sas.ko.xz*` ]; then
	driver_bin="megaraid_sas.ko.xz"
else
	driver_bin="megaraid_sas.ko"
fi

MEGARAIDLINUX_IPATH=/lib/modules/%{kernel}/weak-updates/megaraid_sas
if [ ! -e $MEGARAIDLINUX_IPATH/${driver_bin}.new ] && \
    [ -e $MEGARAIDLINUX_IPATH/${driver_bin} ]; then

	rm -rf $MEGARAIDLINUX_IPATH;

	MEGARAIDLINUX_IPATH=/lib/modules/%{kernel}/kernel/drivers/scsi/megaraid
	if [ -e $MEGARAIDLINUX_IPATH/${driver_bin}.orig ]; then
		mv $MEGARAIDLINUX_IPATH/${driver_bin}.orig \
			$MEGARAIDLINUX_IPATH/${driver_bin}
	fi;

	MEGARAIDLINUX_IPATH=/lib/modules/%{kernel}/updates
	if [ -e $MEGARAIDLINUX_IPATH/${driver_bin}.orig ]; then
		mv $MEGARAIDLINUX_IPATH/${driver_bin}.orig \
			$MEGARAIDLINUX_IPATH/${driver_bin}
	fi;

	MEGARAIDLINUX_IPATH=/lib/modules/%{kernel}/extra/megaraid_sas
	if [ -e $MEGARAIDLINUX_IPATH/${driver_bin}.orig ]; then
		mv $MEGARAIDLINUX_IPATH/${driver_bin}.orig \
			$MEGARAIDLINUX_IPATH/${driver_bin}
	fi;
fi;

bootpart=/boot;

if [ ! -f /lib/modules/%{kernel}/kernel/drivers/scsi/megaraid/${driver_bin} ] && \
   [ ! -f /lib/modules/%{kernel}/udpates/${driver_bin} ] && \
   [ ! -f /lib/modules/%{kernel}/weak-updates/megaraid_sas/${driver_bin} ] && \
   [ ! -f /lib/modules/%{kernel}/extra/megaraid_sas/${driver_bin} ]; then
	sed -e '/megaraid_sas/d' /etc/modprobe.conf > modprobe.edit;
	mv -f modprobe.edit /etc/modprobe.conf;
fi;

depmod -v %{kernel} > /dev/null 2>&1;


if which mkinitramfs |grep -c "mkinitramfs" >> /dev/null; then
	if which mkinitramfs |grep -c "no mkinitramfs" >> /dev/null ; then
		module_init_tool="unknown"
	else
		module_init_tool="mkinitramfs"
		#  Delete the "megaraid_sas" line from /etc/initramfs-tools/modules file
		mkinitramfs_modules=/etc/initramfs-tools/modules
		sed '/megaraid_sas/d' ${mkinitramfs_modules} > /tmp/module_remove
		mv /tmp/module_remove ${mkinitramfs_modules}
		mkinitramfs -k -o ${bootpart}/initrd.img-%{kernel} %{kernel}
		echo -e "${module_init_tool} Uninstall Done."
		exit 0;
	fi
fi

if which mkinitrd |grep -c "mkinitrd" >> /dev/null; then
	if which mkinitrd |grep -c "no mkinitrd" >> /dev/null ; then
		module_init_tool="unknown"
	else
		module_init_tool="mkinitrd"
		mkinitrd -f /boot/initramfs-%{kernel}.img %{kernel}
		ln -s initrd-%{kernel}.img  initramfs-%{kernel}.img
		echo -e "${module_init_tool} Uninstall Done."
		exit 0;
	fi
fi

echo -e "Uninstall Done."

# files ########################################################################
%files -f ../file.list.%{name}

# changelog  ###################################################################
%changelog
