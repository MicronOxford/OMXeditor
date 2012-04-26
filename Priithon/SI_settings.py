import ConfigParser
import warnings

class Settings:
    'A wrapper of all options for SI reconstruction'
    def __init__(self):
        self.otffile = ''
        self.corr_fn=''      
        self.crop_nx = 0
        self.crop_ny = 0
        self.FixDrift      = False
        self.search4vector = True
        self.TwoLens       = False
        self.recalcarrays = 1
        self.apodizeoutput = 2  # Triangular
        self.suppress_singularities = 1
        self.suppress_radius = 5
        self.rescale = 1    # How to correct bleaching: 1 -- Inter-direction; 2 -- equalize the whole data set
        self.forceamp = [0.0, 0.0]   # order 1 and 2 modulation amplitudes to be forced to
        self.rzoomfact = 2

        self.orders_factor = [1.0, 20.0, 30.0]

        self.wiener = 0.001

        self.background = 65
        self.ndirs = 3
        self.nphases = 5
        self.phi_list = None
        self.napodize = 10

        self.NA = 1.4
        self.NIMM = 1.5128
        self.SPOTRATIO = 0.06

        self.k0angleguess = [0, 1.047, 2.094] 
        self.linespacing  = 0.203


    def loadSettings(self, settings_file):
        config = ConfigParser.ConfigParser()
        config.read(settings_file)

        if config.has_section("general"):
            if config.has_option("general", "crop"):
                self.crop_nx, self.crop_ny = map(int, config.get("general", "crop").split(','))

            if config.has_option("general", "wiener"):
                self.wiener = config.getfloat("general", "wiener")
            a = {
                "no" : 0,
                "cosine" : 1,
                "triangular" : 2
            }
            if config.has_option("general", "Output apodization"):
                try:
                    self.apodizeoutput =  a[config.get("general", "Output apodization")]
                except KeyError:
                    warnings.warn('Invalid option for output apodization')

            if config.has_option("general", "Input apodization pixels"):
                try:
                    self.napodize = config.getint("general", "Input apodization pixels")
                except ValueError:
                    pass
            if config.has_option("general", "equalize"):
                try:
                    self.rescale = config.getint("general", "equalize")
                except ValueError:
                    pass
            if config.has_option("general", "Fix drift"):
                try:
                    self.FixDrift =  config.getboolean("general", "Fix drift")
                except ValueError:
                    pass
        if config.has_section("microscope"):
            if config.has_option("microscope", "corr file"):
                try:
                    self.corr_fn = config.get("microscope", "corr file")
                except ValueError:
                    pass

            if config.has_option("microscope", "ndirs"):
                try:
                    self.ndirs =  config.getint("microscope", "ndirs")
                except ValueError:
                    pass

            if config.has_option("microscope", "nphases"):
                try:
                    self.nphases =  config.getint("microscope", "nphases")
                except ValueError:
                    pass

            if config.has_option("microscope", "phase list"):
                try:
                    self.phi_list =  map(float, config.get("microscope", "phase_list").split(','))
                except ValueError:
                    pass

            if config.has_option("microscope", "2-lens mode"):
                try:
                    self.twolens =  config.getboolean("microscope", "2-lens mode")
                except ValueError:
                    pass

            if config.has_option("microscope", "line spacing (um)"):
                try:
                    self.linespacing =  config.getfloat("microscope", "line spacing (um)")
                except ValueError:
                    pass

            if config.has_option("microscope", "k0 angles guess"):
                try:
                    self.k0angleguess =  map(float, config.get("microscope", "k0 angles guess").split(','))
                except ValueError:
                    pass

            if config.has_option("microscope", "NA"):
                try:
                    self.NA =  config.getfloat("microscope", "NA")
                except ValueError:
                    pass

            if config.has_option("microscope", "nIMM"):
                try:
                    self.NIMM =  config.getfloat("microscope", "nIMM")
                except ValueError:
                    pass
            if config.has_option("microscope", "order 1, 2 factor"):
                try:
                    self.orders_factor[1:] =  map(float, config.get("microscope", "order 1, 2 factor").split(','))
                except ValueError:
                    pass
            if config.has_option("microscope", "spot ratio"):
                try:
                    self.SPOTRATIO =  config.getfloat("microscope", "spot ratio")
                except ValueError:
                    pass

            if config.has_option("microscope", "background"):
                try:
                    self.background = config.getfloat("microscope", "background")
                except ValueError:
                    pass
            if config.has_option("microscope", "OTF"):
                try:
                    self.otffile = config.get("microscope", "OTF")
                except ValueError:
                    pass

        else:
            warnings.warn('\nNo valid SI_settings.ini file is found. \nIf relevant commandline options are not provided, default settings will be used')
            
    def printall(self):
        print "OTF file:\t\t", self.otffile
        print '#dirs:\t\t\t', self.ndirs
        print '#phases:\t\t', self.nphases
        print '#input apodization:\t', self.napodize
        a = {
            0 : "no",
            1 : "cosine",
            2 : "triangular" 
        }
        print 'Output apodization:\t', a[self.apodizeoutput]
        print 'Two-lens mode?\t\t', self.TwoLens
        print 'Fix drift?\t\t', self.FixDrift
        print 'Data rescaling:\t\t', self.rescale
        if self.corr_fn is not '':
            print 'Flatfielding file:\t', self.corr_fn
        else:
            print '!!No flatfielding file is used.'
            print 'background to subtract:\t', self.background
        print 'Wiener factor:\t\t', self.wiener
        print 'NA:\t\t\t', self.NA
        print 'nImmersion:\t\t', self.NIMM
        print 'k0 angle guess:\t\t', self.k0angleguess
        print 'Line spacing:\t\t', self.linespacing, 'um'
        if self.crop_nx > 0 and self.crop_ny > 0:
            print 'Crop to:\t\t', self.crop_nx, self.crop_ny
        
	
