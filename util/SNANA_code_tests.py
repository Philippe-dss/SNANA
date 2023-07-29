#!/usr/bin/env python
#
# TO DO: make sure this works if TESTINPUT is not given
#        example task: NEARNBR_MAXFOM_DES
#
# Created May 2019, R. Kessler
# Regression testing on SNANA codes (replaces SNANA_tester.pl)
#
# Usage:
#   SNANA_code_tests.py REF  ! launch to get reference values
#   SNANA_code_tests.py      ! launch to test against reference values
#   SNANA_code_tests.py STOP ! send signal to STOP all jobs
#
# Internal usage:
#   SNANA_code_tests.py --cpunum <num> --logDir <dir>
#
#
#       HISTORY
# Sep 4 2019: run SNANA_SETUP for batch mode (bug fix)
#
# Mar 21 2020: in submitTasks_BATCH(), fix slashes in SNANA_SETUP
#              to work with sed.
#
# Jan 8 2021: print python version to SNANA.INFO
# Jan 27 2021: 
#   + replace WALLTIME key in SBATCH file
#   + fix bug to allow blank setup arg
#   + include RUNJOBS* in BACKUP_MISC.tar.gz
#
# Jun 14 2021: refactor using argparse and allow --snana_dir arg
#              to point to arbitrary user code.
#
# Jul 01 2021:
#   + write $HOST to HOST_MONITOR.INFO
#   + increas batch time from 20min to 1hr in case of batch delay
#
# Aug 17 2021: add arguments --nosubmit and --ncpu
#
# July 29 2023: write HOSTNAME in RUNJOB_CPU[nnn].LOG files
#               to help diagnose problems.
#

import os, sys, datetime, shutil, time, glob
import subprocess, argparse


# ===============================================
# define hard-wired globals up here so that they are
# easy to find in case modification is needed.

SNANA_DIR        = os.environ['SNANA_DIR']
SNANA_TESTS_DIR  = os.environ['SNANA_TESTS']
HOSTNAME         = os.uname()[1]  
TASK_DIR         = f"{SNANA_TESTS_DIR}/tasks"
INPUT_DIR        = f"{SNANA_TESTS_DIR}/inputs"
LOG_TOPDIR       = f"{SNANA_TESTS_DIR}/logs"
USERNAME         = os.environ['USER']
USERNAME_TAG     = USERNAME[0:4]       # suffix for logdir name
LIST_TESTS_FILE_DEFAULT = f"{SNANA_TESTS_DIR}/SNANA_code_tests.LIST"
CPU_FILE_DEFAULT        = 'CPU_ASSIGN.DAT'  
RESULT_TASKS_FILE       = 'RESULTS_TASKS.DAT'
RESULT_DIFF_FILE        = 'RESULTS_DIFF.DAT'
SNANA_INFO_FILE         = 'SNANA.INFO'
STOP_FILE               = f"{LOG_TOPDIR}/STOP"
MEMORY                  = 2000   # Mb
WALLTIME_MAX            = "01:00:00"    # 1 hr to allow queue delay

# ========================================================
def parse_args():

    parser = argparse.ArgumentParser()

    msg = "Build reference"
    parser.add_argument("--ref", help=msg, action="store_true")

    msg = "test against reference (default with no args)"
    parser.add_argument("--test", help=msg, action="store_true")

    msg = f"private list of tests (replaces {LIST_TESTS_FILE_DEFAULT}"
    parser.add_argument("-l", "--list_file", help=msg, type=str, 
                        default=LIST_TESTS_FILE_DEFAULT)

    msg = f"private snana code directory (replaces {SNANA_DIR})"
    parser.add_argument("--snana_dir", help=msg, type=str, default=None)

    msg = f"Override number of CPUs in batch file"
    parser.add_argument("--ncpu", help=msg, type=int, default=-1)

    msg = "INTERNAL ARG: CPU number"
    parser.add_argument("--cpunum", help=msg, type=int, default=-9)

    msg = "INTERNAL ARG: log dir"
    parser.add_argument("--logdir", help=msg, type=str,  default=None)

    msg = "only compare TEST vs. REF (do not submit jobs)"
    parser.add_argument("--compare_only", help=msg, action="store_true")

    msg = "stop this script"
    parser.add_argument("--stop", help=msg, action="store_true")

    msg = "prepare jobs, but do not submit"
    parser.add_argument("--nosubmit", help=msg, action="store_true")

    msg = "debug"
    parser.add_argument("--debug", help=msg, action="store_true")

    args = parser.parse_args()

    # - - - - -
    # tack on a few extras
    # if --ref is not given, set test mode to true
    if args.ref is False:  
        args.test    = True
        args.REFTEST = "TEST"
        args.reftest = "--test"
    else:
        args.REFTEST = "REF"
        args.reftest = "--ref"

    if args.snana_dir is None: 
        args.snana_dir = SNANA_DIR

    args.SCRIPTNAME = sys.argv[0]

    # - - - - -

    print(f" Inputs: ")
    print(f"   SNANA_DIR     =  {args.snana_dir} ")
    print(f"   SNANA_TESTS   =  {SNANA_TESTS_DIR} ")
    print(f"   REF or TEST   =  {args.REFTEST} ")

    if args.cpunum >= 0 :
        print(f"   cpunum        =  {args.cpunum} " )

    if args.logdir is not None :
        print(f"   logdir        =  {args.logdir} "   )

    if args.list_file is not None:
        print(f"   list_file     =  {args.list_file} " )

    if args.compare_only is True:
        print("\n !!! DEBUG MODE: COMPARE TEST vs. REF only !!! ")

    return args

# ====================================
def get_LOGDIR_REF():
    # assume most recent REF_* directory is the reference;
    # read list of completed tasks and their results.

    sdirlist = os.listdir(LOG_TOPDIR)
    LOGDIR_REF = None

    # loop over subdirs; use last one in alphabetical list
    for sdir in sorted(sdirlist):
        dir_name = f"{LOG_TOPDIR}/{sdir}"
        if sdir[0:3] == 'REF' and os.path.isdir(dir_name) is True : 
            LOGDIR_REF = dir_name

    if LOGDIR_REF is None :
        msg = '\n ABORT: Could not find REF directory.'
        sys.exit(msg)

    return LOGDIR_REF

