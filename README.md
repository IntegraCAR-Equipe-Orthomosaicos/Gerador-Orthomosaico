# Gerador de Orthomosaico CBERS-4A

Scripts Python para gerar orthomosaicos do estado do Espírito Santo usando imagens CBERS-4A WPM L4 DN.

## 📁 Arquivos

- **`gerador_orthomosaico.py`**: Script principal para geração do orthomosaico
- **`visualizador.py`**: Script para visualização de resultados
- **`workflow-sigma.ipynb`**: Notebook Jupyter original (referência)

## 🚀 Instalação de Dependências

```bash
pip install geopandas pandas rasterio matplotlib cbers4asat
```

### Dependências do Sistema (macOS)

```bash
# GDAL/GEOS (necessário para GeoPandas)
brew install gdal geos

# Alternativa com conda
conda install -c conda-forge geopandas rasterio matplotlib cbers4asat
```

## 📖 Uso Básico

### 1. Geração do Orthomosaico

```bash
# Uso mínimo
python gerador_orthomosaico.py seu.email@exemplo.com ./limites/es_sem_trindade/es.shp

# Uso completo com opções
python gerador_orthomosaico.py seu.email@exemplo.com ./limites/es_sem_trindade/es.shp \
    --output-dir /Volumes/Mestrado \
    --data-inicio 2025-01-01 \
    --data-fim 2025-06-30 \
    --cloud-cover 30
```

#### Parâmetros

- **`email`**: Email para API CBERS-4A (obrigatório)
- **`shapefile`**: Caminho para shapefile da área de interesse (obrigatório)
- **`--output-dir`**: Diretório de saída (padrão: `/Volumes/Mestrado`)
- **`--data-inicio`**: Data de início da busca (formato: YYYY-MM-DD)
- **`--data-fim`**: Data de fim da busca (formato: YYYY-MM-DD)
- **`--cloud-cover`**: Cobertura máxima de nuvens em % (padrão: 40)

### 2. Visualização de Resultados

```bash
# Visualizar mosaico final
python visualizador.py /Volumes/Mestrado/mosaico_final_es.tif

# Visualizar com limites do estado
python visualizador.py /Volumes/Mestrado/mosaico_final_es.tif \
    --shapefile ./limites/es_sem_trindade/es.shp \
    --salvar resultado_visual.png

# Visualizar cobertura das imagens selecionadas
python visualizador.py --cobertura /Volumes/Mestrado/mosaico_cbers4a_es.geojson \
    ./limites/es_sem_trindade/es.shp

# Gerar relatório de arquivos
python visualizador.py --relatorio /Volumes/Mestrado/
```

## 🔄 Workflow Completo

O script executa automaticamente as seguintes etapas:

1. **📍 Carregamento da Geometria**: Lê o shapefile da área de interesse
2. **🔍 Busca de Imagens**: Consulta a API CBERS-4A por imagens no período
3. **🎯 Seleção Otimizada**: Escolhe a melhor imagem por path/row (menor cobertura de nuvens)
4. **💾 Download**: Baixa bandas RGB (BAND1=Blue, BAND2=Green, BAND3=Red)
5. **🌈 Composição RGB**: Cria compostos RGB de cada imagem
6. **🗺️ Reprojeção**: Padroniza para EPSG:4674 (SIRGAS 2000)
7. **🔀 Fusão**: Combina todas as imagens em um único mosaico
8. **✂️ Recorte**: Corta o mosaico pela geometria do estado
9. **📊 Resultado**: Gera orthomosaico final pronto para uso

## 📁 Arquivos Gerados

```
/Volumes/Mestrado/
├── mosaico_cbers4a_es.geojson      # Metadados das imagens selecionadas
├── mosaico_final_es.tif            # 🎯 RESULTADO FINAL
├── imagens/                        # Imagens CBERS-4A originais baixadas
│   ├── CBERS_4A_WPM_*/            # Uma pasta por imagem
│   └── ...
└── mosaico_partes/                # Composições RGB individuais
    ├── CBERS_4A_WPM_*.tif
    └── ...
```

## ⚠️ Considerações Importantes

### Recursos Computacionais

- **RAM Recomendada**: 16GB+ (mosaicos podem ser muito grandes)
- **Espaço em Disco**: 5-20GB dependendo do número de imagens
- **Processamento**: Pode levar várias horas dependendo da cobertura

### Limitações de Memória

Se encontrar erros de memória:

1. **Execute em máquina com mais RAM**
2. **Reduza o período de busca** (menos imagens)
3. **Aumente o filtro de nuvens** (imagens mais seletivas)
4. **Execute em lotes menores** se necessário

### Formato de Saída

- **Formato**: GeoTIFF com suporte BIGTIFF
- **Compressão**: LZW para reduzir tamanho
- **CRS**: EPSG:4674 (SIRGAS 2000)
- **Estrutura**: Tiled para melhor performance

## 🐛 Solução de Problemas

### Erro: "cbers4asat não encontrado"
```bash
pip install cbers4asat
```

### Erro: "GDAL/GEOS não encontrado"
```bash
# macOS
brew install gdal geos

# Ubuntu/Debian
sudo apt-get install gdal-bin libgdal-dev libgeos-dev

# Conda (recomendado)
conda install -c conda-forge gdal geos
```

### Erro de Memória durante Processamento
- Reduza o período de busca (`--data-inicio` e `--data-fim`)
- Aumente o filtro de nuvens (`--cloud-cover`)
- Execute em máquina com mais RAM
- Considere processar regiões menores

### API CBERS-4A não responde
- Verifique conexão com internet
- Confirme se o email está correto
- Tente novamente após alguns minutos (pode haver limitação de taxa)

## 📊 Exemplo Completo

```bash
# 1. Gerar orthomosaico para primeiro semestre de 2025
python gerador_orthomosaico.py usuario@email.com ./limites/es_sem_trindade/es.shp \
    --output-dir ./resultados \
    --data-inicio 2025-01-01 \
    --data-fim 2025-06-30 \
    --cloud-cover 25

# 2. Visualizar resultado
python visualizador.py ./resultados/mosaico_final_es.tif \
    --shapefile ./limites/es_sem_trindade/es.shp \
    --salvar orthomosaico_es_2025.png

# 3. Gerar relatório
python visualizador.py --relatorio ./resultados/
```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique se todas as dependências estão instaladas
2. Confirme se os caminhos dos arquivos estão corretos
3. Verifique se há espaço suficiente em disco
4. Consulte os logs de erro para diagnóstico detalhado

---

**Baseado em**: `workflow-sigma.ipynb`  
**Data**: Dezembro 2025  
**Compatibilidade**: Python 3.8+

## Equipe SIGMA - Sistema Integrado de Geração de Mosaicos Aeroespaciais
