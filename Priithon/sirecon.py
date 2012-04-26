import SI_settings
import Priithon_bin.om2proc as om2C   ## all the functions that're a lot more time consuming if written in Python
import numpy as N
from Priithon import fftw

def makematrix(nphases, phi_list=None):
    """ This version has two cases: 1. we're certain that phases are equally spaced within 2Pi range;
    2. user supply a list of phases (so that phi_list is not None) actually used (e.g., prototype Nikon SI)
    """
    sepmat = N.empty((nphases,nphases), dtype=N.float32)

    if nphases<1 or nphases>5:
        s = raw_input('In makematrix(), nphases is either >5 or <1. Are you sure you want to continue?')
        if s=='y' or s=='Y':
            pass
        else:
            return -1

    factor = 2.0
    norders = (nphases+1)//2
    if not phi_list: # equal phase steps
        phi = 2*N.pi/nphases
        for j in range(nphases):
            sepmat[0, j] = 1.0/nphases
            for order in range(1,norders):
                sepmat[2*order-1,j] = factor * N.cos(j*order*phi)/nphases
                sepmat[2*order  ,j] = factor * N.sin(j*order*phi)/nphases
    else:  # non-ideal case where user has to supply phase values used in data acquisition
        if len(phi_list) != nphases:
            raise ValueError, "length of phi_list does not equal to nphases=%d" % nphases
        for j in range(nphases):
            sepmat[j,0] = 1.0
            for order in range(1,norders):
                sepmat[j, 2*order-1] = factor * N.cos(order*phi_list[j])
                sepmat[j, 2*order  ] = factor * N.sin(order*phi_list[j])
        # Then invert sepmat
        sepmat = N.linalg.inv(sepmat)

    return sepmat

def separate(raw, sepmat):

    nz_raw, ny, nx = raw.shape
    nphases = sepmat.shape[0]
    nz = nz_raw // nphases
    raw.shape = nz, nphases, ny, nx
    t = raw.transpose(0,2,1,3)
    raw.shape = nphases, nz, ny, nx
    raw[:] = N.dot(sepmat, t)

    del t

sum0 = None  # to hold the lateral sums of the first direction

def rescale(data, direction, method=1):
    ''' To correct bleaching based on method chosen
    Method 1 -- only the same section across all directions are equalized;
    Method 2 -- sections of the entire dataset are equalized to overalll section 0.
    Criterion of equalizing is the sum of order 0 intensity
    '''
    global sum0
    
    # data's shape is (nphases, nz, ny, nx)

    nz = data.shape[1]

    xy_sums = N.sum(N.sum(data, 3), 2)

    if direction == 0:
        sum0 = xy_sums.copy()

    if method == 2:
        ref = sum0[0, 0]
    elif method == 1:
        ref = sum0[0]  # entire row (length=nz) will be reference
    else:
        print 'Unknown rescaling method ', method
        raise
    
    if not (direction == 0 and method == 1):   # otherwise nothing to be done
        ratio = ref / xy_sums[0]   # ref could be scalar or an array of length nz, doesn't matter
        ratio.shape = (nz, 1, 1)   # so we can multiply it with a 4D array (data)
        data *= ratio

def apodize(indat, napodize):

    nz, ny, nx = indat.shape
    
    factor = 1 - N.sin( (N.arange(napodize, dtype=N.float32) + 0.5) / napodize * N.pi/2 )
    for in2d in indat:

        diffV = (in2d[-1] - in2d[0])/2
        factorV = N.repeat(factor.reshape(napodize,1), nx, axis=1)
        in2d[:napodize, :] += diffV * factorV
        in2d[-napodize:,:] -= diffV * factorV[::-1]

        diffH = (in2d[:,-1] - in2d[:,0])/2
        factorH = N.repeat(factor.reshape(1, napodize), ny, axis=0)
        in2d[:, :napodize] += diffH.reshape(ny, 1) * factorH
        in2d[:, -napodize:] -= diffH.reshape(ny, 1) * factorH[:,::-1]
        