# ========================================
def read_SNANA_INFO(LOGDIR):

    snana_file = f"{LOGDIR}/{SNANA_INFO_FILE}"
    with open(snana_file, 'rt') as f:
        lineList = f.readlines()    

    for line in lineList:          
        line  = line.rstrip()  # remove trailing space and linefeed
        words = line.split()
        if len(words) == 0 : continue

        if words[0] == "SNANA_VERSION:" :
            SNANA_VERSION = words[1]
        elif words[0] == "SNANA_DIR:" :
            SNANA_DIR     = words[1]

    return(SNANA_VERSION,SNANA_DIR)

# ========================================
def get_RESULTS_TASKS(LOGDIR):

    # Read task-result file in LOGDIR, and return info dictionary
    # Also read SNANA.INFO file

    LINE_LIST        = []
    TASKNAME_LIST    = []
    TASKNUM_LIST     = []  # list of NUM only
    TASKRESULT_LIST  = []  # list of NAMEs only
    TASKNUMNAME_LIST = []  # list of TASKnnn-[NAME]

    SNANA_DIR     = None
    SNANA_VERSION = None

    # scoop up everything in RESULTS file
    result_file = f"{LOGDIR}/{RESULT_TASKS_FILE}"
    with open(result_file, 'rt') as f:
        lineList = f.readlines()    

    for line in lineList:          
        line  = line.rstrip()  # remove trailing space and linefeed
        words = line.split()
        if len(words) == 0 :   continue
        wd0   = words[0]
        if wd0[0:4] != 'TASK' : continue
        TASKNUM    = int(wd0[4:7])  # strip NUM from TASK[NUM]
        TASKNAME   = wd0[8:]        # strip name from TASKnnn-[TASKNAME]
        TASKRESULT = ' '.join(words[2:])  # skip colon
        LINE_LIST.append(line)
        TASKNAME_LIST.append(TASKNAME)
        TASKNUM_LIST.append(TASKNUM)
        TASKRESULT_LIST.append(TASKRESULT)
        TASKNUMNAME_LIST.append(wd0)

#       print(" xxx %s -> NUM=%d RES='%s' " % (words[0],TASKNUM,TASKRESULT))

    ntask = len(TASKNAME_LIST)
    print(f" Stored {ntask} task results " )
    sys.stdout.flush()

    # - - - - - - - - - - - - - - -
    # read SNANA info
    (SNANA_VERSION,SNANA_DIR) = read_SNANA_INFO(LOGDIR)

    # - - - - - - - - - - - - - - -
    RESULTS_INFO = {
        "LOGDIR"           : LOGDIR,
        "LINE_LIST"        : LINE_LIST,
        "TASKNAME_LIST"    : TASKNAME_LIST,
        "TASKNUM_LIST"     : TASKNUM_LIST,
        "TASKNUMNAME_LIST" : TASKNUMNAME_LIST,
        "TASKRESULT_LIST"  : TASKRESULT_LIST,
        "SNANA_DIR"        : SNANA_DIR,
        "SNANA_VERSION"    : SNANA_VERSION,
        }

    return RESULTS_INFO


# ===================================
def set_task_order(TASKNAME_LIST):

    # return TASKORDER_LIST to priortize SIMGEN jobs to run first.

    NTASK          = len(TASKNAME_LIST)
    TASKORDER_LIST = [-9]*NTASK
    nuse           = [0]*NTASK
    order = 0; itask=0
    for TASKNAME in TASKNAME_LIST :
        if TASKNAME.startswith("SIMGEN") is True:
            TASKORDER_LIST[order] = itask
            order += 1
            nuse[itask] += 1
        itask += 1

    # loop again and set order for those not already on SIMGEN list
    itask = 0
    for TASKNAME in TASKNAME_LIST :
        if  nuse[itask] == 0 :
            TASKORDER_LIST[order] = itask
            order += 1
            nuse[itask] += 1
        itask += 1

    # sanity check that every task got flaged once
    for order in range(0,NTASK):
        itask = TASKORDER_LIST[order]
        if itask < 0 or itask >= NTASK :
            msg = f" ABORT: invalid itask={itask} for order={order}"
            sys.exit(msg)     
#        TASKNAME = TASKNAME_LIST[itask]
#        print(' xxx itask=%3d -> order=%3d (%s) ' % (itask,order,TASKNAME) )

    for itask in range(0,NTASK) :
        n = nuse[itask]
        TASKNAME = TASKNAME_LIST[itask]
        if n != 1:
            msg = f" ABORT: itask={itask} ({TASKNAME}) used {n}" \
                  f"times in ordering\n\t" \
                  f" Something is really messed up."
            sys.exit(msg) 

    return TASKORDER_LIST

