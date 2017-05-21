#! /usr/bin/env python2.7

import os
import shutil
import subprocess
import sys

def clean():
    deleteDirectory('build')
    deleteDirectory('dist')
    deleteDirectory('deb_dist')
    deleteDirectory('Cryptully.egg-info')
    deleteFile('logdict2.7.4.final.0-1.log')


def deleteDirectory(path):
    try:
        shutil.rmtree(path)
    except OSError as ose:
        # Ignore 'no such file or directory' errors
        if ose.errno != 2:
            print(ose)


def deleteFile(path):
    try:
        os.unlink(path)
    except OSError as ose:
        if ose.errno != 2:
            print(ose)


arg = sys.argv[1] if len(sys.argv) >= 2 else None

if arg == 'dist':
    if len(sys.argv) == 3:
        pyinstallerPath = sys.argv[2]
    else:
        pyinstallerPath = input("Path to pyinstaller: ")

    clean()
    subprocess.call(['python2.7', os.path.join(pyinstallerPath, 'pyinstaller.py'), 'cryptully.spec'])

elif arg == 'deb':
    print("Ensure you have the python-stdeb package installed!")
    subprocess.call(['python2.7', 'setup.py', '--command-packages=stdeb.command', 'bdist_deb'])

elif arg == 'rpm':
    subprocss.call(['python2.7', 'setup.py', 'bdist_rpm', '--post-install=rpm/postinstall', '--pre-uninstall=rpm/preuninstall'])

elif arg == 'install':
    subprocess.call(['python2.7', 'setup.py', 'install'])

elif arg == 'source':
    subprocess.call(['python2.7', 'setup.py', 'sdist'])

elif arg == 'run':
    subprocess.call(['python2.7', os.path.join('src', 'cryptully.py')])

elif arg == 'test':
    # Carry the exit code from the tests
    exitCode = subprocess.call(['python2.7', os.path.join('src', 'test.py')])
    sys.exit(exitCode)

elif arg == 'clean':
    clean()

else:
    print("Invalid option\nPossible options: dist, deb, rpm, install, source, run, test, clean")