def findpeak(array2d, peak):
    # Locates the peak of the 2D array to sub-pixel precision by fitting a parabola
    # to the highest pixel and its 4 neighbors.
    from Priithon.all import U
    
    maxval, max_z, max_y, max_x = U.findMax(array2d)
    a1 = array2d[max_y, max_x-1]
    a2 = maxval
    a3 = array2d[max_y, max_x+1]
    peak.x = fitparabola(a1,a2,a3) + max_x

    a1 = array2d[max_y-1, max_x]
    a3 = array2d[max_y+1, max_x]
    peak.y = fitparabola(a1,a2,a3) + max_y

def fitparabola(a1, a2, a3):
    slope = 0.5 * (a3-a1)
    curve = (a3+a1) - 2*a2
    if curve == 0:
        print "no peak: a1=%f, a2=%f, a3=%f, slope=%f, curvature=%f" %  (a1, a2, a3, slope, curve)
        peak = 0
    else:
        peak = -slope / curve
        if peak > 1.5 or peak < -1.5:
            raise ValueError, "bad peak position: a1=%f, a2=%f, a3=%f, slope=%f, curvature=%f, peak=%f" \
                  % (a1, a2, a3, slope, curve, peak)
    return peak

def fitxyparabola(x1, y1, x2, y2, x3, y3):

    if x1==x2 or x2==x3 or x3==x1:
        print "Fit fails; two points are equal: x1=%f, x2=%f, x3=%f" %(x1, x2, x3)
        return 0.0
    xbar1 = 0.5 * (x1 + x2)               # middle of x1 and x2
    xbar2 = 0.5 * (x2 + x3)               # middle of x2 and x3
    slope1 = (y2-y1)/(x2-x1)              # the slope at (x=xbar1)
    slope2 = (y3-y2)/(x3-x2)              # the slope at (x=xbar2)
    curve = (slope2-slope1) / (xbar2-xbar1)       # The change in slope per unit of x
    if curve == 0:
        print "Fit fails; no curvature: r1=(%f,%f), r2=(%f,%f), r3=(%f,%f) slope1=%f, slope2=%f, curvature=%f\n" \
              % (x1, y1, x2, y2, x3, y3, slope1, slope2, curve)
        return 0.0

    peak = xbar2 - slope2/curve          #the x value where slope = 0

    return peak

def flatfield(rdat, corr):

    if rdat.shape[-2] != corr.shape[-2] or rdat.shape[-1] != corr.shape[-1]:  # corr file could be 2D or 3D
        raise ValueError, "In flatfield(), image size doesn't match correction file"
    
    rdat -= corr[0]  # this works sec by sec as long as the last two dimensions of rdat and corr[0] matches
    if len(corr.shape) > 2 and corr.shape[0] > 1:
        rdat *= corr[1]

	
class SISolver:
    def __init__(self, inFile, settings_file = '', otf_file = ''):#, wiener = 0.0001, background = 0, ndirs = 3, nphases = 5):
        self.infile = inFile
        self.params = SI_settings.Settings()
        if settings_file != '':
            self.params.loadSettings(settings_file)

        if otf_file != '':
            self.params.otffile = otf_file

        ## these are the parameters most likely users want to change at class instantiation
