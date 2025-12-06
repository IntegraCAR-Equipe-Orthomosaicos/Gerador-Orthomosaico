#!/usr/bin/env python3
"""
Gerador de Orthomosaico CBERS-4A para o Estado do Espírito Santo

Este script implementa um workflow completo para gerar um ortomosaico do estado do 
Espírito Santo usando imagens CBERS-4A WPM L4 DN.

Autor: Baseado no workflow-sigma.ipynb
Data: Dezembro 2025
"""

import os
import sys
import argparse
import traceback
from datetime import date
from glob import glob
from os.path import basename

import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.windows import from_bounds
import matplotlib.pyplot as plt

try:
    from cbers4asat import Cbers4aAPI
    from cbers4asat.tools import rgbn_composite
except ImportError:
    print("❌ Erro: Biblioteca cbers4asat não encontrada.")
    print("💡 Instale com: pip install cbers4asat")
    sys.exit(1)


class GeradorOrthomosaico:
    """Classe principal para geração de orthomosaico CBERS-4A"""
    
    def __init__(self, email, shapefile_path, output_dir="./output", 
                 data_inicio=None, data_fim=None, cloud_cover=40):
        """
        Inicializar o gerador de orthomosaico
        
        Args:
            email (str): Email para API CBERS-4A
            shapefile_path (str): Caminho para shapefile da área de interesse
            output_dir (str): Diretório de saída para arquivos
            data_inicio (date): Data de início da busca
            data_fim (date): Data de fim da busca
            cloud_cover (int): Cobertura máxima de nuvens (%)
        """
        self.email = email
        self.shapefile_path = shapefile_path
        self.output_dir = output_dir
        self.data_inicio = data_inicio or date(2025, 1, 1)
        self.data_fim = data_fim or date(2025, 11, 30)
        self.cloud_cover = cloud_cover
        
        # Diretórios de trabalho
        self.dir_imagens = os.path.join(output_dir, "imagens")
        self.dir_mosaico_partes = os.path.join(output_dir, "mosaico_partes")
        
        # API
        self.api = Cbers4aAPI(email)
        
        # Dados
        self.es_geometry = None
        self.es_mosaic = None
        
        print(f"🚀 Gerador de Orthomosaico CBERS-4A inicializado")
        print(f"   📧 Email: {email}")
        print(f"   📁 Diretório de saída: {output_dir}")
        print(f"   📅 Período: {self.data_inicio} até {self.data_fim}")
        print(f"   ☁️ Cobertura máxima de nuvens: {cloud_cover}%")

    def criar_diretorios(self):
        """Criar diretórios necessários"""
        for directory in [self.output_dir, self.dir_imagens, self.dir_mosaico_partes]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"📁 Diretório criado: {directory}")

    def carregar_geometria(self):
        """Carregar geometria do shapefile"""
        print("\n📍 Carregando geometria da área de interesse...")
        
        if not os.path.exists(self.shapefile_path):
            raise FileNotFoundError(f"Shapefile não encontrado: {self.shapefile_path}")
        
        es = gpd.read_file(self.shapefile_path)
        self.es_geometry = es.union_all()
        
        print(f"✅ Geometria carregada: {self.shapefile_path}")
        print(f"   Bounds: {self.es_geometry.bounds}")

    def buscar_imagens(self):
        """Buscar imagens CBERS-4A na API"""
        print("\n🔍 Buscando imagens CBERS-4A...")
        
        # Usar o bounding box da geometria
        bbox = list(self.es_geometry.bounds)  # [minx, miny, maxx, maxy]
        print(f"   Bounding box: {bbox}")
        
        produtos = self.api.query(
            location=bbox,
            initial_date=self.data_inicio,
            end_date=self.data_fim,
            cloud=self.cloud_cover,
            limit=2000,
            collections=["CBERS4A_WPM_L4_DN"]
        )
        
        gdf = self.api.to_geodataframe(produtos)
        print(f"✅ {len(gdf)} imagens encontradas")
        
        return gdf

    def selecionar_melhores_imagens(self, gdf):
        """Selecionar a melhor imagem por path/row"""
        print("\n🎯 Selecionando melhores imagens por path/row...")
        
        mosaic = gpd.GeoDataFrame()
        
        for group_name, dframe in gdf.groupby(by=['path', 'row']):
            # Menor cobertura de nuvens
            img = dframe.loc[(dframe.cloud_cover == dframe.cloud_cover.min())]
            # Data mais recente
            img = img.loc[(img.datetime == img.datetime.min())]
            mosaic = pd.concat([mosaic, img])
        
        # Reprojetar para EPSG:4674
        mosaic.to_crs(epsg=4674, inplace=True)
        
        # Filtrar apenas imagens que intersectam o estado
        es = gpd.read_file(self.shapefile_path).to_crs(epsg=4674)
        mosaicos_dentro_estado = mosaic.geometry.apply(lambda g: es.intersects(g))
        
        es_mosaic = mosaic.merge(
            right=mosaicos_dentro_estado, 
            left_index=True, 
            right_index=True
        ).rename(columns={0: 'intersects'})
        
        self.es_mosaic = es_mosaic.loc[es_mosaic['intersects'] == True]
        
        print(f"✅ {len(self.es_mosaic)} imagens selecionadas")
        
        # Salvar metadados
        geojson_path = os.path.join(self.output_dir, "mosaico_cbers4a_es.geojson")
        if os.path.exists(geojson_path):
            os.remove(geojson_path)
        self.es_mosaic.to_file(geojson_path, driver='GeoJSON', index=False)
        print(f"💾 Metadados salvos: {geojson_path}")
        
        return self.es_mosaic

    def fazer_download(self):
        """Fazer download das imagens"""
        print(f"\n💾 Iniciando download de {len(self.es_mosaic)} imagens...")
        
        self.api.download(
            self.es_mosaic, 
            bands=['red', 'green', 'blue'], 
            outdir=self.dir_imagens, 
            with_folder=True
        )
        
        # Verificar download
        imagens_dirs = glob(f"{self.dir_imagens}/*")
        print(f"✅ Download concluído: {len(imagens_dirs)} diretórios criados")
        
        return imagens_dirs

    def criar_composicoes_rgb(self):
        """Criar composições RGB das imagens baixadas"""
        print("\n🌈 Criando composições RGB...")
        
        imagens_dirs = glob(f"{self.dir_imagens}/*")
        processed_count = 0
        error_count = 0
        
        for dirs in imagens_dirs:
            red, green, blue = '', '', ''
            img_name = ''
            
            print(f"\nProcessando: {basename(dirs)}")
            
            for file in glob(f"{dirs}/*.tif"):
                filename = basename(file)
                img_name = filename.split('_BAND')[0]
                
                if 'BAND3' in filename:  # Red
                    red = file
                elif 'BAND2' in filename:  # Green
                    green = file
                elif 'BAND1' in filename:  # Blue
                    blue = file
            
            # Verificar se todas as bandas foram encontradas
            if (red and green and blue and 
                os.path.exists(red) and os.path.exists(green) and os.path.exists(blue)):
                try:
                    output_file = f'{img_name}.tif'
                    rgbn_composite(
                        red=red, green=green, blue=blue, 
                        outdir=self.dir_mosaico_partes, 
                        filename=output_file
                    )
                    processed_count += 1
                    print(f"  ✅ Sucesso: {output_file}")
                except Exception as e:
                    print(f"  ❌ Erro: {e}")
                    error_count += 1
            else:
                print(f"  ❌ Bandas incompletas")
                error_count += 1
        
        print(f"\n{'='*50}")
        print(f"Composições RGB concluídas!")
        print(f"Sucessos: {processed_count}")
        print(f"Erros: {error_count}")
        
        rgb_files = glob(f"{self.dir_mosaico_partes}/*.tif")
        print(f"Arquivos RGB criados: {len(rgb_files)}")
        
        return rgb_files

    def reprojetar_imagens(self):
        """Reprojetar imagens para EPSG:4674"""
        print("\n🗺️ Reprojetando imagens para EPSG:4674...")
        
        dst_crs = 'EPSG:4674'
        rgb_files = glob(f"{self.dir_mosaico_partes}/*.tif")
        
        for file in rgb_files:
            print(f"Reprojetando: {basename(file)}")
            
            with rasterio.open(file) as src:
                transform, width, height = calculate_default_transform(
                    src.crs, dst_crs, src.width, src.height, *src.bounds
                )
                
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': dst_crs,
                    'transform': transform,
                    'width': width,
                    'height': height
                })
                
                # Sobrescrever arquivo reprojetado
                temp_file = file + ".temp"
                with rasterio.open(temp_file, 'w', **kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs=dst_crs,
                            resampling=Resampling.cubic
                        )
                
                # Substituir arquivo original
                os.replace(temp_file, file)
        
        print("✅ Reprojeção concluída")

    def criar_mosaico_fusao(self):
        """Fazer fusão das imagens em um mosaico"""
        print("\n🔀 Criando mosaico por fusão...")
        
        rgb_files = glob(f"{self.dir_mosaico_partes}/*.tif")
        
        if len(rgb_files) == 0:
            raise RuntimeError("❌ Nenhum arquivo encontrado para fusão!")
        
        print(f"Fusionando {len(rgb_files)} imagens...")
        
        # Abrir todas as imagens
        raster_list = []
        for file in rgb_files:
            try:
                src = rasterio.open(file)
                raster_list.append(src)
            except Exception as e:
                print(f"❌ Erro ao carregar {file}: {e}")
        
        if len(raster_list) == 0:
            raise RuntimeError("❌ Nenhum arquivo válido para fusão!")
        
        # Fazer o merge das imagens
        mosaic, out_transform = merge(raster_list, method='first')
        
        # Obter metadados
        out_meta = raster_list[0].meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_transform,
            "compress": "lzw",
            "BIGTIFF": "YES",
            "tiled": True,
            "blockxsize": 512,
            "blockysize": 512
        })
        
        # Salvar mosaico temporário
        temp_mosaic_path = os.path.join(self.output_dir, "mosaico_temp.tif")
        with rasterio.open(temp_mosaic_path, "w", **out_meta) as dest:
            dest.write(mosaic)
        
        print("✅ Mosaico inicial criado")
        
        # Fechar arquivos
        for src in raster_list:
            src.close()
        
        return temp_mosaic_path

    def recortar_por_geometria(self, temp_mosaic_path):
        """Recortar mosaico pela geometria do estado"""
        print("\n✂️ Recortando mosaico pela geometria do Estado do ES...")
        
        # Preparar geometria
        es_gdf = gpd.GeoDataFrame([1], geometry=[self.es_geometry], crs='EPSG:4674')
        
        final_mosaic_path = os.path.join(self.output_dir, "mosaico_final_es.tif")
        
        with rasterio.open(temp_mosaic_path) as src:
            print(f"CRS do mosaico: {src.crs}")
            print(f"Dimensões do mosaico: {src.width} x {src.height}")
            
            # Calcular tamanho aproximado
            size_gb = (src.width * src.height * src.count * 2) / (1024**3)
            print(f"⚠️ Tamanho aproximado: {size_gb:.1f} GB")
            
            if size_gb > 4:
                print("⚠️ AVISO: Mosaico muito grande! Pode haver problemas de memória.")
            
            # Reprojetar geometria se necessário
            if str(src.crs) != 'EPSG:4674':
                es_gdf = es_gdf.to_crs(src.crs)
            
            try:
                print("🔄 Processando recorte...")
                
                # Recorte com mask
                out_image, out_transform = mask(
                    src, es_gdf.geometry, crop=True, nodata=0, filled=True
                )
                
                print(f"Recorte concluído. Nova dimensão: {out_image.shape}")
                
                out_meta = src.meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                    "nodata": 0,
                    "compress": "lzw",
                    "BIGTIFF": "YES",
                    "tiled": True,
                    "blockxsize": 512,
                    "blockysize": 512
                })
                
                print("💾 Salvando arquivo final...")
                with rasterio.open(final_mosaic_path, "w", **out_meta) as dest:
                    dest.write(out_image)
                
                print(f"✅ Mosaico final salvo: {final_mosaic_path}")
                print(f"   Dimensões: {out_image.shape[2]} x {out_image.shape[1]} pixels")
                
                # Limpar memória
                del out_image
                
                # Remover arquivo temporário
                if os.path.exists(temp_mosaic_path):
                    os.remove(temp_mosaic_path)
                    print("🗑️ Arquivo temporário removido")
                
                return final_mosaic_path
                
            except MemoryError:
                print("❌ Erro de memória. Mosaico muito grande para processar.")
                print("💡 Sugestão: Execute em ambiente com mais RAM (16GB+)")
                raise
            except Exception as e:
                print(f"❌ Erro durante recorte: {e}")
                traceback.print_exc()
                raise

    def executar_workflow_completo(self):
        """Executar workflow completo de geração do orthomosaico"""
        try:
            print("🚀 INICIANDO WORKFLOW COMPLETO DE GERAÇÃO DE ORTHOMOSAICO")
            print("="*60)
            
            # Etapa 1: Preparação
            self.criar_diretorios()
            self.carregar_geometria()
            
            # Etapa 2: Busca e seleção de imagens
            gdf = self.buscar_imagens()
            self.selecionar_melhores_imagens(gdf)
            
            # Etapa 3: Download e processamento
            self.fazer_download()
            self.criar_composicoes_rgb()
            self.reprojetar_imagens()
            
            # Etapa 4: Fusão e recorte
            temp_mosaic = self.criar_mosaico_fusao()
            final_path = self.recortar_por_geometria(temp_mosaic)
            
            # Relatório final
            print("\n" + "="*60)
            print("🎉 WORKFLOW CONCLUÍDO COM SUCESSO!")
            print("="*60)
            print(f"📁 Arquivo final: {final_path}")
            
            if os.path.exists(final_path):
                size_mb = os.path.getsize(final_path) / (1024*1024)
                print(f"💾 Tamanho: {size_mb:.1f} MB")
            
            print(f"\n📊 Arquivos gerados em: {self.output_dir}")
            print("   - mosaico_cbers4a_es.geojson (metadados)")
            print("   - imagens/ (imagens CBERS-4A originais)")
            print("   - mosaico_partes/ (composições RGB)")
            print("   - mosaico_final_es.tif (RESULTADO FINAL)")
            
            return final_path
            
        except Exception as e:
            print(f"\n❌ ERRO NO WORKFLOW: {e}")
            traceback.print_exc()
            return None


