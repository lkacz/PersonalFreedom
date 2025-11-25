; Inno Setup Script for Personal Freedom - AI-Powered Focus Blocker
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isinfo.php

#define MyAppName "Personal Freedom"
#define MyAppVersion "2.1"
#define MyAppPublisher "Personal Freedom"
#define MyAppURL "https://github.com/lkacz/PersonalFreedom"
#define MyAppExeName "PersonalFreedom.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application
AppId={{8F3A2B1C-4D5E-6F7A-8B9C-0D1E2F3A4B5C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
InfoBeforeFile=INSTALLER_INFO.txt
OutputDir=installer_output
OutputBaseFilename=PersonalFreedom_Setup_v{#MyAppVersion}
SetupIconFile=
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Start with Windows (recommended)"; GroupDescription: "Startup Options:"

[Files]
; Main executables with AI bundled
Source: "dist\PersonalFreedom.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\PersonalFreedomTray.exe"; DestDir: "{app}"; Flags: ignoreversion
; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "QUICK_START.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "GPU_AI_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion
; Helper scripts
Source: "run_as_admin.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "setup_autostart.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: ""; WorkingDir: "{app}"; Comment: "AI-Powered Focus & Productivity Tool"
Name: "{group}\{#MyAppName} (Tray)"; Filename: "{app}\PersonalFreedomTray.exe"; WorkingDir: "{app}"; Comment: "System Tray Version"
Name: "{group}\Quick Start Guide"; Filename: "{app}\QUICK_START.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Run as admin is required for hosts file modification
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent runascurrentuser shellexec

[Registry]
; Add to startup if selected
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\PersonalFreedomTray.exe"""; Tasks: autostart; Flags: uninsdeletevalue

[Code]
procedure InitializeWizard();
var
  InfoPage: TOutputMsgMemoWizardPage;
begin
  InfoPage := CreateOutputMsgMemoPage(wpWelcome,
    'About Personal Freedom', 
    'AI-Powered Productivity & Focus Tool',
    'Personal Freedom helps you stay focused by blocking distracting websites during work sessions.' + #13#10 + #13#10 +
    'KEY FEATURES:' + #13#10 +
    '  • Website blocking with flexible scheduling' + #13#10 +
    '  • AI-powered productivity insights' + #13#10 +
    '  • GPU-accelerated sentiment analysis' + #13#10 +
    '  • Distraction pattern detection' + #13#10 +
    '  • Achievement system & goal tracking' + #13#10 +
    '  • Smart break suggestions' + #13#10 + #13#10 +
    'FULLY BUNDLED AI:' + #13#10 +
    '  • All AI features work out of the box' + #13#10 +
    '  • No Python or pip installation required' + #13#10 +
    '  • Automatic GPU detection & usage' + #13#10 +
    '  • 100% private - runs completely offline' + #13#10 + #13#10 +
    'FIRST LAUNCH:' + #13#10 +
    '  • May take ~30 seconds (downloading AI models)' + #13#10 +
    '  • Models cached locally (~400MB in AppData)' + #13#10 +
    '  • Subsequent launches are instant' + #13#10 + #13#10 +
    'NOTE: Administrator privileges required for website blocking!'
  );
end;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // Check if already installed
  if RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1') or
     RegKeyExists(HKEY_CURRENT_USER, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1') then
  begin
    if MsgBox('Personal Freedom is already installed. Do you want to uninstall it first?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Attempt uninstall
      if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1', 'UninstallString', UninstallString) then
      begin
        Exec(RemoveQuotes(UninstallString), '/SILENT', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      end;
    end
    else
    begin
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Clean up any previous config if needed
    // (Currently we preserve user settings)
  end;
end;

function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  if MsgBox('Do you want to keep your settings, statistics, and goals?', mbConfirmation, MB_YESNO or MB_DEFBUTTON1) = IDNO then
  begin
    // Delete user data
    DelTree(ExpandConstant('{userappdata}\PersonalFreedom'), True, True, True);
  end;
end;