# ===================================
def parse_listfile(INPUTS, RESULTS_INFO_REF):

    LIST_FILE = INPUTS.list_file
    if os.path.isfile(LIST_FILE) is False  :
        msg = f"ERROR: Cannot find list file of tests: \n  {LIST_FILE}"
        sys.exit(msg)

    REF_SNANA_SETUP   = ''
    TEST_SNANA_SETUP  = ''
    SNANA_SETUP       = ''
    SSH_NODES         = []
    BATCH_INFO        = []
    RUN_SSH           = False
    RUN_BATCH         = False
    NTASK             = 0 
    TASKNAME_LIST     = []
    TASKNUM_LIST      = []
    
    DOREF   = INPUTS.ref
    DOTEST  = INPUTS.test
    REFTEST = INPUTS.REFTEST

    NERR_TASKNUM = 0  # used only for TEST mode

    # if this is test mode, get REF info, mainlly list of TASKS
    # to compare
    if DOTEST is True :
        LOGDIR_REF        = RESULTS_INFO_REF["LOGDIR"]
        REF_TASKNAME_LIST = RESULTS_INFO_REF["TASKNAME_LIST"]
        REF_TASKNUM_LIST  = RESULTS_INFO_REF["TASKNUM_LIST"]
        print(f" Select REF logdir: {LOGDIR_REF} " )


    with open(LIST_FILE, 'rt') as f:
        lineList = f.readlines()

    for line in lineList:          
        line = line.rstrip()  # remove trailing space and linefeed
        words = line.split()
        lw    = len(words)
        if lw == 0 :
            continue
        if  words[0][0:1] == '#' :
            continue   # skip comment lines
        elif  words[0] == 'REF_SNANA_SETUP:' :
            REF_SNANA_SETUP = ' '.join(words[1:])
        elif words[0] == 'TEST_SNANA_SETUP:' :
            TEST_SNANA_SETUP = ' '.join(words[1:])
        elif  words[0] == 'SSH_NODES:' :
            SSH_NODES = words[1:]
            NCPU      = len(SSH_NODES)
            RUN_SSH   = True
        elif words[0] == 'BATCH_INFO:' :
            BATCH_INFO = words[1:]
            if INPUTS.ncpu > 0 :
                NCPU = INPUTS.ncpu  # command line override (Aug 17, 2021
            else:
                NCPU       = int(BATCH_INFO[2])
            RUN_BATCH  = True 
        elif words[0] == 'TEST:' :
            NTASK += 1
            TASKNAME = words[1]
            TASKNAME_LIST.append(TASKNAME)
            if DOREF  :
                TASKNUM = NTASK
            else:
                # for TEST, fetch TASKNUM from REF job
                if TASKNAME in REF_TASKNAME_LIST :
                    itask_ref = REF_TASKNAME_LIST.index(TASKNAME)
                    TASKNUM   = REF_TASKNUM_LIST[itask_ref]
                else:
                    print(' ERROR: TASK %s not found in REF' % TASKNAME)
                    NERR_TASKNUM += 1
                    TASKNUM = -9

            TASKNUM_LIST.append(TASKNUM)

        elif words[0] == 'END:':
            break


    if ( NERR_TASKNUM > 0 ) :
        msg = f" ABORT: {NERR_TASKNUM} TASKS not in REF"
        sys.exit(msg)


    # ----------------------------------
    # determine process order so that SIMGEN_XXX jobs go first
    TASKORDER_LIST = set_task_order(TASKNAME_LIST)

    # pick which snana-setup to use
    if DOTEST is True :
        SNANA_SETUP = TEST_SNANA_SETUP
    else:
        SNANA_SETUP = REF_SNANA_SETUP

    # parse contents of LIST_FILE and return contents in dictionary
    CONTENTS = {
        "LIST_FILE"        :   LIST_FILE,
        "REFTEST"          :   REFTEST,
        "REF_SNANA_SETUP"  :   REF_SNANA_SETUP,
        "TEST_SNANA_SETUP" :   TEST_SNANA_SETUP,
        "SNANA_SETUP"      :   SNANA_SETUP,
        "SSH_NODES"        :   SSH_NODES,
        "BATCH_INFO"       :   BATCH_INFO, 
        "RUN_SSH"          :   RUN_SSH,
        "RUN_BATCH"        :   RUN_BATCH,
        "NCPU"             :   NCPU,
        "NTASK"            :   NTASK,
        "TASKNAME_LIST"    :   TASKNAME_LIST,
        "TASKNUM_LIST"     :   TASKNUM_LIST,
        "TASKORDER_LIST"   :   TASKORDER_LIST,
        }

    return CONTENTS
    # end parse_listfile

# ============================================
def parse_taskfile(TASKFILE):
    # parse user TASKFILE (read from listFile) and 
    # return dictionary of contents
    CONTENTS     = []
    TESTINPUT    = ''    # name of input file(s)
    TESTJOB      = ''    # job name; e..g, snlc_sim.exe
    TESTJOB_ARGS = ''    # optional arguments to TESTJOB
    TESTNAME     = ''    # name of test quantite; e.g., 'Efficiency'
    TESTRESULT   = ''    # grep command for log file  
    WORDNUM      = ''    # word range to extract from grep string
    DEPENDENCY   = None  # must wait for this other task to finish

    with open(TASKFILE, 'rt') as f:
        lineList = f.readlines()

    for line in lineList:          
        line = line.rstrip()  # remove trailing space and linefeed
        words = line.split()
        lw    = len(words)
        if lw == 0 :
            continue
        if words[0][0:1] == '#' :
            continue   # skip comment lines
        elif words[0] == 'TESTINPUT:' :
            TESTINPUT = words[1:]
        elif words[0] == 'TESTJOB:' :
            TESTJOB = words[1]
        elif words[0] == 'TESTJOB_ARGS:' :
            TESTJOB_ARGS = ' '.join(words[1:])
        elif words[0] == 'TESTNAME:' :
            TESTNAME = words[1]
        elif words[0] == 'TESTRESULT:' :
            TESTRESULT = ' '.join(words[1:])
        elif words[0] == 'WORDNUM:' :
            WORDNUM = words[1].split('-')
        elif words[0] == 'DEPENDENCY:' :
            DEPENDENCY = words[1]

    CONTENTS = {
        "TESTINPUT"     : TESTINPUT,
        "TESTJOB"       : TESTJOB,
        "TESTJOB_ARGS"  : TESTJOB_ARGS,
        "TESTNAME"      : TESTNAME,
        "TESTRESULT"    : TESTRESULT,
        "WORDNUM"       : WORDNUM,
        "DEPENDENCY"    : DEPENDENCY,
        }
    return CONTENTS

# =======================================
def check_listfile_contents(LIST_FILE_INFO):

    # run sanity checks on contents of list file, and abort
    # if anything is clearly going to fail later.
    #
    
    NTASK           = LIST_FILE_INFO["NTASK"] 
    LIST_FILE       = LIST_FILE_INFO["LIST_FILE"] 
    REFTEST         = LIST_FILE_INFO["REFTEST"]
    TASKNAME_LIST   = LIST_FILE_INFO["TASKNAME_LIST"]
    TASKNUM_LIST    = LIST_FILE_INFO["TASKNUM_LIST"]
    ABORT_FLAG       = False

    if NTASK == 0 :
        msg = f" ABORT: found no tasks in\n {LIST_FILE}"
        sys.exit(msg)

    # check for  missing task files and missing input files
    # specified by task
    NOTFOUND_TASK   = 0  # missing task files
    NOTFOUND_INPUT  = 0  # missing input files (code arg)
    NOTFOUND_DEPEND = 0  # missing task dependencies
    NDUPLICATE      = 0  # duplicate tasks

    itask = 0
    for  TASKNAME in TASKNAME_LIST :
        TASKNUM = TASKNUM_LIST[itask]
        TASKFILE = ('%s/%s' % (TASK_DIR,TASKNAME) )

        itask += 1
        comment_substring = f"{REFTEST} TASKNUM {TASKNUM:03d} : " \
                            f"file={TASKNAME}"
        if os.path.isfile(TASKFILE) is False :
            NOTFOUND_TASK += 1 ; ABORT_FLAG = True
            print(f" ERROR: cannot find {comment_substring}")
            continue
        else:
            print(f" Found {comment_substring}")
            sys.stdout.flush()

        # parse TASKFILE contents, and make sure things exist.
        CONTENTS_TASK = parse_taskfile(TASKFILE)

        TESTINPUT       = CONTENTS_TASK["TESTINPUT"]
        TASKNAME_DEPEND = CONTENTS_TASK["DEPENDENCY"]

        for infile in TESTINPUT :
            INFILE = f"{INPUT_DIR}/{infile}"
            if os.path.isfile(INFILE) is False :
                print(f"\t--> ERROR: cannot find TESTINPUT file='{TESTINPUT}'"\
                      f"\n\t\t for task {TASKNAME}")
                NOTFOUND_INPUT += 1
                ABORT_FLAG = True
    
        # check DEPENDENCY
        if TASKNAME_DEPEND is not None :
            if TASKNAME_DEPEND not in TASKNAME_LIST :
                NOTFOUND_DEPEND += 1 ; ABORT_FLAG = True
                print(f"\t--> ERROR: DEPENDENCY-Task {TASKNAME_DEPEND} "\
                      f"not defined. ")   


        # check for duplicates 
        NFIND = TASKNAME_LIST.count(TASKNAME)
        if NFIND > 1 :
            print("\t--> DUPLICATE ERROR: Task {TASKNAME} " \
                  f"occurs {NFIND} times.")
            NDUPLICATE += 1 ; ABORT_FLAG = True

    # =================================================
    # done looping over task files; abort on error

    print(' ')
    if NOTFOUND_TASK > 0 :
        print(f" ERROR: {NOTFOUND_TASK} missing TASK files.")

    if NOTFOUND_INPUT > 0 :
        print(f" ERROR: {NOTFOUND_INPUT} missing INPUT files.") 

    if NOTFOUND_DEPEND > 0 :
        print(f" ERROR: {NOTFOUND_DEPEND} missing DEPENDENCY tasks.")

    if NDUPLICATE > 0 :
        NDUPLICATE /= 2
        print(f" ERROR: {NDUPLICATE} duplicate tasks.") 

    if ABORT_FLAG is True :
        sys.exit(' ABORT ')

    return


