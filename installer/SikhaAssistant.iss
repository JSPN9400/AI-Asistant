#define MyAppName "Sikha Assistant"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Sikha"
#define MyAppExeName "SikhaAssistant.exe"

[Setup]
AppId={{7B3E3370-31D2-4D39-9A63-EF8C4E9F21B9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Sikha Assistant
DefaultGroupName=Sikha Assistant
DisableProgramGroupPage=yes
OutputDir=dist\installer
OutputBaseFilename=SikhaAssistantSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Sikha Assistant"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Sikha Assistant"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Sikha Assistant"; Flags: nowait postinstall skipifsilent
