import xarray
import rasterio
import os
import numpy as np
import ellipsis as el

file = '/home/daniel/Ellipsis/db/testset/example.nc'
file = '/home/daniel/Ellipsis/db/swan_output.nc'
file = '/home/daniel/Ellipsis/db/RASTER/knmi.nc'
file = '/home/daniel/Downloads/sresa1b_ncar_ccsm3-example.nc'

usualXSuspects = ['xc', 'longitude', 'lat']
usualYSuspects = ['yc', 'latitude', 'lon']




def parseNetCDF(file, token, epsg = 4326, folderId = None):
    xds = xarray.open_dataset(file, decode_times=False)
    L = list(xds.variables.items())

    names = []
    for i in range(len(L)):
        names = names + [L[i][0]]

    names.sort()

    dims = [{'lower': x.lower(), 'name': x} for x in list(xds.dims)]

    xdim = None
    ydim = None
    for d in dims:
        if d['lower'] in usualXSuspects:
            xdim = d['name']
        if d['lower'] in usualYSuspects:
            ydim = d['name']

    if len(np.array(xds[xdim].coords)) == 0 or len(np.array(xds[ydim].coords)) == 0 or \
            xds[xdim][np.array(xds[xdim].coords)[0]].values[-1] == len(xds[xdim]) and \
            xds[ydim][np.array(xds[ydim].coords)[0]].values[-1] == len(xds[ydim]):
        for d in dims:
            if d['lower'] in usualXSuspects:
                xds = xds.rename_dims({d['name']: 'x'})
            if d['lower'] in usualYSuspects:
                xds = xds.rename_dims({d['name']: 'y'})

        for v in usualYSuspects:
            if v in names:
                xds['y'] = xds[v][:, 0].values
        for v in usualXSuspects:
            if v in names:
                xds['x'] = xds[v][0, :].values

    name = None

    dimnames = [d['name'] for d in dims]
    if 'time' in dimnames:
        timeIndex = dimnames.index('time')
        n_timestamps = xds['time'].shape[0]

    else:
        timeIndex = -1
        n_timestamps = 1

    file_out = 'temp.tif'

    name = file.split('.')[0].split(os.path.sep )[-1]
    pathId = el.path.raster.add(name = name, token = token, parentId=folderId)['id']

    for t in range(n_timestamps):
        timestampId = el.path.raster.timestamp.add(pathId = pathId, token = token)['id']
        name_list = []
        for name in names:
            try:
                if timeIndex == -1:
                    xds[name].rio.to_raster(file_out.replace('.tif', '_' + name + '.tif'))
                elif timeIndex ==0:
                    xds[name][t,:,:].rio.to_raster(file_out.replace('.tif', '_' + name + '.tif'))
                elif timeIndex ==1:
                    xds[name][:,t,:].rio.to_raster(file_out.replace('.tif', '_' + name + '.tif'))
                else:
                    xds[name][:,:,t].rio.to_raster(file_out.replace('.tif', '_' + name + '.tif'))

                xds[name][2, :, :].rio.to_raster(file_out.replace('.tif', '_' + name + '.tif'))
                name_list = name_list + [name]
            except:
                pass


        ws = []
        hs = []
        for name in name_list:
            with rasterio.open(file_out.replace('.tif', '_' + name + '.tif')) as src:
                ws = ws + [src.width]
                hs = hs + [src.height]

        max_w = max(ws)

        for i in range(len(ws)):
            if ws[i] == max_w:
                max_h = hs[i]

        convert_names = []
        for i in range(len(name_list)):
            if ws[i] == max_w and hs[i] == max_h:
                convert_names = convert_names + [name_list[i]]

        # Read metadata for first file
        with rasterio.open(file_out.replace('.tif', '_' + convert_names[0] + '.tif')) as src0:
            meta = src0.meta

        # Update meta to reflect the number of layers
        meta.update(count=len(convert_names))
        meta.update(dtype='float32')

        # Read each layer and write it to stack
        with rasterio.open(file_out, 'w', **meta) as dst:
            for id, layer in enumerate(convert_names, start=1):
                with rasterio.open(file_out.replace('.tif', '_' + layer + '.tif')) as src1:
                    r = src1.read(1)
                    r = r.astype('float32')
                    dst.write_band(id, r)
                    dst.set_band_description(id, name_list[id - 1])

        for name in name_list:
            os.remove(file_out.replace('.tif', '_' + name + '.tif'))
        el.path.raster.timestamp.file.add(pathId = pathId, timestampId=timestampId, token = token, fileFormat='tif', filePath=file_out, epsg=epsg)
        el.path.raster.timestamp.activate(pathId=pathId, timestampId=timestampId, token=token)

    if os.path.exists(file_out):
        os.remove(file_out)

