#! /usr/bin/env python

import os
import shutil
import subprocess
import sys

def clean():
    try:
        shutil.rmtree('build')
        shutil.rmtree('dist')
        os.unlink('logdict2.7.4.final.0-1.log')
    except OSError:
        pass

arg = sys.argv[1] if len(sys.argv) >= 2 else None

if arg == 'package':
    if len(sys.argv) == 3:
        pyinstallerPath = sys.argv[2]
    else:
        pyinstallerPath = raw_input("Path to pyinstaller: ")
    clean()
    subprocess.call(['python', os.path.join(pyinstallerPath, 'pyinstaller.py'), 'cryptully.spec'])

elif arg == 'deb':
    print "Ensure you have the python-stdeb package installed!"
    subprocess.call(['python', 'setup.py', '--command-packages=stdeb.command', 'bdist_deb'])

elif arg == 'rpm':
    subprocss.call(['python', 'setup.py', 'bdist_rpm', '--post-install=rpm/postinstall', '--pre-uninstall=rpm/preuninstall'])

elif arg == 'install':
    subprocess.call(['python', 'setup.py', 'install'])

elif arg == 'source':
    subprocess.call(['python', 'setup.py', 'sdist'])

elif arg == 'clean':
    clean()

else:
    print "Invalid option"
    print "Possible options: package, deb, rpm, install, source, clean"
