#!/usr/bin/python2
"""
 Logical Volume Management utitltes python wrapper

 Written by : Vladimir Kushnir
 Created date: 30.04.2019
 Last modified: 04.05.2019
 Tested with : Python 2.7

"""

__version__ = "0.12"
__copyright__ = "Vladimir Kushnir aka Kvantum (c)2019"

__all__ = ['find_lv', 'find_mount_target', 'find_mount_source', 'LogicalVolume', 'LogicalVolumeCOW']

import os
import json
from subprocess import check_call, check_output

CMD_MOUNT = '/usr/bin/mount'
CMD_UMOUNT = '/usr/bin/umount'
CMD_FINDMNT = '/usr/bin/findmnt'

LVM_UNITS = '--units=b'
CMD_LVS = '/usr/sbin/lvs'
LVS_OPTIONS = '--options=vg_name,lv_name,lv_full_name,lv_size,lv_dm_path,lv_role,lv_host,origin,snap_percent'
CMD_LVCREATE = '/sbin/lvcreate'
CMD_LVREMOVE = '/sbin/lvremove'


# FUNCTIONS
def find_lv(name):
    """
    Find logical volume by name
    :param str name: logical volume name
    :returns: logical volume pearameters if fond, None otherwize
    :rtype: dict
    """
    lvs = json.loads(check_output([CMD_LVS, '--reportformat=json', LVM_UNITS, LVS_OPTIONS]))['report'][0]['lv']
    if len(lvs) > 0:
        lvf = filter(lambda lv: lv['lv_name'] == name, lvs)
        if len(lvf) > 0:
            return lvf[0]
    return None


def find_mount_target(source):
    """
    Search mounts by source and return target
    :param str source: mount source
    :returns: mount target if found, None otherwize
    :rtype: str
    """
    try:
        return check_output([CMD_FINDMNT, '--output=target', '--source={}'.format(source)]).splitlines()[1]
    except:
        return None


def find_mount_source(target):
    """
    Search mounts and target and return source
    :param str target: mount source
    :returns: mount source if found, None otherwize
    :rtype: str
    """
    return check_output([CMD_FINDMNT, '--output=source', '--target={}'.format(target)]).splitlines()[1]


def get_size_opt(size):
    """
    Generate size option for LVM utitlites 1024|512GiB|50%|100%
    :param str size: size of volume
    :returns: options string
    :rtype: str
    """
    if size is None:
        return '--extents=100%FREE'
    elif size[-1:] == '%':
        return '--extents={}FREE'.format(size)
    else:
        return '--size={}'.format(size)


# EXCEPTIONS
class LogicalVolumeError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


# DECORATORS
def lv_property(function):
    """
    Check self._lv before return value
    :param function:
    :return: wrapper
    """

    @property
    def wrapper(self, *args, **kwargs):
        if self._lv is None:
            self._update()
        if self._lv is None:
            raise LogicalVolumeError('Can\'t get property from non existent volume!')
        else:
            return function(self, *args, **kwargs)

    return wrapper


