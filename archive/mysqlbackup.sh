#!/bin/bash
# Backup MySQL database with mysqldump
# 
# #TODO: comannd line parameters
# #TODO: posibility exclude columns from table
# OPTIONS:
#  -f Check diff between last backup and save only if differs
#  -z <Y|M> Compress results Y - yearly, M - monthly
# PARAMS:
#  -s <Server>
#  -d <Database>
#  -u <User>
#  -p <Password>
#  -t <table1 table2 ... tablen>
#  -b <backup folder>

self=$(basename $0)
self_cfg=${self%.*}.cfg
if [ -s ${self_cfg} ]; then
  cfg=${self_cfg}
else
  if [ -s /etc/${self_cfg} ]; then
    cfg=/etc/${self_cfg}
  else
    echo "Configuration file not found. Please check ${self_cfg} exist in current directory or /etc/${self_cfg}!"
    exit 1
  fi
fi

#Set a default value for variables
source ${cfg}
#db_server="<MySQL Server Address>"
#db_user="Backup Username"
#db_pass="Backup Username Password"
#db_name="Database Name"

#declare -A db_table
#db_table['<table1>']="field1,field2,...,filedn"
#db_table['<table2>']="*"

#do_diff=1      - compare with previos archive
#save_diff=1    - store diff files
#do_inc=0       - delete unmodified files

db_tables=${!db_table[@]}
broot="/backup/${db_name}"
droot=`mktemp -d`
lroot=`mktemp -d`

chmod 777 ${droot}
chmod 777 ${lroot}

opt_dump="--routines --events --triggers --quote-names --skip-add-drop-table"
opt_diff="--ignore-case --ignore-tab-expansion --ignore-blank-lines --ignore-space-change --ignore-matching-lines=^-- -u"
opt_zip="-9 --junk-paths --latest-time"
opt_mysql="--host=${db_server} --user=${db_user} --password=${db_pass} ${db_name}"

Y=`date +%Y`
M=`date +%m`
D=`date +%d`

#TODO: process command line arguments
#Process the arguments 
while getopts fz:s:d:u:p:t:b: opt; do
  case "$opt" in
    f) do_diff=1;;
    z) do_zip=${OPTARG^^};;
    s) db_server=$OPTARG;;
    d) db_name=$OPTARG;;
    u) db_user=$OPTARG;;
    p) db_pass=$OPTARG;;
    t) db_tables=$OPTARG;;
    b) backup_root=$OPTARG;;
  esac
done

bfolder="${broot}/${Y}/${Y}-${M}"
bfile="${broot}/${Y}/${Y}-${M}/${db_name}_${Y}-${M}-${D}.zip"

mkdir -p ${backup_folder}

# Dump Structure
mysqldump ${opt_dump} --log-error="${bfile}.log" --user=${db_user} --password=${db_pass} ${db_name} ${db_tables} > "${droot}/mysqldump.sql
"

# Dump Tables
for tbl in ${db_tables}; do
  sql="SELECT ${db_table[${tbl}]} INTO OUTFILE '${droot}/${tbl}.csv' FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED
 BY '\\n' FROM ${tbl};"
  mysql ${opt_mysql} -e "${sql}" >> ${bfile}.log
  if [ -s ${droot}/${tbl}.csv ]; then
    echo "${db_table[${tbl}]}" > ${droot}/${tbl}.hdr
  else
    rm ${droot}/${tbl}.csv
  fi
done

do_save=1
if (( ${do_diff} )); then
  do_save=0
  flast=`find ${broot}/${Y} -name "*zip" -type f | xargs ls -tr | tail -1`
  unzip ${flast} -d ${lroot}
  for f in ${droot}/*.{csv,sql}; do
    fn=$(basename "$f")
    fl=${lroot}/$fn
    if [ -s $fl ]; then
      res_diff=`diff --brief ${opt_diff} $f $fl`
      if [ -n "${res_diff}" ]; then
        do_save=1
        if (( ${save_diff} )); then
          diff ${opt_diff} $f $fl > ${droot}/$fn.diff
        fi
      else
        if (( ${do_inc} )); then
          rm -f $f
          rm -f ${droot}/${fn%.*}.hdr
        fi
      fi
    fi
  done
fi

# Pack Files
if (( ${do_save} )); then
  zip ${opt_zip} -r ${bfile} "${droot}"
fi

# Delete Temp Files
rm --recursive --force ${droot}
rm --recursive --force ${lroot}
find ${broot} -type f -name *.log -size 0 -exec rm -f {} \;
