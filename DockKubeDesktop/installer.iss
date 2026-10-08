; DocKube installer.
;
; Built by build_installer.py, which runs this through ISCC.exe. The output is a
; single DocKubeSetup.exe that installs the whole application, puts a shortcut
; on the desktop and in the Start menu, and registers an uninstaller.
;
; The install directory is deliberately under LOCALAPPDATA rather than
; Program Files. Program Files needs elevation to write to, which would mean the
; in-app Update button could never replace its own files. A per-user install is
; writable, needs no administrator, and still appears in Start menu search.

#define AppName "DocKube"
#define AppVersion "1.8.1"
#define AppPublisher "DocKube"
#define AppExeName "DocKube.exe"
#define SourceDir "dist\DocKube"

[Setup]
AppId={{8D3F2A61-4C7B-4E9A-9E21-5B7C0D4F8A32}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=DocKubeSetup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; The app is a portable build with no code signature, so Windows SmartScreen
; will warn. Allowing the install directly keeps the warning to one click
; instead of an unexplained failure.
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}
; Everything is per-user, so a shared install would need elevation we do not want.
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; The whole bundle, not just the executable. The interpreter and every library
; live in _internal next to the exe, and an install missing either of them dies
; with "Failed to load Python DLL".
Source: "{#SourceDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent