# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/32813 MHM Hamdhi/Desktop/DocKube/DockKubeDesktop/app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/32813 MHM Hamdhi/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/customtkinter/assets', 'customtkinter/assets')],
    hiddenimports=['customtkinter', 'customtkinter', 'app_update', 'fast_scroller', 'shared_console', 'learning', 'learning_index', 'port_manager', 'devops_tools', 'command_specs', 'docs_content', 'templates_content', 'learning_content_net1', 'learning_content_net2', 'learning_content_net3', 'learning_content_net4', 'learning_content_net5', 'learning_content_net6', 'learning_content_net7', 'learning_content_linux', 'learning_content_se', 'learning_content_sysadmin', 'learning_content_agile', 'learning_content_aws', 'learning_content_delivery', 'learning_content_devops', 'learning_content_security', 'learning_content_firewall', 'learning_content_diagrams', 'learning_content_database', 'learning_content_observability', 'learning_content_sre', 'learning_content_cloud', 'learning_content_fintech', 'learning_content_business', 'learning_content_testing', 'learning_content_deployment', 'learning_content_auth', 'learning_content_python_adv', 'learning_content_python_internals', 'learning_content_fastapi', 'learning_content_email', 'learning_content_crypto', 'learning_content_net_advanced', 'learning_content_ccna', 'learning_content_packettracer', 'learning_content_windows_admin', 'learning_content_linux_admin', 'learning_content_kernel', 'learning_content_diagnostics', 'learning_content_ml', 'learning_content_ai_models', 'learning_content_ai_engineering', 'learning_content_platform', 'learning_content_docker'],
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
    [],
    exclude_binaries=True,
    name='DocKube',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DocKube',
)