# =====================================
def parse_cpufile(INPUTS,CPUNUM_REQ):

    LOGDIR    = INPUTS.logdir
    CPU_FILE  = f"{LOGDIR}/{CPU_FILE_DEFAULT}"

    TASK      = []
    TASKNUM   = []
    CPUNUM    = []
    PREFIX    = []
    TASKFILE  = []
    LOGFILE   = []
    DONEFILE  = []

    NTASK_TOT = 0    # total number of tasks
    NTASK_REQ = 0    # number of requested tasks for CPUNUM

    with open(CPU_FILE, 'rt') as f:
        lineList = f.readlines()

    for line in lineList:          
        line  = line.rstrip()  # remove trailing space and linefeed
        words = line.split()
        lw    = len(words)
        if lw == 0 :
            continue        
        if words[0] == 'TASK:' :
            tmp_numcpu   = int(words[1])
            tmp_numtask  = int(words[2])
            tmp_task     = words[3]
            tmp_prefix   = f"TASK{tmp_numtask:03d}"
            tmp_taskfile = f"{TASK_DIR}/{tmp_task}"
            tmp_logfile  = f"{LOGDIR}/{tmp_prefix}_{tmp_task}.LOG"
            tmp_donefile = f"{LOGDIR}/{tmp_prefix}_{tmp_task}.DONE"

            TASK.append(tmp_task)
            TASKNUM.append(tmp_numtask)
            CPUNUM.append(tmp_numcpu)
            PREFIX.append(tmp_prefix)
            TASKFILE.append(tmp_taskfile)
            DONEFILE.append(tmp_donefile)
            LOGFILE.append(tmp_logfile)

            NTASK_TOT += 1
            if CPUNUM_REQ == tmp_numcpu :   NTASK_REQ += 1

    CPU_TASKLIST = {
        "NTASK_TOT"    :  NTASK_TOT,
        "NTASK_REQ"    :  NTASK_REQ,
        "TASK"         :  TASK,
        "TASKNUM"      :  TASKNUM,
        "CPUNUM"       :  CPUNUM,
        "PREFIX"       :  PREFIX,
        "TASKFILE"     :  TASKFILE,
        "DONEFILE"     :  DONEFILE,
        "LOGFILE"      :  LOGFILE,
        }
    
    return CPU_TASKLIST


# ==============================================
def copy_input_files(INPUTS, PREFIX, *TESTINPUT):

    # Copy first input to logdir and tack on PREFIX = TASKnnn_.
    # If not HBOOK or ROOT file,  use 'sed' to copy with 
    # XXX -> REF or TEST substution.
    # If HBOOK or ROOT file, just do regular copy.


    if ( not TESTINPUT ):
        print (' No TESTINPUT --> no input files to copy. ')
        return

    REFTEST     = INPUTS.REFTEST
    LOGDIR      = INPUTS.logdir 
    infile_orig = TESTINPUT[0]
    infile_copy = f"{PREFIX}_{infile_orig}"
    INFILE_ORIG = f"{INPUT_DIR}/{infile_orig}"
    INFILE_COPY = f"{LOGDIR}/{infile_copy}"

    print(f"\t Copy input file {infile_orig}")

    if ".HBOOK" in INFILE_ORIG  or  ".ROOT" in INFILE_ORIG :
        # regular copy
        CMD_COPY = f"cp {INFILE_ORIG} {INFILE_COPY}"
    else:
        # sed with substitution of XXX -> REF or TEST
        CMD_COPY = f"sed -e \'s/XXX/{REFTEST}/g\'  {INFILE_ORIG} " \
                   f" > {INFILE_COPY}" 
    os.system(CMD_COPY)

    # make sure INFILE_COPY is created; if not, abort
    if os.path.isfile(INFILE_COPY) is False :
        msg = f"\n ABORT: Unable to create input file with" \
              f"\n\t {CMD_COPY}"
        sys.exit(msg)

    # copy remaining input files (without alteration) if more than
    # one input file is specified.
    for ifile in range(1,len(TESTINPUT)):
        infile_orig = TESTINPUT[ifile]
        print(f"\t Copy supplemental input file {infile_orig}")
        INFILE_ORIG = f"{INPUT_DIR}/{infile_orig}"
        INFILE_COPY = f"{LOGDIR}/{infile_orig}"
        CMD_cp      = f"cp {INFILE_ORIG} {INFILE_COPY}"
        os.system(CMD_cp)

    # return input file name with prefix used for task
    return(infile_copy)

