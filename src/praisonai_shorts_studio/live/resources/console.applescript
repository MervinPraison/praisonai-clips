on run argv
with timeout of 10 seconds
tell application "System Events"
 tell process "Resolve"
  set frontmost to true
  delay 0.2
  if not (exists (first window whose subrole is "AXFloatingWindow")) then
   click menu bar item "Workspace" of menu bar 1
   click menu item "Console" of menu 1 of menu bar item "Workspace" of menu bar 1
   repeat 30 times
    if exists (first window whose subrole is "AXFloatingWindow") then exit repeat
    delay 0.1
   end repeat
  end if
  perform action "AXRaise" of (first window whose subrole is "AXFloatingWindow")
  set focused of text area 1 of (first window whose subrole is "AXFloatingWindow") to true
  set pendingInput to value of text area 1 of (first window whose subrole is "AXFloatingWindow")
  if pendingInput is not missing value and pendingInput is not "" then error "Console has unsubmitted input; preserving it"
  set previousClipboard to the clipboard as record
  try
   set the clipboard to item 1 of argv
   keystroke "a" using command down
   keystroke "v" using command down
   delay 0.1
   key code 36
   set resultText to ""
   set replyDeadline to (current date) + 30
   repeat 300 times
    if (current date) > replyDeadline then exit repeat
    delay 0.1
    try
     if not (exists (first window whose subrole is "AXFloatingWindow")) then
      click menu bar item "Workspace" of menu bar 1
      click menu item "Console" of menu 1 of menu bar item "Workspace" of menu bar 1
      repeat 30 times
       if exists (first window whose subrole is "AXFloatingWindow") then exit repeat
       delay 0.1
      end repeat
     end if
     set resultText to value of text area 2 of (first window whose subrole is "AXFloatingWindow")
     if resultText contains (item 2 of argv) then exit repeat
    end try
   end repeat
   set the clipboard to previousClipboard
   return resultText
  on error errorMessage number errorNumber
   set the clipboard to previousClipboard
   error errorMessage number errorNumber
  end try
 end tell
end tell
end timeout
end run
