/*******************************************
  simlib_tools.c:  Created April 4, 2007 by R.Kessler


  Public tools to write simulation library in standard
  format for snlc_sim program.
  Does lots of error checking and aborts on any
  hint of trouble !   You are not allowed to pass 
  nonsense values to this these functions.
  When you pass "NOBS" ovservations, it will then count
  how many times you call simlib_add_mjd to make sure
  that you add the correct number of epochs.

  Here is how to use these four functions.
  Make sure to read comments at the top of each function
  so that you know what arguments to pass.

  1. call simlib_open_write() to open file and write global info.

  2. for each RA,DECL position where a supernova could have been
     observed, call function
          simlib_add_header(...)

  3. For RA,DECL above, loop over observed MJDs & filters and call
        simlib_add_mjd(...) 

  3b. After last enry, call 
          simlib_add_header(-1, ...)
      to leave  END marker.

  4. call simlib_close() at the end of job.

  
      HISTORY
     ~~~~~~~~~~

  May 20,. 2008: add char *telescope argument to simlib_open_write

  May 27, 2009: define new global CFILT_LAST so that both MHJ & filter
                are compared to determine new MJD.  Handles case where
                MJD for different filters is the same to given precision.

  Jun 8, 2009: add FIELD as argument to simlib_add_header(..).

  Feb 25, 2012: add HEADERFILE argument to simlib_open to paste in
                arbitrary header info from another file.

  Aug 31, 2012: "NOBS" check 1-1400 changed to 1-3000

  Jun 20 2017: add MJD arg to simlib_add_mjd() so that MJD is double
               rather than float.

  Apr 3 2018:
   + long int IDEXPT -> char STRINGID[20] to allow ID*NEXPOSE
     e.g., 123438*2

 Jan 5 2021: 
   + allow PSF max to 50 (was 10) [for LSST]
   + rename DECL -> DEC

********************************************/

#include "simlib_tools.h"

FILE *FPLIB;      // global pointer to library file.

struct {
  int   NSIMLIB         ;  // number of simlib entries          
  int   NOBS_FOUND      ;  // number of add_mjd  calls; should equal NOBS
  int   NOBS_EXPECT ; // = 0 ;  // = NOBS
  double   MJD_LAST;
  char     STRINGID_LAST[20];
  char     CFILT_LAST[2];
  
  int OPT_CHECKVAL ;
} SIMLIB_TOOLS;



// *************************************
void simlib_open_write(
		 char *filename     // full name of file to open
		 ,char *surveyname  // name of survey; i.e, "SDSS"
		 ,char *filters     // filter list; i.e, "ugriz"
		 ,char *telescope   // name of telescope
		 ,char *comment     // user comment
		 ,char *headFile    // optional file with header contents
		 ) {

  // Created Apr 6, 2007 by R.Kessler
  // Open library file and write global information 
  // May 20, 2008: add telescope as argument
  // Feb 25, 2012: add *headFile argument

  time_t tstart;

  FILE *fp_head ;
  char cline[200];
  char fnam[20] = "simlib_open_write";
  
  // -------------- BEGIN --------------


  SIMLIB_TOOLS.NSIMLIB = 0;

  if ( (FPLIB = fopen(filename, "wt"))==NULL ) {       
    sprintf(c1err, "Cannot open simlib file :" );
    sprintf(c2err, " '%s' \n", filename);
    errmsg(SEV_FATAL, 0, fnam, c1err, c2err); 
  }

  printf("\n Opened sim-library output file : \n\t %s \n", filename);

  // write global info at top of lib-file

  fprintf(FPLIB,"SURVEY: %s     FILTERS: %s   TELESCOPE:  %s \n", 
	  surveyname, filters, telescope );
  fprintf(FPLIB,"USER: %s     HOST: %s \n", 
	  getenv("USER"), getenv("HOST") );
  fprintf(FPLIB,"COMMENT: '%s'  \n", comment);

  // Check or optional header file

  if ( strlen(headFile) > 0 ) {
    if ( (fp_head = fopen(headFile, "rt"))==NULL ) {       
      sprintf(c1err, "Cannot open headFile: headFile :\n" );
      sprintf(c2err, " '%s' \n", headFile);
      errmsg(SEV_FATAL, 0, fnam, c1err, c2err); 
    }

    printf("\t Extract header contents from : %s \n", headFile);

    // copy each line of header file into simlib header.
    fprintf(FPLIB,"COMMENT: Header below extracted from %s \n", headFile);
    while ( fgets (cline, 100, fp_head) !=NULL  ) 
      {      fprintf(FPLIB,"%s", cline);    }

    fclose(fp_head);

  }  // end of headFile 

  time(&tstart);
  fprintf(FPLIB,"\nBEGIN LIBGEN  %s \n", ctime(&tstart) ) ;

  fprintf(FPLIB,"\n");

  fflush(FPLIB);

  return ;

}  // end of function simlib_open_write
 

