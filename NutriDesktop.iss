; Inno Setup script - compile locally with ISCC NutriDesktop.iss
#define MyAppName "NutriDesktop"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "NutriDesktop"
#define MyAppExeName "NutriDesktop.exe"

[Setup]
AppId={{A5EBA612-ECD4-436D-9599-4AD8D77E4A40}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\NutriDesktop
DefaultGroupName=NutriDesktop
PrivilegesRequired=admin
OutputDir=installer
OutputBaseFilename=NutriDesktop-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "dist\NutriDesktop.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\NutriDesktop"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\NutriDesktop"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir NutriDesktop"; Flags: nowait postinstall skipifsilent