# ==============================================
def execute_task(itask, CPU_TASKLIST, INPUTS) :

    # execute job, grep out result, and  create DONE file with result.

    TASKNUM  = CPU_TASKLIST["TASKNUM"][itask]
    TASK     = CPU_TASKLIST["TASK"][itask]
    PREFIX   = CPU_TASKLIST["PREFIX"][itask]
    TASKFILE = CPU_TASKLIST["TASKFILE"][itask]
    DONEFILE = CPU_TASKLIST["DONEFILE"][itask]
    LOGFILE  = CPU_TASKLIST["LOGFILE"][itask]
    REFTEST  = INPUTS.REFTEST
    LOGDIR   = INPUTS.logdir
    TASKNUMNAME = f"{PREFIX}_{TASK}"

    # if done file already exists bail
    if os.path.isfile(DONEFILE)  :        return 0

    CONTENTS_TASK = parse_taskfile(TASKFILE)

    # check dependency 
    TASK_DEPEND = CONTENTS_TASK["DEPENDENCY"]
    if TASK_DEPEND is not None  :  
        itask_depend    = CPU_TASKLIST["TASK"].index(TASK_DEPEND)
        DONEFILE_DEPEND = CPU_TASKLIST["DONEFILE"][itask_depend]
        PREFIX_DEPEND   = CPU_TASKLIST["PREFIX"][itask_depend]
        if os.path.isfile(DONEFILE_DEPEND) is False : 
            print(' Delay   %s_%s (waiting for %s_%s) ' %
                  (PREFIX,TASK, PREFIX_DEPEND,TASK_DEPEND) )
            sys.stdout.flush()
            return 0

    # run the job using os.system    
    print(' Process %s_%s ' % (PREFIX,TASK) )
    sys.stdout.flush()
#    sys.stdout.flush()
    TESTJOB       = CONTENTS_TASK["TESTJOB"]
    TESTJOB_ARGS  = CONTENTS_TASK["TESTJOB_ARGS"]
    TESTINPUT     = CONTENTS_TASK["TESTINPUT"]
    TESTRESULT    = CONTENTS_TASK["TESTRESULT"]
    TESTNAME      = CONTENTS_TASK["TESTNAME"]
    GREP_WD0      = int(CONTENTS_TASK["WORDNUM"][0])
    GREP_WD1      = int(CONTENTS_TASK["WORDNUM"][1]) + 1

    # copy input file(s) to output log dir, and append PREFIX to input name
    # return arg 'input_copy' includes TASK[nnn] PREFIX.
    infile_copy = copy_input_files(INPUTS,PREFIX,*TESTINPUT)

    # construct job name with arguments
    if len(TESTJOB_ARGS) > 1 :
        # if TESTJOB_ARGS contains "TESTINPUT" string, substitute
        # the actual input file name that includes TASKnnn prefix
        if "TESTINPUT" in TESTJOB_ARGS:
            TESTJOB_ARGS = TESTJOB_ARGS.replace("TESTINPUT", infile_copy)

        job_plus_args = f"{TESTJOB} {TESTJOB_ARGS}"
    else:
        job_plus_args = f"{TESTJOB} {infile_copy}"


    # run full job, include 'cd' and pipe to LOGFILE
    CMD_JOB     = f"cd {LOGDIR}; {job_plus_args} >& {LOGFILE}"
    os.system(CMD_JOB)

    # - - - - - - - - - - - - - - - - 
    # single task has finished
    # check for ABORT, then check for no result-string, then result

    if ' ABORT ' in open(LOGFILE).read() :
        DONE_STRING = ('%-40s:  ABORT' % (TASKNUMNAME) )
    else:
        # grep out results
        CMD_grep = TESTRESULT.replace("logFile",LOGFILE)
        CMD_grep = f"{CMD_grep} | tail -1"
        resultLine = subprocess.check_output(CMD_grep,shell=True).rstrip()
        if sys.version_info > (3,0):
            resultLine = resultLine.decode('utf-8')

        if ( len(resultLine) > 0 ) :
            # split resultLine into word array, then select word-range,
            # then rejoin word-range into single string
            resultLine  = (resultLine.strip()).split()
            resultLine  = ' '.join(resultLine[GREP_WD0:GREP_WD1])
            DONE_STRING = ('%-40s: %s = %s' % 
                           (TASKNUMNAME, TESTNAME, resultLine) )
        else:
            DONE_STRING = ('%-40s: BLANK (grep failed, no abort) ' % 
                           (TASKNUMNAME) )

    # finally, write DONE_STRING to the DONE file
    f = open(DONEFILE, 'wt')
    f.write(f"{DONE_STRING}\n")
    f.close()

    return 1

# ============================
def runTasks_driver(INPUTS):

    # process all tasks for one CPU (CPUNUM_REQ)

    CPUNUM_REQ      = INPUTS.cpunum
    CPU_TASKLIST    = parse_cpufile(INPUTS,CPUNUM_REQ)

    NTASK_TOT     = CPU_TASKLIST["NTASK_TOT"]  # total number of tasks
    NTASK_REQ     = CPU_TASKLIST["NTASK_REQ"]  # number for CPUNUM
    TASKNUM       = CPU_TASKLIST["TASKNUM"]
    CPUNUM        = CPU_TASKLIST["CPUNUM"]
    NDONE_REQ     = 0

    print(f" Begin execution of {NTASK_REQ} tasks for CPUNUM={CPUNUM_REQ}")
    print(f" HOSTNAME: {HOSTNAME}")

    sys.stdout.flush()

    while NDONE_REQ < NTASK_REQ :
        for itask in range(0,NTASK_TOT) :
            if os.path.isfile(STOP_FILE) :
                sys.exit()
            if  CPUNUM[itask] == CPUNUM_REQ  :
                NDONE_REQ += execute_task(itask,CPU_TASKLIST,INPUTS)
                time.sleep(2)

    return

# ====================
def make_logdir(INPUTS):

    DOREF          = INPUTS.ref
    DOCOMPARE_ONLY = INPUTS.compare_only
    REFTEST        = INPUTS.REFTEST
    DEBUG_FLAG     = INPUTS.debug

    tnow   = datetime.datetime.now()
    TSTAMP = ('%4.4d%2.2d%2.2d-%2.2d%2.2d' % 
              (tnow.year, tnow.month, tnow.day, tnow.hour, tnow.minute) )
    
    if DEBUG_FLAG is True:
        TSTAMP = 'DEBUG' 

    logDir = f"{REFTEST}_{TSTAMP}_{USERNAME_TAG}"
    LOGDIR = f"{LOG_TOPDIR}/{logDir}"

    if DOCOMPARE_ONLY is True :
        return LOGDIR

    # - - - - - - - - - - - - - - - - - 
    print(f" Create log-dir = \n\t {LOGDIR} \n")
    sys.stdout.flush()

    if os.path.exists(LOGDIR) :
        shutil.rmtree(LOGDIR)

    os.mkdir(LOGDIR)

    return LOGDIR

