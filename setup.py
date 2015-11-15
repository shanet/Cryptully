#!/usr/bin/env python2.7

from setuptools import setup
from setuptools import find_packages

setup(
    name='Cryptully',
    version='4.1.3',
    author='Shane Tully',
    author_email='shane@shanetully.com',
    url='https://github.com/shanet/Cryptully',
    license='LGPL3',
    description='An encrypted chat program for those that don\'t know crypto',
    packages=find_packages(),
    package_data={
        'cryptully': ['images/*.png', 'images/light/*.png', 'images/dark/*.png']
    },
    install_requires=[
        'M2Crypto'
        # PyQt4 is also required, but it doesn't play nicely with setup.py
    ],
)
