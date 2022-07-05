
#define MXMAP_STRONGLENS 100000
#define MXIMG_STRONGLENS 8   // max number of images per lens

struct {
  int USE_FLAG; // logical flag for simulation
  int NCALL;

  // contents from model file/library
  int   NLENS;     // number of lenses in library
  int   *IDLENS;  // ID for each lens
  float *ZLENS;  // lens redshift
  float *LOGMASS_LENS, *LOGMASS_ERR_LENS;
  float *ZSRC; //source redshift
  int   *NIMG; // Number of images per lens
  float **XIMG, **YIMG ; // X and Y offsets, arcsec
  float **DELAY ; // time delay of each image (days)
  float **MAG; //magnification of each image
  
  char VARNAME_LENSID[40];
  char VARNAME_ZSRC[40];
  char VARNAME_ZLENS[40];
  char VARNAME_LOGMASS_LENS[40];
  char VARNAME_LOGMASS_ERR_LENS[40];
  char VARNAME_NIMG[40];
  char VARNAME_XIMG[40];
  char VARNAME_YIMG[40];
  char VARNAME_MAG[40];
  char VARNAME_DELAY[40];

  int ICOL_LENSID, ICOL_ZSRC, ICOL_ZLENS;
  int ICOL_LOGMASS_LENS, ICOL_LOGMASS_ERR_LENS; // Jun 30 2022
  int ICOL_NIMG, ICOL_XIMG, ICOL_YIMG;
  int ICOL_MAG, ICOL_DELAY;

} INPUTS_STRONGLENS;


// function declarations

void init_stronglens(char *MODEL_FILE);
void malloc_stronglens(int NLENS);

void get_stronglens(double zSN, double *hostpar, int LDMP,
		    int *IDLENS, double *ZLENS, 
		    double *LOGMASS_LENS, double *LOGMASS_ERR_LENS,
		    int *blend_flag, int *NIMG,
		    double *DELAY, double *MAG, double *XIMG, double *YIMG);

double prob_stronglens(double z);

// end:
