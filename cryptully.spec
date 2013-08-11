# -*- mode: python -*-
import sys

a = Analysis(['cryptully/cryptully.py'],
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
          a.datas + [('images/light/delete.png',      'cryptully/images/light/delete.png', 'DATA'),
                     ('images/light/exit.png',        'cryptully/images/light/exit.png', 'DATA'),
                     ('images/light/fingerprint.png', 'cryptully/images/light/fingerprint.png', 'DATA'),
                     ('images/light/help.png',        'cryptully/images/light/help.png', 'DATA'),
                     ('images/light/icon.png',        'cryptully/images/light/icon.png', 'DATA'),
                     ('images/light/menu.png',        'cryptully/images/light/menu.png', 'DATA'),
                     ('images/light/new_chat.png',    'cryptully/images/light/new_chat.png', 'DATA'),
                     ('images/light/save.png',        'cryptully/images/light/save.png', 'DATA'),
                     ('images/light/splash_icon.png', 'cryptully/images/light/splash_icon.png', 'DATA'),
                     ('images/light/waiting.gif',     'cryptully/images/light/waiting.gif', 'DATA'),

                     ('images/dark/delete.png',       'cryptully/images/dark/delete.png', 'DATA'),
                     ('images/dark/exit.png',         'cryptully/images/dark/exit.png', 'DATA'),
                     ('images/dark/fingerprint.png',  'cryptully/images/dark/fingerprint.png', 'DATA'),
                     ('images/dark/help.png',         'cryptully/images/dark/help.png', 'DATA'),
                     ('images/dark/icon.png',         'cryptully/images/dark/icon.png', 'DATA'),
                     ('images/dark/menu.png',         'cryptully/images/dark/menu.png', 'DATA'),
                     ('images/dark/new_chat.png',     'cryptully/images/dark/new_chat.png', 'DATA'),
                     ('images/dark/save.png',         'cryptully/images/dark/save.png', 'DATA'),
                     ('images/dark/splash_icon.png',  'cryptully/images/dark/splash_icon.png', 'DATA'),
                     ('images/dark/waiting.gif',      'cryptully/images/dark/waiting.gif', 'DATA')],
          name=os.path.join('dist', 'cryptully' + ('.exe' if sys.platform == 'win32' else '')),
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon='cryptully/images/icon.ico')

# Build a .app if on OS X
if sys.platform == 'darwin':
   app = BUNDLE(exe,
                name='cryptully.app',
                icon=None)
