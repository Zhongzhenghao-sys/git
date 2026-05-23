# hermes_守护进程.ps1
# 自动守护飞书网关进程，检测崩溃或卡死后立即重启
# 运行方式：右键 -> 用PowerShell运行，或在新的命令行窗口中运行

$HERMES_DIR = "D:\hermes_agent"
$HERMES_DATA = "C:\Users\Phil.pan\.hermes"
$STATE_FILE = "$HERMES_DATA\gateway_state.json"
$STARTUP_SCRIPT = "$HERMES_DIR\启动飞书网关_稳定版.bat"

# 配置项
$CHECK_INTERVAL = 30          # 每30秒检查一次
$STATE_TIMEOUT = 300          # 状态文件超过5分钟未更新 = 卡死
$AGENT_TASK_TIMEOUT = 600     # agent任务超过10分钟 = 超时重启（长任务保护）

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Hermes Gateway 守护进程已启动" -ForegroundColor Cyan
Write-Host " 检查间隔: ${CHECK_INTERVAL}s" -ForegroundColor Cyan
Write-Host " 状态超时: ${STATE_TIMEOUT}s" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

function Get-GatewayPid {
    try {
        if (Test-Path $STATE_FILE) {
            $content = [System.IO.File]::ReadAllText($STATE_FILE)
            $json = $content | ConvertFrom-Json
            return $json.pid
        }
    } catch {}
    return $null
}

function Is-ProcessAlive {
    param([int]$Pid)
    try {
        $proc = Get-Process -Id $Pid -ErrorAction Stop
        return $proc -ne $null
    } catch {
        return $false
    }
}

function Get-StateAge {
    try {
        if (Test-Path $STATE_FILE) {
            $content = [System.IO.File]::ReadAllText($STATE_FILE)
            $json = $content | ConvertFrom-Json
            $updatedAt = [DateTime]::Parse($json.updated_at).ToUniversalTime()
            $now = [DateTime]::UtcNow
            return ($now - $updatedAt).TotalSeconds
        }
    } catch {}
    return 99999
}

function Get-ActiveAgents {
    try {
        if (Test-Path $STATE_FILE) {
            $content = [System.IO.File]::ReadAllText($STATE_FILE)
            $json = $content | ConvertFrom-Json
            return $json.active_agents
        }
    } catch {}
    return 0
}

function Start-Gateway {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 正在清理锁文件..." -ForegroundColor Yellow
    Remove-Item "$HERMES_DATA\gateway.pid" -Force -ErrorAction SilentlyContinue
    Get-ChildItem $HERMES_DATA -Filter "*.lock" | Remove-Item -Force -ErrorAction SilentlyContinue
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 正在启动网关..." -ForegroundColor Yellow
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$STARTUP_SCRIPT`"" -WorkingDirectory $HERMES_DIR -WindowStyle Normal
    
    # 等待启动
    Start-Sleep -Seconds 12
    $newPid = Get-GatewayPid
    if ($newPid -and (Is-ProcessAlive $newPid)) {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✓ 网关已启动 PID=$newPid" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✗ 网关启动失败，等待下一轮重试" -ForegroundColor Red
        return $false
    }
}

$consecutiveFailures = 0
$agentStartTime = $null
$lastActiveAgents = 0

while ($true) {
    Start-Sleep -Seconds $CHECK_INTERVAL
    
    $gwPid = Get-GatewayPid
    $stateAge = Get-StateAge
    $activeAgents = Get-ActiveAgents
    
    # 检测 agent 任务开始时间（用于超时保护）
    if ($activeAgents -gt 0 -and $lastActiveAgents -eq 0) {
        $agentStartTime = [DateTime]::UtcNow
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Agent 开始处理任务..." -ForegroundColor DarkCyan
    } elseif ($activeAgents -eq 0) {
        $agentStartTime = $null
    }
    $lastActiveAgents = $activeAgents
    
    # 检查1：进程是否存在
    $processAlive = $false
    if ($gwPid) {
        $processAlive = Is-ProcessAlive $gwPid
    }
    
    # 检查2：状态文件是否超时（网关卡死检测）
    # 注意：如果有agent在运行，状态文件更新会变慢，给更长的宽限期
    $effectiveTimeout = if ($activeAgents -gt 0) { $STATE_TIMEOUT * 2 } else { $STATE_TIMEOUT }
    $stateTimedOut = $stateAge -gt $effectiveTimeout
    
    # 检查3：agent任务是否超时
    $agentTimedOut = $false
    if ($agentStartTime -ne $null) {
        $agentRunTime = ([DateTime]::UtcNow - $agentStartTime).TotalSeconds
        if ($agentRunTime -gt $AGENT_TASK_TIMEOUT) {
            $agentTimedOut = $true
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠ Agent任务已运行 $([math]::Round($agentRunTime/60, 1)) 分钟，超过 $($AGENT_TASK_TIMEOUT/60) 分钟限制" -ForegroundColor Magenta
        }
    }
    
    $needRestart = $false
    $reason = ""
    
    if (-not $processAlive) {
        $needRestart = $true
        $reason = "进程 PID=$gwPid 不存在"
    } elseif ($stateTimedOut) {
        $needRestart = $true
        $reason = "状态文件 $([math]::Round($stateAge))s 未更新（超过阈值 ${effectiveTimeout}s）"
    } elseif ($agentTimedOut) {
        $needRestart = $true
        $reason = "Agent任务超时"
    }
    
    if ($needRestart) {
        $consecutiveFailures++
        Write-Host "" 
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠ 检测到问题: $reason" -ForegroundColor Red
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 正在重启网关（第 $consecutiveFailures 次）..." -ForegroundColor Yellow
        
        # 强制终止旧进程
        if ($gwPid -and (Is-ProcessAlive $gwPid)) {
            Stop-Process -Id $gwPid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        $success = Start-Gateway
        if ($success) {
            $consecutiveFailures = 0
            $agentStartTime = $null
            $lastActiveAgents = 0
        }
        
        # 连续失败保护：超过5次失败则等待更长时间
        if ($consecutiveFailures -ge 5) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠ 连续 $consecutiveFailures 次失败，等待60s后重试" -ForegroundColor Red
            Start-Sleep -Seconds 60
        }
    } else {
        # 正常状态，每5分钟输出一次心跳
        $minute = [int](Get-Date -Format 'mm')
        if ($minute % 5 -eq 0 -and [int](Get-Date -Format 'ss') -lt $CHECK_INTERVAL) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✓ 网关正常 PID=$gwPid 状态更新${([math]::Round($stateAge))}s前 活跃Agent=${activeAgents}" -ForegroundColor DarkGreen
        }
    }
}
