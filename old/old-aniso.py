"""
make a realization of an 'ill-proportioned' toroidal universe with
given P(k), excise a small cubic box, and examine the vector power
spectrum P(|k|, angle)

"""

#### need to make into a constant Delta f=i/Delta
#### maybe make a class that carries along delta with it?

from __future__ import division

import math
from itertools import tee, izip

import numpy as np
import numpy.random as npr
from matplotlib import pyplot as plt

import realization

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    try:
        b.next()
    except StopIteration:
        pass
    return izip(a, b)




def excise(rlzn, slices):
    """
    excise a region of dimensions n[...] from the realization rlzn.

    slices is a sequence of elements correspinding to slices
    e.g., ( 3, 3, 3 ) for a 3x3x3 submatrix starting at 0,0,0
          ( (1,4), (1,4), (1,4) ) for a  3x3x3 submatrix starting at 1,1,1
    """
    return rlzn[[slice(*s) for s in slices]]

def getAngDist(rlzn, kbin, deltas=None, nk=10, isFFT=False):
    """
    get the actual values of rlzn_k for k in a linear bin,
    as a function of angle
    
    need to normalize by the power -- but need to be more fine-grained than the bincd
    """
    # probably should have fewer angular bins for low k
    rshape = rlzn.shape
    if isFFT:
        rshape[-1] = 2*rshape[-1]-2
        rlznk = rlzn
    else:
        rlznk =np.fft.rfftn(rlzn)

    k =np.sqrt(realization.get_k2(rshape, deltas=deltas))
    
    idxsx =np.squeeze(realization.DFT_indices(rshape, dim1=[0], real=True))
    idxsy =np.squeeze(realization.DFT_indices(rshape, dim1=[1], real=True))
    ang =np.arctan2(idxsy, idxsx)

    kk =np.linspace(0, k.ravel().max(), nk)
    kdxi =np.logical_and(k>kk[kbin-1], k<=kk[kbin])

    return ang[kdxi], rlzn[kdxi]
    

def getPower(rlzn, deltas=None, nk=10, nangle=None, isFFT=False):
    """
    get the power spectrum of the realization, possibly in angular bins
    
    """
    
    ## can use & instead of logical_and???
        
    if nangle < 1 or nangle is None:
        nangle = 1
    
    if deltas is None:
        deltas=1
        
    rshape = rlzn.shape
    if isFFT:
        rshape[-1] = 2*rshape[-1]-2

    k =np.sqrt(realization.get_k2(rshape, deltas=deltas))

    if nangle>1:
        idxsx =np.squeeze(realization.DFT_indices(rshape, dim1=[0], real=True))
        idxsy =np.squeeze(realization.DFT_indices(rshape, dim1=[1], real=True))
        ang =np.arctan2(idxsy, idxsx)
    
    # probably should have fewer angular bins for low k
    if isFFT:
        power =np.absolute(rlzn)**2
    else:
        power =np.absolute(np.fft.rfftn(rlzn))**2
    
    kk =np.linspace(0, k.ravel().max(), nk)
    aa =np.linspace(0, 2*np.pi, nangle+1)
    Pk =np.empty(shape=(nk,nangle), dtype=np.float64)
    Sk =np.empty_like(Pk)
    
    Pk[0,:] = power.flat[0]   ## 0 is always the first DFT index...
    Sk[0,:] = 0

    for ii,ki in enumerate(pairwise(kk)):
        kdxi =np.logical_and(k>ki[0], k<=ki[1])
        for jj, aj in enumerate(pairwise(aa)):
            if nangle>1:
                adxj =np.logical_and(ang>aj[0], ang<=aj[1])
                idx =np.logical_and(kdxi, adxj)
            else:
                idx = kdxi
            Pk[ii+1, jj] = power[idx].mean()
            Sk[ii+1, jj] = power[idx].std()
        
    Pk =np.squeeze(Pk)
    Sk =np.squeeze(Sk)

    volume = (np.array(deltas)*np.array(rshape)).prod()
    Pk /= volume
    Sk /= volume
    ## normalization needed for 'volume factor' 
    #      <dk dk'> = delta(k+k')P(k) => <d^2>=Vol*P(k)
    
    ## or always return the same thing?
    if nangle > 1: 
        return (kk, aa), Pk, Sk
    else:
        return kk, Pk, Sk



def driver(n=0, dims=(512,512), deltas=None, ex=2.0):

    print 'dims=', dims

    Pk = n
    
    delta_k = realization.dft_realizn(dims, Pk, deltas=deltas)

    print 'delta_k: shape=', delta_k.shape

    delta_r =np.fft.irfftn(delta_k)

    print 'delta_r: shape=', delta_r.shape

    assert delta_r.shape==dims

    #### plot the map
    pylab.figure(0)
    pylab.imshow(delta_r)
    pylab.axis('scaled')
    
    print 'map plotted'
    

    ## plot the power spectra
    k, P, S = getPower(delta_r, nk=20)

    pylab.figure(1)
    pylab.loglog(k[1:], P[1:], '.')
    pylab.loglog(k[1:], P[1:]+S[1:])
    
    print 'full spectra plotted'

    ###nb. each entry is a tuple that will be turned into a slice
    ex_dims = [(int(min(dims)/ex),)]*len(dims)
    print 'Excising region of dimensions: ', ex_dims
    ex_delta_r = excise(delta_r, ex_dims)

    ek, eP, eS = getPower(ex_delta_r, nk=20)
    pylab.loglog(ek[1:], eP[1:])
    pylab.loglog(ek[1:], eP[1:]+eS[1:])
    
    print 'excised spectra plotted'

    #plot the power distribution
    nk = 10
    pylab.figure(2)

    nrc = nk-1   ## don't plot k=0
    nr = int(math.sqrt(nrc))
    nc = int(nrc/nr)
    if nr*nc<nrc: nc += 1

    for i in xrange(1,nk):
        pylab.subplot(nr, nc, i)
        ang, rlzk = getAngDist(ex_delta_r, i, nk=nk)
        std =np.sqrt(((np.absolute(rlzk))**2).mean())
        pylab.plot(ang, rlzk.real, '.')
        pylab.plot(ang, rlzk.imag, '.')
        pylab.plot([0,math.pi], [std,std], 'r')
        pylab.plot([0,math.pi], [-std,-std], 'r')
