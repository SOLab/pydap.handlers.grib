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
        _shape = msg1.data()[0].shape
        _dim = ('lat', 'lon')
        _type = UInt16

        self.variables = []
        for i in range(self.grib.messages):

            self.variables.append(
                BaseType(
                    name=str(self.grib.message(i+1)),
                    data=None,
                    shape=_shape,
                    dimensions=_dim,
                    type=_type,
                    attributes={
                    }
                ))

        lonVar = BaseType(
            name='lon',
            data=None,
            shape=(_shape[1],),
            dimensions=('lon',),
            type=Float32,
            attributes=({
                'long_name' : 'longitude',
                # 'add_offset' : 0,
                # 'scale_factor' : 1,
                'valid_range' : '-180, 180',
                'units' : 'degrees_east'
            })
        )

        latVar = BaseType(
            name='lat',
            data=None,
            shape=(_shape[0],),
            dimensions=('lat',),
            type=Float32,
            attributes=({
                'long_name' : 'latitude',
                # 'add_offset' : 0,
                # 'scale_factor' : 1,
                'valid_range' : '-90, 90',
                'units' : 'degrees_north'
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

    def parse_constraints(self, environ):
        projection, selection = parse_qs(environ.get('QUERY_STRING', ''))

        if projection:
            pass
            # for name in self.f.files:
            #     data = self.f[name][:]
            #     dataset[name] = BaseType(name=name, data=data, shape=data.shape, type=data.dtype.char)

        dataset_copy = copy.deepcopy(self.dataset)
        return dataset_copy