# ===================================
def  make_cpufile(CPU_FILE,LIST_FILE_INFO):

    f = open(CPU_FILE, 'wt')
    f.write('VARNAMES: CPUNUM TASKNUM  TASK \n')
    
    NCPU           = LIST_FILE_INFO["NCPU"]
    NTASK          = LIST_FILE_INFO["NTASK"]
    TASKNAME_LIST  = LIST_FILE_INFO["TASKNAME_LIST"]
    TASKNUM_LIST   = LIST_FILE_INFO["TASKNUM_LIST"]
    TASKORDER_LIST = LIST_FILE_INFO["TASKORDER_LIST"]

    cpunum         = 0  # CPU number
    for order in range (0,NTASK):
        itask    = TASKORDER_LIST[order]
        TASK     = TASKNAME_LIST[itask]
        TASKNUM  = TASKNUM_LIST[itask]
        f.write(f"TASK: {cpunum:3d} {TASKNUM:3d}   {TASK} \n")
        cpunum  += 1
        if cpunum == NCPU :  cpunum = 0
        
    f.close()
    return

# =========================================
def submitTasks_SSH(INPUTS,LIST_FILE_INFO,SUBMIT_INFO) :

    # launch SSH jobs
    SCRIPTNAME     = INPUTS.SCRIPTNAME
    REFTEST        = INPUTS.REFTEST   # REF or TEST 
    reftest        = INPUTS.reftest   # --ref or --test
    SNANA_SETUP    = LIST_FILE_INFO["SNANA_SETUP"]
    SSH_NODES      = LIST_FILE_INFO["SSH_NODES"]
    NCPU           = LIST_FILE_INFO["NCPU"]
    LOGDIR         = SUBMIT_INFO["LOGDIR"]

    # loop over CPUs and launch each SSH job
    for cpunum in range(0,NCPU) :

        node        =  SSH_NODES[cpunum]
        logfile_cpu = f"{LOGDIR}/RUNJOB_CPU{cpunum:03d}.LOG"

        cmd_ssh   = f"ssh -x {node}"
        cmd_cd    = f"cd {LOGDIR}"
        cmd_job   = f"{SCRIPTNAME} {reftest} --cpunum {cpunum}  " \
                    f"--logdir {LOGDIR} > {logfile_cpu}"
 
        # on first job, run snana.exe to leave version info
        if cpunum == 0 :
            cmd_snana_version  = f"snana.exe --snana_version > " \
                                 f"{SNANA_INFO_FILE}"

            cmd_python_version = f"python    --version       >> " \
                                 f"{SNANA_INFO_FILE}"

            cmd_job = f"{cmd_snana_version} ; {cmd_python_version} ; {cmd_job}"

        # - - - - 
        if INPUTS.nosubmit is False :
            cmd = f"{cmd_ssh}  \"{SNANA_SETUP}; {cmd_cd} ; {cmd_job}\" & "
            print(f" Launch tasks for CPU {cpunum:3d}")
            sys.stdout.flush()
            os.system(cmd)

    return
    # end submitTasks_SSH

# =========================================
def submitTasks_BATCH(INPUTS,LIST_FILE_INFO,SUBMIT_INFO) :
    # launch batch jobs
    SCRIPTNAME     = INPUTS.SCRIPTNAME
    REFTEST        = INPUTS.REFTEST
    reftest        = INPUTS.reftest   # --ref or --test
    SNANA_SETUP    = LIST_FILE_INFO["SNANA_SETUP"]
    BATCH_INFO     = LIST_FILE_INFO["BATCH_INFO"]
    NCPU           = LIST_FILE_INFO["NCPU"]
    LOGDIR         = SUBMIT_INFO["LOGDIR"]

    BATCH_SUBMIT_COMMAND = BATCH_INFO[0]
    BATCH_TEMPLATE_FILE  = BATCH_INFO[1]

    SNANA_SETUP_forSed = SNANA_SETUP.replace('/','\/')
    if len(SNANA_SETUP_forSed) == 0:
        SNANA_SETUP_forSed = 'echo "No setup"'

    # Jun 2021: check user snana_dir
    snana_dir = os.path.expandvars(INPUTS.snana_dir)
    if snana_dir != SNANA_DIR :
        path_list = f"{snana_dir}/bin:{snana_dir}/util:\$PATH"
        SNANA_SETUP_forSed = f"export SNANA_DIR={snana_dir} ; " \
                             f"export PATH={path_list}"
        SNANA_SETUP_forSed  = SNANA_SETUP_forSed.replace('/','\/')
        #print(f" xxx SNANA_SETUP_forSed = {SNANA_SETUP_forSed}")

    for cpunum in range(0,NCPU) :
        batch_runfile = f"RUNJOBS_CPU{cpunum:03d}.BATCH"
        batch_logfile = f"RUNJOBS_CPU{cpunum:03d}.BATCH-LOG"
        BATCH_RUNFILE = f"{LOGDIR}/{batch_runfile}"

        cmd_job  = f"{SCRIPTNAME} {reftest} --cpunum {cpunum}  " \
                   f"--logdir {LOGDIR}"
        cmd_job  = cmd_job.replace('/','\/')

        # on first job, run snana.exe to leave version info
        if cpunum == 0 :
            cmd_snana_version = f"snana.exe --snana_version " \
                                f"> {SNANA_INFO_FILE}"
            cmd_python_version = f"python --version          " \
                                 f">> {SNANA_INFO_FILE}"
            cmd_job = f"{cmd_snana_version} ; {cmd_python_version} ; " \
                      f"{cmd_job}"

        # construct sed command to replace strings in batch-template
        cmd_sed  = 'sed  '
        cmd_sed += f"-e 's/REPLACE_NAME/CodeTest_CPU{cpunum:03d}/g' "
        cmd_sed += f"-e 's/REPLACE_LOGFILE/{batch_logfile}/g' "
        cmd_sed += f"-e 's/REPLACE_MEM/{MEMORY}/g' "
        cmd_sed += f"-e 's/REPLACE_WALLTIME/{WALLTIME_MAX}/g' "
        cmd_sed += f"-e 's/REPLACE_JOB/{SNANA_SETUP_forSed} ; {cmd_job}/g' " 
        cmd_sed += f" {BATCH_TEMPLATE_FILE} > {BATCH_RUNFILE}"
        #print(f" xxx sed = {cmd_sed} ")
        os.system(cmd_sed)

        # make sure batch file was created 
        if os.path.isfile(BATCH_RUNFILE) is False  :
            msg = f" ABORT: could not create BATCH_RUNFILE = \n" \
              f" {BATCH_RUNFILE}"
            sys.exit(msg)

        # launch the job
        cmd_submit = f"cd {LOGDIR} ; {BATCH_SUBMIT_COMMAND} {batch_runfile}"

        if INPUTS.nosubmit :
            print(f" Skip {BATCH_SUBMIT_COMMAND} {batch_runfile}")
            sys.stdout.flush()
        else:
            os.system(cmd_submit)


    return
    # end submitTasks_BATCH

