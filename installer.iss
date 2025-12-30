; Inno Setup Script for Personal Liberty - AI-Powered Focus Blocker
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isinfo.php

#define MyAppName "Personal Liberty"
#define MyAppVersion "4.0.0"
#define MyAppPublisher "Personal Liberty"
#define MyAppURL "https://github.com/lkacz/PersonalLiberty"
#define MyAppExeName "PersonalLiberty.exe"

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
OutputBaseFilename=PersonalLiberty_Setup_v{#MyAppVersion}
SetupIconFile=icons\app.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\app.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Start with Windows (recommended)"; GroupDescription: "Startup Options:"
Name: "nouac"; Description: "Create no-UAC shortcut (skip admin prompt on launch)"; GroupDescription: "Startup Options:"; Flags: unchecked

[Files]
; Main executable with AI bundled (includes tray functionality)
Source: "dist\PersonalLiberty.exe"; DestDir: "{app}"; Flags: ignoreversion
; Icons
Source: "icons\app.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "icons\tray_ready.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "icons\tray_blocking.png"; DestDir: "{app}"; Flags: ignoreversion
; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "QUICK_START.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "GPU_AI_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion
; Helper scripts
Source: "run_as_admin.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "setup_autostart.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "setup_no_uac.bat"; DestDir: "{app}"; Flags: ignoreversion
; Cleanup script for uninstall
Source: "cleanup_hosts.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"; WorkingDir: "{app}"; Comment: "AI-Powered Focus & Productivity Tool"
Name: "{group}\Quick Start Guide"; Filename: "{app}\QUICK_START.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Run as admin is required for hosts file modification
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent runascurrentuser shellexec
; Create no-UAC scheduled task if selected
Filename: "{sys}\schtasks.exe"; Parameters: "/create /tn ""PersonalLibertyLauncher"" /tr """"""{app}\{#MyAppExeName}"""""" /sc onlogon /rl highest /f"; Tasks: nouac; Flags: runhidden

[Registry]
; Add to startup if selected (uses main app with --minimized to start in tray)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"" --minimized"; Tasks: autostart; Flags: uninsdeletevalue

[UninstallRun]
; Kill running processes first
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM PersonalLiberty.exe"; Flags: runhidden; RunOnceId: "KillMain"
; Remove scheduled task if exists
Filename: "{sys}\schtasks.exe"; Parameters: "/delete /tn PersonalLibertyAutostart /f"; Flags: runhidden; RunOnceId: "RemoveTask"
Filename: "{sys}\schtasks.exe"; Parameters: "/delete /tn PersonalLibertyLauncher /f"; Flags: runhidden; RunOnceId: "RemoveNoUACTask"
; Run cleanup script before uninstall (primary method)
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\cleanup_hosts.ps1"" -Silent"; Flags: runhidden waituntilterminated; RunOnceId: "CleanupHosts"
; Flush DNS cache
Filename: "{sys}\ipconfig.exe"; Parameters: "/flushdns"; Flags: runhidden waituntilterminated; RunOnceId: "FlushDNS"

[Code]
// Helper function to run PowerShell cleanup script
function RunCleanupScript(AppPath: String): Boolean;
var
  ResultCode: Integer;
  PSPath: String;
  ScriptPath: String;
  Params: String;
begin
  Result := True;
  
  // Get PowerShell path
  PSPath := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  ScriptPath := AppPath + '\cleanup_hosts.ps1';
  
  // Check if cleanup script exists
  if FileExists(ScriptPath) then
  begin
    // Run PowerShell with execution policy bypass and silent mode
    Params := '-NoProfile -ExecutionPolicy Bypass -File "' + ScriptPath + '" -Silent';
    
    // Execute and wait for completion
    if not Exec(PSPath, Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
      // PowerShell execution failed, try alternative method
      Result := False;
    end;
  end;
end;

// Alternative cleanup using direct file manipulation (backup method)
procedure DirectHostsCleanup();
var
  HostsPath: String;
  HostsContent: AnsiString;
  StartPos, EndPos: Integer;
  MarkerStart, MarkerEnd: String;
  NewContent: String;
begin
  MarkerStart := '# === Personal Liberty BLOCK START ===';
  MarkerEnd := '# === Personal Liberty BLOCK END ===';
  HostsPath := ExpandConstant('{sys}\drivers\etc\hosts');
  
  if FileExists(HostsPath) then
  begin
    if LoadStringFromFile(HostsPath, HostsContent) then
    begin
      StartPos := Pos(MarkerStart, HostsContent);
      if StartPos > 0 then
      begin
        EndPos := Pos(MarkerEnd, HostsContent);
        if EndPos > StartPos then
        begin
          // Calculate the end position including the marker
          EndPos := EndPos + Length(MarkerEnd);
          
          // Build new content without the block
          NewContent := Copy(HostsContent, 1, StartPos - 1) + Copy(HostsContent, EndPos + 1, Length(HostsContent));
          
          // Write back
          SaveStringToFile(HostsPath, NewContent, False);
        end;
      end;
    end;
  end;
end;

// Flush DNS cache
procedure FlushDNSCache();
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\ipconfig.exe'), '/flushdns', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  UninstallString: String;
begin
  Result := True;
  
  // Check if already installed
  if RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1') or
     RegKeyExists(HKEY_CURRENT_USER, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1') then
  begin
    if MsgBox('Personal Liberty is already installed. Do you want to uninstall it first?', mbConfirmation, MB_YESNO) = IDYES then
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

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppPath: String;
begin
  // Run cleanup at the start of uninstall process (before files are deleted)
  if CurUninstallStep = usUninstall then
  begin
    AppPath := ExpandConstant('{app}');
    
    // Try PowerShell script first
    if not RunCleanupScript(AppPath) then
    begin
      // Fall back to direct cleanup
      DirectHostsCleanup();
    end;
    
    // Always flush DNS
    FlushDNSCache();
  end;
end;

function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
  AppPath: String;
begin
  Result := True;
  AppPath := ExpandConstant('{app}');
  
  // First, clean up the hosts file BEFORE asking about user data
  // This ensures blocked sites are always unblocked on uninstall
  
  // Try PowerShell script first (more reliable)
  if not RunCleanupScript(AppPath) then
  begin
    // Fall back to direct cleanup
    DirectHostsCleanup();
  end;
  
  // Always flush DNS
  FlushDNSCache();
  
  // Now ask about keeping user data
  if MsgBox('Do you want to keep your settings, statistics, and goals?', mbConfirmation, MB_YESNO or MB_DEFBUTTON1) = IDNO then
  begin
    // Delete user data
    DelTree(ExpandConstant('{userappdata}\PersonalLiberty'), True, True, True);
  end;
end;
