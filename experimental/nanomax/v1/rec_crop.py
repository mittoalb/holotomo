import dxchange
import numpy as np
import sys
import ptychotomo

data_prefix = '/gdata/RAVEN/vnikitin/nanomax/'

if __name__ == "__main__":

    n = 512-128
    nz = 512-192
    ndet = 128
    ntheta = 1
    ptheta = 1
    voxelsize = 18.03*1e-7  # cm
    energy = 12.4
    nprb = 128  # probe size
    recover_prb = True
    # Reconstrucion parameters
    model = 'gaussian'  # minimization funcitonal (poisson,gaussian)
    piter = 128  # ptychography iterations
    nmodes = 4
    ngpus = 1
    nscan = 13689

    id_theta = int(sys.argv[1])
    data = np.zeros([1, nscan, ndet, ndet], dtype='float32')
    
    data[0] = np.load(data_prefix+'datanpy/data128sorted_'+str(id_theta)+'.npy')
    scan0 = np.load(data_prefix+'datanpy/scan128sorted_'+str(id_theta)+'.npy')
    shifts = np.load(data_prefix+'/datanpy/shifts.npy')[id_theta]
    scan0[1] -= shifts[1]
    scan0[0] -= shifts[0]
    scan0[1] -= 64
    scan0[0] -= 160

    # ignore position out of field of view
    ids = np.where((scan0[1, 0] < n-nprb)*(scan0[0, 0] <
                                           nz-nprb)*(scan0[0, 0] >= 0)*(scan0[1, 0] >= 0))[0]

    nscan = len(ids)
    scan = scan0[:, :, ids]
    data = data[:, ids]
    print(nscan)

    # init probes
    prb = np.zeros([1, nmodes, nprb, nprb], dtype='complex64')
    prb[:] = np.load(data_prefix+'datanpy/prb128.npy')[:nmodes]
    dxchange.write_tiff(np.abs(prb),data_prefix+'tmp/prbamp',overwrite=True)
    dxchange.write_tiff(np.angle(prb),data_prefix+'tmp/prbang',overwrite=True)
    # Initial guess
    psi = np.ones([1, nz, n], dtype='complex64')

    # data sh
    data = np.fft.fftshift(data, axes=(2, 3))/ndet/ndet

    name = data_prefix+'rec'+str(recover_prb)+str(nmodes)+str(scan.shape[2])

    with ptychotomo.SolverPtycho(ntheta, ptheta, nz, n, nscan, ndet, nprb, nmodes, voxelsize, energy, ngpus) as pslv:
        psi, prb = pslv.grad_ptycho_batch(
            data, psi, prb, scan, psi*0, -1, piter, recover_prb)   

    # Save result
    dxchange.write_tiff(np.angle(psi),  data_prefix+'rec_crop/psiangle'+str(nmodes)+str(nscan)+'/r'+str(id_theta), overwrite=True)
    dxchange.write_tiff(np.abs(psi),   data_prefix+'rec_crop/psiamp'+str(nmodes)+str(nscan)+'/r'+str(id_theta), overwrite=True)
    
    for m in range(nmodes):
        dxchange.write_tiff(np.angle(
            prb[:, m]),   data_prefix+'rec_crop/prbangle/r'+str(id_theta), overwrite=True)
        dxchange.write_tiff(np.abs(
            prb[:, m]),   data_prefix+'rec_crop/prbamp/r'+str(id_theta), overwrite=True)
