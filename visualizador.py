#!/usr/bin/env python3
"""
Visualizador para orthomosaicos CBERS-4A

Script separado para visualização de resultados do gerador de orthomosaicos.

Autor: Baseado no workflow-sigma.ipynb
Data: Dezembro 2025
"""

import os
import sys
import argparse
import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import geopandas as gpd


def visualizar_mosaico(caminho_mosaico, caminho_shapefile=None, salvar_figura=None):
    """
    Visualizar o mosaico final
    
    Args:
        caminho_mosaico (str): Caminho para o arquivo mosaico final
        caminho_shapefile (str): Caminho opcional para shapefile dos limites
        salvar_figura (str): Caminho opcional para salvar a figura
    """
    if not os.path.exists(caminho_mosaico):
        print(f"❌ Arquivo não encontrado: {caminho_mosaico}")
        return False
    
    print("📊 Carregando mosaico final para visualização...")
    
    try:
        with rasterio.open(caminho_mosaico) as src:
            # Ler os dados
            data = src.read()
            
            print(f"✅ Mosaico carregado com sucesso!")
            print(f"📏 Dimensões: {src.width} x {src.height} pixels")
            print(f"📦 Bandas: {src.count}")
            print(f"🌍 CRS: {src.crs}")
            print(f"📍 Bounds: {src.bounds}")
            
            # Criar visualização
            fig, axes = plt.subplots(1, 2, figsize=(20, 10))
            ax1, ax2 = axes
            
            # Mostrar o mosaico RGB
            if src.count >= 3:
                # Normalizar os valores para visualização
                rgb = data[:3].transpose(1, 2, 0)
                
                # Remover pixels com valor 0 (nodata) para melhor visualização
                rgb_vis = rgb.copy()
                rgb_vis[rgb_vis == 0] = np.nan
                
                # Normalizar para 0-1 se necessário
                if rgb_vis.max() > 1:
                    rgb_vis = rgb_vis / rgb_vis.max()
                
                ax1.imshow(rgb_vis, extent=[src.bounds.left, src.bounds.right, 
                                           src.bounds.bottom, src.bounds.top])
                ax1.set_title('Mosaico Final - Estado do ES', fontsize=14, fontweight='bold')
                ax1.set_xlabel('Longitude')
                ax1.set_ylabel('Latitude')
                
                # Sobrepor o limite do estado se shapefile fornecido
                if caminho_shapefile and os.path.exists(caminho_shapefile):
                    try:
                        es_gdf = gpd.read_file(caminho_shapefile)
                        if str(es_gdf.crs) != str(src.crs):
                            es_gdf = es_gdf.to_crs(src.crs)
                        es_gdf.boundary.plot(ax=ax1, color='red', linewidth=2, alpha=0.8)
                    except Exception as e:
                        print(f"⚠️ Aviso: Não foi possível carregar shapefile: {e}")
            else:
                show(src, ax=ax1, title='Mosaico Final - Estado do ES')
            
            # Mostrar histograma das bandas
            colors = ['red', 'green', 'blue']
            for i in range(min(3, src.count)):
                band_data = data[i][data[i] > 0]  # Excluir nodata
                if len(band_data) > 0:
                    ax2.hist(band_data.flatten(), bins=100, alpha=0.7, 
                            label=f'Banda {i+1}', color=colors[i], density=True)
            
            ax2.set_title('Histograma das Bandas RGB')
            ax2.set_xlabel('Valor do Pixel')
            ax2.set_ylabel('Densidade')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Salvar figura se solicitado
            if salvar_figura:
                plt.savefig(salvar_figura, dpi=300, bbox_inches='tight')
                print(f"💾 Figura salva: {salvar_figura}")
            
            plt.show()
            
            # Estatísticas finais
            print(f"\n📊 Estatísticas do Mosaico Final:")
            for i in range(src.count):
                band_data = data[i][data[i] > 0]
                if len(band_data) > 0:
                    print(f"   Banda {i+1}: Min={band_data.min():.2f}, "
                          f"Max={band_data.max():.2f}, Média={band_data.mean():.2f}")
            
            print(f"\n📁 Arquivo: {caminho_mosaico}")
            print(f"💾 Tamanho: {os.path.getsize(caminho_mosaico) / (1024*1024):.1f} MB")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao visualizar mosaico: {e}")
        return False


