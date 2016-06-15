### MYSQLBACKUP
*Simple backup utility for small MySQL databases.*

## Use:
    
    #!/usr/bin/python
    from mysqlbackup import get_options, do_backup
    do_backup(get_options())
system automayicaly search file with **'\<script name\>.conf'** in centrain folders (_if **mysqlbackup_asterisk.py** then **mysqlbackup_asterisk.conf**_) or just with command-line

    mysqlbackup.py -c <configuration file>.conf
    
## Configuration file:
_Configuration file must have same name as main script with extention **'.conf'**. And located in the same directory as script or in **'/etc/'** direcotory_

**Structure:**

    [database]
    backup-root=
    # root folder to place archives
    
    login-path=backup
    # access to mysql with '**.mylogin.cnf**' file
    # mysql_config_editor set --login-path=<login-path> --host=<server> --user=<username> --password 
    
    database=mysql
    # database name to backup
    
    save-diff=True
    # true - generate diff file for each table if it changed from previous backup
    
    save-data=True    
    # true - save data from tables
    
    save-changed=True    
    # true - save only changed tables
    save-changed=True
    
    [tables]
    # List included or excluded tables
    # include - to backup only selected tables
    # exclude - to backup all except selected tables
    # include/exclude = <table1>,<table2>,<table3>,...<tablen>
    exclude=cdr,queue_log,iaxfriends
    
    [columns]
    # included or exluded columns
    # mode = true - to backup only selected columns
    # mode = false - to backup all except selected tables
    # <table_name>=<mode>,<column1>,<column2>,<column3>,...<columnn>
    sippeers=0,lastms,ipaddr,port,regseconds,defaultuser,fullcontact,regserver,useragent
    time_limits=0,seconds
    manage_partitions=0,last_updated

## Command-Line Arguments
*Command-Line Arguments override setting from config files*

 - -c , ---configuration _- Load configuration from file_
 - -r, --backup-root _- backup root folder_
 - -l, --login-path _- 'login-path' from '.mylogin.cnf' with data for mysql database backup access_
 - -d, --database _- MySQL database name_
 - --save-data _- save data from tables in 'csv' format_
 - --no-data _- don't save data from tables in 'csv' format_
 - --save-diff _- generate diff file for each table if it changed from previous backup_
 - --no-diff _- don't generate diff file for each table if it changed from previous backup_
 - --save-changed _- save data only for tables that have changed with the previous backup_
 - --save-all _- save data only from all tables_

## Imports
### Classes
 - BackupOptions
   - backup_date
   - database_name
   - database_auth
   - backup_root
   - save_diff
   - save_data
   - save_changed
   - tables
   - columns
   - dump_tables
   - dump_columns
   - path
 - BackupFolders
   - root
   - find
   - dir
   - backup
   - log
   - temp_dump
   - temp_last

### Functions
 - sqlf_to_str - _convert list object to list of string sql_
 - sqls_to_str - _convert list object to list of fields sql_
 - str_to_bool - _convert string to boolean value_
 - find_config_file - _search configuration file_

### Procedures
 - load_config_file
 - load_command_arguments
 - get_last_dumps
 - get_diff
 - get_db_tables
 - get_db_table_columns
 - dump_db_schema
 - dump_db_tables
 - dump_db_table_hdr
 - dump_db_table_csv
 - db_table_has_data
 - pack_new_dump
 - make_folders
 - clean_folders
 - do_backup
 - get_options

