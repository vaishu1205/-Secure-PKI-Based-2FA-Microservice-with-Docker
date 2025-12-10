$ErrorActionPreference = "Stop"
$log = "diag_output.txt"
if (Test-Path $log) { Remove-Item $log -Force }

function Log { param($s) $s.ToString() | Out-File -FilePath $log -Append -Encoding utf8 }

Log "=== DIAGNOSTIC START $(Get-Date -Format o) ==="

Log "PWD: $(Get-Location)"
Log "PowerShell Version: $($PSVersionTable.PSVersion.ToString())"

Log "`nChecking required files:"
Log ("student_public.pem exists: " + (Test-Path student_public.pem))
Log ("student_public_escaped.txt exists: " + (Test-Path student_public_escaped.txt))

if (Test-Path student_public_escaped.txt) {
    $pub = Get-Content student_public_escaped.txt -Raw
    Log ("Escaped key length: " + $pub.Length)
    Log ("Escaped key preview (first 200 chars):")
    Log ($pub.Substring(0,[Math]::Min(200,$pub.Length)))
} else {
    Log "ERROR: student_public_escaped.txt missing."
}

$hostToTest = "eajeyq4r3zljoq4rpovy2nthda0vtjqf.lambda-url.ap-south-1.on.aws"

Log "`nRunning Test-NetConnection to $hostToTest on port 443..."
try {
    $tnc = Test-NetConnection -ComputerName $hostToTest -Port 443 -WarningAction SilentlyContinue
    Log ("TcpTestSucceeded: " + $tnc.TcpTestSucceeded)
    Log ("RemoteAddress: " + $tnc.RemoteAddress)
} catch {
    Log ("Test-NetConnection ERROR: " + $_.Exception.Message)
}

$API_URL = "https://eajeyq4r3zljoq4rpovy2nthda0vtjqf.lambda-url.ap-south-1.on.aws"
$STUDENT_ID = "22P31A1205"
$GIT_URL = "https://github.com/vaishu1205/-Secure-PKI-Based-2FA-Microservice-with-Docker"

Log "`nAPI_URL: $API_URL"
Log "STUDENT_ID: $STUDENT_ID"
Log "GIT_URL: $GIT_URL"

if (-not (Test-Path student_public_escaped.txt)) {
    Log "Cannot continue: student_public_escaped.txt missing."
    Log "=== DIAGNOSTIC END ==="
    exit 1
}

$pubEscaped = Get-Content student_public_escaped.txt -Raw

$body = @{
    student_id = $STUDENT_ID
    github_repo_url = $GIT_URL
    public_key = $pubEscaped
} | ConvertTo-Json -Compress

Log ("JSON payload length: " + $body.Length)
Log "Attempting POST request..."

try {
    $resp = Invoke-RestMethod -Uri $API_URL -Method Post -ContentType "application/json" -Body $body -TimeoutSec 60
    Log "`nPOST succeeded."
    Log ($resp | ConvertTo-Json -Depth 5)

    if ($resp.status -eq "success" -and $resp.encrypted_seed) {
        $resp.encrypted_seed | Out-File -Encoding ascii encrypted_seed.txt
        Log "encrypted_seed saved to encrypted_seed.txt"
    } else {
        Log "ERROR: API returned non-success or missing encrypted_seed."
    }
} catch {
    Log "`nEXCEPTION: $($_.Exception.GetType().FullName)"
    Log "Message: $($_.Exception.Message)"

    if ($_.Exception.Response) {
        try {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $bodyText = $reader.ReadToEnd()
            Log "HTTP Response Body:"
            Log $bodyText
        } catch {
            Log "Could not read HTTP response body: $($_.Exception.Message)"
        }
    } else {
        Log "No HTTP response available (network error)."
    }
}

Log "`n=== DIAGNOSTIC END ==="