#         self.params.weiner = wiener
#         self.params.background = background
#         self.params.ndirs = ndirs
#         self.params.nphases = nphases

        self.validate_files()  ## validate input, OTF, and CCD correction (if any) files

    
    def validate_files(self):
        ''' Validating input file, OTF file, and CCD correction file
        '''
        from Priithon.all import Mrc
        try:
            self.indat = Mrc.bindFile(self.infile)
        except IOError:
            print "Can't open MRC file %s" % self.infile
            raise
        except:
            raise

        if self.indat.shape[0] % (self.params.nphases*self.params.ndirs) != 0:
            print "Error: the number of sections in raw data is not right"
            raise ValueError

        try:
            self.otf = Mrc.bindFile(self.params.otffile)
        except IOError:
            print "Can't open MRC file ", self.params.otffile
            raise
        except:
            raise

        self.otf_Mrc_hdr_d = self.otf.Mrc.hdr.d ## store header info before N.asarray() destroy it
        self.otf = N.asarray(self.otf, dtype=N.complex64)   ## N.asarray(): force native byte-order complex64; force in-memory 

        if self.params.corr_fn is not '':
            try:
                self.corr = Mrc.bindFile(self.params.corr_fn)
            except IOError:
                print "Can't open correction file ", self.params.corr_fn
                raise
            except:
                raise
        else:
            self.corr=N.zeros((2,self.indat.shape[-2], self.indat.shape[-1]), dtype=N.float32)
            self.corr[0,:,:] = self.params.background
            self.corr[1,:,:] = 1.0

    def SIrecon(self, returnB4assm=False):
        '''
        The main SI reconstruction procedure; calls self.preprocess(), self.filterbands(), and self.assemblerealspacebands()
        returnB4assm -- if True, return the filtered bands before assembly is done
        '''
        all_bands = self.preprocess()
        
        if returnB4assm:     # sometime one wants to see the intermediate results before assembly
            output_bands = [None]*self.params.ndirs
        else:
            bigbuffer = N.empty((self.nz, self.params.rzoomfact*self.ny, self.params.rzoomfact*self.nx), N.complex64) # work place for storing bands and shifting them
            outbuffer = N.zeros((self.nz, self.params.rzoomfact*self.ny, self.params.rzoomfact*self.nx), N.float32)   # work place for assembly

        for d in range(self.params.ndirs):
            bands = all_bands[d]

            print "Before filterbands"
            self.filterbands(d, bands)

            if returnB4assm:
                output_bands[d]=bands
            else:
                print "Before assembling bands"
                self.assemblerealspacebands(d, outbuffer, bigbuffer, bands)

        if returnB4assm:
            return output_bands
        else:
            return outbuffer

    def preprocess(self):
        '''
        1. separate
        2. find k0 (illumination wave vector)
        3. find modulation amplitude (complex)
        '''
        # gather essential header info
        orig_nz, orig_ny, orig_nx = self.indat.shape
        nz = orig_nz // (self.params.ndirs*self.params.nphases)


        if self.otf.shape[0] > 3:
            l = raw_input("OTF file has more than 3 sections. Are you sure that's correct?")
            if l == 'y' or l == 'Y':
                pass
            else:
                raise RuntimeError, "User stopped program"

        norders = (self.params.nphases+1)//2

        dy, _dummy , dz = self.indat.Mrc.hdr.d
        wave = self.indat.Mrc.hdr.wave[0]

        dkzotf, dkrotf, _dummy = self.otf_Mrc_hdr_d

        if self.params.crop_nx<orig_nx and self.params.crop_nx>0 and self.params.crop_ny<orig_ny and self.params.crop_ny>0:
            Crop = True
            nx = self.params.crop_nx
            ny = self.params.crop_ny
        else:
            Crop = False
            nx = orig_nx
            ny = orig_ny

        inscale = 1.0/(nx*ny*nz)

        dkr = 1.0/(ny*dy)
        dkz = 1.0/(nz*dz)

        ## save these information so that other class methods can see them
        self.norders = norders
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.dy = dy
        self.dz = dz
        self.wave = wave
        self.nzotf = self.otf.shape[-1]
        self.dkzotf = dkzotf
        self.dkrotf = dkrotf
        self.dkz = dkz
        self.dkr = dkr

        if self.params.FixDrift:  ## find out amount of drift
            drift = self.determinedrift()
            print 'Estimated drift is (x,y,z):'
            print '(',drift[1],') and (', drift[2], ')'

        k0magguess = (1/self.params.linespacing)/dkr

        # Allocate memory or placeholder

        all_bands = [None] * self.params.ndirs
        overlap0 = N.empty((nz, ny, nx), dtype=N.complex64)
        overlap1 = N.empty((nz, ny, nx), dtype=N.complex64)

        amp = N.empty((self.params.ndirs, norders), dtype=N.complex64)
        k0 = [None] * self.params.ndirs

        for direction in range(self.params.ndirs):
            bands = [None] * self.params.nphases
            floatimage = self.load_sep(direction)

            floatimage *= inscale

            if self.params.rescale:
                rescale(floatimage, direction, self.params.rescale)

            for i in range(self.params.nphases):
                bands[i] = fftw.rfft(floatimage[i], inplace=0)
            del floatimage

            k0[direction] = om2C.vector(k0magguess * N.cos(self.params.k0angleguess[direction]),
                                        k0magguess * N.sin(self.params.k0angleguess[direction]), 0)

            print "k0guess[%d] is (%f,%f) " % (direction, k0[direction].x, k0[direction].y)

            if direction != 0 and self.params.FixDrift:
                dr = om2C.vector(drift[direction][0], drift[direction][1], drift[direction][2])
                om2C.fixdrift_3D(bands, norders, dr, nx, ny, nz)

            if self.params.search4vector:
                self.findk0(bands, overlap0, overlap1, k0[direction])
                print "k0[%d] is (%f,%f) " % (direction, k0[direction].x, k0[direction].y)

                self.fitk0andmodamps(bands, overlap0, overlap1, k0[direction], amp[direction])
            else:
                for order in range(1, norders):
                    amp[direction, order] = self.findrealspacemodamp(bands, overlap0, overlap1, order, k0[direction])
                    print "modamp mag = %f, phase = %f" %(N.absolute(amp[direction,order]), 
                                                          N.arctan2(amp[direction,order].imag, amp[direction,order].real))
            #if self.params.forceamp[0] > 0.0 or self.params.forceamp[1] > 0.0:
            if N.array(self.params.forceamp).any():
                for order in range(1, norders):
                    if self.params.forceamp[order-1] > 0.0:
                        print "order %d's amps forced to %f" % (order, self.params.forceamp[order-1])
                        factor = self.params.forceamp[order-1] / N.absolute(amp[direction,order])
                        amp[direction, order] *= factor
            all_bands[direction] = bands
                        
        del overlap0
        del overlap1

        self.modamps = amp
        self.k0s = k0

        return all_bands
    ## end of preprocess()

    def filterbands(self, dir, bands):
        '''
        Just a wrapper for SWIGed filterbands() function
        '''
        om2C.filterbands(dir, bands, self.k0s, self.params.ndirs, self.norders, self.otf, self.dkrotf, self.dkzotf, self.nzotf, 
                         self.dy, self.dz, self.modamps, self.nx, self.ny, self.nz, self.wave, self.params.apodizeoutput, 
                         self.params.suppress_singularities, self.params.suppress_radius, self.params.wiener, self.params.NA, 
                         self.params.NIMM, self.params.SPOTRATIO, self.params.TwoLens)

    def assemblerealspacebands(self, dir, outbuffer, bigbuffer, bands):
        '''assemble the filtered bands into their right place. Done in real space for subpixel accuracy
        '''

        fact = 2.0

        # move center band to bigbuffer, fill in with zeroes
        om2C.move(bands, 0, bigbuffer, self.nx, self.ny, self.nz, self.params.rzoomfact)
        # transform it into real space
        fftw.ifft(bigbuffer, inplace=1)

        outbuffer += bigbuffer.real

        yindArr, xindArr = N.indices((self.ny*self.params.rzoomfact, self.nx*self.params.rzoomfact))
        xindArr -= self.nx*self.params.rzoomfact//2
        yindArr -= self.ny*self.params.rzoomfact//2

        for order in range(1, self.norders):
            #move side band to bigbuffer, fill in with zeroes
            om2C.move(bands, order, bigbuffer, self.nx, self.ny, self.nz, self.params.rzoomfact)
            fftw.ifft(bigbuffer, inplace=1)
            k0x = self.k0s[dir].x * float(order) / (self.norders-1)
            k0y = self.k0s[dir].y * float(order) / (self.norders-1)

            # calculate lookup tables
            angleArr = fact * N.pi * (xindArr * k0x/(self.params.rzoomfact*self.nx) + yindArr * k0y/(self.params.rzoomfact*self.ny))
            coslookup = N.cos(angleArr).astype(N.float32)
            sinlookup = N.sin(angleArr).astype(N.float32)
            om2C.insert_sidebands(outbuffer, bigbuffer, coslookup, sinlookup, self.nx*self.params.rzoomfact, self.ny*self.params.rzoomfact, self.nz)

    def determinedrift(self):
        from Priithon.all import U
        nz, ny, nx = self.nz, self.ny, self.nx
        nphases = self.params.nphases

        nxy2 = (nx+2)*ny #nx+2 because in-place FFT
        subz = nz//2 #the number of middle sections to include in drift estimation

        rdistcutoff = int(self.params.NA*2/(self.wave/1000.0) / self.dkr)
    
        drift=[None]*self.params.ndirs
        for i in range(self.params.ndirs):
            drift[i] = N.array([0.,0.,0.])

        # allocate space for order 0 bands of all directions and calculate them
        bandcenter = [None] * self.params.ndirs
    
        for i in range(self.params.ndirs):
            bandcenter[i] = N.empty((subz, ny, nx+2), dtype=N.float32)
            bandcenter[i][:,:,:nx] = N.average(N.reshape(self.indat[i*nphases*nz+(nz-subz)//2*nphases:
                                                                        i*nphases*nz+(nz+subz)//2*nphases].astype(N.float32),
                                                         (subz,nphases,ny,nx)), 1)
        
            bandcenter[i][:,:,:nx] -= self.params.background
            bandcenter[i] = fftw.rfft(bandcenter[i], None, inplace=1)
            # bandcenter[i] now is complex
            bandcenter[i] /= nx*ny*subz

            if i > 0:   # for the 2nd and 3rd pattern directions

                # real-space cross-correlation is Fourier-space multiplication
                crosscorr = bandcenter[i].conj()
                crosscorr *= bandcenter[0]
                crosscorr = fftw.irfft(crosscorr, None, 1) ### Now crosscorr is in real space

                # find the peak (z,y,x) of crosscorr and fit parabola
                valmax, zmax, ymax, xmax = U.findMax(crosscorr)

                xminus = xmax-1
                if xminus < 0:
                    xminus += nx
                xplus  = xmax+1
                if xplus >= nx:
                    xplus -= nx
                yminus = ymax-1
                if yminus < 0:
                    yminus += ny
                yplus = ymax+1
                if yplus >= ny:
                    yplus -= ny
                zminus = zmax-1
                if zminus < 0:
                    zminus += subz
                zplus = zmax+1
                if zplus >= subz:
                    zplus -= subz

                drift[i][2] = zmax + fitparabola(abs(crosscorr[zminus,ymax,xmax]), abs(valmax),
                                                 abs(crosscorr[zplus,ymax,xmax]))
                if drift[i][2] > subz//2:
                    drift[i][2] -= subz

                drift[i][1] = ymax + fitparabola(abs(crosscorr[zmax,yminus,xmax]), abs(valmax),
                                                 abs(crosscorr[zmax,yplus,xmax]))
                if drift[i][1] > ny//2:
                    drift[i][1] -= ny

                drift[i][0] = xmax + fitparabola(abs(crosscorr[zmax,ymax,xminus]), abs(valmax),
                                             abs(crosscorr[zmax,ymax,xplus]))
                if drift[i][0] > nx//2:
                    drift[i][0] -= nx


        for i in range(self.params.ndirs):
            del bandcenter[0]

        return drift

    def load_sep(self, dir, phi_list=None):
        """
        Load stack of one direction (dir), flat-field if corr is not None, appodize if napodize>0, and then separate.
        User can specify phi_list in case N*2Pi/nphases (N in range(nphases)) is not used in reality
        """

        nRawSec = self.nz * self.params.nphases
        sec = dir * nRawSec   ## which section in the original file to start reading

        floatimage = N.zeros((nRawSec, self.ny, self.nx), dtype=N.float32)
   
        floatimage[:] = self.indat[sec:sec+nRawSec, :, :]

        flatfield(floatimage, self.corr)

        if self.indat[0, -1, -1] == -1: # old CH250 CCD (OM2) problem at corner when even binning
            floatimage[:, -1, -1] = (floatimage[:,-1,-2] + floatimage[:,-2,-1]) / 2

        if (self.params.napodize > 0):
            apodize(floatimage, self.params.napodize)

        sepMatrix = makematrix(self.params.nphases, phi_list)
        separate(floatimage, sepMatrix)

        return floatimage


    def findk0(self, bands, overlap0, overlap1, k0):
        # A coarse first step to estimate k0 using 2D cross-correlation

        fitorder = self.norders - 1
        nz, ny, nx = overlap0.shape

        self.makeoverlaps(bands, overlap0, overlap1, fitorder, k0)
        # the returned overlap arrays are in real space, but are still complex since we cut out a 
        # non-hermitian part in fourier space

        # multiply and retransform (i.e. cross-correlate).  Average over z to get 2D lateral-only correlation
        crosscorr = N.sum(overlap0 * overlap1.conjugate(), 0)  # sum() along z axis (axis 0)

        fftw.fft(crosscorr, None, inplace=1)

        crosscorr = N.absolute(crosscorr)

        findpeak(crosscorr, k0)
        k0.x *= float(self.norders-1)/fitorder
        k0.y *= float(self.norders-1)/fitorder

        if k0.x > nx//2:
            k0.x -= nx
        if k0.y > ny//2:
            k0.y -= ny

    def fitk0andmodamps(self, bands, overlap0, overlap1, k0, amps):

        nz, ny, nx = overlap0.shape

        deltaangle = 0.001
        deltamag = 0.1

        k0mag = N.sqrt(k0.x*k0.x + k0.y*k0.y)
        k0angle = N.arctan2(k0.y, k0.x)

        fitorder = self.norders-1
        redoarrays = self.params.recalcarrays >= 1
        x2 = k0angle
        amp2 = self.getmodamp(k0angle, k0mag, bands, overlap0, overlap1, fitorder, redoarrays)
        redoarrays = self.params.recalcarrays >= 3
        angle = k0angle + deltaangle
        x3 = angle
        amp3 = self.getmodamp(angle, k0mag, bands, overlap0, overlap1, fitorder, redoarrays)

        if N.absolute(amp3) > N.absolute(amp2):
            while N.absolute(amp3) > N.absolute(amp2):
                amp1 = amp2
                x1 = x2
                amp2 = amp3
                x2 = x3
                angle += deltaangle
                x3 = angle
                amp3 = self.getmodamp(angle, k0mag, bands, overlap0, overlap1, fitorder, redoarrays)

        else:
            angle = k0angle
            a = amp3
            amp3 = amp2
            amp2 = a
            a = x3
            x3 = x2
            x2 = a
            while N.absolute(amp3) > N.absolute(amp2):
                amp1 = amp2
                x1 = x2
                amp2 = amp3
                x2 = x3
                angle -= deltaangle
                x3 = angle
                amp3 = self.getmodamp(angle, k0mag, bands, overlap0, overlap1, fitorder, redoarrays)
        #the maximum of modamp(x) is now between x1 and x3
        angle = fitxyparabola(x1, N.absolute(amp1), x2, N.absolute(amp2), x3, N.absolute(amp3))  #this should be a good angle.

        x2 = k0mag
        amp2 = self.getmodamp(angle, k0mag, bands, overlap0, overlap1, fitorder, redoarrays)
        mag = k0mag + deltamag
        x3 = mag
        amp3 = self.getmodamp(angle, mag, bands, overlap0, overlap1, fitorder, redoarrays)
        if N.absolute(amp3) > N.absolute(amp2):
            while N.absolute(amp3) > N.absolute(amp2):
                amp1 = amp2
                x1 = x2
                amp2 = amp3
                x2 = x3
                mag += deltamag
                x3 = mag
                amp3 = self.getmodamp(angle, mag, bands, overlap0, overlap1, fitorder, redoarrays)
        else:
            mag = k0mag
            a = amp3
            amp3 = amp2
            amp2 = a
            a = x3
            x3 = x2
            x2 = a
            while N.absolute(amp3) > N.absolute(amp2):
                amp1 = amp2
                x1 = x2
                amp2 = amp3
                x2 = x3
                mag -= deltamag
                x3 = mag
                amp3 = self.getmodamp(angle, mag, bands, overlap0, overlap1, fitorder, redoarrays)
        mag = fitxyparabola(x1, N.absolute(amp1), x2, N.absolute(amp2), x3, N.absolute(amp3))

        print "Optimum modulation amplitude:"
        redoarrays = self.params.recalcarrays>=2
        amps[fitorder] = self.getmodamp(angle, mag, bands, overlap0, overlap1, fitorder, redoarrays)
        print "Optimum k0 angle=%f, length=%f, spacing=%f microns" % (angle, mag, 1.0/(mag*self.dkr))

        k0.x = mag * N.cos(angle)
        k0.y = mag * N.sin(angle)
        print "amp=%f, phase=%f" % (N.absolute(amps[fitorder]), N.arctan2(amps[fitorder].imag, amps[fitorder].real))
    
        redoarrays = True
        for order in range(1, self.norders):
            if order != fitorder:
                amps[order] = self.getmodamp(angle, mag, bands, overlap0, overlap1, order, redoarrays)
            
                print "amp=%f, phase=%f" % (N.absolute(amps[order]), N.arctan2(amps[order].imag, amps[order].real))
        

    def makeoverlaps(self, bands, overlap0, overlap1, fitorder, k0):

        nz, ny, nx = overlap0.shape
    
        om2C.makeoverlaps(bands, overlap0, overlap1, nx, ny, nz, fitorder, self.norders, k0.x, k0.y, self.dy, self.dz, self.otf, self.dkzotf,
                          self.dkrotf, self.nzotf, self.wave, self.params.NA, self.params.NIMM, self.params.SPOTRATIO, 
                          N.array(self.params.orders_factor, dtype=N.float32), self.params.twolens)

        fftw.ifft(overlap0, inplace = 1)
        fftw.ifft(overlap1, inplace = 1)

    def getmodamp(self, angle, mag, bands, overlap0, overlap1, order, redoarrays):

        k0 = om2C.vector(mag*N.cos(angle), mag*N.sin(angle), 0)
        modamp = self.findrealspacemodamp(bands, overlap0, overlap1, order, k0, redoarrays)

        print "angle=%f, mag=%f, amp=%f, phase=%f" % (angle, mag, N.absolute(modamp), N.arctan2(modamp.imag, modamp.real))
        return modamp

    def findrealspacemodamp(self, bands, overlap0, overlap1, order, k0, redoarrays):

        nz, ny, nx = overlap0.shape

        if redoarrays:
            self.makeoverlaps(bands, overlap0, overlap1, order, k0)

        k0x = k0.x * float(order) / (self.norders-1)
        k0y = k0.y * float(order) / (self.norders-1)
        
        yindArr, xindArr = N.indices((ny, nx))
        xindArr -= nx//2
        yindArr -= ny//2

        expiphi = N.empty((ny, nx), dtype=N.complex64)
        angle = 2*N.pi * (xindArr*k0x/nx + yindArr*k0y/ny)
        expiphi.real[:] = N.cos(angle)
        expiphi.imag[:] = N.sin(angle)
    
        sumXstarY = (overlap0.conj() * (overlap1 * expiphi)).sum()
        sumXmag = (overlap0 * overlap0.conjugate()).real.sum()
    
        modamp = sumXstarY / sumXmag
        return modamp
