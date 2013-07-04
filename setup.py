#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages

setup(
    name='Cryptully',
    version='1.0.0',
    author='Shane Tully',
    author_email='shane@shanetully.com',
    url='https://github.com/shanet/Cryptully',
    license='LGPL3',
    description='An encrypted chat program for those that don\'t know crypto',
    packages=find_packages(),
    package_data={
        'cryptully': ['src/images/*']
    },
    install_requires=[
        'Qt4',
        'M2Crypto'
    ],
)
