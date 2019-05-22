#!/usr/bin/python
"""
 This python module:
 1. create lvm snapshot and run separate copy mysql from that snapshot
 2. execute mysqlbuckup module for selected configuration files
 3. stop snapshoted mysql and remove snapshot

 Written by : Vladimir Kushnir
 Created date: 30.04.2019
 Last modified: 30.04.2019
 Tested with : Python 2.7

    Simple usage example:

    mysqlsnapshot <custom my.cnf> <logical volume path> <mount point> <config1 for mysqlbackup> <config2 for mysqlbackup> ...

    do_backup(get_options())

"""

__version__ = "0.1"
__copyright__ = "Vladimir Kushnir aka Kvantum i(c)2019"

__all__ = ['']

# Import required python libraries
import os
import sys
import stat
import tempfile
import datetime
import argparse
import mysqlbackup
import lvm
import MySQLdb
from subprocess import check_call

def set_snapshot(options):
    pass

def remove_snapshot(optios):
    """unmount and remove snapchot"""

    print "unounting snapshot \"{}\" from \"{}\" ...".format(os.path.join(options.vgname, options.snap),
                                                             options.mpath)
    check_call([UMOUNT_CMD, os.path.join(options.vgname, options.snap)],
                   stdout=sys.stdout, stderr=sys.stderr)

    print "removing snapshot \"{}\" ...".format(os.path.join(options.vgname, options.snap))
    check_call([LVREMOVE_CMD, "-f", os.path.join(options.vgname, options.snap)],
               stdout=sys.stdout, stderr=sys.stderr)


def get_options():
    parser = argparse.ArgumentParser(usage='%(prog)s [options] <config1 for mysqlbackup> [config2 for mysqlbackup] ...',
                                     description='Create LVM snapshot, then use mysqlbackup.py with provided configs.')
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('--cnf', required=True, dest='cnf',
                        help='my.cnf file to run mysql from snapshot')
    parser.add_argument('--volume', required=True, dest='logical_volume',
                        help='logical volume for snapshot source')
    parser.add_argument('--mount', required=True, dest='mount_point',
                        help='mount point')
    parser.add_argument('--size', dest='size', default='50G',
                        help='snapshot size')
    parser.add_argument('--snap', dest='snapshot_name', default='mysql_{:%Y%m%d}_snapshot'.format(datetime.datetime.now()),
                        help='snapshot name')
    parser.add_argument('configs', nargs='+',
                        help='list backup configs')
    return parser.parse_args()

if __name__ == "__main__":
    opt = get_options()
    with lvm.LogicalVolumeCOW('mysql_test', 'mysql', create=True) as snapshot:
        if snapshot.exists:
            for cfg in opt.configs:
                mysql_options = mysqlbackup.BackupOptions()
                mysqlbackup.load_config_file(mysql_options, cfg)
                mysqlbackup.do_backup(mysql_options)
