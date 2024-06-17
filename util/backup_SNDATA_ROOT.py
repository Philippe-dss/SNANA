#!/usr/bin/env python
#
# Created Aug 27 2020 by R.Kessler
#  + create tar file of SNDATA_ROOT (for Zenodo)
#  + find and write list of new files since last backup
#  + update BACKUPS.LOG
#
# Can re-run this script multiple times and previous output 
# (tar file and BACKUPS.LOG) from same calendar date will be 
# overwritten. Thus if this script needs to be re-run (same day)
# after some SNDATA_ROOT updates,  there is no need to remove or 
# alter previous script output. If you wait until next day, new
# output will be created.
#
# Beware that this script makes a local backup in the same 
# top-dir as SNDATA_ROOT. Backups to other locations
# (e.g., zenodo) must be done manually, or with another script.
# 
# Nov 3 2020: add SURVEY.DEF to TAR_SUBDIR_LIST
# ================================================

import os, sys, yaml, datetime

USERNAME      = os.environ['USER']
SNDATA_ROOT   = os.environ['SNDATA_ROOT']

backup_logdir  = 'backup_logs'
BACKUP_LOGDIR  = (f"{SNDATA_ROOT}/{backup_logdir}")

backup_logfile = "BACKUPS.LOG"
BACKUP_LOGFILE = f"{BACKUP_LOGDIR}/{backup_logfile}"

# explicitly define directories to include in backup tar file
TAR_SUBDIR_LIST = \
    'filters kcor lcmerge models MWDUST sample_input_files ' \
    'SIM simlib snsed standards  SURVEY.DEF'

# specify content to exclude from tar file
EXCLUDE_FROM_TAR = [ 'SIM/*' ]

BACKUP_SIZE_ALARM = 1500  # give warning of backup tar file exceeds this size

# specify content to exclude from list of new files
EXCLUDE_FROM_NEW_FILES = \
    [ './SIM/*', './SNANA_TESTS/*', (f"./{backup_logdir}/*") ]

# define date stamp to mark backup version
tnow       = datetime.datetime.now()
DATE_STAMP = ('%4.4d-%2.2d-%2.2d' % (tnow.year,tnow.month,tnow.day) )

# ================================================
def get_tar_file_name(backup_dict):

    # backup path is $SNDATA_ROOT up to last slash so that
    # SNDATA_ROOT and its backup are viewable together with ls
    jslash      = SNDATA_ROOT.rindex('/')
    path_backup = SNDATA_ROOT[0:jslash]

    prefix      = f"SNDATA_ROOT_{DATE_STAMP}"
    tar_file    = f"SNDATA_ROOT_{DATE_STAMP}.tar"
    TAR_FILE    = f"{path_backup}/{tar_file}"

    print(f" TAR_FILE    : {TAR_FILE} ")
    print(f" tar_file    : {tar_file} ")

    backup_dict['tar_prefix'] = prefix
    backup_dict['tar_file']   = tar_file
    backup_dict['TAR_FILE']   = TAR_FILE

    # end get_tar_file_name

def create_tar_file(backup_dict):
    
    TAR_FILE   = backup_dict['TAR_FILE']
    TAR_FILEgz = TAR_FILE + '.gz'
    if os.path.isfile(TAR_FILEgz):
        cmd_rm = f"rm {TAR_FILEgz}"
        os.system(cmd_rm)

    print(f"\n Creating tar file: \n     {TAR_FILEgz} ... ")

    # combine list of things to exclude
    x_string = ''
    for x in EXCLUDE_FROM_TAR :
        x_string += f"--exclude='{x}' "

    cmd_tar =  f"cd {SNDATA_ROOT}; " \
        f"tar -czf " \
        f"{TAR_FILEgz} " \
        f"{x_string} " \
        f"{TAR_SUBDIR_LIST} "

    os.system(cmd_tar)

    # get size of tar file
    b = os.path.getsize(TAR_FILEgz)
    size_mb  = int(b * 1.0E-6)
    backup_dict['tar_size'] = size_mb

    print(f" Size is {size_mb} MB")

    if size_mb > BACKUP_SIZE_ALARM :
        print(f"\n")
        print(f" ****** BACKUP SIZE ALARM: {size_mb} MB ***** ")
        print(f" ****** BACKUP SIZE ALARM: {size_mb} MB ***** ")
        print(f" ****** BACKUP SIZE ALARM: {size_mb} MB ***** ")

    # end create_tar_file

