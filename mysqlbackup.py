#!/usr/bin/python 
########################################################### 
# 
# This python script is used for mysql database backup 
# using mysqldump utility. 
# 
# Written by : Vladimir Kushnir
# Created date: 25.05.2016 
# Last modified: 02.06.2016 
# Tested with : Python 2.6.6 
# Script Revision: 1.01
# 
########################################################## 

# Import required python libraries 
import os, sys, stat
import tempfile
import datetime
import ConfigParser
from subprocess import Popen, PIPE, STDOUT

# Get configuretion file
cfg_name = os.path.splitext(os.path.basename(__file__))[0]+".cfg"
cfg_full = cfg_name
if not os.path.exists(cfg_full):
	cfg_full = "/etc/" + cfg_name
	if not os.path.exists(cfg_full):
		sys.exit ("Can't find \"" + cfg_name + "\" file\n")	
cfg = ConfigParser.RawConfigParser()
cfg.read (cfg_full)

# Deafult Constants
date=datetime.date.today()

# Read configuration data
db_path = cfg.get("database", "login-path")
db_name = cfg.get("database", "database")
do_inc = cfg.getboolean("database", "incremental")
do_diff = cfg.getboolean("database", "diff")

# Generate backup and temporary directories
backup_root = "/backup/" + db_name
backup_folder = backup_root + "/{0}/{0}-{1:02d}".format(date.year, date.month)
backup_file = backup_folder + "/{3}_{0}{1:02d}{2:02d}".format(date.year, date.month, date.day, db_name)
log_file = backup_file + ".log"
# Create backup directory
try:
	os.makedirs(backup_folder)
except OSError:
	if not os.path.isdir(backup_folder):
		raise
dump_root = tempfile.mkdtemp()
last_root = tempfile.mkdtemp()
os.chmod(dump_root, 0o777)
os.chmod(last_root, 0o777)
print ("Folders:", backup_folder, dump_root, last_root)

# External applications
mysqlc = ["mysql", "--login-path="+db_path]
mysqldc = ["mysqldump", "--login-path="+db_path, "--routines", "--complete-insert", "--extended-insert", "--order-by-primary", "--quote-names", "--skip-add-drop-table"]
pkzipc = ["zip", "-9", "--junk-paths", "--latest-time", "--recurse-paths", backup_file+".zip", dump_root]
unzipc = ["unzip", "-uo"]
findc = ["find", backup_root + "/{0}".format(date.year), "-name", "*.zip", "-type", "f"]
xargsc = ["xargs", "ls", "-tr"]
diffc = ["diff", "--ignore-case", "--ignore-tab-expansion", "--ignore-blank-lines", "--ignore-space-change", "--ignore-matching-lines=^--", "-u"]

flog = open(log_file, "a")

# Functions
def fexit(msg):
	flog.write(msg+"\n")
	sys.exit(msg+"\n")

### START
## Check previous archive
if do_diff or do_inc:
	find = Popen(findc, stdout=PIPE, stderr=flog)
	cfind = find.communicate()
	if find.returncode > 0:
		fexit("Find previous archive error!")
	if cfind[0] != '':
		xargs = Popen(xargsc, stdin=PIPE, stdout=PIPE, stderr=flog)
		cxargs = xargs.communicate(cfind[0])
		if xargs.returncode > 0:
			fexit("Sort previous archives error!")
		if cxargs[0] != '':
			for pzip in reversed(cxargs[0].split()):
			# extract files to temporary folder
				unzip = Popen(unzipc+[pzip, "-d", last_root], stderr=flog)
				cunzip = unzip.communicate()
				if unzip.returncode > 0:
					fexit("Extract files from '"+pzip+"' error!")
	else:
		do_diff = so_inc = False

## Save database schema
dump_sql = dump_root+"/"+db_name+".sql"
with open(dump_sql, "w") as mysqld_sql:
	mysqld = Popen(mysqldc + ["--no-data", "--log-error="+log_file, db_name], stdout=mysqld_sql, stderr=flog)
	cmysqld = mysqld.communicate()
	if mysqld.returncode > 0:
		fexit("Save database schema error!")
# Compare files
if do_diff or do_inc:
	dump_last = last_root+"/"+db_name+".sql"
	if os.path.exists(dump_last):
		dump_diff = dump_root+"/"+db_name+".diff"
		with open(dump_diff, "w") as fdiff:
			diff = Popen(diffc + [dump_last, dump_root+"/"+db_name+".sql"], stdout=fdiff, stderr=flog)
			cdiff = diff.communicate()
		if diff.returncode == 0:
			os.remove(dump_diff)
			if do_inc:
				os.remove(dump_sql)
		elif diff.returncode == 1:
			if not do_diff:
				os.remove(dump_diff)
		else:
			fexit("Generate diff for "+db_name+".sql error!")

