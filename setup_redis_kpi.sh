#!/bin/bash

# Configuración de Redis optimizada para el sistema de KPIs
# Este script configura Redis para máximo rendimiento con el dashboard

echo "🚀 Configurando Redis para optimización de KPIs..."

# Verificar si Redis está instalado
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis no está instalado. Instalando..."
    
    # Para Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y redis-server
    # Para CentOS/RHEL
    elif command -v yum &> /dev/null; then
        sudo yum install -y redis
    # Para macOS
    elif command -v brew &> /dev/null; then
        brew install redis
    else
        echo "❌ No se puede instalar Redis automáticamente. Por favor instálalo manualmente."
        exit 1
    fi
fi

# Crear directorio de configuración si no existe
sudo mkdir -p /etc/redis/

# Crear configuración optimizada para KPIs
sudo tee /etc/redis/redis-kpi.conf > /dev/null <<EOF
# Configuración Redis optimizada para KPIs EDP Dashboard
# Puerto por defecto
port 6379

# Escuchar en todas las interfaces (cambiar por 127.0.0.1 en producción)
bind 0.0.0.0

# Configuración de memoria
maxmemory 512mb
maxmemory-policy allkeys-lru

# Configuración de persistencia para KPIs
# RDB: Snapshot cada 15 minutos si hay al menos 1 cambio
save 900 1
save 300 10
save 60 10000

# AOF para mayor durabilidad de cache crítico
appendonly yes
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Configuración de rendimiento
tcp-keepalive 300
timeout 0

# Configuración de logs
loglevel notice
logfile /var/log/redis/redis-kpi.log

# Directorio de trabajo
dir /var/lib/redis/

# Configuración de red optimizada
tcp-backlog 511
databases 16

# Configuración específica para cache de KPIs
# Deshabilitar comandos peligrosos en producción
# rename-command FLUSHDB ""
# rename-command FLUSHALL ""
# rename-command DEBUG ""

# Configuración de cliente
maxclients 1000

# Configuración de slowlog para debugging
slowlog-log-slower-than 10000
slowlog-max-len 128

# Configuración de notificaciones para cache expiration
notify-keyspace-events Ex
EOF

# Crear script de inicio optimizado
sudo tee /usr/local/bin/start-redis-kpi.sh > /dev/null <<'EOF'
#!/bin/bash

echo "🚀 Iniciando Redis optimizado para KPIs..."

# Verificar directorio de logs
sudo mkdir -p /var/log/redis
sudo chown redis:redis /var/log/redis

# Verificar directorio de datos
sudo mkdir -p /var/lib/redis
sudo chown redis:redis /var/lib/redis

# Iniciar Redis con configuración optimizada
if [ -f /etc/redis/redis-kpi.conf ]; then
    redis-server /etc/redis/redis-kpi.conf
else
    echo "❌ Archivo de configuración no encontrado"
    exit 1
fi
EOF

sudo chmod +x /usr/local/bin/start-redis-kpi.sh

# Crear script de monitoreo
sudo tee /usr/local/bin/monitor-redis-kpi.sh > /dev/null <<'EOF'
#!/bin/bash

echo "📊 Estado de Redis para KPIs:"
echo "=============================="

# Verificar si Redis está corriendo
if pgrep -x "redis-server" > /dev/null; then
    echo "✅ Redis está ejecutándose"
    
    # Conectar y obtener información
    redis-cli info memory | grep -E "(used_memory_human|maxmemory_human|used_memory_peak_human)"
    echo ""
    
    redis-cli info stats | grep -E "(total_connections_received|total_commands_processed|keyspace_hits|keyspace_misses)"
    echo ""
    
    echo "📈 KPIs Cache Keys:"
    redis-cli eval "
        local keys = redis.call('keys', ARGV[1])
        local result = {}
        for i=1,#keys do
            local ttl = redis.call('ttl', keys[i])
            table.insert(result, keys[i] .. ' (TTL: ' .. ttl .. 's)')
        end
        return result
    " 0 "manager_dashboard:*" | head -10
    
    echo ""
    echo "🔍 Cache Stats:"
    echo "Dashboard keys: $(redis-cli eval "return #redis.call('keys', 'manager_dashboard:*')" 0)"
    echo "KPI keys: $(redis-cli eval "return #redis.call('keys', 'kpis:*')" 0)"
    echo "Chart keys: $(redis-cli eval "return #redis.call('keys', 'charts:*')" 0)"
    
else
    echo "❌ Redis no está ejecutándose"
fi
EOF

sudo chmod +x /usr/local/bin/monitor-redis-kpi.sh

# Crear script de limpieza de cache
sudo tee /usr/local/bin/cleanup-redis-kpi.sh > /dev/null <<'EOF'
#!/bin/bash

echo "🧹 Limpiando cache de KPIs..."

if ! pgrep -x "redis-server" > /dev/null; then
    echo "❌ Redis no está ejecutándose"
    exit 1
fi

# Limpiar cache antiguo (TTL < 60 segundos)
echo "Limpiando entradas con TTL < 60 segundos..."
redis-cli eval "
    local patterns = {'manager_dashboard:*', 'kpis:*', 'charts:*', 'financials:*'}
    local cleaned = 0
    for _, pattern in ipairs(patterns) do
        local keys = redis.call('keys', pattern)
        for _, key in ipairs(keys) do
            local ttl = redis.call('ttl', key)
            if ttl > 0 and ttl < 60 then
                redis.call('del', key)
                cleaned = cleaned + 1
            end
        end
    end
    return cleaned
" 0

echo "✅ Limpieza completada"
EOF

sudo chmod +x /usr/local/bin/cleanup-redis-kpi.sh

# Crear configuración de systemd (para sistemas que lo soporten)
if command -v systemctl &> /dev/null; then
    sudo tee /etc/systemd/system/redis-kpi.service > /dev/null <<EOF
[Unit]
Description=Redis KPI Cache Server
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/start-redis-kpi.sh
User=redis
Group=redis
RuntimeDirectory=redis
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF

    echo "📋 Servicio systemd creado. Para habilitarlo:"
    echo "   sudo systemctl enable redis-kpi"
    echo "   sudo systemctl start redis-kpi"
fi

# Crear archivo de variables de entorno
tee .env.redis >> .env <<EOF

# Redis Configuration for KPI Optimization
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL_DASHBOARD=300
REDIS_CACHE_TTL_KPIS=600
REDIS_CACHE_TTL_CHARTS=900
REDIS_CACHE_TTL_FINANCIALS=1800
EOF

echo ""
echo "✅ Configuración de Redis completada!"
echo ""
echo "📋 Comandos útiles:"
echo "   Iniciar Redis:     /usr/local/bin/start-redis-kpi.sh"
echo "   Monitorear:        /usr/local/bin/monitor-redis-kpi.sh"
echo "   Limpiar cache:     /usr/local/bin/cleanup-redis-kpi.sh"
echo "   Cliente Redis:     redis-cli"
echo ""
echo "🔧 Para probar la configuración:"
echo "   redis-cli ping"
echo "   redis-cli info memory"
echo ""
echo "📊 Para monitorear KPIs en tiempo real:"
echo "   watch -n 2 '/usr/local/bin/monitor-redis-kpi.sh'"
