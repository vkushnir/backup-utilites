#MYSQLBACKUP
*Simple backup utility for small MySQL databases.*

## Use:
    
    #!/usr/bin/python
    
    from mysqlbackup import get_options, do_backup
    
    do_backup(get_options())

##Configuration file:
*Configuration file must have same name as main script with extention '**.cfg'**. And located in the same directory as sycript or in '**/etc/**' direcotory*
###Structure:

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

##Command-Line Arguments
*Command-Line Arguments override setting from config files*

 - -c , ---configuration *- Load configuration from file*
 - -r, --backup-root *- backup root folder*
 - -l, --login-path *- 'login-path' from '.mylogin.cnf' with data for mysql database backup access*
 - -d, --database *- MySQL database name*
 - --save-data *- save data from tables in 'csv' format*
 - --no-data *- don't save data from tables in 'csv' format*
 - --save-diff *- generate diff file for each table if it changed from previous backup*
 - --no-diff *- don't generate diff file for each table if it changed from previous backup*
 - --save-changed *- save data only for tables that have changed with the previous backup*
 - --save-all *- save data only from all tables*

