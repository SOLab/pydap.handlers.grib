from setuptools import setup, find_packages
import sys, os


version = '0.1'

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
    'Pydap',
    'ConfigObj',
    'pupynere',
    'Numpy',
    'pygrib',
]


setup(name='pydap.handlers.grib',
    version=version,
    description="Handler for that allows Pydap to serve grib data",
    long_description="",
    classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords='netcdf opendap dods dap science',
    author='Denis Spiridonov',
    author_email='sdi@rshu.ru',
    url='https://github.com/SOLab/pydap.handlers.grib',
    license='MIT',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    namespace_packages = ['pydap', 'pydap.handlers'],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    entry_points="""
        [pydap.handler]
        grib = pydap.handlers.grib:GribHandler
    """,
)