// *****************************************
void simlib_add_header(
		       int optflag     // (I) option for debug (0=nominal)
		       ,int   IDLIB    // (I) incremental lib id (1,2,3 ... )
		       ,int   NOBS     // (I) # obs  to follow (must be >=3)
		       ,char *FIELD    // (I) name of field
		       ,float *INFO    // (I) header info; see unpacking below
		       ) {
  /*****
   Created April 2007 by R.Kessler
   Write header for new SN event at new RA,DECL position.
   Unpacking comments below specify required or optional for each 
   *INFO element.

   "optional" means that only positive values are used.
   If optional Z or PEAKMJD  are positive, these values will be used
   in the simulation instead of picking them randomly.

   optflag = 0 => nominal (recommended)

   optflag = 1 => skip tests on variables to allow garbage written to file.
                     (for debugging)


   optflag = -1  leave END_LIBID marker after all epochs 
                      (all other args ignored) 

      HISTORY

  Dec 6 2021: fix setting NEA_PSF_UNIT

  *****/

  char msgerr[100];
  int istat, NOPT, NEA_PSF_UNIT ;

  float RA, DEC, MWEBV, PIXSIZE, Z, PEAKMJD ;
  char fnam[] = "simlib_add_header";

  // ------------ BEGIN ------------

  SIMLIB_TOOLS.OPT_CHECKVAL = 1;  // default: make checks on variable values
  SIMLIB_TOOLS.NOBS_EXPECT  = NOBS ;

  // turn off sanity checks (for debugging)
  if ( optflag == 1 )  { SIMLIB_TOOLS.OPT_CHECKVAL = 0; }

  // check number of MJDs for last lib entry
  //  if ( NMJD_EXPECT > 0 &&  NMJD_FOUND != NMJD_EXPECT )

  if ( optflag == -1 ) {

    fprintf(FPLIB,"END_LIBID: %d \n", IDLIB );

    if ( SIMLIB_TOOLS.NOBS_FOUND != SIMLIB_TOOLS.NOBS_EXPECT ) {

      PRINT_SIMLIB_ERROR("\n");

      sprintf(msgerr,"  FATAL ERROR in %s \n", fnam);
      PRINT_SIMLIB_ERROR(msgerr);

      sprintf(c1err,"Found %d MJDs, but expect %d from user NOBS arg.\n", 
	      SIMLIB_TOOLS.NOBS_FOUND, SIMLIB_TOOLS.NOBS_EXPECT);
      PRINT_SIMLIB_ERROR(c1err);

      sprintf(c2err,"\t Check last entry in your library file. \n");
      PRINT_SIMLIB_ERROR(c2err);
      
      errmsg(SEV_FATAL, 0, fnam, c1err, c2err); 
    }
    return;
  }


  SIMLIB_TOOLS.NOBS_EXPECT = NOBS;
  SIMLIB_TOOLS.NOBS_FOUND  = 0;
  SIMLIB_TOOLS.MJD_LAST    = 0.0 ;
  SIMLIB_TOOLS.STRINGID_LAST[0] = 0 ;
  sprintf(SIMLIB_TOOLS.CFILT_LAST,"?");

  // unpack header info

  RA      = INFO[IPAR_RA] ;  // required: right-ascension, degrees
  DEC     = INFO[IPAR_DEC] ;  // required: declination, degrees
  MWEBV   = INFO[IPAR_MWEBV] ;  // required: MilkyWay extinction = AV/RV
  PIXSIZE = INFO[IPAR_PIXSIZE] ;  // required: pixel size, arcseconds
  Z       = INFO[IPAR_Z] ;  // optional: redshift
  PEAKMJD = INFO[IPAR_PKMJD] ;  // optional: MJD at maximum B-band luminosity
  NEA_PSF_UNIT = (int)INFO[IPAR_NEA_UNIT] ; // Dec 2021

  // start by writing required info.

  fprintf(FPLIB, "# -------------------------------------------- \n");
  fprintf(FPLIB, "LIBID: %d \n", IDLIB);

  fprintf(FPLIB, "RA: %f   DEC: %f   NOBS: %d    "
	  "MWEBV: %.4f   PIXSIZE: %5.3f \n", 
	  RA, DEC, NOBS,   MWEBV, PIXSIZE );

  if ( strlen(FIELD) > 0 ) 
    fprintf(FPLIB,"FIELD: %s \n", FIELD );

  // now check for optional info
  NOPT=0;
  if ( Z       >= 0.0 ) {NOPT++; fprintf(FPLIB,"REDSHIFT: %6.4f    ", Z); }
  if ( PEAKMJD >= 0.0 ) {NOPT++; fprintf(FPLIB,"PEAKMJD:  %9.3f    ", PEAKMJD); }
  if ( NOPT > 0 ) fprintf(FPLIB,"\n");


  if ( optflag == 1 && NOBS == 0 ) {
    fprintf(FPLIB, "\t WARNING: ZERO OBSERVATIONS !!! \n");
    fflush(FPLIB);
    return ;
  }


  // make table header to that file is self-documented.

  fprintf(FPLIB, "\n");
  if ( NEA_PSF_UNIT ) {
    fprintf(FPLIB,"#                           CCD  CCD         "
	    "PSF1 PSF2 PSF2/1                    \n");
    fprintf(FPLIB,"#     MJD      IDEXPT  FLT GAIN NOISE SKYSIG "
	    "(pixels)  RATIO  ZPTAVG ZPTERR  MAG \n");
  }
  else {
    fprintf(FPLIB,"#                           CCD  CCD   \n" );
    fprintf(FPLIB,"#     MJD      IDEXPT  FLT GAIN NOISE SKYSIG "
	    "  NEA     ZPTAVG ZPTERR  MAG \n");
  }



  SIMLIB_TOOLS.NSIMLIB++ ;

  // make sanity checks on input values.

  if ( SIMLIB_TOOLS.OPT_CHECKVAL == 1 ) {
    istat = CHECK_SIMLIB_VAL("IDLIB",   (float)IDLIB,  0.0, 100000. );
    istat = CHECK_SIMLIB_VAL("NOBS",    (float)NOBS,   1.0, 3000.   );
    istat = CHECK_SIMLIB_VAL("RA",      RA,           -200., 400.0  );
    istat = CHECK_SIMLIB_VAL("DEC",     DEC,          -200., 400.0  );
    istat = CHECK_SIMLIB_VAL("MWEBV",   MWEBV,         0.0, 2.0     );
    istat = CHECK_SIMLIB_VAL("PIXSIZE", PIXSIZE,       0.0, 2.0     );
  }

  return ;

} // end of simlib_add_header



