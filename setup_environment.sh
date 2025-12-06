#!/bin/bash
# setup_environment.sh
# Script para configurar ambiente para geração de orthomosaicos CBERS-4A

echo "🚀 Configurando ambiente para Gerador de Orthomosaico CBERS-4A"
echo "================================================================"

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8+"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Verificar se pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Instalando..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi

echo "✅ pip encontrado: $(pip3 --version)"

# Detectar sistema operacional
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
else
    OS="Outro"
fi

echo "🖥️ Sistema operacional: $OS"

# Instalar dependências do sistema
if [[ "$OS" == "macOS" ]]; then
    echo "📦 Instalando dependências do sistema (macOS)..."
    
    # Verificar se Homebrew está instalado
    if ! command -v brew &> /dev/null; then
        echo "⚠️ Homebrew não encontrado. Instalando..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    echo "📦 Instalando GDAL e GEOS via Homebrew..."
    brew install gdal geos
    
elif [[ "$OS" == "Linux" ]]; then
    echo "📦 Instalando dependências do sistema (Linux)..."
    
    # Detectar distribuição
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y gdal-bin libgdal-dev libgeos-dev python3-dev
    elif command -v yum &> /dev/null; then
        sudo yum install -y gdal gdal-devel geos geos-devel python3-devel
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y gdal gdal-devel geos geos-devel python3-devel
    else
        echo "⚠️ Distribuição Linux não suportada automaticamente."
        echo "   Por favor, instale GDAL e GEOS manualmente."
    fi
else
    echo "⚠️ Sistema operacional não suportado automaticamente."
    echo "   Por favor, instale GDAL e GEOS manualmente."
fi

# Criar ambiente virtual (opcional mas recomendado)
echo "🔧 Configurando ambiente virtual Python..."

if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    echo "✅ Ambiente virtual criado: ./venv"
else
    echo "✅ Ambiente virtual já existe: ./venv"
fi

# Ativar ambiente virtual
source venv/bin/activate
echo "🔧 Ambiente virtual ativado"

# Atualizar pip
pip install --upgrade pip

# Instalar dependências Python
echo "📦 Instalando dependências Python..."

# Lista de pacotes necessários
PACKAGES=(
    "geopandas"
    "pandas"
    "rasterio"
    "matplotlib"
    "cbers4asat"
    "numpy"
)

for package in "${PACKAGES[@]}"; do
    echo "📦 Instalando $package..."
    pip install "$package"
    
    if [[ $? -eq 0 ]]; then
        echo "✅ $package instalado com sucesso"
    else
        echo "❌ Erro ao instalar $package"
    fi
done

# Verificar instalação
echo ""
echo "🧪 Verificando instalação..."

python3 -c "
try:
    import geopandas as gpd
    print('✅ GeoPandas: OK')
except ImportError as e:
    print('❌ GeoPandas: ERRO -', e)

try:
    import rasterio
    print('✅ Rasterio: OK')
except ImportError as e:
    print('❌ Rasterio: ERRO -', e)

try:
    import matplotlib.pyplot as plt
    print('✅ Matplotlib: OK')
except ImportError as e:
    print('❌ Matplotlib: ERRO -', e)

try:
    from cbers4asat import Cbers4aAPI
    print('✅ CBERS4ASAT: OK')
except ImportError as e:
    print('❌ CBERS4ASAT: ERRO -', e)

try:
    import pandas as pd
    print('✅ Pandas: OK')
except ImportError as e:
    print('❌ Pandas: ERRO -', e)
"

# Verificar se shapefile de exemplo existe
if [[ -f "./limites/es_sem_trindade/ES_UF_2024.shp" ]]; then
    echo "✅ Shapefile de exemplo encontrado"
else
    echo "⚠️ Shapefile de exemplo não encontrado em ./limites/es_sem_trindade/"
fi

# Criar diretórios de saída se não existirem
mkdir -p /tmp/orthomosaico_test
echo "📁 Diretório de teste criado: /tmp/orthomosaico_test"

# Tornar scripts executáveis
chmod +x gerador_orthomosaico.py
chmod +x visualizador.py

echo ""
echo "================================================================"
echo "🎉 Configuração concluída!"
echo "================================================================"
echo ""
echo "📋 Próximos passos:"
echo "1. Ative o ambiente virtual: source venv/bin/activate"
echo "2. Execute o gerador: python gerador_orthomosaico.py --help"
echo "3. Teste com seus dados: python gerador_orthomosaico.py email@exemplo.com caminho/para/shapefile.shp"
echo ""
echo "📖 Para mais informações, consulte o README.md"
echo ""

# Mostrar comando de exemplo
if [[ -f "./limites/es_sem_trindade/ES_UF_2024.shp" ]]; then
    echo "🚀 Comando de exemplo:"
    echo "python gerador_orthomosaico.py seu.email@exemplo.com ./limites/es_sem_trindade/ES_UF_2024.shp --output-dir /tmp/orthomosaico_test"
fi