#!/usr/bin/python
"""
 This python module is used for mysql database backup
 using mysqldump utility and INTO OUTFILE MySQL function.

 Written by : Vladimir Kushnir
 Created date: 25.05.2016
 Last modified: 06.06.2016
 Tested with : Python 2.6.6

    Simple usage example:


    from mysqlbackup import get_options, do_buckup

    do_backup(get_options())

"""

__version__ = "1.32"
__copyright__ = "Vladimir Kushnir aka Kvantum i(c)2016"

__all__ = ['BackupOptions',
           'BackupFolders',
           'sqlf_to_str',
           'sqls_to_str',
           'str_to_bool',
           'find_config_file',
           'load_config_file',
           'load_command_arguments',
           'get_last_dumps',
           'get_diff',
           'get_db_tables',
           'get_db_table_columns',
           'dump_db_schema',
           'dump_db_tables'
           'dump_db_table_hdr',
           'dump_db_table_csv',
           'db_table_has_data',
           'pack_new_dump',
           'make_folders',
           'clean_folders',
           'do_backup',
           'get_options']


# Import required python libraries
import os
import sys
import stat
import tempfile
import datetime
import ConfigParser
from subprocess import Popen, PIPE, STDOUT
from optparse import OptionParser, OptionGroup


class BackupOptions(object):
    def __init__(self):
        self._backup_date = datetime.date.today()
        self._database_name = 'mysql'
        self._database_auth = 'backup'
        self._backup_root = 'backup'
        self._save_diff = True
        self._save_data = True
        self._save_changed = True
        self.tables = None
        self.columns = {}
        self.dump_tables = None
        self.dump_columns = {}
        self.path = BackupFolders(self._get_value)

    def _get_value(self, attr):
        if hasattr(self, attr):
            return getattr(self, attr)
        else:
            return None

    @property
    def backup_root(self):
        return self._backup_root
    @backup_root.setter
    def backup_root(self, value):
        self._backup_root = value
        self.path._set()
        
    @property
    def backup_date(self):
        return self._backup_date
    @backup_date.setter
    def backup_date(self, value):
        self._backup_date = value
        self.path._set()
        
    @property
    def database_name(self):
        return self._database_name
    @database_name.setter
    def database_name(self, value):
        self._database_name = value
        self.path._set()

    @property
    def database_auth(self):
        return self._database_auth
    @database_auth.setter
    def database_auth(self, value):
        self._database_auth = value

    @property
    def save_diff(self):
        return self._save_diff
    @save_diff.setter
    def save_diff(self, value):
        self._save_diff = value
    
    @property
    def save_data(self):
        return self._save_data
    @save_data.setter
    def save_data(self, value):
        self._save_data = value

    @property
    def save_changed(self):
        return self._save_changed
    @save_changed.setter
    def save_changed(self, value):
        self._save_changed = value


class BackupNames:
    include = None
    def __init__(self, names=[]):
        self.names = names

class BackupFolders(object):
    def __init__(self, get_value_func):
        self._set(get_value_func)

    def _set(self, get_value_func=None):
        if get_value_func is not None:
            self._get = get_value_func

        rt = self._get('backup_root')
        dt = self._get('backup_date')
        db = self._get('database_name')

        self._root = os.path.join('/', rt, db).replace(' ', '_')
        self._find = os.path.join(self._root, '{0}'.format(dt.year))
        self._dir = os.path.join(self._root, '{0}/{0}-{1:02d}'.format(dt.year, dt.month))
        name = os.path.join(self._dir, '{3}_{0}{1:02d}{2:02d}'.format(dt.year, dt.month, dt.day, db)).replace(' ', '_')
        self._backup = name + '.zip'
        self._log = name + '.log'
    
    @property 
    def root(self):
        return self._root

    @property
    def find(self):
        return self._find

    @property
    def dir(self):
        return self._dir

    @property
    def backup(self):
        return self._backup

    @property
    def log(self):
        return self._log
    

