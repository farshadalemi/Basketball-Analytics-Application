# PowerShell script to test the visual image analysis endpoint

Write-Host "Testing Visual Image Analysis Endpoint" -ForegroundColor Green
Write-Host "=" * 40

# Check if we have a test image
$testImagePath = "test_image.jpg"

if (-not (Test-Path $testImagePath)) {
    Write-Host "No test image found. Please provide a basketball image as 'test_image.jpg'" -ForegroundColor Yellow
    Write-Host "You can use any basketball court image for testing." -ForegroundColor Yellow
    exit 1
}

# Test the visual endpoint
$url = "http://localhost:8001/api/computer-vision/analyze-image-visual"

try {
    Write-Host "Sending request to visual analysis endpoint..." -ForegroundColor Cyan
    
    # Create multipart form data
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    # Read the image file
    $imageBytes = [System.IO.File]::ReadAllBytes($testImagePath)
    
    # Create form data
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"image`"; filename=`"test_image.jpg`"",
        "Content-Type: image/jpeg",
        "",
        [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString($imageBytes),
        "--$boundary",
        "Content-Disposition: form-data; name=`"enable_court_detection`"",
        "",
        "true",
        "--$boundary",
        "Content-Disposition: form-data; name=`"enable_player_detection`"",
        "",
        "true",
        "--$boundary",
        "Content-Disposition: form-data; name=`"enable_team_classification`"",
        "",
        "true",
        "--$boundary",
        "Content-Disposition: form-data; name=`"enable_ball_detection`"",
        "",
        "true",
        "--$boundary--"
    )
    
    $body = $bodyLines -join $LF
    $bodyBytes = [System.Text.Encoding]::GetEncoding("iso-8859-1").GetBytes($body)
    
    # Make the request
    $response = Invoke-WebRequest -Uri $url -Method POST -Body $bodyBytes -ContentType "multipart/form-data; boundary=$boundary" -TimeoutSec 60
    
    if ($response.StatusCode -eq 200) {
        # Save the annotated image
        $outputPath = "annotated_result.jpg"
        [System.IO.File]::WriteAllBytes($outputPath, $response.Content)
        
        Write-Host "✅ Success! Annotated image saved as: $outputPath" -ForegroundColor Green
        Write-Host "Content-Type: $($response.Headers.'Content-Type')" -ForegroundColor Cyan
        Write-Host "Image size: $($response.Content.Length) bytes" -ForegroundColor Cyan
        
        Write-Host "`n🎉 Visual endpoint is working correctly!" -ForegroundColor Green
        Write-Host "You can now use the frontend to upload images and see visual analysis results." -ForegroundColor Green
    } else {
        Write-Host "❌ Error: $($response.StatusCode)" -ForegroundColor Red
        Write-Host "Response: $($response.Content)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Request failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please check if the scouting-service is running on port 8001" -ForegroundColor Yellow
}