def find_new_files(backup_dict) :
    # find all files created since last backup (from backup_yaml input).
    # Use linux find command with os.system.
    # Finally, write NEW_FILES_[date].DAT

    backup_log_yaml = backup_dict['backup_log_yaml']

    last_backup_key  = list(backup_log_yaml.keys())[-1]
    last_backup_date = backup_log_yaml[last_backup_key]['BACKUP_DATE']
    
    x_string = ''
    for x in EXCLUDE_FROM_NEW_FILES:
        x_string += f"! -path '{x}' "

    new_file_log = f"{backup_logdir}/NEW_FILES_{DATE_STAMP}.LOG"
    NEW_LOG_FILE = f"{BACKUP_LOGDIR}/NEW_FILES_{DATE_STAMP}.LOG"

    print(f" Search new files since last backup date:   {last_backup_date}")
    print(f" Write list of new files to \n    $SNDATA_ROOT/{new_file_log} ")

    cmd_find = f"cd {SNDATA_ROOT}; " \
        f"find . -type f -newermt '{last_backup_date}' {x_string} " \
        f"> {new_file_log}"
    os.system(cmd_find)

    # count number of new files:
    with open(NEW_LOG_FILE,'r') as f:
        n_file_new = len([0 for _ in f])

    backup_dict['n_file_new']   = n_file_new
    backup_dict['new_log_file'] = new_file_log
    backup_dict['NEW_LOG_FILE'] = NEW_LOG_FILE

    #find . -type f -newermt '7/11/2020' ! -path "./SIM/*" ! -path "./SNANA_TESTS/*"
    # end find_new_files

def read_backup_log(backup_dict):
    line_list = []
    with open(BACKUP_LOGFILE, "r") as f:
        for line in f:
            line_list.append(line)

    backup_yaml = yaml.safe_load("\n".join(line_list))
    backup_dict['backup_log_lines']   = line_list   # verbatim lines
    backup_dict['backup_log_yaml']    = backup_yaml

    # if backup log includes yaml block with current date,
    # re-write log EXCLUDING this block so that it can be
    # over-written. I.e., we don't want multiple yaml blocks
    # with the same date.
    tar_prefix = backup_dict['tar_prefix']
    word_stop  = tar_prefix + ':'  # stop writing log at this word
    flag_stop  = False 
    if tar_prefix in backup_yaml :
        print(f"\n  !! Remove already existing {tar_prefix} " \
              f"from {backup_logfile} !! \n")

        with open(BACKUP_LOGFILE, "w") as f:
            for line in line_list :
                line = line.rstrip("\n")
                if len(line) > 0 :
                    word_list = line.split()
                    if word_list[0] == word_stop: flag_stop = True
                if flag_stop is False : f.write(f"{line}\n")
    
    # end  read_backup_log

def update_backup_log(backup_dict) :
    # for name of new yaml block, remove .tar from tar_file name
    tar_file     = backup_dict['tar_file']
    TAR_FILE     = backup_dict['TAR_FILE']    # includes full path
    n_file_new   = backup_dict['n_file_new']  
    tar_size     = backup_dict['tar_size'] 
    tar_prefix   = backup_dict['tar_prefix']
    NEW_LOG_FILE = backup_dict['NEW_LOG_FILE']
    jdot            = tar_file.rindex('.')
    yaml_block_name = tar_file[0:jdot]

    with open(BACKUP_LOGFILE,"a") as b :
        b.write(f"{tar_prefix}: \n")
        b.write(f"   NFILE_NEW:     {n_file_new}   " \
                f"# new file count since last backup\n")
        b.write(f"   BACKUP_DATE:   {DATE_STAMP} \n")
        b.write(f"   BACKUP_OWNER:  {USERNAME} \n")
        b.write(f"   BACKUP_SIZE:   {tar_size}   # MB\n")
        b.write(f"   BACKUP_FILE:   {TAR_FILE}.gz\n")
        b.write(f"   ZENODO_UPLOAD: '*** READY(NOT_DONE) ***' \n")
        b.write(f"\n")

    print(f"\n Finished updating   \n     {BACKUP_LOGFILE}\n")

#
# ==================================================
# ==================================================
if __name__ == "__main__":

    print(f"\n")
    print(f" SNDATA_ROOT : {SNDATA_ROOT}")

    backup_dict = {}

    get_tar_file_name(backup_dict)

    # read backup log for all previous backups
    read_backup_log(backup_dict)

    # make list of all new files since last backup; 
    # return name of log file with list of new files.
    find_new_files(backup_dict)

    # create tar file
    create_tar_file(backup_dict)

    # update backup.log with info about current backup
    update_backup_log(backup_dict)

    print(f" Before public release, examine new files in\n" \
          f"     {backup_dict['NEW_LOG_FILE']} \n")

    sys.stdout.flush()
    exit(0)

    # end

