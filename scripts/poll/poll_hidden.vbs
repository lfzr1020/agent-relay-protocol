' Hidden window wrapper: runs poll_task.cmd invisibly via Task Scheduler.
' Assumes layout: %USERPROFILE%\.agent-relay\scripts\poll\poll_task.cmd
Dim sh, cmd
Set sh = CreateObject("Wscript.Shell")
cmd = """" & sh.ExpandEnvironmentStrings("%USERPROFILE%") & "\.agent-relay\scripts\poll\poll_task.cmd"""
sh.Run cmd, 0, False