# CLASSES
class LogicalVolume(object):
    """
    Wrapper for Logical Volume
    """

    def __init__(self, name):
        """
        Create LogicalVolume LV Object
        :param str name: name of Logical Volume
        """
        if (name is None) or (len(name) <= 0):
            raise LogicalVolumeError('Can\'t create LogicalVolume with name "{}"!'.format(name))
        self._name = name
        self._lv = find_lv(self._name)
        self._mount = None
        if self._lv is not None:
            self._mount = find_mount_target(self._lv['lv_dm_path'])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            raise LogicalVolumeError(
                "Exit error! Exception type:{}, value:{}, trace:{}".format(exc_type, exc_value, tb))
        self.remove()

    def __str__(self):
        self._update()
        return json.dumps(self._lv)

    def _update(self):
        """
        Update LV parameters
        """
        self._lv = find_lv(self._name)

    @property
    def name(self):
        """
        Name. LVs created for internal use.
        :return: name
        :rtype: str
        """
        return self._name

    @property
    def exists(self):
        """
        :return: True if LV exists
        :rtype: bool
        """
        if self._lv is None:
            self._update()
        return self._lv is not None

    @lv_property
    def vg(self):
        """
        Volume Group name.
        :return: VG name.
        :rtype: str
        """
        return self._lv['vg_name']

    @lv_property
    def full_name(self):
        """
        Full name of LV including its VG, namely VG/LV.
        :return: full name
        :rtype: str
        """
        return self._lv['lv_full_name']

    @lv_property
    def size(self):
        """
        Size of LV in current units
        :return: size
        :rtype: int
        """
        return int(self._lv['lv_size'])

    @lv_property
    def dm_path(self):
        """
        Internal device-mapper pathname for LV (in /dev/mapper directory).
        :return: device-mapper pathname
        :rtype: str
        """
        return self._lv['lv_dm_path']

    @lv_property
    def role(self):
        """
        LV role.
        :return: role
        :rtype: list
        """
        return self._lv['lv_role'].split(',')

    @lv_property
    def host(self):
        """
        Creation host of the LV, if known.
        :return: creation host
        :rtype: str
        """
        return self._lv['lv_host']

    def create(self):
        """
        Create logical volume
        NOT IMPLEMENTED
        """
        pass

    def remove(self):
        """
        Remove Logical Volume with ``lvremove``
        :raises LogicalVolumeError: if LV mounted
        """
        if find_mount_target(self._lv['lv_dm_path']) is not None:
            raise LogicalVolumeError('Can\'t remove mounted volume!')
        check_call([CMD_LVREMOVE, '--force', self._lv['lv_full_name']])
        # raise LogicalVolumeError('Removing snapshot "{}" failed!'.format(self._lv['lv_full_name']))

    @property
    def mounted(self):
        """
        Check if LV mounted
        :return: mounted
        :rtype: bool
        """
        return find_mount_target(self._lv['lv_dm_path']) is not None

    @property
    def mounted_directory(self):
        """
        Find where LV mounted
        :return: mounted directory, None otherwize
        :rtype: str
        """
        return find_mount_target(self._lv['lv_dm_path'])

    @property
    def mount_directory(self):
        """
        Return directory to mount
        :return: directory to mount
        :rtype: str
        """
        return self._mount

    @mount_directory.setter
    def mount_directory(self, directory):
        """
        Set directory to mount
        :raises LogicalVolumeError: if mount directory is not exists or already mounted somwere
        :param str directory: directory to mount
        """
        if not os.path.isdir(directory):
            raise LogicalVolumeError('Can\'t set mount directory "{}", is not exists!'.format(directory))
        if find_mount_source(directory) is not None:
            raise LogicalVolumeError('Can\'t set mount directory "{}", already mounted!'.format(directory))
        self._mount = os.path.normpath(directory)

    def mount(self):
        """
        Mount Logical Volume to **self._mount**
        :raises LogicalVolumeError: if LV not exists, directory for mount is not exists or directory already mounted
        """
        if self._lv is None:
            raise LogicalVolumeError('Can\'t mount, Logical Volume:"{}" is not created!'.format(self._name))
        if not os.path.isdir(self._mount):
            raise LogicalVolumeError('Can\'t mount, directory:"{}" is not exists!'.format(self._mount))
        if find_mount_target(self._lv['lv_dm_path']) is not None:
            raise LogicalVolumeError('Can\'t mount, logical volume:"{}" already mounted!'.format(self._name))
        check_call([CMD_MOUNT, '--source={}'.format(self._lv['lv_dm_path']), '--target={}'.format(self._mount)])

    def umount(self):
        """
        Unmount Logical Volume
        :raises LogicalVolumeError: if LV not exists or not mounted
        """
        if self._lv is None:
            raise LogicalVolumeError('Can\'t umount, Logical Volume:"{}" is not created!'.format(self._name))
        if find_mount_target(self._lv['lv_dm_path']) is None:
            raise LogicalVolumeError('Can\'t umount, logical volume:"{}" not mounted!'.format(self._name))
        check_call([CMD_UMOUNT, self._lv['lv_dm_path']])

    def get_snapshot(self):
        # TODO: generate COW snapshot
        pass

    def has_snaphots(self):
        # TODO: check snaphot
        pass

    def snaphots(self):
        # TODO: list snapshots
        pass


class LogicalVolumeCOW(LogicalVolume):
    def __init__(self, name, origin, create=False, mode='r', size=None):
        """
        Create LogicalVolumeCOW object. If create=True also create LV
        :param str name: LV snapshot name
        :param origin: parent LV
        :param bool create: if True create snapshot volume
        :param str mode: creation mode r, rw
        :param str size: size of new snapshot volume
        :raises LogicalVolumeError: if origin is not created
        """
        if type(origin) is LogicalVolume:
            if origin.exists:
                self._origin = origin
        elif type(origin) is str:
            olv = find_lv(origin)
            if olv is not None:
                self._origin = LogicalVolume(olv['lv_name'])
            else:
                raise LogicalVolumeError('Can\'t create snapshot from non existent origin!')
        else:
            raise LogicalVolumeError('Can\'t create snapshot from non existent origin!')
        super(LogicalVolumeCOW, self).__init__(name)
        if create:
            self.create(mode, size)

    @property
    def origin(self):
        """
        For LVs that are components of another LV, the parent LV.
        :return: parent object
        :rtype: LogicalVolume
        """
        return self._origin

    @lv_property
    def percent(self):
        """
        For snapshots, the percentage full if LV is active.
        :return: percentage
        :rtype: float
        """
        return float(self._lv['snap_percent'])

    def create(self, mode='r', size=None):
        """
        Create snapshot from **self._origin**
        :param str mode: creation mode r, rw
        :param str size: size of new snapshot volume
        """
        sopt = get_size_opt(size)
        check_call([CMD_LVCREATE, '--snapshot', '--name={}'.format(self._name), '--permission={}'.format(mode), sopt,
                    self._origin.full_name])
        # raise LogicalVolumeError('Creating snapshot from "{}" failed!'.format(self._origin.full_name))
