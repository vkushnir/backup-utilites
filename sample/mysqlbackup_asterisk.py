#!/usr/bin/python

# Import required python libraries

from mysqlbackup import get_options, do_backup

opt = get_options()
do_backup(opt)