def main():
    """Função principal com interface de linha de comando"""
    parser = argparse.ArgumentParser(
        description="Gerador de Orthomosaico CBERS-4A para o Estado do Espírito Santo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
    python gerador_orthomosaico.py usuario@email.com ./limites/es_sem_trindade/es.shp
    
    python gerador_orthomosaico.py usuario@email.com ./limites/es_sem_trindade/es.shp \\
        --output-dir ./custom_output \\
        --data-inicio 2025-01-01 \\
        --data-fim 2025-06-30 \\
        --cloud-cover 30
        """
    )
    
    parser.add_argument("email", help="Email para API CBERS-4A")
    parser.add_argument("shapefile", help="Caminho para shapefile da área de interesse")
    parser.add_argument("--output-dir", default="./output", 
                       help="Diretório de saída (default: ./output)")
    parser.add_argument("--data-inicio", type=str, help="Data início (YYYY-MM-DD)")
    parser.add_argument("--data-fim", type=str, help="Data fim (YYYY-MM-DD)")
    parser.add_argument("--cloud-cover", type=int, default=40, 
                       help="Cobertura máxima de nuvens %% (default: 40)")
    
    args = parser.parse_args()
    
    # Converter datas se fornecidas
    data_inicio = None
    data_fim = None
    
    if args.data_inicio:
        try:
            year, month, day = map(int, args.data_inicio.split('-'))
            data_inicio = date(year, month, day)
        except ValueError:
            print("❌ Formato inválido para data-inicio. Use YYYY-MM-DD")
            sys.exit(1)
    
    if args.data_fim:
        try:
            year, month, day = map(int, args.data_fim.split('-'))
            data_fim = date(year, month, day)
        except ValueError:
            print("❌ Formato inválido para data-fim. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Verificar se shapefile existe
    if not os.path.exists(args.shapefile):
        print(f"❌ Shapefile não encontrado: {args.shapefile}")
        sys.exit(1)
    
    # Criar e executar gerador
    try:
        gerador = GeradorOrthomosaico(
            email=args.email,
            shapefile_path=args.shapefile,
            output_dir=args.output_dir,
            data_inicio=data_inicio,
            data_fim=data_fim,
            cloud_cover=args.cloud_cover
        )
        
        resultado = gerador.executar_workflow_completo()
        
        if resultado:
            print(f"\n✅ Sucesso! Orthomosaico gerado: {resultado}")
            sys.exit(0)
        else:
            print(f"\n❌ Falha na geração do orthomosaico")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Processo interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()