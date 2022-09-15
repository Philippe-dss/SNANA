#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  makeDataFiles_params.py
#
#  Copyright July 2021 R. Kessler
#
#  Jun 24 2022 R.Kessler - add HOSTGAL_LOGMASS_ERR

"""Constant definitions for makeDatafile framework.
Relevant configuration gets loaded here.
"""

# import datetime
# import time
import os
import getpass


# =============================================================================
#  Documentation constants
# =============================================================================
DOCANA_KEY     = "DOCUMENTATION"
DOCANA_KEY_END = "DOCUMENTATION_END"


# =============================================================================
#  Formats
# =============================================================================
FORMAT_TEXT = "TEXT"
FORMAT_FITS = "FITS"

# =============================================================================
# User, hosts, passwords
# =============================================================================
USERNAME = getpass.getuser()
HOSTNAME = os.environ['HOSTNAME']

# =============================================================================
# Survey information
# =============================================================================
MXSEASON = 12    # max number of seasons

# -----------------------------------------------------------------------------
# Survey info that is fixed for all events;
# e.g., NXPIX = SURVEY_INFO['CCD'][survey][0]

SURVEY_INFO = {
    'FILTERS' : {           # mandatory
        'LSST'  : "ugrizY",
        'SIRAH' : "GRcogrizyABCLYJNH",  # ztf/ATLAS/PS1/WFC3
        'DES'   : "griz" ,
        'PS1'   : "griz"
    },
    'CCD' : {   # optional
        'LSST'  : [4072, 4000, 0.199598],  # NXPIX, NYPIX, pixsize
        'DES'   : [2048, 4096, 0.263]
    }
}


# =============================================================================
# SNANA specifics
# =============================================================================
SNANA_FLAG_DATA = 0
SNANA_FLAG_FAKE = 1
SNANA_FLAG_SIM  = 2

SNANA_ZP = 27.5   # FLUXCAL = FLUX * 10^[ -0.4*(ZP-SNANA_ZP) ]
VPEC_DEFAULT = [0.0, 300.0]  # VPEC and error, km/sec

# -----------------------------------------------------------------------------
# define list of variable names for each observation;
VARNAMES_OBS = "MJD BAND FIELD PHOTFLAG  " \
               "XPIX YPIX CCDNUM IMGNUM GAIN " \
               "FLUXCAL FLUXCALERR PSF_SIG1 ZEROPT SKY_SIG"

VARNAMES_OBS_LIST = VARNAMES_OBS.split()

# -----------------------------------------------------------------------------
# define text format for each VARNAMES_OBS
VARNAMES_FMT = "10.4f 2s   8s    5d      6.1f 6.1f  4d  6d   6.3f "\
               "12.4e    12.4e    8.4f  6.3f 6.2f "

VARNAMES_FMT_LIST = VARNAMES_FMT.split()
# -----------------------------------------------------------------------------
# define values for undefined variables
# value set to VAL_ABORT will trigger abort because it is required.
VAL_ABORT     = 666
VAL_NULL      = -999
VAL_NULL_LIST = [ -9, -99, -999, 999 ] # any of these is treated as no value
VAL_UNDEFINED_LIST = [
    VAL_ABORT, VAL_ABORT, "VOID",  0,      # for MJD BAND FIELD PHOTFLAG
    VAL_NULL,  VAL_NULL,  VAL_NULL, VAL_NULL, VAL_NULL,
    VAL_ABORT, VAL_ABORT, VAL_NULL, VAL_NULL, VAL_NULL
]

# -----------------------------------------------------------------------------
VARNAME_TRUEMAG = "SIM_MAGOBS"   # for fakes or sim, add this to VARNAMES_OBS

# -----------------------------------------------------------------------------
#  Field names
FIELD_DDF      = "DDF"
FIELD_WFD      = "WFD"
FIELD_HST      = "HST"
FIELD_DEEP     = "DEEP"
FIELD_MEDIUM   = "MEDIUM"
FIELD_SHALLOW  = "SHALLOW"
FIELD_VOID     = "VOID"
FIELD_NULL     = "NULL"