// *********************************************
void simlib_add_mjd(
		    int opt            // 1=>search info;  2=> template info
		    ,double *INFO      // see IPAR_xxx params 
		    ,char *STRINGID    // exposure ID/RUN/FIELD/whatever
		    ,char *FILTNAME    // filter name, abbreviation
		    ) {

  /*****
   Created April 2007 by R.Kessler
   Write info related to observed MJD; can then be used by snlc_sim.
   Here are a few comments:

      - OPT =  1 for search image is required
      - OPT =  2 for template image is optional.

      - SKYSIG (in measured ADU) is for search or template image.
        However, if you do not give template info, then SKYSIG(search)
        shuold include your best estimate of template noise when doing
        galaxy-subtraction.

      - If you only want single Guassian PSF, then set PSF = { PSF, 0.0, 0.0 }

      - to ignore MAGOBS, set it to -99.0; otherwise this magnitude is used
        in the simulation rather than generating a mag from a model.
        This feature allows you to over-ride the simulated mags with your 
        own mags.

      - Note that the units are measured ADU and pixels.
        Since you also provide CCDGAIN (electrons/ADU) and pixel size in
        arcseconds, the simulation will make the necessary conversions.

   May 27, 2009:  ISNWMJD requires different MJD and different filter.
                  See new global declaration CFILT_LAST[2].

   Oct 25, 2010: %10d -> %10ld  for IDEXPT

   Jan 6, 2011: increase SKYSIG CHECK_LIBVAL-limit from 400 to 600 
                so that it works for LSST coadd.

  Jun 20 2017: 
    + SKYSIG ABORT = 1000 -> 2000 (for LSST-DDF)
    + add MJD argument

  Mar 2022: 
     + INFO -> double (was float) and absorb MJD
     + remove MJD arg from function
  *****/


  char key[2], string_psf[80] ;
  int istat, ISNEWMJD, ISNEWID ;
  double MJD, PSF[3], ZPT[2], SKYSIG, CCDGAIN, CCDNOISE, MAGOBS;

  char fnam[] = "simlib_add_mjd" ;

  // --------------- BEGIN --------------

  // unpack *INFO array
  MJD      = INFO[IPAR_MJD];
  CCDGAIN  = INFO[IPAR_CCDGAIN] ;  // electrons per ADU
  CCDNOISE = INFO[IPAR_CCDNOISE]; // CCD read noise in electrons
  SKYSIG   = INFO[IPAR_SKYSIG] ;  // skynoise in ADU per pixel
  PSF[0]   = INFO[IPAR_PSF0]   ;  // PSF-sigma (pixels) for inner Gaussian
  PSF[1]   = INFO[IPAR_PSF0+1] ;  // PSF-sigma (pixels) for outer Gaussian
  PSF[2]   = INFO[IPAR_PSF0+2] ;  // PSF(outer)/PSF(inner) ratio at origin
  ZPT[0]   = INFO[IPAR_ZPT0]   ;  // zero point
  ZPT[1]   = INFO[IPAR_ZPT0+1] ;  // zero point error, or spread
  MAGOBS   = INFO[IPAR_MAG] ;  // model of observed mag (optional)

  if ( opt == 1 ) {
    sprintf(key, "S") ;

    ISNEWMJD = ISNEWID = 0 ;
    if ( MJD != SIMLIB_TOOLS.MJD_LAST || 
	 strcmp(FILTNAME,SIMLIB_TOOLS.CFILT_LAST) != 0 ) 
      { ISNEWMJD = 1 ; }

    if ( strcmp(STRINGID,SIMLIB_TOOLS.STRINGID_LAST) != 0 ) 
      { ISNEWID = 1; }

    if ( ISNEWMJD == 1  || ISNEWID )  
      { SIMLIB_TOOLS.NOBS_FOUND++ ;  }

    SIMLIB_TOOLS.MJD_LAST = MJD ;
    sprintf(SIMLIB_TOOLS.CFILT_LAST,    "%s", FILTNAME);
    sprintf(SIMLIB_TOOLS.STRINGID_LAST, "%s", STRINGID);
  }
  else if ( opt == 2 ) 
    sprintf(key, "T") ;
  else {
    sprintf(c1err, "opt=%d is invalid for function %s \n", opt, fnam);
    sprintf(c2err, "Something is messed up.");
    errmsg(SEV_FATAL, 0, fnam, c1err, c2err); 
  }


  if ( PSF[1] < -900.0 ) 
    { sprintf(string_psf, "%6.3f ", PSF[0]); } // write NEA
  else
    { sprintf(string_psf, "%4.2f %4.2f %5.3f ", 
	      PSF[0], PSF[1], PSF[2] ); 
    } // write PSF params

  fprintf(FPLIB,"%s: "
	  "%9.4f %10.10s %s %5.2f %5.2f %6.2f "
	  "%s "
	  // "%4.2f %4.2f %5.3f "
	  "%6.2f %6.3f"
	  , key
	  , MJD, STRINGID, FILTNAME, CCDGAIN, CCDNOISE, SKYSIG
	  , string_psf
	  , ZPT[0], ZPT[1]
	  );


  // print MAGOBS for "Search-image" option only
  if ( opt == 1 ) fprintf(FPLIB," %7.3f", MAGOBS );

  fflush(FPLIB);

  // add <CR>
  fprintf(FPLIB, "\n");

  // make sanity checks after adding entry to file

  if ( SIMLIB_TOOLS.OPT_CHECKVAL == 1 ) {
    
    istat = CHECK_SIMLIB_VAL("MJD",         MJD,     20000., 80000. );
    istat = CHECK_SIMLIB_VAL("CCDGAIN",     CCDGAIN, 0.0, 100. );
    istat = CHECK_SIMLIB_VAL("CCDNOISE",    CCDNOISE,0.0, 100. );
    istat = CHECK_SIMLIB_VAL("SKYSIG",      SKYSIG,  0.0,2000. );

    istat = CHECK_SIMLIB_VAL("PSF(inner)",  PSF[0], 0.0, 550. );
    //    istat = CHECK_SIMLIB_VAL("PSF(outer)",  PSF[1], 0.0, 50. );
    //    istat = CHECK_SIMLIB_VAL("PSF-ratio",   PSF[2], 0.0, 10. );
    
    istat = CHECK_SIMLIB_VAL("ZeroPoint",       ZPT[0], 10.0, 40. );
    istat = CHECK_SIMLIB_VAL("ZeroPoint-sigma", ZPT[1],  0.0, 4.0 );
  }

  return ;
}  // end of simlib_add_mjd


