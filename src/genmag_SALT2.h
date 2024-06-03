// genmag_SALT2.h
// May 21 2024: define REFAC_SALT2_COV=T to enable x_2 component.
//

// useful numbers
#define X0SCALE_SALT2   1.0E-12        // arbitrary normalization

// define bounds for filter and SED arrays
#define MXBIN_VAR_SALT2   200000 // Apr 2022 -> 200k for IR (was 120k)

// wavelengths used for color correction

#define U_WAVELENGTH  3500.
#define B_WAVELENGTH  4302.57  // from SALT2 code
#define V_WAVELENGTH  5428.55  // idem
#define R_WAVELENGTH  6500.

#define COLOR_DISP_MAX_DEFAULT 2.0 // to avod crazyFLux abort (Apr 2023)

// Sep 2020: define indices for values read after COLORCOR_PARAMS key
#define ICLPAR_REFLAM_CL0  0  // aka, B_WAVE
#define ICLPAR_REFLAM_CL1  1  // aka, V_WAVE
#define ICLPAR_LAM_MIN     2
#define ICLPAR_LAM_MAX     3
#define ICLPAR_NPAR_POLY   4
#define ICLPAR_POLY        5 // starts here

#define RVMW_SALT2_DEFAULT  3.1 
#define MXCOLORPAR  20

#define SALT2_INTERP_LINEAR 1
#define SALT2_INTERP_SPLINE 2

// user OPTMASK passed via sim-input 
//  GENMODEL_MSKOPT: <MSKOPT>
#define GENMODEL_MSKOPT_SALT2_REQUIRE_DOCANA      OPENMASK_REQUIRE_DOCANA  // =2
#define GENMODEL_MSKOPT_SALT2_DISABLE_MAGSHIFT    4  // disable MAGSHIFT keys
#define GENMODEL_MSKOPT_SALT2_DISABLE_WAVESHIFT   8  // disable WAVESHIFT keys
#define GENMODEL_MSKOPT_SALT2_ABORT_LAMRANGE   64  // abort on bad model-LAMRANGE
#define GENMODEL_MSKOPT_SALT2_DEBUG   1024    // Refactor for developer only

//#define REFAC_SALT2_COV false
#define REFAC_SALT2_COV true

int  DEBUG_SALT2;
int  NCALL_DBUG_SALT2 ; 
int  RELAX_IDIOT_CHECK_SALT2;
int  IMODEL_SALT ; // 2 or 3
bool ISMODEL_SALT2, ISMODEL_SALT3 ;

/**********************************************
  Init Information
***********************************************/

char SALT2_MODELPATH[MXPATHLEN] ;
char SALT2_INFO_FILE[20]     ;
char SALT2_VERSION[100];  // store version passed to init_genmag_SALT2
char SALT2_PREFIX_FILENAME[20]; // e.g., "salt2", "salt3", etc ...

double RVMW_SALT2 ;

#define MXSURFACE_SALT2 4
#define MXERRMAP_SALT2  10
int     NERRMAP_SALT2 ;
struct  { // define indices for ERROR maps
  int VAR[MXSURFACE_SALT2];
  int COVAR[MXSURFACE_SALT2][MXSURFACE_SALT2];
  int ERRSCALE ;
  int COLORDISP ;
} INDEX_SALT2_ERRMAP;



struct SALT2_ERRMAP {
  int     NDAY, NLAM;
  double  LAMMIN, LAMMAX, LAMSTEP;
  double  DAYMIN, DAYMAX, DAYSTEP;

  double  LAM[MXBIN_LAMSED_SEDMODEL];    // lambda array
  double  DAY[MXBIN_DAYSED_SEDMODEL];    // epoch array
  double  VALUE[MXBIN_VAR_SALT2];      // variance values

  // stuff for spline
  int     INDEX_SPLINE ;   
  int     ISGN[MXBIN_VAR_SALT2];  // sign of value since log10|err| is stored

  int NBADVAL_NAN, NBADVAL_CRAZY; // July 2020 (for retraining)
  double  RANGE_VALID[2] ;  // valid range for each map
  double  RANGE_FOUND[2] ;  // actual min/max for each map
} SALT2_ERRMAP[MXERRMAP_SALT2]; // SALT2_VAR[2], SALT2_COVAR, SALT2_ERRSCALE ;

#define CALIB_SALT2_MAGSHIFT  1
#define CALIB_SALT2_WAVESHIFT 2
#define MXSHIFT_CALIB_SALT2 500

