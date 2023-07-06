# Define the file pattern
$filePattern = "probabilities*"

# Define the output zip file name
$zipFileName = "only_probabilities_files.zip"

# Get the directory of the file - put it one above "simulation-results"
$currentDir = Join-Path -Path $PSScriptRoot -ChildPath "simulation-results"

# If you want to do it directly in the shell - use absolute paths
#$currentDir = "C:\Users\Your\Path"
Write-Host "Got currentDir: $currentDir"

# Define the log file name
$logFileName = Join-Path -Path $currentDir -ChildPath "error_log.txt"


try {
    # Get a list of all files in the subdirectory and its subdirectories that match the pattern
    $fileList = Get-ChildItem -Path $currentDir -Recurse -File | Where-Object { $_.Name -like $filePattern }
    Write-Host "Got file list: $fileList"

    # Create a zip file containing the files
    Compress-Archive -Path $fileList.FullName -DestinationPath $zipFileName
    Write-Host "Created zip file"
}
catch {
    # If an error occurs, log it to the error log file
    $_ | Out-File $logFileName -Append
    Write-Host "Caught an error: $_"
}



# to run, you have to be an administrator and invoke "Set-ExecutionPolicy RemoteSigned"