def comparar_cobertura(caminho_geojson, caminho_shapefile):
    """
    Visualizar a cobertura das imagens CBERS-4A sobre o estado
    
    Args:
        caminho_geojson (str): Caminho para arquivo GeoJSON com metadados das imagens
        caminho_shapefile (str): Caminho para shapefile do estado
    """
    if not os.path.exists(caminho_geojson):
        print(f"❌ Arquivo GeoJSON não encontrado: {caminho_geojson}")
        return False
        
    if not os.path.exists(caminho_shapefile):
        print(f"❌ Shapefile não encontrado: {caminho_shapefile}")
        return False
    
    try:
        # Carregar dados
        imagens = gpd.read_file(caminho_geojson)
        estado = gpd.read_file(caminho_shapefile)
        
        # Garantir mesmo CRS
        if imagens.crs != estado.crs:
            imagens = imagens.to_crs(estado.crs)
        
        # Criar visualização
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Plotar estado em amarelo
        estado.plot(ax=ax, color='yellow', alpha=0.7, edgecolor='black', linewidth=1)
        
        # Plotar imagens selecionadas
        imagens.plot(ax=ax, facecolor="blue", edgecolor='red', alpha=0.4, linewidth=1)
        
        ax.set_title(f'Cobertura CBERS-4A - {len(imagens)} imagens selecionadas', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        
        # Adicionar grid
        ax.grid(True, alpha=0.3)
        
        # Informações adicionais
        total_area_estado = estado.area.sum()
        area_coberta = imagens.area.sum()
        
        print(f"📊 Estatísticas de Cobertura:")
        print(f"   Total de imagens: {len(imagens)}")
        print(f"   Área do estado: {total_area_estado:.2f}")
        print(f"   Área total das imagens: {area_coberta:.2f}")
        
        plt.tight_layout()
        plt.show()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao visualizar cobertura: {e}")
        return False


def gerar_relatorio_detalhado(output_dir):
    """
    Gerar relatório detalhado dos arquivos gerados
    
    Args:
        output_dir (str): Diretório de saída do processamento
    """
    print("📋 RELATÓRIO DETALHADO DO PROCESSAMENTO")
    print("="*50)
    
    arquivos_esperados = {
        "mosaico_cbers4a_es.geojson": "Metadados das imagens selecionadas",
        "mosaico_final_es.tif": "Orthomosaico final recortado",
        "imagens/": "Diretório com imagens CBERS-4A originais",
        "mosaico_partes/": "Diretório com composições RGB individuais"
    }
    
    for arquivo, descricao in arquivos_esperados.items():
        caminho = os.path.join(output_dir, arquivo)
        
        if os.path.exists(caminho):
            if os.path.isfile(caminho):
                tamanho = os.path.getsize(caminho) / (1024*1024)
                print(f"✅ {arquivo}: {descricao} ({tamanho:.1f} MB)")
            else:
                # É um diretório
                num_arquivos = len([f for f in os.listdir(caminho) 
                                  if os.path.isfile(os.path.join(caminho, f))])
                print(f"✅ {arquivo}: {descricao} ({num_arquivos} arquivos)")
        else:
            print(f"❌ {arquivo}: {descricao} (NÃO ENCONTRADO)")
    
    print("="*50)


def main():
    """Função principal com interface de linha de comando"""
    parser = argparse.ArgumentParser(
        description="Visualizador para orthomosaicos CBERS-4A",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
    # Visualizar mosaico final
    python visualizador.py ./output/mosaico_final_es.tif
    
    # Visualizar com limites do estado
    python visualizador.py ./output/mosaico_final_es.tif \
        --shapefile ./limites/es_sem_trindade/es.shp
    
    # Visualizar cobertura das imagens
    python visualizador.py --cobertura ./output/mosaico_cbers4a_es.geojson \
        ./limites/es_sem_trindade/es.shp
    
    # Gerar relatório
    python visualizador.py --relatorio ./output/
        """
    )
    
    parser.add_argument("arquivo", nargs='?', help="Arquivo do mosaico final (.tif)")
    parser.add_argument("--shapefile", help="Shapefile com limites para sobrepor")
    parser.add_argument("--salvar", help="Caminho para salvar a figura")
    parser.add_argument("--cobertura", help="Visualizar cobertura usando arquivo GeoJSON")
    parser.add_argument("--relatorio", help="Gerar relatório do diretório especificado")
    
    args = parser.parse_args()
    
    try:
        if args.relatorio:
            # Gerar relatório
            gerar_relatorio_detalhado(args.relatorio)
            
        elif args.cobertura:
            # Visualizar cobertura
            if not args.arquivo:
                print("❌ Shapefile do estado é obrigatório para visualização de cobertura")
                sys.exit(1)
            comparar_cobertura(args.cobertura, args.arquivo)
            
        elif args.arquivo:
            # Visualizar mosaico
            visualizar_mosaico(args.arquivo, args.shapefile, args.salvar)
            
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n⚠️ Visualização interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()