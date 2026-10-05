# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/32813 MHM Hamdhi/Desktop/DocKube/DockKubeDesktop/app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/32813 MHM Hamdhi/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/customtkinter/assets', 'customtkinter/assets')],
    hiddenimports=['customtkinter', 'customtkinter', 'app_update', 'fast_scroller', 'shared_console', 'learning', 'learning_index', 'port_manager', 'devops_tools', 'command_specs', 'docs_content', 'templates_content', 'learning_content_net1', 'learning_content_net2', 'learning_content_net3', 'learning_content_net4', 'learning_content_net5', 'learning_content_net6', 'learning_content_net7', 'learning_content_linux', 'learning_content_se', 'learning_content_sysadmin', 'learning_content_agile', 'learning_content_aws', 'learning_content_delivery', 'learning_content_devops', 'learning_content_security', 'learning_content_firewall', 'learning_content_diagrams', 'learning_content_database', 'learning_content_observability', 'learning_content_sre', 'learning_content_cloud', 'learning_content_fintech', 'learning_content_business'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PIL', 'Pillow', 'numpy', 'pandas', 'matplotlib', 'scipy', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'pytest', 'setuptools', 'pip', 'unittest', 'pydoc', 'doctest', 'lib2to3', 'distutils'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DocKube',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