#    sys.exit('\n\n xxx Bye bye from submitTasks_BATCH' )

# ===================================
def submitTasks_driver(INPUTS, LIST_FILE_INFO):

    print('\n Prepare to Submit tasks ')
    sys.stdout.flush()
    SCRIPTNAME     = INPUTS.SCRIPTNAME
    DOCOMPARE_ONLY = INPUTS.compare_only
    REFTEST        = INPUTS.REFTEST
    SSH_NODES      = LIST_FILE_INFO["SSH_NODES"]
    BATCH_INFO     = LIST_FILE_INFO["BATCH_INFO"]
    RUN_SSH        = LIST_FILE_INFO["RUN_SSH"]
    RUN_BATCH      = LIST_FILE_INFO["RUN_BATCH"]
    NCPU           = LIST_FILE_INFO["NCPU"]
    NTASK          = LIST_FILE_INFO["NTASK"]

    # construct name of log dir under LOG_TOPDIR
    LOGDIR = make_logdir(INPUTS)

    # remove relic STOP-file flag if it's still there
    if os.path.isfile(STOP_FILE) :
        cmd_rm = f"rm {STOP_FILE}"
        os.system(cmd_rm)

    # - - - - - - - - - - - - - - 
    # get file nanme with CPU assignments
    CPU_FILE =  f"{LOGDIR}/{CPU_FILE_DEFAULT}"
    
    SUBMIT_INFO = {
        "NTASK"    : NTASK,
        "LOGDIR"   : LOGDIR,
        "CPU_FILE" : CPU_FILE
        }

    if DOCOMPARE_ONLY is True :
        return SUBMIT_INFO

    # - - - - - - - - - - - - - - - - - - - 
    # below we actually do stuff.
    make_cpufile(CPU_FILE,LIST_FILE_INFO)

    if RUN_SSH :
        submitTasks_SSH(INPUTS, LIST_FILE_INFO, SUBMIT_INFO)

    if RUN_BATCH :
        submitTasks_BATCH(INPUTS, LIST_FILE_INFO, SUBMIT_INFO)

    # - - - - - - - - - - - - - -

    return SUBMIT_INFO
    # end submitTasks_driver

# ========================================
def compare_results(INPUTS, RESULTS_INFO_REF, RESULTS_INFO_TEST):

    # compare TEST vs. REF and write final summary file.

    print(' Compare TEST vs. REF \n')
    sys.stdout.flush()

    TASKNAME_REF    = RESULTS_INFO_REF["TASKNAME_LIST"]
    TASKNUMNAME_REF = RESULTS_INFO_REF["TASKNUMNAME_LIST"]

    LOGDIR_REF      = RESULTS_INFO_REF["LOGDIR"]
    LOGDIR_TEST     = RESULTS_INFO_TEST["LOGDIR"]
    logdir_ref      = LOGDIR_REF.split("/")[-1]  # after last slash
    logdir_test     = LOGDIR_TEST.split("/")[-1]  # after last slash

    TASKNUM_REF     = RESULTS_INFO_REF["TASKNUM_LIST"]
    TASKNUM_TEST    = RESULTS_INFO_TEST["TASKNUM_LIST"]

    TASKRESULT_REF  = RESULTS_INFO_REF["TASKRESULT_LIST"]
    TASKRESULT_TEST = RESULTS_INFO_TEST["TASKRESULT_LIST"]

    SNANA_DIR_REF   = RESULTS_INFO_REF["SNANA_DIR"]
    SNANA_DIR_TEST  = RESULTS_INFO_TEST["SNANA_DIR"]

    SNANA_VER_REF   = RESULTS_INFO_REF["SNANA_VERSION"]
    SNANA_VER_TEST  = RESULTS_INFO_TEST["SNANA_VERSION"] 

    DIFF_FILE = f"{LOGDIR_TEST}/{RESULT_DIFF_FILE}"
    f = open(DIFF_FILE, 'wt')

    NTASK_TEST  = len(TASKNUM_TEST)
    NTASK_MATCH = 0
    NTASK_FAIL  = 0

    # write header info before comparison infox
    f.write(f"LIST_FILE: {INPUTS.list_file} \n")
    f.write(f"REF  LOGDIR    : {logdir_ref} \n")
    f.write(f"TEST LOGDIR    : {logdir_test} \n")
    f.write(f"REF  SNANA_DIR : {SNANA_DIR_REF} ({SNANA_VER_REF})\n")
    f.write(f"TEST SNANA_DIR : {INPUTS.snana_dir} ({SNANA_VER_TEST})\n")
    f.write(f"\n# ------------------------------------------------- \n");
    f.flush()

    for NUM in TASKNUM_TEST :
        itask_test   = TASKNUM_TEST.index(NUM)
        itask_ref    = TASKNUM_REF.index(NUM)
        RESULT_REF   = TASKRESULT_REF[itask_ref]
        RESULT_TEST  = TASKRESULT_TEST[itask_test]
        TASKNAME     = TASKNAME_REF[itask_ref]
        TASKNUMNAME  = TASKNUMNAME_REF[itask_ref]

        if RESULT_REF == RESULT_TEST :
            f.write('%-40s:  Perfect match (REF = TEST)\n' % TASKNUMNAME )
            NTASK_MATCH += 1
        else:
            f.write('%-40s:  mis-match (REF != TEST)\n' % TASKNUMNAME )
            f.write(f"\t ==> REF:  {RESULT_REF}\n")
            f.write(f"\t ==> TEST: {RESULT_TEST}\n")
            NTASK_FAIL += 1

    # write final summary
    f.write(f"\n TEST Summary\n")
    f.write(f"  {NTASK_MATCH:3d} tests have perfect match \n" )
    f.write(f"  {NTASK_FAIL:3d} tests have mis-match \n")
    f.close()

    # dump DIFF_FILE to screen
    cmd_cat = (f"cat {DIFF_FILE}")
    os.system(cmd_cat)

    return(NTASK_FAIL)