typedef struct {
  int    WHICH ;  // specifies MAGSHIFT or WAVESHIFT
  char   SURVEY_STRING[60];  // e.g., 'CFA3,CFA3S,CFA3K'
  char   BAND[2];            // e.g.  'r'
  char   FILTER_STRING[60];  //e.g. 'SDSS-r'
  double SHIFT ;  
} SHIFT_CALIB_SALT2_DEF ;


struct INPUT_SALT2_INFO {
  double RESTLAMMIN_FILTERCEN ;    // RESTLAMBDA_RANGE key
  double RESTLAMMAX_FILTERCEN ;
  int    COLORLAW_VERSION;
  int    NCOLORLAW_PARAMS ;
  double COLORLAW_PARAMS[MXCOLORPAR] ; // for IVER=1 (SALT2.Guy10,JLA-B14)
  double COLOR_OFFSET  ;   // separate from COLORLAW_PARAMS (Aug 2, 2010)
  double COLOR_DISP_MAX;  // Oct 2022, 

  double MAG_OFFSET; // global mag offset (Nov 24, 2011)

  int SEDFLUX_INTERP_OPT;    // 1=>linear,  2=> spline
  int ERRMAP_INTERP_OPT ;    // 1=>linear,  2=> spline in log10 space
  int ERRMAP_KCOR_OPT   ;    // turn KCOR erro on(default) or off
  int ERRMAP_BADVAL_ABORT ;  // 1=> abort on bad errmap values (default)

  // rebin factor for SED-interp option
  int INTERP_SEDREBIN_LAM ; 
  int INTERP_SEDREBIN_DAY ;

  // optional error fudges
  double MAGERR_FLOOR  ;     // don't let error fall below this value
  double MAGERR_LAMOBS[3];   // magerr=[0] for [1] < lamobs  [2]
  double MAGERR_LAMREST[3];  // magerr=[0] for [1] < lamrest [2]

  // option to force g-band flux to zero at high redshift (Oct 2015)
  double RESTLAM_FORCEZEROFLUX[2];

  int NSHIFT_CALIB;
  SHIFT_CALIB_SALT2_DEF SHIFT_CALIB[MXSHIFT_CALIB_SALT2];

} INPUT_SALT2_INFO ;


// Oct 2020: info specific to SALT3
struct INPUT_SALT3_INFO {
  //  SALT3_COLORPAR_DEF COLORPAR3 ; // color law params
  double FNORM_ERROR[MXFILTINDX]; // convert flux to Flux/Angstron for error

} INPUT_SALT3_INFO;


struct SALT2_SPLINE_ARGS {  
  double  DAY[MXBIN_VAR_SALT2] ;
  double  LAM[MXBIN_VAR_SALT2] ;
  double  VALUE[MXBIN_VAR_SALT2] ; 
  double  DAYLIM[2] ;
  double  LAMLIM[2] ;
} SALT2_SPLINE_ARGS ;


double mBoff_SALT2;
int    ifiltB_SALT2;

// define filenames that contain model-error information
char SALT2_ERRMAP_FILES[MXERRMAP_SALT2][60] ;
char SALT2_ERRMAP_COMMENT[MXERRMAP_SALT2][40] ;
int  NERRMAP_BADRANGE_SALT2;  // bad wave and/or day range
int  NERRMAP_BADVALUE_SALT2 ; // bad map value: nan or crazy value

// 4/30/2011: define SALT2 tables on same lambda grid as SED templates
// These table-lookups are used to speed the integrations.
// All tables are allocated dynamically when the size is known.
struct SALT2_TABLE {
  double **COLORLAW   ;   // color law table [color][lambda]
  double **XTMW_FRAC  ;   // XTMW table [ifilt][lambda]
  double **SEDFLUX[MXSURFACE_SALT2] ;   // SED flux vs. Trest and lambda [iday][ilam]

  // parameters (binning) of SEDFLUX table
  int    NDAY, NLAMSED  ;   // Number of DAY and LAM bins for SEDs
  double *DAY,   *LAMSED ;   // list of DAYs and Lambdas (rest-frame SED)
  double DAYSTEP, LAMSTEP;  // step sizes (rest-frame SED)
  double DAYMIN,  LAMMIN ;
  double DAYMAX,  LAMMAX ;

  // parameters of COLORLAW table
  int NCBIN ;
  double CMIN, CMAX, CSTEP ;
  double *COLOR ;     // list of color values on grid

