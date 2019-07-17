# -*- mode: python -*-

import os
import random
import string
import sys


def rand_string(length=10):
    """Generate random string"""
    return "".join(random.choice(string.printable) for i in range(length))


# TODO: Standardize versioning
name = "Cyckei"
identifier = "com.cyclikal.cyckei"
block_cipher = pyi_crypto.PyiBlockCipher(key=rand_string())
mac_icon = os.path.join("assets", "cyckei.icns")
win_icon = os.path.join("assets", "cyckei.ico")
data = ("assets/*", "assets")
path = os.path.dirname(sys.argv[0])


a = Analysis(["cyckei.py"],
             pathex=[path],
             binaries=[],
             datas=[data],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name=name,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon=win_icon)
app = BUNDLE(exe,
             name="{}.app".format(name),
             icon=mac_icon,
             bundle_identifier=identifier,
             info_plist={
                'NSPrincipalClass': 'NSApplication',
             })
