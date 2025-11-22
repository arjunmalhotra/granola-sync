-- Granola Sync Application
-- Double-click to sync Granola meetings to Basic Memory

on run
	try
		-- Show starting notification
		display notification "Starting Granola sync..." with title "Granola Sync"

		-- Run the import script and capture output
		set scriptPath to (POSIX path of (path to home folder)) & "import-granola-to-memory.py"
		set pythonPath to "/usr/local/bin/python3"

		-- Check if python3 exists at expected location, otherwise try /usr/bin/python3
		try
			do shell script "test -f " & pythonPath
		on error
			set pythonPath to "/usr/bin/python3"
		end try

		-- Run the sync
		set output to do shell script pythonPath & " " & quoted form of scriptPath & " 2>&1"

		-- Parse output for new/updated meetings count (strip ANSI codes first)
		set newCount to 0
		set updatedCount to 0

		try
			-- Strip ANSI color codes and extract numbers
			if output contains "New meetings:" then
				set newCount to (do shell script "echo " & quoted form of output & " | sed 's/\\x1b\\[[0-9;]*m//g' | grep 'New meetings:' | awk '{print $NF}'")
				if newCount is "" then set newCount to "0"
			end if
			if output contains "Updated meetings:" then
				set updatedCount to (do shell script "echo " & quoted form of output & " | sed 's/\\x1b\\[[0-9;]*m//g' | grep 'Updated meetings:' | awk '{print $NF}'")
				if updatedCount is "" then set updatedCount to "0"
			end if
		end try

		-- Prepare success message
		try
			set totalChanges to (newCount as integer) + (updatedCount as integer)
		on error
			set totalChanges to 0
		end try

		if totalChanges > 0 then
			set message to "✅ Synced " & totalChanges & " meeting"
			if totalChanges > 1 then
				set message to message & "s"
			end if
		else
			set message to "✅ All meetings up to date"
		end if

		-- Show success notification
		display notification message with title "Granola Sync Complete"

		-- Also show a dialog so user sees it completed
		display dialog message buttons {"OK"} default button 1 with title "Granola Sync" with icon note giving up after 3

	on error errMsg
		-- Show error notification
		display notification "Sync failed: " & errMsg with title "Granola Sync Error"
		display dialog "Sync failed: " & errMsg buttons {"OK"} default button 1 with title "Granola Sync Error" with icon stop
	end try
end run