// ************************************************
void simlib_close_write(void) {

  fprintf(FPLIB, "\n");
  fprintf(FPLIB, "END_OF_SIMLIB: %d ENTRIES \n", SIMLIB_TOOLS.NSIMLIB );
  fclose(FPLIB) ;
  return;
}  


// ================================================   
void parse_SIMLIB_IDplusNEXPOSE(char *inString, int *IDEXPT, int *NEXPOSE) {

  // Copied from snlc_sim.c [Jan 2021]                          
  // If inString has no *   -->  IDEXPT = inString and NEXPOSE=1
  // If inString = ID*NEXP  -->  IDEXPT = ID and NEXPOSE=NEXP

  int  IDTMP, NTMP, NRD;
  char star[] = "*" ;
  char WDLIST[2][20], *ptrWDLIST[2];
  //  char fnam[] = "parse_SIMLIB_IDplusNEXPOSE" ;     
  // ----------- BEGIN ------------ 

  NTMP = 1;  // default                                                        
  if ( strchr(inString,'*') == NULL ) {
    // no star, just read IDEXPT   
    sscanf(inString , "%d", &IDTMP );
  }
  else {
    // found star, read both ID and NEXPOSE  
    ptrWDLIST[0] = WDLIST[0] ;
    ptrWDLIST[1] = WDLIST[1] ;
    splitString(inString, star, 3,  &NRD, ptrWDLIST );
    sscanf( WDLIST[0] , "%d", &IDTMP );
    sscanf( WDLIST[1] , "%d", &NTMP );
  }

  // load output arguments    
  *IDEXPT  = IDTMP ;
  *NEXPOSE = NTMP ;

  return ;

} // end parse_SIMLIB_IDplusNEXPOSE                                             