# EXCEPTIONS
class ConfigError (Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


# FUNCTIONS
def sqlf_to_str(list):
    return "`"+"`,`".join(list)+"`"

def sqls_to_str(list):
    return "'"+"','".join(list)+"'"

def str_to_bool(value):
    if str(value).lower() in ("yes", "y", "true",  "t", "1"): 
        return True
    return False


def find_config_file(name=None, locations=['/etc', os.path.dirname(sys.argv[0])], read=True):
    # search cofiguration file
    if name is None:
        #name = os.path.splitext(os.path.basename(__file__))[0]+'.conf'
        name = os.path.splitext(os.path.basename(sys.argv[0]))[0]+'.conf'
    if os.path.exists(name):
        return name
    else:
        for loc in locations:
            test = os.path.join('/', loc, name)
            if os.path.exists(test):
                return test
    return None


def load_config_file(options, name=None):
    if (name is None) or (not os.path.exists(name)):
        name = find_config_file(name)
    if name is None:
        return False
    if options is None:
        raise ConfigError("Can't find options!")

    cfg = ConfigParser.RawConfigParser()
    if not cfg.read(name):
        raise ConfigError("Read configureation from file '"+name+"' error!")

    if cfg.has_option('database', 'database'):
        options.database_name = cfg.get('database', 'database')

    if cfg.has_option('database', 'login-path'):
        options.database_auth = cfg.get('database', 'login-path')      

    if cfg.has_option('database', 'backup-root'):
        options.backup_root = cfg.get('database', 'backup-root')

    if cfg.has_option('database', 'save-diff'):
        options.save_diff = cfg.getboolean('database', 'save-diff')

    if cfg.has_option('database', 'save-data'):
        options.save_data = cfg.getboolean('database', 'save-data')

    if cfg.has_option('database', 'save-changed'):
        options.save_changed = cfg.getboolean('database', 'save-changed')

    if cfg.has_section('tables'):
        if cfg.has_option('tables', 'include'):
            options.tables = BackupNames(cfg.get('tables', 'include').split(','))
            options.tables.include = True
        elif cfg.has_option('tables', 'exclude'):
            options.tables = BackupNames(cfg.get('tables', 'exclude').split(','))
            options.tables.include = False

    if cfg.has_section('columns'):
        options.columns = {}
        for table in cfg.options('columns'):
            print "table: "+table
            options.columns[table] = BackupNames(cfg.get('columns', table).split(','))
            options.columns[table].include = str_to_bool(options.columns[table].names.pop(0))
    return True


def load_command_arguments(options, arguments=None):
    prs = OptionParser(version="%prog "+__version__)
    prs.add_option('-c', '--configuration', dest='conf', help=
                   "Load configuration from file")

    grp = OptionGroup(prs, "Override CFG", "Next options override data loaded from config file")
    grp.add_option("-r", "--backup-root", dest="root",
                   help="Backup root folder")
    grp.add_option("-l", "--login-path", dest="db_path",
                   help="'login-path' from '.mylogin.cnf' with data for mysql database backup access")
    grp.add_option("-d", "--database", dest="db_name",
                   help="MySQL database name")
    grp.add_option("--save-data", dest="do_save", action="store_true",
                   help="Save data from tables in 'csv' format")
    grp.add_option("--no-data", dest="do_save", action="store_false",
                   help="Don't save data from tables in 'csv' format")
    grp.add_option("--save-diff", dest="do_diff", action="store_true",
                   help="Generate diff file for each table if it changed from previous backup")
    grp.add_option("--no-diff", dest="do_diff", action="store_false",
                   help="Don't generate diff file for each table if it changed from previous backup")
    grp.add_option("--save-changed", dest="do_inc", action="store_true",
                   help="Save data only for tables that have changed with the previous backup")
    grp.add_option("--save-all", dest="do_inc", action="store_false",
                   help="Save data only from all tables")
    prs.add_option_group(grp)

    (opt, oargs) = prs.parse_args(arguments)
    
    if opt.conf is not None:
        print "search "+ opt.conf
        load_config_file(options, opt.conf)

    if opt.db_name is not None:
        options.database_name = opt.db_name

    if opt.db_path is not None:
        options.database_auth = opt.db_path

    if opt.root is not None:
        options.database_root = opt.root

    if opt.do_diff is not None:
        options.save_diff = opt.do_diff

    if opt.do_save is not None:
        options.save_data = opt.do_save

    if opt.do_inc is not None:
        options.save_changed = opt.do_inc


def get_last_dumps(options, log=None):
    find = Popen(["find", options.path.find, "-name", "*.zip", "-type", "f"], stdout=PIPE, stderr=log)
    cfind = find.communicate()
    if find.returncode > 0:
        lexit("Find previous archive error!")
    if cfind[0] != '':
        xargs = Popen(["xargs", "ls", "-t"], stdin=PIPE, stdout=PIPE, stderr=log)
        cxargs = xargs.communicate(cfind[0])
        if xargs.returncode > 0:
            lexit("Sort previous archives error!")
        if cxargs[0] != '':
            for pzip in cxargs[0].split():
                # extract files to temporary folder
                unzip = Popen(["unzip", "-uo", pzip, "-d", options.path.temp_last], stderr=log)
                cunzip = unzip.communicate()
                if unzip.returncode > 0:
                    lexit("Extract files from '"+pzip+"' error!")
            return True
    else:
        return False


def get_diff(options, new, old, log=None, new2=None):
    if os.path.exists(old):
        new_diff = os.path.splitext(new)[0]+'.diff'
    with open(new_diff, "w") as fnd:
        diff = Popen(["diff", "--ignore-case", "--ignore-tab-expansion", 
                     "--ignore-blank-lines", "--ignore-space-change", 
                     "--ignore-matching-lines=^--", "-u", new, old], 
                     stdout = fnd, stderr = log)
        cdiff = diff.communicate()
        if diff.returncode == 0:
            os.remove(new_diff)
            if options.save_changed:
                os.remove(new)
                if new2 is not None:
                    os.remove(new2)
                return False
        elif diff.returncode == 1:
            if not options.save_diff:
                os.remove(new_diff)
            return True
        else:
            lexit('Generate diff file "'+new_diff+'" error!')


def get_db_tables(options, log):
    mysql = Popen(["mysql", "--login-path="+options.database_auth, "information_schema", "-e",
                  "SELECT `t`.`TABLE_NAME` FROM `information_schema`.`TABLES` `t`"
                  " WHERE `t`.`TABLE_SCHEMA`='"+options.database_name+"' AND `t`.`TABLE_TYPE`='BASE TABLE';"],
                  stdout=PIPE, stderr=log)
    cmysql = mysql.communicate()
    if cmysql[0] == '' or mysql.returncode > 0:
        log.write("Get tables list error!")
        if cmysql[0] == '':
            log.write("Can't get any data")
        sys.exit("Get tables list error!\n")
    all_tables = cmysql[0].split()
    all_tables.pop(0)

    if options.tables is not None:
        if options.tables.include:
            tables = [tbl for tbl in all_tables if tbl in options.tables.names]
        else:
            tables = [tbl for tbl in all_tables if tbl not in options.tables.names]
    else:
        tables = all_tables

    setattr(options, 'dump_tables', tables)
    return tables


def get_db_table_columns(options, table, log=None):
    mysql = Popen(["mysql", "--login-path="+options.database_auth, "information_schema", "-e",
                  "SELECT `c`.`COLUMN_NAME` FROM `information_schema`.`COLUMNS` c"
                  " WHERE c.TABLE_SCHEMA='"+options.database_name+"' AND c.TABLE_NAME='"+table+"';"],
                  stdout=PIPE, stderr=log)
    cmysql = mysql.communicate()
    if mysql.returncode > 0:
        lexit("Get table '"+table+"' columns error!")
    all_columns = cmysql[0].split()
    all_columns.pop(0)

    if options.columns.get(table) is not None:
        if options.columns[table].include:
            columns = [col for col in all_columns if col in options.columns[table].names]
        else:
            columns = [col for col in all_columns if col not in options.columns[table].names]
    else:
        columns = all_columns
    options.dump_columns[table] = BackupNames(columns)
    return columns


def dump_db_schema(options, log=None):
    sql_dump = os.path.join(options.path.temp_dump, options.database_name+".sql")
    with open(sql_dump, "w") as fsd:
        mysqld = Popen(["mysqldump", "--login-path="+options.database_auth, "--routines",
                       "--complete-insert", "--extended-insert", "--order-by-primary", 
                       "--quote-names", "--skip-add-drop-table","--no-data", 
                       options.database_name], stdout = fsd, stderr = log)
        cmysqld = mysqld.communicate()
        if mysqld.returncode > 0:
            lexit("Save '"+options.database_name+"' schema error!")
    return sql_dump


def dump_db_tables(options, log=None):
    tables = get_db_tables(options, log)
    for table in tables:
        if db_table_has_data(options, table, log):
            columns = get_db_table_columns(options, table, log)
            table_hdr = dump_db_table_hdr(options, table, log)
            table_csv = dump_db_table_csv(options, table, log)
            get_diff(options, table_csv, os.path.join(options.path.temp_last, table+'.csv'), log, table_hdr)


def dump_db_table_hdr(options, table, log=None):
    table_hdr = os.path.join(options.path.temp_dump, table+".hdr")
    if os.path.exists(table_hdr):
        os.remove(table_hdr)
    mysql = Popen(["mysql", "--login-path="+options.database_auth, options.database_name, "-e",
                  "SELECT "+sqls_to_str(options.dump_columns[table].names)+" INTO OUTFILE '"+table_hdr+"'"
                  " FIELDS TERMINATED BY ','"
                  " OPTIONALLY ENCLOSED BY '\"'"
                  " LINES TERMINATED BY '\\n';"], stderr=log)
    cmysql = mysql.communicate()
    if mysql.returncode > 0:
        lexit("Save table '"+table+"' headers error!")
    return table_hdr


def dump_db_table_csv(options, table, log=None):
    table_csv = os.path.join(options.path.temp_dump, table+".csv")
    if os.path.exists(table_csv):
        os.remove(table_csv)
    mysql = Popen(["mysql", "--login-path="+options.database_auth, options.database_name, "-e",
                  "SELECT "+sqlf_to_str(options.dump_columns[table].names)+" FROM `"+table+"` INTO OUTFILE '"+table_csv+"'"
                  " FIELDS TERMINATED BY ','"
                  " OPTIONALLY ENCLOSED BY '\"'"
                  " LINES TERMINATED BY '\\n';"], stderr=log)
    cmysql = mysql.communicate()
    if mysql.returncode > 0:
        lexit("Get table '"+table+"' data error!")
    return table_csv


def db_table_has_data(options, table, log=None):
    mysql = Popen(["mysql", "--login-path="+options.database_auth, options.database_name, "-e",
                  "SELECT * FROM `"+table+"` LIMIT 1;"], stdout=PIPE, stderr=log)
    cmysql = mysql.communicate()
    if mysql.returncode > 0:
        lexit("Check table '"+table+"' error!")
    return cmysql[0] != ''


def pack_new_dump(options, log=None):
    if len(os.listdir(options.path.temp_dump)) > 0:
        pkzip = Popen(["zip", "-9", "--junk-paths", "--latest-time", "--recurse-paths", 
                       options.path.backup, options.path.temp_dump], stderr=log)
        cpkzip = pkzip.communicate()
        if pkzip.returncode > 0:
            lexit("ZIP files error!")

def make_folders(options, tdump=None, tlast=None):
    try:
        os.makedirs(options.path.root)
    except OSError:
        if not os.path.isdir(options.path.root):
            raise

    if tdump is None:
        tdump = tempfile.mkdtemp()
    if tlast is None:
        tlast = tempfile.mkdtemp()

    #if hasattr(options.path, 'temp_dump'):
    #    options.path.temp_dump = tdump
    #else:
    setattr(options.path, 'temp_dump', tdump)

    #if hasattr(options.path, 'temp_last'):
    #    options.path.temp_last = tlast
    #else:
    setattr(options.path, 'temp_last', tlast)

    os.chmod(tdump, 0o777)
    os.chmod(tlast, 0o777)  

def clean_folders(options):
    cmd = ["rm", "-rf", options.path.temp_dump, options.path.temp_last]
    if os.path.getsize(options.path.log) == 0:
        if len(os.listdir(options.path.dir)) > 1:
            cmd.append(options.path.log)
        else:
            cmd.append(options.path.dir)

    rm = Popen(cmd)
    rm.wait()
    if rm.returncode > 0:
        sys.exit("Cleanup folders error!")


def lexit(msg, log=None):
    if log is not None:
        log.write(msg+"\n")
    sys.exit(msg+"\n")


def do_backup(options):
    make_folders(options)
    with open(options.path.log, "w") as log:
        get_last_dumps(options, log)
        sql = dump_db_schema(options, log)
        get_diff(options, sql, os.path.join(options.path.temp_last, options.database_name+".sql"))
        dump_db_tables(options, log)
        pack_new_dump(options)
    clean_folders(options)


def get_options():
    options = BackupOptions()
    load_config_file(options)
    load_command_arguments(options)
    return options


if __name__ == "__main__":
    do_backup(get_options())
