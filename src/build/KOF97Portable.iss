#define AppName "KOF97 Mod Studio Portable"
#define AppVersion "2026.11.15"
#define PackageDir AddBackslash(SourcePath) + "..\..\dist\KOF97-Portable-20261115"

[Setup]
AppId={{94B939CC-17ED-4688-8437-EA2E4E134F72}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\KOF97 Mod Studio Portable
DefaultGroupName={#AppName}
OutputDir={#PackageDir}\..\Installer
OutputBaseFilename=KOF97-Mod-Studio-Setup-20261115
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
Uninstallable=yes
SetupLogging=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式："; Flags: unchecked

[Files]
Source: "{#PackageDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\KOF97 游戏"; Filename: "{app}\KOF97GameLauncher.exe"; WorkingDir: "{app}"
Name: "{group}\KOF97 Mod Studio"; Filename: "{app}\studio.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\KOF97 游戏"; Filename: "{app}\KOF97GameLauncher.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\studio.exe"; Description: "启动 KOF97 Mod Studio"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent unchecked
