$ErrorActionPreference = "Stop"
$ErrorView = "NormalView"

$EMAIL = $env:E2E_EMAIL
if ([string]::IsNullOrEmpty($EMAIL)) { $EMAIL = "demo_e2e@asep.ai" }
$PASSWORD = $env:E2E_PASSWORD
if ([string]::IsNullOrEmpty($PASSWORD)) { $PASSWORD = "password123" }

$BASE_URL = "http://localhost:8011/api/v1"

Write-Host "Registering seed user..."
$body = @{
    email = $EMAIL
    password = $PASSWORD
} | ConvertTo-Json
Invoke-RestMethod -Uri "$BASE_URL/auth/e2e/seed-user" -Method Post -ContentType "application/json" -Body $body | Out-Null

Write-Host "Logging in..."
$loginResponse = Invoke-RestMethod -Uri "$BASE_URL/auth/login" -Method Post -ContentType "application/json" -Body $body
$TOKEN = $loginResponse.access_token

$Headers = @{
    "Authorization" = "Bearer $TOKEN"
}

Write-Host "Running agent..."
$body = '{"goal": "Tell me a short fact about space and use a tool to search if you can.", "research_mode": "balanced", "environment_mode": "local"}'
Invoke-RestMethod -Uri "$BASE_URL/conversations/run" -Method Post -ContentType "application/json" -Headers $Headers -Body $body | Out-Null

Write-Host "Waiting 5 seconds for background tasks..."
Start-Sleep -Seconds 5

Write-Host "--- GET ME ---"
Invoke-RestMethod -Uri "$BASE_URL/auth/me" -Method Get -Headers $Headers | ConvertTo-Json -Depth 10

Write-Host "--- WORKING MEMORY ---"
Invoke-RestMethod -Uri "$BASE_URL/memory/?type=working" -Method Get -Headers $Headers | ConvertTo-Json -Depth 10

Write-Host "--- EPISODIC MEMORY ---"
Invoke-RestMethod -Uri "$BASE_URL/memory/?type=episodic" -Method Get -Headers $Headers | ConvertTo-Json -Depth 10

Write-Host "--- SEMANTIC MEMORY ---"
Invoke-RestMethod -Uri "$BASE_URL/memory/?type=semantic" -Method Get -Headers $Headers | ConvertTo-Json -Depth 10

Write-Host "--- PROCEDURAL MEMORY ---"
Invoke-RestMethod -Uri "$BASE_URL/memory/?type=procedural" -Method Get -Headers $Headers | ConvertTo-Json -Depth 10
