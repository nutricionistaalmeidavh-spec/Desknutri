#define MyAppName "NutriDesk"
#define MyAppVersion "6.0.0"
#define MyAppPublisher "NutriDesk"
#define MyAppExeName "NutriDesktop.exe"
[Setup]
AppId={{A5EBA612-ECD4-436D-9599-4AD8D77E4A40}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\NutriDesktop
DefaultGroupName=NutriDesk
PrivilegesRequired=admin
OutputDir=installer
OutputBaseFilename=NutriDesktop-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}
[Files]
Source: "dist\NutriDesktop.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\NutriDesk"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\NutriDesk"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; Flags: unchecked
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir NutriDesk"; Flags: nowait postinstall skipifsilent
