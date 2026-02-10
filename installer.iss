; Inno Setup Script for Personal Liberty - AI-Powered Focus Blocker
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isinfo.php

#define MyAppName "Personal Liberty"
#define MyAppVersion "6.0.41"
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
; Automatically close running instances during install/upgrade
CloseApplications=force
CloseApplicationsFilter=PersonalLiberty.exe
RestartApplications=no
; Suppress warning about admin install using per-user areas (expected: we create per-user desktop shortcuts)
UsedUserAreasWarning=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
; Autostart task - only shown when Full Mode is selected (controlled by code)
Name: "autostart"; Description: "Start with Windows as Administrator (recommended for Full Mode)"; GroupDescription: "Startup Options:"; Flags: unchecked

[Files]
; Main executable with AI bundled (includes tray functionality)
Source: "dist\PersonalLiberty.exe"; DestDir: "{app}"; Flags: ignoreversion
; Icons (both .ico and .png for compatibility)
Source: "icons\app.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "icons\tray_ready.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "icons\tray_ready.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "icons\tray_blocking.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "icons\tray_blocking.ico"; DestDir: "{app}"; Flags: ignoreversion
; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "QUICK_START.md"; DestDir: "{app}"; Flags: ignoreversion
; Helper scripts
Source: "run_as_admin.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "setup_autostart.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "setup_no_uac.bat"; DestDir: "{app}"; Flags: ignoreversion
; Cleanup script for uninstall
Source: "cleanup_hosts.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start menu and desktop shortcuts - these are updated in code to use scheduled task for admin mode
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"; WorkingDir: "{app}"; Comment: "AI-Powered Focus & Productivity Tool"
Name: "{group}\Quick Start Guide"; Filename: "{app}\QUICK_START.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Create a "Launcher" scheduled task that can be triggered on-demand to run as admin
; This is separate from the autostart task and is used by shortcuts
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$action = New-ScheduledTaskAction -Execute '\""""{app}\{#MyAppExeName}\""""'; $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest; $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 0); Register-ScheduledTask -TaskName 'PersonalLibertyLauncher' -Action $action -Principal $principal -Settings $settings -Force"""; Tasks: autostart; Flags: runhidden
; Run as admin is required for hosts file modification in Full Mode
; For Light Mode, we don't need admin elevation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent runascurrentuser shellexec
; Create scheduled task with admin privileges for autostart (Full Mode only)
; Use PowerShell to properly handle paths with spaces
; Added: MultipleInstancesPolicy to prevent duplicate starts
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$action = New-ScheduledTaskAction -Execute '\""""{app}\{#MyAppExeName}\""""' -Argument '--minimized'; $trigger = New-ScheduledTaskTrigger -AtLogon; $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest; $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew; Register-ScheduledTask -TaskName 'PersonalLibertyAutostart' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force"""; Tasks: autostart; Flags: runhidden

[Registry]
; Note: We use Task Scheduler instead of registry for admin autostart
; Registry entry removed - it doesn't support admin elevation

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

[UninstallDelete]
; Remove startup shortcut if created manually via setup_autostart.bat
Type: files; Name: "{userappdata}\Microsoft\Windows\Start Menu\Programs\Startup\PersonalLiberty.lnk"
; Remove Quick Launch shortcut
Type: files; Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Personal Liberty.lnk"
; Remove No-UAC desktop shortcut if created via setup_no_uac.bat
Type: files; Name: "{userdesktop}\Personal Liberty (No UAC).lnk"
; Remove log and temporary files (always cleaned - not user data)
Type: files; Name: "{app}\app.log"
Type: files; Name: "{app}\.session_state.json"
; Note: config.json, stats.json, goals.json, bypass_attempts.json are handled
; conditionally in InitializeUninstall() based on user's choice to keep settings

[Code]
// ============================================================================
// Enforcement Mode Selection Variables
// ============================================================================
var
  EnforcementModePage: TWizardPage;
  FullModeRadio: TRadioButton;
  LightModeRadio: TRadioButton;
  FullModeDesc: TNewStaticText;
  LightModeDesc: TNewStaticText;
  ModeInfoLabel: TNewStaticText;
  SelectedEnforcementMode: String;

// ============================================================================
// Create the Enforcement Mode Selection Page
// ============================================================================
procedure CreateEnforcementModePage();
var
  TopPos: Integer;
begin
  EnforcementModePage := CreateCustomPage(
    wpSelectTasks,
    'Choose Blocking Mode',
    'Select how Personal Liberty should enforce focus sessions.'
  );

  TopPos := 8;

  // Introduction text
  ModeInfoLabel := TNewStaticText.Create(EnforcementModePage);
  ModeInfoLabel.Parent := EnforcementModePage.Surface;
  ModeInfoLabel.Left := 0;
  ModeInfoLabel.Top := TopPos;
  ModeInfoLabel.Width := EnforcementModePage.SurfaceWidth;
  ModeInfoLabel.Height := 40;
  ModeInfoLabel.WordWrap := True;
  ModeInfoLabel.Caption := 'This choice affects how effectively sites are blocked. You can change this later in Settings.';
  TopPos := TopPos + 50;

  // Full Mode radio button
  FullModeRadio := TRadioButton.Create(EnforcementModePage);
  FullModeRadio.Parent := EnforcementModePage.Surface;
  FullModeRadio.Left := 0;
  FullModeRadio.Top := TopPos;
  FullModeRadio.Width := EnforcementModePage.SurfaceWidth;
  FullModeRadio.Height := 20;
  FullModeRadio.Caption := 'Full Mode (Recommended)';
  FullModeRadio.Font.Style := [fsBold];
  FullModeRadio.Checked := True;
  SelectedEnforcementMode := 'full';
  TopPos := TopPos + 24;

  // Full Mode description
  FullModeDesc := TNewStaticText.Create(EnforcementModePage);
  FullModeDesc.Parent := EnforcementModePage.Surface;
  FullModeDesc.Left := 24;
  FullModeDesc.Top := TopPos;
  FullModeDesc.Width := EnforcementModePage.SurfaceWidth - 24;
  FullModeDesc.Height := 60;
  FullModeDesc.WordWrap := True;
  FullModeDesc.Caption := 
    '* Blocks sites at the system level - impossible to bypass' + #13#10 +
    '* Requires running the app as Administrator' + #13#10 +
    '* Best for serious focus sessions and building discipline' + #13#10 +
    '* Modifies the Windows hosts file (cleaned up on uninstall)';
  TopPos := TopPos + 75;

  // Light Mode radio button
  LightModeRadio := TRadioButton.Create(EnforcementModePage);
  LightModeRadio.Parent := EnforcementModePage.Surface;
  LightModeRadio.Left := 0;
  LightModeRadio.Top := TopPos;
  LightModeRadio.Width := EnforcementModePage.SurfaceWidth;
  LightModeRadio.Height := 20;
  LightModeRadio.Caption := 'Light Mode (No Admin Required)';
  LightModeRadio.Font.Style := [fsBold];
  TopPos := TopPos + 24;

  // Light Mode description
  LightModeDesc := TNewStaticText.Create(EnforcementModePage);
  LightModeDesc.Parent := EnforcementModePage.Surface;
  LightModeDesc.Left := 24;
  LightModeDesc.Top := TopPos;
  LightModeDesc.Width := EnforcementModePage.SurfaceWidth - 24;
  LightModeDesc.Height := 60;
  LightModeDesc.WordWrap := True;
  LightModeDesc.Caption := 
    '* Shows reminder notifications when visiting blocked sites' + #13#10 +
    '* No administrator privileges needed' + #13#10 +
    '* Good for building awareness and habits' + #13#10 +
    '* Does NOT modify any system files - completely portable';
end;

// ============================================================================
// Update selected mode when radio buttons change
// ============================================================================
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  if CurPageID = EnforcementModePage.ID then
  begin
    if LightModeRadio.Checked then
      SelectedEnforcementMode := 'light'
    else
      SelectedEnforcementMode := 'full';
  end;
end;

// ============================================================================
// Create initial config file with selected enforcement mode
// ============================================================================
procedure CreateInitialConfig();
var
  ConfigPath: String;
  ConfigContent: String;
begin
  ConfigPath := ExpandConstant('{userappdata}\PersonalLiberty\users\Default\config.json');
  
  // Create directory structure
  ForceDirectories(ExtractFilePath(ConfigPath));
  
  // Only create config if it doesn't exist (preserve user settings on upgrade)
  if not FileExists(ConfigPath) then
  begin
    ConfigContent := '{' + #13#10 +
      '  "enforcement_mode": "' + SelectedEnforcementMode + '",' + #13#10 +
      '  "enforcement_mode_set_by_installer": true,' + #13#10 +
      '  "blacklist": [],' + #13#10 +
      '  "whitelist": [],' + #13#10 +
      '  "categories_enabled": {},' + #13#10 +
      '  "minimize_to_tray": true,' + #13#10 +
      '  "startup_sound_enabled": true' + #13#10 +
      '}';
    SaveStringToFile(ConfigPath, ConfigContent, False);
  end;
end;

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
  
  // Kill any running instances before installation
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM PersonalLiberty.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  
  // Remove scheduled task that might be holding the file
  Exec(ExpandConstant('{sys}\schtasks.exe'), '/delete /tn PersonalLibertyAutostart /f', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  
  // Small delay to ensure file handles are released
  Sleep(500);
  
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

procedure InitializeWizard();
begin
  // Create the enforcement mode selection page
  CreateEnforcementModePage();
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ShortcutPath: String;
  PSCommand: String;
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Create initial config with selected enforcement mode
    CreateInitialConfig();
    
    // If Full Mode (autostart task) is selected, update shortcuts to use scheduled task launcher
    // This ensures the app always runs as admin when launched from Start menu or desktop
    if SelectedEnforcementMode = 'full' then
    begin
      // Update Start Menu shortcut to use schtasks to run the launcher task
      ShortcutPath := ExpandConstant('{group}\{#MyAppName}.lnk');
      PSCommand := '-NoProfile -ExecutionPolicy Bypass -Command "' +
        '$shell = New-Object -ComObject WScript.Shell; ' +
        '$shortcut = $shell.CreateShortcut(''' + ShortcutPath + '''); ' +
        '$shortcut.TargetPath = ''schtasks.exe''; ' +
        '$shortcut.Arguments = ''/run /tn PersonalLibertyLauncher''; ' +
        '$shortcut.IconLocation = ''' + ExpandConstant('{app}\app.ico') + ',0''; ' +
        '$shortcut.WorkingDirectory = ''' + ExpandConstant('{app}') + '''; ' +
        '$shortcut.WindowStyle = 7; ' +
        '$shortcut.Description = ''AI-Powered Focus & Productivity Tool (Admin Mode)''; ' +
        '$shortcut.Save()"';
      Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'), PSCommand, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      
      // Update Desktop shortcut if it exists
      ShortcutPath := ExpandConstant('{autodesktop}\{#MyAppName}.lnk');
      if FileExists(ShortcutPath) then
      begin
        PSCommand := '-NoProfile -ExecutionPolicy Bypass -Command "' +
          '$shell = New-Object -ComObject WScript.Shell; ' +
          '$shortcut = $shell.CreateShortcut(''' + ShortcutPath + '''); ' +
          '$shortcut.TargetPath = ''schtasks.exe''; ' +
          '$shortcut.Arguments = ''/run /tn PersonalLibertyLauncher''; ' +
          '$shortcut.IconLocation = ''' + ExpandConstant('{app}\app.ico') + ',0''; ' +
          '$shortcut.WorkingDirectory = ''' + ExpandConstant('{app}') + '''; ' +
          '$shortcut.WindowStyle = 7; ' +
          '$shortcut.Description = ''AI-Powered Focus & Productivity Tool (Admin Mode)''; ' +
          '$shortcut.Save()"';
        Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'), PSCommand, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      end;
    end;
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
    // Delete user data from install directory
    DeleteFile(AppPath + '\config.json');
    DeleteFile(AppPath + '\stats.json');
    DeleteFile(AppPath + '\goals.json');
    DeleteFile(AppPath + '\bypass_attempts.json');
    // Also try AppData location (in case future versions use it)
    DelTree(ExpandConstant('{userappdata}\PersonalLiberty'), True, True, True);
  end;
end;
