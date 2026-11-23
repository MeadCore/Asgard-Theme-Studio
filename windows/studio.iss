; Asgard Theme Studio per-user installer (Inno Setup 6). No admin needed; installs to %LOCALAPPDATA%\Programs\Asgard Theme Studio.
; Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin. Copyright (c) 2026 The_Mead_Maker & Odin. MIT License.
#ifndef AppVer
#define AppVer "1.0.0"
#endif
[Setup]
AppId={{5C7E3B1A-2F4D-4E8B-9A61-7D2C0B9E4F13}
AppName=Asgard Theme Studio
AppVersion={#AppVer}
AppVerName=Asgard Theme Studio {#AppVer}
AppPublisher=The_Mead_Maker & Odin
AppCopyright=Copyright (c) 2026 The_Mead_Maker & Odin
VersionInfoVersion={#AppVer}.0
VersionInfoDescription=Asgard Theme Studio installer
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\Asgard Theme Studio
DisableProgramGroupPage=yes
DisableDirPage=auto
OutputDir=..\Output
OutputBaseFilename=Asgard-Theme-Studio-Setup-{#AppVer}
SetupIconFile=studio.ico
UninstallDisplayIcon={app}\Asgard Theme Studio.exe
UninstallDisplayName=Asgard Theme Studio
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
LicenseFile=..\LICENSE

[Tasks]
Name: desktopicon; Description: "Create a &desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\Asgard Theme Studio\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion; Excludes: "*.log,window\*"

[Icons]
Name: "{userprograms}\Asgard Theme Studio"; Filename: "{app}\Asgard Theme Studio.exe"; Comment: "Make themes for Asgard and Valhalla"
Name: "{userdesktop}\Asgard Theme Studio"; Filename: "{app}\Asgard Theme Studio.exe"; Comment: "Make themes for Asgard and Valhalla"; Tasks: desktopicon

[Run]
Filename: "{app}\Asgard Theme Studio.exe"; Description: "Open Asgard Theme Studio now"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Stop only the copy that runs from this install folder.
Filename: "powershell.exe"; Parameters: "-NoProfile -Command ""Get-Process 'Asgard Theme Studio' -ErrorAction SilentlyContinue | Where-Object {{ $_.Path -like '{app}\*' } | Stop-Process -Force"""; Flags: runhidden; RunOnceId: "StopStudio"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var D: String;
begin
  if CurUninstallStep = usPostUninstall then begin
    D := ExpandConstant('{userappdata}\Asgard Theme Studio');
    if DirExists(D) then DelTree(D, True, True, True);
  end;
end;
