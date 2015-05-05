"""A Pydap handler for grib files."""

import os
import re

import gzip

from pkg_resources import get_distribution
from pydap.model import *
from pydap.handlers.lib import BaseHandler
from pydap.handlers.helper import constrain
from pydap.lib import parse_qs, walk
from pydap.exceptions import OpenFileError
import numpy as np
import struct
import copy
import pygrib

def replace_name(pp_name):
    pp_name = str(pp_name)
    for ch in ': ()*%-':
        pp_name = pp_name.replace(ch, '_')
    return pp_name


class GribHandler(BaseHandler):
    regexp = r"^.*\.(gr|grb|grib|gr1|grb1|grib1|gr2|grb2|grib2?|f\d{3}|anl)$"
    extensions = re.compile(regexp, re.IGNORECASE)

    def __init__(self, filepath):
        self.filename = os.path.split(filepath)[1]
        self.grib = pygrib.open(filepath)
        self.dataset = DatasetType(name=self.filename, attributes={
            "GLOBAL": {
                "granule_name": self.filename,
            }
        })


        msg1 = self.grib.message(1)
        self._shape = msg1.data()[0].shape
        _dim = ('lat', 'lon')
        _type = UInt16
        self.lats, self.lons = msg1.latlons()
        self.lats = self.lats[:, 0]
        self.lons = self.lons[0]

        self.variables = []
        for i in range(self.grib.messages):
            pp_name = replace_name(self.grib.message(i+1))

            self.variables.append(
                BaseType(
                    name=str(pp_name),
                    data=None,
                    shape=self._shape,
                    dimensions=_dim,
                    type=_type,
                    attributes={
                    }
                ))

        lonVar = BaseType(
            name='lon',
            data=None,
            shape=(self._shape[1],),
            dimensions=('lon',),
            type=Float32,
            attributes=({
                'long_name': 'longitude',
                # 'add_offset' : 0,
                # 'scale_factor' : 1,
                'valid_range': '-180, 180',
                'units': 'degrees_east'
            })
        )

        latVar = BaseType(
            name='lat',
            data=None,
            shape=(self._shape[0],),
            dimensions=('lat',),
            type=Float32,
            attributes=({
                'long_name': 'latitude',
                # 'add_offset' : 0,
                # 'scale_factor' : 1,
                'valid_range': '-90, 90',
                'units': 'degrees_north'
            })
        )

        self.dataset['lon'] = lonVar
        self.dataset['lat'] = latVar

        for variable in self.variables:
            # print variable.name
            g = GridType(name=variable.name)
            g[variable.name] = variable

            g['lon'] = lonVar.__deepcopy__()
            g['lat'] = latVar.__deepcopy__()
            g.attributes = variable.attributes

            self.dataset[variable.name] = g

    def get_data_for_parameter(self, pp_name, slices):
        for i in range(self.grib.messages):
            if replace_name(self.grib.message(i+1)) == pp_name:
                if slices:
                    return self.grib.message(i+1).data()[0][slices]
                else:
                    return self.grib.message(i+1).data()[0]

    def parse_constraints(self, environ):
        dataset = copy.deepcopy(self.dataset)

        projection, selection = parse_qs(environ.get('QUERY_STRING', ''))
        list_of_var = []
        if projection:
            for var in projection:
                var_name = var[len(var)-1][0]
                if var_name in list_of_var:
                    continue
                list_of_var.append(var_name)
                if var_name in ['lat', 'lon']:
                    if var_name == 'lon':
                        dataset[var_name] = BaseType(name=var_name,
                                                     data=self.lons,
                                                     shape=self.lons.shape,
                                                     dimensions=('lon',),
                                                     type=self.lons.dtype.char)
                    elif var_name == 'lat':
                        dataset[var_name] = BaseType(name=var_name,
                                                     data=self.lats,
                                                     shape=self.lats.shape,
                                                     dimensions=('lat',),
                                                     type=self.lats.dtype.char)
                else:
                    for variable in self.variables:
                        if variable.name == var_name:
                            data = self.get_data_for_parameter(var_name, None)
                            dataset[var_name] = BaseType(name=var_name,
                                                         data=data,
                                                         shape=data.shape,
                                                         dimensions=('lat', 'lon'),
                                                         type=data.dtype.char)
                            break

        return constrain(dataset, environ.get('QUERY_STRING', ''))