  double MWEBV_LAST ; // needed to know when to re-make XTMW table

  int INDEX_SPLINE[2] ; // spline index (for spline option)
} SALT2_TABLE ;



// define structure for storing SALT2 spectrum and storing in table.


/**********************************************
   Function Declarations
**********************************************/

int  init_genmag_SALT2(char *model_version, char *model_extrap_latetime, 
		       int OPTMASK );

void genmag_SALT2(int OPTMASK, int ifilt, 
		  double *parList_SN, double *parList_HOST, double mwebv,
		  double z, double z_forErr, int nobs, double *Tobs_list, 
		  double *magobs_list, double *magerr_list );

int  NSURFACE_SALT2(void);

void colordump_SALT2(double lam, double c, char *cfilt);
void errorSummary_SALT2(void) ;

void  fill_SALT2_TABLE_SED(int ised);
void  fill_SALT2_TABLE_COLORLAW(void);   

double SALT2colorCor(double lam_rest, double c); 

double SALT2x0calc(double alpha, double beta, double x1, double c, 
		   double dlmag );

double SALT2mBcalc(double x0); 

double SALT2magerr(double Trest, double lamRest,  double z,
		   double x1, double x2, double Finteg_errPar, int LDMP);

double SALT2magerr_legacy(double Trest, double lamRest,  double z,
			  double x1, double Finteg_errPar, int LDMP);

double SALT2colorDisp(double lam, char *callFun);

void   setFlags_ISMODEL_SALT2(char *version);

void getFileName_SALT2colorDisp(char *fileName) ;
void read_SALT2_INFO_FILE(int OPTMASK);
void read_SALT2errmaps(double Trange[2], double Lrange[2] );
void read_SALT2errmaps_legacy(double Trange[2], double Lrange[2] );
void read_SALT2colorDisp(void);

void check_lamRange_SALT2errmap(int imap);
void check_dayRange_SALT2errmap(int imap);
void check_BADVAL_SALT2errmap(int imap);  // check for Nan & crazy values
void init_BADVAL_SALT2errmap(int imap);  
void init_BADVAL_SALT2errmap_legacy(int imap);  

void get_SALT2_ERRMAP(double Trest, double Lrest, double *ERRMAP );

void load_mBoff_SALT2(void);

void test_SALT2colorlaw1(void);

double magerrFudge_SALT2(double magerr, 
			 double meanlam_obs, double meanlam_rest );

void  init_SALT2interp_SEDFLUX(void);
void  init_SALT2interp_ERRMAP(void);
void  init_calib_shift_SALT2train(void) ;

bool  match_SALT2train(char *survey_calib, char *filter_calib, int ifilt) ;
int copy_filter_trans_SALT2(int ifilt, double **lam, double **trans, 
			    double **transREF) ;

// obs-frame integration (filter-lambda bins)
void INTEG_zSED_SALT2(int OPT_SPEC, int ifilt_obs, double z, double Tobs, 
		      double *parList_SN, double *parList_HOST,
		      double *Finteg, double *Finteg_errPar, 
		      double *Fspec );

int gencovar_SALT2(int MATSIZE, int *ifilt_obs, double *epobs, 
		   double z, double *parList_SN, double *parList_HOST, 
		   double mwebv, double *covar );


// ----------------------------------------------------
// ---------- SPECTROGRAPH FUNCTIONS ------------------
// ----------------------------------------------------

// function to generate spectrum for SPECTROGRAPH option in simulation.
void genSpec_SALT2(double *parList_SN, double *parList_HOST, double mwebv,
		   double z, double Tobs, 
		   double *GENFLUX_LIST,     // (O)
		   double *GENMAG_LIST 	);   // (O)

// function called by analysis program to return spectrum over band.
// Note that all I/O is float instead of double.
int getSpec_band_SALT2(int ifilt_obs, float Tobs, float z,
		       float x0, float x1, float c, float mwebv,
		       float *LAMLIST, float *FLUXLIST);

// SALT2 color laws
// colorlaw0 - version 0 from Guy 2007  
// colorlaw1 - version 1 from Guy 2010
double SALT2colorlaw0(double lam_rest, double c, double *colorPar );
double SALT2colorlaw1(double lam_rest, double c, double *colorPar );

double SALT2colorfun_dpol(const double rl, int nparams,
                          const double *params, const double alpha);
double SALT2colorfun_pol(const double rl, int nparams,
                         const double *params, const double alpha);

// END


