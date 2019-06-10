# pylint: disable=invalid-name
"""ESMValTool CMORizer for ESACCI-OC data.

Tier

Source
   ftp://oceancolour.org/occci-v3.1/geographic/netcdf/monthly/chlor_a/
   user: oc-cci-data
   pass: ELaiWai8ae

Last access
   20190227

Download and processing instructions
   In case of issues with data download, check also the information provided at
       OceanColour webpage https://esa-oceancolour-cci.org/
   Put all files under a single directory (no subdirectories with years)
   in ${RAWOBS}/Tier2/ESACCI-OC

Modification history
   20190227-A_lova_to: written.

"""

import logging
import os
import glob
import xarray as xr

import iris

from .utilities import (constant_metadata, fix_coords, fix_var_metadata,
                        read_cmor_config, save_variable, set_global_atts)

logger = logging.getLogger(__name__)

# read in CMOR configuration
CFG = read_cmor_config('ESACCI-OC.yml')


def _fix_data(cube, var):
    """Specific data fixes for different variables."""
    logger.info("Fixing data ...")
    with constant_metadata(cube):
        if var == 'chl':
            cube *= 1.e-06
    return cube


def _add_depth_coord(cube):
    """Add depth auxiliary coordinate for CMIP5 standard."""
    if not cube.coords('depth'):
        depth = 1.
        depth_coord = iris.coords.AuxCoord(
            depth,
            standard_name='depth',
            long_name='depth',
            var_name='depth',
            units='m',
            attributes={'positive': 'down'})
        cube.add_aux_coord(depth_coord)
        cube.coordinates = 'depth'


def extract_variable(var_info, raw_info, out_dir, attrs):
    """Extract to all vars."""
    var = var_info.short_name
    cubes = iris.load(raw_info['file'])
    rawvar = raw_info['name']

    for cube in cubes:
        if cube.var_name == rawvar:
            fix_var_metadata(cube, var_info)
            fix_coords(cube)
            _add_depth_coord(cube)
            _fix_data(cube, var)
            set_global_atts(cube, attrs)
            save_variable(
                cube,
                var,
                out_dir,
                attrs,
                local_keys=['coordinates'],
                unlimited_dimensions=['time'],
            )


def merge_data(in_dir, out_dir, raw_info, bins):
    """Merge all data into a single (regridded) file."""
    var = raw_info['name']
    do_bin = True if (bins % 2 == 0) & (bins != 0) else False
    datafile = sorted(glob.glob(in_dir + '/' + raw_info['file'] + '*.nc'))
    for x in datafile:
        ds = xr.open_dataset(x)
        da = ds[var].sel(lat=slice(None, None, -1))
        # remove inconsistent attributes
        for thekeys in [
                'grid_mapping', 'ancillary_variables', 'parameter_vocab_uri'
        ]:
            del da.attrs[thekeys]

        if do_bin:
            da = da.coarsen(lat=bins, boundary='exact').mean()
            da = da.coarsen(lon=bins, boundary='exact').mean()

        if x == datafile[0]:
            newda = da
            thekeys = [
                'creator_name', 'creator_url', 'license', 'sensor',
                'processing_level'
            ]
            dsmeta = dict((y, ds.attrs[y]) for y in thekeys)
            if do_bin:
                dsmeta['BINNING'] = ' '.join([
                    'Data binned using ', "{}".format(bins), 'by',
                    "{}".format(bins), 'cells average'
                ])
            else:
                dsmeta['BINNING'] = ""
            continue

        newda = xr.concat((newda, da), dim='time')

    # save to file
    ds = newda.to_dataset(name=var)
    for x, y in dsmeta.items():
        ds.attrs[x] = y
    thekeys = {
        'lat': {
            '_FillValue': False
        },
        'lon': {
            '_FillValue': False
        },
        'time': {
            'calendar': 'gregorian'
        },
        var: {
            '_FillValue': 1.e20
        }
    }
    datafile = os.path.join(out_dir, raw_info['file'] + '_merged.nc')
    ds.to_netcdf(datafile, encoding=thekeys, unlimited_dims='time')

    logger.info("Merged data written to: %s", datafile)

    return (datafile, dsmeta['BINNING'])


def cmorization(in_dir, out_dir):
    """Cmorization func call."""
    cmor_table = CFG['cmor_table']
    glob_attrs = CFG['attributes']

    logger.info("Starting cmorization for Tier%s OBS files: %s",
                glob_attrs['tier'], glob_attrs['dataset_id'])
    logger.info("Input data from: %s", in_dir)
    logger.info("Output will be written to: %s", out_dir)

    # run the cmorization
    for var, vals in CFG['variables'].items():
        var_info = cmor_table.get_variable(vals['mip'], var)
        glob_attrs['mip'] = vals['mip']
        raw_info = {'name': vals['raw'], 'file': vals['file']}

        # merge yearly data and apply binning
        inpfile, addinfo = merge_data(in_dir, out_dir, raw_info,
                                      CFG['custom']['bin_size'])

        logger.info("CMORizing var %s from file %s", var, inpfile)
        raw_info['file'] = inpfile
        glob_attrs['comment'] = addinfo + glob_attrs['comment']
        extract_variable(var_info, raw_info, out_dir, glob_attrs)

    # Remove temporary input file
    os.remove(inpfile)