# -*- mode: python -*-
import sys

a = Analysis(['src/cryptully.py'],
             pathex=['/home/shane/Devel/Python/cryptully'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          # Static link the Visual C++ Redistributable DLLs if on Windows
          a.binaries + [('msvcp100.dll', 'C:\\Windows\\System32\\msvcp100.dll', 'BINARY'),
                        ('msvcr100.dll', 'C:\\Windows\\System32\\msvcr100.dll', 'BINARY')]
          if sys.platform == 'win32' else a.binaries,
          a.zipfiles,
          a.datas + [('images/client.png', 'src/images/client.png', 'DATA'),
                     ('images/server.png', 'src/images/server.png', 'DATA'),
                     ('images/light/delete.png', 'src/images/light/delete.png', 'DATA'),
                     ('images/light/exit.png', 'src/images/light/exit.png', 'DATA'),
                     ('images/light/fingerprint.png', 'src/images/light/fingerprint.png', 'DATA'),
                     ('images/light/help.png', 'src/images/light/help.png', 'DATA'),
                     ('images/light/icon.png', 'src/images/light/icon.png', 'DATA'),
                     ('images/light/menu.png', 'src/images/light/menu.png', 'DATA'),
                     ('images/light/save.png', 'src/images/light/save.png', 'DATA'),
                     ('images/light/waiting.gif', 'src/images/light/waiting.gif', 'DATA'),
                     ('images/dark/delete.png', 'src/images/dark/delete.png', 'DATA'),
                     ('images/dark/exit.png', 'src/images/dark/exit.png', 'DATA'),
                     ('images/dark/fingerprint.png', 'src/images/dark/fingerprint.png', 'DATA'),
                     ('images/dark/help.png', 'src/images/dark/help.png', 'DATA'),
                     ('images/dark/icon.png', 'src/images/dark/icon.png', 'DATA'),
                     ('images/dark/menu.png', 'src/images/dark/menu.png', 'DATA'),
                     ('images/dark/save.png', 'src/images/dark/save.png', 'DATA'),
                     ('images/dark/waiting.gif', 'src/images/dark/waiting.gif', 'DATA')],
          name=os.path.join('dist', 'cryptully' + ('.exe' if sys.platform == 'win32' else '')),
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon='src/images/icon.ico')

# Build a .app if on OS X
if sys.platform == 'darwin':
   app = BUNDLE(exe,
                name='cryptully.app',
                icon=None)