// ************************************************
int CHECK_SIMLIB_VAL(char *varname, 
		     float value, float varmin, float varmax) {

  // check that 'value' is between varmin and varmax;
  // if not, then print message and MADABORT

  char msgerr[10][80];
  int i;
  char fnam[] = "CHECK_SIMLIB_VAL" ;

  // ---------------- BEGIN --------------

  if ( value < varmin || value > varmax ) {
    sprintf(msgerr[0],"\n ERROR WRITING LIBRARY: \n");
    sprintf(msgerr[1],"\t %s = %f is invalid. \n", varname, value );
    sprintf(msgerr[2],"\t %s valid range is %f to %f \n", 
	    varname, varmin, varmax );
    sprintf(msgerr[3],"\t Check last entry in your library file. \n");

    for ( i=0; i<=3; i++ ) {
      PRINT_SIMLIB_ERROR ( msgerr[i] );
    }

    errmsg(SEV_FATAL, 0, fnam, msgerr[1], msgerr[2] ); 
  }

  return 0 ;

} // end of CHECK_SIMLIB_VAL


// ************************************
void PRINT_SIMLIB_ERROR(char *msgerr ) {
  // print message to both stdout and to FPLIB
  printf("%s", msgerr );
  fprintf(FPLIB, "%s", msgerr );
  return ;
}  // end of PRINT_SIMLIB_ERROR