PREFIX_SEASON   = "Y"       # e.g.. for Y03 in file name
PREFIX_SPLIT    = "SPLIT"   # e.g., for SPLIT012 in file name
TEXTFILE_SUFFIX = ".DAT"    # used for intermediate TEXT  file name

# -----------------------------------------------------------------------------
# snana program to convert TEXT to FITS
PROGRAM_SNANA = "snana.exe"

# -----------------------------------------------------------------------------
# set TEXT->FITS options to
#  + define MWEBV from SFD98
#  + estimate PEAKMJD from fmax-clump method

OPTIONS_TEXT2FITS_SNANA = \
        "OPT_YAML 1  OPT_MWEBV 3  OPT_SETPKMJD 20"
OPTION_TEXT2FITS_SPECTRA_SNANA =  \
        "OPT_REFORMAT_FITS 128"

# -----------------------------------------------------------------------------
# for writing events, update screen after this many
NEVT_SCREEN_UPDATE = 500

# -----------------------------------------------------------------------------
# define yaml keys to store statistics for README
KEYLIST_README_STATS = [
    'NEVT_ALL', 'NEVT_HOSTGAL_SPECZ', 'NEVT_HOSTGAL_PHOTOZ', 'NEVT_SPECTRA'
]

# -----------------------------------------------------------------------------
# for lsst alerts
KEYNAME_NOBS_ALERT = "NOBS_ALERT"

# -----------------------------------------------------------------------------
# define key names for data_event_dict dictionary,
# and for TEXT-formatted data files (readable by snana codes)
# The global list is used to initial all values to -9

DATAKEY_SURVEY      = "SURVEY"
DATAKEY_FILTERS     = "FILTERS"
DATAKEY_NXPIX       = "NXPIX"
DATAKEY_NYPIX       = "NYPIX"
DATAKEY_PIXSIZE     = "PIXSIZE"

DATAKEY_SNID        = "SNID"
DATAKEY_SNTYPE      = "SNTYPE"
DATAKEY_FAKE        = "FAKE"
DATAKEY_RA          = "RA"
DATAKEY_DEC         = "DEC"
DATAKEY_zHEL        = "REDSHIFT_HELIO"
DATAKEY_zHEL_ERR    = "REDSHIFT_HELIO_ERR"
DATAKEY_zCMB        = "REDSHIFT_CMB"
DATAKEY_zCMB_ERR    = "REDSHIFT_CMB_ERR"
DATAKEY_VPEC        = "VPEC"
DATAKEY_VPEC_ERR    = "VPEC_ERR"

DATAKEY_MWEBV       = "MWEBV"
DATAKEY_MWEBV_ERR   = "MWEBV_ERR"
DATAKEY_PEAKMJD     = "PEAKMJD"
DATAKEY_MJD_DETECT_FIRST  = "MJD_DETECT_FIRST"
DATAKEY_MJD_DETECT_LAST   = "MJD_DETECT_LAST"
DATAKEY_FIELD       = "FIELD"
DATAKEY_NOBS        = "NOBS"

HOSTKEY_BASE          = "HOSTGAL"
HOSTKEY_NMATCH        = "HOSTGAL_NMATCH"
HOSTKEY_NMATCH2       = "HOSTGAL_NMATCH2"
HOSTKEY_OBJID         = "HOSTGAL_OBJID"
HOSTKEY_PHOTOZ        = "HOSTGAL_PHOTOZ"
HOSTKEY_PHOTOZ_ERR    = "HOSTGAL_PHOTOZ_ERR"
HOSTKEY_SPECZ         = "HOSTGAL_SPECZ"
HOSTKEY_SPECZ_ERR     = "HOSTGAL_SPECZ_ERR"
HOSTKEY_SNSEP         = "HOSTGAL_SNSEP"
HOSTKEY_DDLR          = "HOSTGAL_DDLR"
HOSTKEY_LOGMASS       = "HOSTGAL_LOGMASS"
HOSTKEY_LOGMASS_ERR   = "HOSTGAL_LOGMASS_ERR"
HOSTKEY_ELLIP         = "HOSTGAL_ELLIPTICITY"
HOSTKEY_SQRADIUS      = "HOSTGAL_SQRADIUS"
HOSTKEY_RA            = "HOSTGAL_RA"
HOSTKEY_DEC           = "HOSTGAL_DEC"