## SAVE TABLES
if cfg.getboolean("database", "save-data"):
	 
	# Get tables list
	mysql = Popen(mysqlc+["information_schema", "-e", "SELECT `t`.`TABLE_NAME` FROM `information_schema`.`TABLES` `t` WHERE `t`.`TABLE_SCHEMA`='"+db_name+"' AND `t`.`TABLE_TYPE`='BASE TABLE';"], stdout=PIPE, stderr=flog)
	cmysql = mysql.communicate()
	if cmysql[0] == '' or mysql.returncode > 0:
		flog.write("Get tables list error!")
		if cmysql[0] == '':
			flog.write("Can't get any data")
		sys.exit("Get tables list error!\n")
	all_tables = cmysql[0].split()
	all_tables.pop(0)
	if cfg.has_option("tables", "include"):
		tables = cfg.get("tables", "include").split(",")
	elif cfg.has_option("tables", "exclude"):
		tables = cfg.get("tables", "exclude").split(",")
		#tables = list(set(all_tables) - set(tables))
		tables = [table for table in all_tables if table not in tables]
	else:
		tables = all_tables
	
	# Save tables
	for table in tables:
		mysql = Popen(mysqlc+["information_schema", "-e", "SELECT `c`.`COLUMN_NAME` FROM `information_schema`.`COLUMNS` c WHERE c.TABLE_SCHEMA='"+db_name+"' AND c.TABLE_NAME='"+table+"';"], stdout=PIPE, stderr=flog)
		cmysql = mysql.communicate()
		if mysql.returncode > 0:
			fexit("Get table '"+table+"' columns error!")
		all_columns = cmysql[0].split()
		all_columns.pop(0)
		if cfg.has_option("columns", table):
			columns = cfg.get("columns", table).split(",")
			columns_include = eval(columns.pop(0))
			if not columns_include:
				#columns = list(set(all_columns) - set(columns))
				columns = [col for col in all_columns if col not in columns]
		else:
			columns = all_columns
		# check if table have data
		mysql = Popen(mysqlc+[db_name, "-e", "SELECT `"+columns[0]+"` FROM `"+table+"` LIMIT 1;"], stdout=PIPE, stderr=flog)
		cmysql = mysql.communicate()
		if mysql.returncode > 0:
			fexit("Check table '"+table+"' error!")
		if cmysql[0] != '':
			# save table header
			table_hdr = dump_root+"/"+table+".hdr"
			if os.path.exists(table_hdr):
				os.remove(table_hdr)
			mysql = Popen(mysqlc+[db_name, "-e", "SELECT '"+"','".join(columns)+"' INTO OUTFILE '"+table_hdr+"' FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\\n';"], stderr=flog)
			cmysql = mysql.communicate()
			if mysql.returncode > 0:
				fexit("Save table '"+table+"' headers error!")
			# save table data
			table_csv = dump_root+"/"+table+".csv"
			if os.path.exists(table_csv):
				os.remove(table_csv)
			mysql = Popen(mysqlc+[db_name, "-e", "SELECT `"+'`,`'.join(columns)+"` FROM `"+table+"` INTO OUTFILE '"+table_csv+"' FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\\n';"], stderr=flog)
			cmysql = mysql.communicate()
			if mysql.returncode > 0:
				fexit("Get table '"+table+"' data error!")
			# Compare files
			if do_diff or do_inc:
				table_last = last_root+"/"+table+".csv"
				if os.path.exists(table_last):
					table_diff = dump_root+"/"+table+".diff"
					with open(table_diff, "w") as fdiff:
						diff = Popen(diffc + [table_last, table_csv], stdout=fdiff, stderr=flog)
						cdiff = diff.communicate()
					if diff.returncode == 0:
						os.remove(table_diff)
						if do_inc:
							os.remove(table_hdr)
							os.remove(table_csv)
					elif diff.returncode == 1:
						if not do_diff:
							os.remove(table_diff)
					else:
						fexit("Generate diff for table "+table+" error!")

## PACK DATA
pkzip = Popen(pkzipc, stderr=flog)
cpkzip = pkzip.communicate()
if pkzip.returncode > 0:
	fexit("ZIP files error!")

# Clean
rm = Popen(["rm", "-rf", last_root, dump_root], stderr=flog)
rm.communicate()

### FINISH
flog.close()
if os.path.getsize(log_file) == 0:
	os.remove(log_file)