# ========================================
def make_tarfiles(LOGDIR):

    # to cleanup files, make tar files and then remove files.
    filespec_list = []
    tarfile_list  = []

    filespec_list.append('TASK*')
    filespec_list.append('*.LOG *.fitres *.FITRES *.M0DIF *.COV *.SPEC *.out *.OUT *.ROOT *.HBOOK *.fits *.FITS *.LIST RUNJOBS* ')

    tarfile_list.append('BACKUP_TASKFILES.tar')
    tarfile_list.append('BACKUP_MISC.tar')
    
    NLIST = len(tarfile_list)

    print(' Create tar file backups. ' )
    sys.stdout.flush()
    for i in range(0,NLIST):
        filespec  = filespec_list[i]
        tarfile   = tarfile_list[i]
        cmd_cd    = f"cd {LOGDIR}"
        cmd_tar   = f"tar -cf {tarfile} {filespec} >/dev/null 2>&1"
        cmd_gzip  = f"gzip {tarfile}"
        cmd_rm    = f"rm {filespec} >/dev/null 2>&1"
        cmd_all   = f"{cmd_cd} ; {cmd_tar} ; {cmd_gzip} ; {cmd_rm}"

        os.system(cmd_all)

# ========================================
def monitorTasks_driver(INPUTS,SUBMIT_INFO,RESULTS_INFO_REF):

    t_start = time.time()

    DOREF   = INPUTS.ref
    DOTEST  = INPUTS.test
    REFTEST = INPUTS.REFTEST
    NTASK   = SUBMIT_INFO["NTASK"]
    LOGDIR  = SUBMIT_INFO["LOGDIR"]

    # July 2021: write login HOST in case we forget later
    host_info_file = f"{LOGDIR}/HOST_MONITOR.INFO"
    # xxx mark HOSTNAME         = os.environ['HOSTNAME']
    with open(host_info_file,"wt") as f:
        f.write(f"HOST: {HOSTNAME}    # monitor task runs here\n")

    print(f"\n Begin monitor of {NTASK} {REFTEST} tasks")
    sys.stdout.flush()

    NDONE = 0
    while ( NDONE < NTASK ) :
        NDONE = len(glob.glob1(LOGDIR,"*.DONE"))
        # track total run time
        t_now  = time.time()
        t_proc = (t_now-t_start)/60.0  # time in minutes
        print(f" Found {NDONE} of {NTASK} done files  " \
              f"({t_proc:0.1f} minutes elapsed).")
        sys.stdout.flush()
        if os.path.isfile(STOP_FILE) :
            cmd_cp = f"cp {STOP_FILE} {LOGDIR}"
            os.system(cmd_cp)
            sys.exit()

        if NDONE < NTASK :
            time.sleep(10)

    # everything has finished.
    # Catenate the one-line summary from each DONE file
    result_file = f"{LOGDIR}/{RESULT_TASKS_FILE}"
    print(f" All jobs have finished; check RESULTS summary file: \n" \
          f"    {result_file}")
    sys.stdout.flush()

    CMD = f"cd {LOGDIR} ; cat TASK*DONE > {RESULT_TASKS_FILE}"
    os.system(CMD)

    # Count number or ABORT and BLANK entries
    NABORT = 0 ;  NBLANK = 0

    with open(result_file, 'rt') as f:
        lineList = f.readlines()    
    for line in lineList:          
        line  = line.rstrip()  # remove trailing space and linefeed
        if "ABORT" in line:
            NABORT += 1
        if "BLANK" in line:
            NBLANK += 1

    # get SNANA info
    (SNANA_VER,SNANA_DIR) = read_SNANA_INFO(LOGDIR)

    # append NABORT and NBLANK to results file.
    f = open(result_file, 'at')
    f.write(f"\n")
    f.write(f" SNANA_VERSION: {SNANA_VER}\n")
    f.write(f" SNANA_DIR:     {INPUTS.snana_dir}\n")
    f.write(f" Total process time for {NTASK} tasks: {t_proc:0.1f} minutes\n")
    f.write(f" Number of jobs with ABORT output: {NABORT} \n")
    f.write(f" Number of jobs with BLANK output: {NBLANK} \n")
    f.close()

    if DOTEST is True :
        RESULTS_INFO_TEST = get_RESULTS_TASKS(LOGDIR)
        NCOMPARE_FAIL     = compare_results(INPUTS, RESULTS_INFO_REF,
                                            RESULTS_INFO_TEST)
    else:
        NCOMPARE_FAIL = 0   # REF cannot have compare errors

    # if no errors, tar things up
    if NABORT==0 and NBLANK==0 and NCOMPARE_FAIL==0 :
        make_tarfiles(LOGDIR)

    return               
       
# ===================================
# ============== MAIN ===============
# ===================================

if __name__ == "__main__":


    # parse input arguments
    INPUTS = parse_args()

    if INPUTS.stop :
        os.system(f"touch {STOP_FILE}")
        sys.exit('STOP flag sent. Wait for current job to finish')

    print(" ")
    sys.stdout.flush()

    if INPUTS.cpunum >= 0 :
        runTasks_driver(INPUTS)  # run jobs for this CPUNUM
    else:
        # for TEST, need to read REF_RESULTS now to make sure
        # that each TEST has a corresponding REF entry.
        if INPUTS.test  :
            LOGDIR_REF        = get_LOGDIR_REF()
            RESULTS_INFO_REF  = get_RESULTS_TASKS(LOGDIR_REF)
        else:
            RESULTS_INFO_REF = []

        LIST_FILE_INFO = parse_listfile(INPUTS, RESULTS_INFO_REF)
        check_listfile_contents(LIST_FILE_INFO)

        #sys.exit("\n xxx DEBUG STOP xxx \n")

        SUBMIT_INFO = submitTasks_driver(INPUTS,LIST_FILE_INFO)  

        if INPUTS.nosubmit :
            LOGDIR = SUBMIT_INFO['LOGDIR']
            sys.exit(f"\n Exit without submitting jobs. " \
                     f"\n Check output in {LOGDIR} \n")

        monitorTasks_driver(INPUTS,SUBMIT_INFO,RESULTS_INFO_REF) 

    print('\n ALL DONE.') 
    sys.stdout.flush()

# ====== END =====
        

    