# define prefix for filter-dependent quantities
HOSTKEY_PREFIX_MAG     = "HOSTGAL_MAG"         # band-dependent
HOSTKEY_PREFIX_MAGERR  = "HOSTGAL_MAGERR"      # idem
HOSTKEY2_PREFIX_MAG    = "HOSTGAL2_MAG"
HOSTKEY2_PREFIX_MAGERR = "HOSTGAL2_MAGERR"
HOSTKEY_PREFIX_SB      = "HOSTGAL_SB_FLUXCAL"  # idem

# define prefix for photo-z quantiles
HOSTKEY_PREFIX_ZPHOT_Q       = "HOSTGAL_ZPHOT_Q"

# =============================================================================
# LISTS
# =============================================================================
# -----------------------------------------------------------------------------

HOSTKEY_PREFIX_LIST = [ HOSTKEY_PREFIX_MAG, HOSTKEY_PREFIX_MAGERR,
                        HOSTKEY2_PREFIX_MAG, HOSTKEY2_PREFIX_MAGERR, # restore
                        HOSTKEY_PREFIX_SB ]

# -----------------------------------------------------------------------------
DATAKEY_LIST_RAW = [
    DATAKEY_SURVEY, DATAKEY_SNID, DATAKEY_SNTYPE, DATAKEY_FAKE,
    DATAKEY_FILTERS,
    DATAKEY_NXPIX, DATAKEY_NYPIX, DATAKEY_PIXSIZE,
    DATAKEY_RA, DATAKEY_DEC,
    DATAKEY_zHEL, DATAKEY_zHEL_ERR, DATAKEY_FIELD,
    HOSTKEY_NMATCH, HOSTKEY_NMATCH2, HOSTKEY_OBJID,
    HOSTKEY_SPECZ,  HOSTKEY_SPECZ_ERR,
    HOSTKEY_SNSEP,  HOSTKEY_DDLR,
    HOSTKEY_RA,     HOSTKEY_DEC,
    HOSTKEY_ELLIP,  HOSTKEY_SQRADIUS
]

# -----------------------------------------------------------------------------
DATAKEY_LIST_CALC = [
    DATAKEY_zCMB, DATAKEY_zCMB_ERR, DATAKEY_MWEBV, DATAKEY_MWEBV_ERR,
    DATAKEY_PEAKMJD, DATAKEY_MJD_DETECT_FIRST, DATAKEY_MJD_DETECT_LAST,
    HOSTKEY_PHOTOZ, HOSTKEY_PHOTOZ_ERR, 
    HOSTKEY_LOGMASS, HOSTKEY_LOGMASS_ERR
]


# define null lists for optional variables whose names are specified
# in global header and thus cannot be specified here.
DATAKEY_LIST_PRIVATE = [] # filled if private variables exist
DATAKEY_LIST_ZPHOT_Q = [] # filled of ZPHOT_Qnn variables exist (Feb 11 2022)

# -----------------------------------------------------------------------------
SIMKEY_TYPE_INDEX = "SIM_TYPE_INDEX"
DATAKEY_LIST_SIM = [SIMKEY_TYPE_INDEX]

# -----------------------------------------------------------------------------
MODE_MERGE_MOVE = "MERGE_MOVE"  # move files, then remove original folder
MODE_MERGE_LINK = "MERGE_LINK"  # merge with sym links; keep orig folder


# =============================================================================
# ERROR MESSAGES
# =============================================================================
ABORT_FACE_MSSG = (
    f"\n\n"
    f"\n   `|```````|`    "
    f"\n   <| o\\ /o |>   "
    f"\n    | ' ; ' |     "
    f"\n    |  ___  |     ABORT makeDataFiles on Fatal Error. "
    f"\n    | |' '| |     "
    f"\n    | `---' |     "
    f"\n    \\_______/    "
    f"\n"
    f"\nFATAL ERROR ABORT : "
)

# == END ===

