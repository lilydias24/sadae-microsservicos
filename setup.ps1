# ============================================
# Script de Setup - Sistema SADAE
# ============================================
# Este script automatiza a configuração e inicialização
# completa do sistema SADAE no Windows.
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sistema SADAE - Setup Automatizado" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Função para verificar comandos
function Test-Command {
    param($command)
    try {
        if (Get-Command $command -ErrorAction SilentlyContinue) {
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

# Função para verificar porta
function Test-Port {
    param($port)
    $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet -ErrorAction SilentlyContinue
    return $connection
}

# Função para aguardar serviço
function Wait-ForService {
    param($url, $serviceName, $timeout = 90)
    Write-Host "  Aguardando $serviceName iniciar..." -ForegroundColor Yellow -NoNewline
    $elapsed = 0
    $dots = 0
    while ($elapsed -lt $timeout) {
        try {
            $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 3 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host " [OK]" -ForegroundColor Green
                return $true
            }
        } catch {
            # Ignora erros e continua tentando
        }
        Start-Sleep -Seconds 3
        $elapsed += 3
        $dots++
        if ($dots -lt 30) {
            Write-Host "." -ForegroundColor Yellow -NoNewline
        }
    }
    Write-Host " [TIMEOUT]" -ForegroundColor Red
    return $false
}

# Função para encontrar container por serviço
function Get-ContainerName {
    param($serviceName)
    try {
        $containers = docker ps --format "{{.Names}}" 2>&1
        foreach ($container in $containers) {
            if ($container -like "*$serviceName*") {
                return $container.Trim()
            }
        }
    } catch {
        return $null
    }
    return $null
}

# ============================================
# 1. Verificações iniciais
# ============================================
Write-Host '[1/6] Verificando pre-requisitos...' -ForegroundColor Cyan

# Verificar Docker
if (-not (Test-Command "docker")) {
    Write-Host '  [ERRO] Docker nao encontrado!' -ForegroundColor Red
    Write-Host "  Por favor, instale o Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}
Write-Host "  [OK] Docker encontrado" -ForegroundColor Green

# Verificar Docker Compose
if (-not (Test-Command "docker-compose")) {
    Write-Host '  [ERRO] Docker Compose nao encontrado!' -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Docker Compose encontrado" -ForegroundColor Green

# Verificar se Docker está rodando
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host '  [ERRO] Docker nao esta rodando!' -ForegroundColor Red
        Write-Host "  Por favor, inicie o Docker Desktop e tente novamente." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  [OK] Docker esta rodando" -ForegroundColor Green
} catch {
    Write-Host "  [ERRO] Erro ao verificar Docker" -ForegroundColor Red
    exit 1
}

# Verificar portas
Write-Host ""
Write-Host '[2/6] Verificando portas disponiveis...' -ForegroundColor Cyan
$ports = @(3000, 8080, 8001, 8002, 8003, 6379)
$portsInUse = @()
foreach ($port in $ports) {
    if (Test-Port $port) {
        Write-Host "  [AVISO] Porta $port esta em uso" -ForegroundColor Yellow
        $portsInUse += $port
    } else {
        Write-Host "  [OK] Porta $port disponivel" -ForegroundColor Green
    }
}

if ($portsInUse.Count -gt 0) {
    Write-Host ""
    Write-Host '  Atencao: Algumas portas estao em uso.' -ForegroundColor Yellow
    Write-Host '  O sistema pode nao iniciar corretamente se os servicos ja estiverem rodando.' -ForegroundColor Yellow
    $continue = Read-Host "  Deseja continuar mesmo assim? (s/N)"
    if ($continue -ne "s" -and $continue -ne "S") {
        exit 0
    }
}

# ============================================
# 2. Parar containers existentes (se houver)
# ============================================
Write-Host ""
Write-Host '[3/6] Limpando containers existentes...' -ForegroundColor Cyan
try {
    docker-compose down 2>&1 | Out-Null
    Write-Host "  [OK] Containers anteriores removidos" -ForegroundColor Green
} catch {
    Write-Host '  [INFO] Nenhum container anterior encontrado' -ForegroundColor Gray
}

# ============================================
# 3. Construir e iniciar serviços
# ============================================
Write-Host ""
Write-Host '[4/6] Construindo e iniciando servicos...' -ForegroundColor Cyan
Write-Host '  Isso pode levar alguns minutos na primeira execucao...' -ForegroundColor Yellow
Write-Host ""

try {
    docker-compose up --build -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host '  [ERRO] Erro ao construir/iniciar servicos!' -ForegroundColor Red
        Write-Host "  Verifique os logs com: docker-compose logs" -ForegroundColor Yellow
        exit 1
    }
    Write-Host ""
    Write-Host "  [OK] Servicos iniciados com sucesso" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "  [ERRO] Erro ao iniciar servicos: $_" -ForegroundColor Red
    exit 1
}

# ============================================
# 4. Aguardar serviços iniciarem
# ============================================
Write-Host ""
Write-Host '[5/6] Aguardando servicos ficarem prontos...' -ForegroundColor Cyan

# Aguardar bancos de dados
Write-Host "  Aguardando bancos de dados..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar serviços principais
Write-Host ""
    Write-Host '  Verificando servicos:' -ForegroundColor Yellow

$authReady = Wait-ForService "http://localhost:8001/health" "Auth Service"
Start-Sleep -Seconds 2
$coreReady = Wait-ForService "http://localhost:8002/health" "Core Service"
Start-Sleep -Seconds 2
$monitoringReady = Wait-ForService "http://localhost:8003/health" "Monitoring Service"
Start-Sleep -Seconds 2
$gatewayReady = Wait-ForService "http://localhost:8080/health" "API Gateway"

$servicesReady = 0
$totalServices = 4

if ($authReady) { $servicesReady++ }
if ($coreReady) { $servicesReady++ }
if ($monitoringReady) { $servicesReady++ }
if ($gatewayReady) { $servicesReady++ }

if ($servicesReady -lt $totalServices) {
    Write-Host ""
    Write-Host "  [AVISO] $servicesReady de $totalServices servicos estao prontos." -ForegroundColor Yellow
    Write-Host '  Aguarde mais alguns segundos e verifique os logs se necessario.' -ForegroundColor Yellow
    Write-Host '  Para ver logs: docker-compose logs -f [servico]' -ForegroundColor Gray
}

# ============================================
# 5. Executar seeds
# ============================================
Write-Host ""
Write-Host '[6/6] Carregando dados iniciais...' -ForegroundColor Cyan

# Aguardar servicos estarem prontos antes de executar seeds
Start-Sleep -Seconds 5

# Seed do auth-service
Write-Host '  Carregando usuarios...' -ForegroundColor Yellow -NoNewline
$authContainer = Get-ContainerName "auth-service"
if ($authContainer) {
    try {
        $seedAuth = docker exec $authContainer python seed_data.py 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host " [OK]" -ForegroundColor Green
        } else {
            # Verifica se o erro é porque já existe
            if ($seedAuth -match 'already exists' -or $seedAuth -match 'duplicate' -or $LASTEXITCODE -eq 1) {
                Write-Host " [AVISO] (ja populado)" -ForegroundColor Yellow
            } else {
                Write-Host " [AVISO] (erro)" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host " [AVISO] (servico ainda nao pronto)" -ForegroundColor Yellow
    }
} else {
    Write-Host " [AVISO] (container nao encontrado)" -ForegroundColor Yellow
}

# Aguardar um pouco antes do proximo seed
Start-Sleep -Seconds 5

# Seed do core-service
Write-Host '  Carregando dados do sistema...' -ForegroundColor Yellow -NoNewline
$coreContainer = Get-ContainerName "core-service"
if ($coreContainer) {
    try {
        $seedCore = docker exec $coreContainer python seed_data.py 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host " [OK]" -ForegroundColor Green
        } else {
            # Verifica se o erro é porque já existe
            if ($seedCore -match 'already exists' -or $seedCore -match 'duplicate' -or $LASTEXITCODE -eq 1) {
                Write-Host " [AVISO] (ja populado)" -ForegroundColor Yellow
            } else {
                Write-Host " [AVISO] (erro)" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host " [AVISO] (servico ainda nao pronto)" -ForegroundColor Yellow
    }
} else {
    Write-Host " [AVISO] (container nao encontrado)" -ForegroundColor Yellow
}

# ============================================
# 6. Resumo final
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host '  Setup Concluido! [OK]' -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host '>> URLs dos Servicos:' -ForegroundColor Cyan
Write-Host "  Frontend:        http://localhost:3000" -ForegroundColor White
Write-Host "  API Gateway:     http://localhost:8080" -ForegroundColor White
Write-Host "  API Docs:        http://localhost:8080/docs" -ForegroundColor White
Write-Host "  Core Service:    http://localhost:8002" -ForegroundColor White
Write-Host "  Core Docs:       http://localhost:8002/docs" -ForegroundColor White
Write-Host "  Auth Service:    http://localhost:8001" -ForegroundColor White
Write-Host "  Monitoring:      http://localhost:8003" -ForegroundColor White
Write-Host ""

Write-Host '>> Credenciais de Acesso:' -ForegroundColor Cyan
Write-Host "  Operador:" -ForegroundColor White
Write-Host "    Email: operador@sadae.com" -ForegroundColor Gray
Write-Host "    Senha: operador123" -ForegroundColor Gray
Write-Host ""

Write-Host '  Outros usuarios disponiveis:' -ForegroundColor White
Write-Host '    - Cidadao: cidadao@email.com / cidadao123' -ForegroundColor Gray
Write-Host '    - Suporte: suporte@sadae.com / suporte123' -ForegroundColor Gray
Write-Host '    - Gestor Crise: gestor.crise@sadae.com / crise123' -ForegroundColor Gray
Write-Host '    - Gestor Manutencao: gestor.manutencao@sadae.com / manutencao123' -ForegroundColor Gray
Write-Host '    - Gestor Financeiro: gestor.financeiro@sadae.com / financeiro123' -ForegroundColor Gray
Write-Host ""

Write-Host '>> Comandos Uteis:' -ForegroundColor Cyan
Write-Host '  Ver logs:           docker-compose logs -f [servico]' -ForegroundColor Gray
Write-Host '  Parar servicos:     docker-compose down' -ForegroundColor Gray
Write-Host '  Reiniciar servico:  docker-compose restart [servico]' -ForegroundColor Gray
Write-Host '  Status:             docker-compose ps' -ForegroundColor Gray
Write-Host ""

Write-Host '[IMPORTANTE]:' -ForegroundColor Yellow
Write-Host '  Se os seeds nao foram executados, rode manualmente:' -ForegroundColor Yellow
Write-Host '    docker exec <auth-container> python seed_data.py' -ForegroundColor Gray
Write-Host '    docker exec <core-container> python seed_data.py' -ForegroundColor Gray
Write-Host '  Para encontrar os containers: docker ps' -ForegroundColor Gray
Write-Host ""

Write-Host '[OK] Sistema pronto para uso!' -ForegroundColor Green
Write-Host ""

