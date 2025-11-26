from cbers4asat import Cbers4aAPI
from datetime import date
import os
import requests
from urllib.parse import urlparse, urljoin
import re

def baixar_imagens_alta_resolucao():
    """Tentar baixar imagens de alta resolução através de URLs diretas"""
    
    api = Cbers4aAPI('tomir.dsj@gmail.com')
    bbox = [-40.3, -20.3, -40.1, -20.0]
    download_folder = 'imagens_alta_resolucao'
    
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        print(f"📁 Pasta criada: {download_folder}")
    
    print("🚀 Tentando acessar imagens de ALTA RESOLUÇÃO...")
    print("👤 Email autenticado: tomir.dsj@gmail.com")
    
    # Buscar produtos
    produtos = api.query(
        location=bbox,
        initial_date=date(2023, 6, 1),
        end_date=date(2023, 12, 31),
        cloud=50,  # Apenas imagens com menos de 50% de nuvens
        limit=5,   # Limitar a 5 para teste
        collections=['CBERS4A_WPM_L4_DN', 'CBERS4A_MUX_L4_DN']
    )
    
    if not produtos['features']:
        print("❌ Nenhuma imagem encontrada")
        return
    
    print(f"✅ Encontradas {len(produtos['features'])} imagens")
    
    download_count = 0
    
    for i, feature in enumerate(produtos['features']):
        try:
            props = feature['properties']
            feature_id = feature.get('id', f'img_{i+1}')
            data = props.get('datetime', '').split('T')[0]
            nuvens = props.get('cloud_cover', 'N/A')
            
            print(f"\n📥 Imagem {i+1}/{len(produtos['features'])}")
            print(f"   ID: {feature_id}")
            print(f"   Data: {data}")
            print(f"   Nuvens: {nuvens}%")
            
            # Extrair informações da URL do thumbnail para construir URLs das bandas
            thumbnail_url = feature['assets']['thumbnail']['href']
            print(f"   🔗 URL base: {thumbnail_url[:80]}...")
            
            # Tentar construir URLs das bandas baseado na estrutura do INPE
            base_url = thumbnail_url.replace('.png', '')
            
            # Possíveis padrões de bandas para CBERS-4A WPM
            banda_patterns = [
                '_BAND1.tif',
                '_BAND2.tif', 
                '_BAND3.tif',
                '_BAND4.tif',
                '_B01.tif',
                '_B02.tif',
                '_B03.tif',
                '_B04.tif'
            ]
            
            pasta_imagem = os.path.join(download_folder, f"{feature_id}_{data}")
            if not os.path.exists(pasta_imagem):
                os.makedirs(pasta_imagem)
            
            banda_success = 0
            
            for banda in banda_patterns:
                try:
                    banda_url = base_url + banda
                    banda_nome = banda.replace('.tif', '') + '.tif'
                    
                    print(f"   🔄 Tentando banda: {banda}")
                    
                    # Headers para simular um navegador
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': '*/*',
                        'Connection': 'keep-alive'
                    }
                    
                    response = requests.get(banda_url, headers=headers, stream=True, timeout=30)
                    
                    if response.status_code == 200:
                        # Verificar se é realmente um arquivo TIFF
                        content_type = response.headers.get('content-type', '')
                        content_length = response.headers.get('content-length', '0')
                        
                        if 'image' in content_type or int(content_length) > 100000:  # Maior que 100KB
                            arquivo_local = os.path.join(pasta_imagem, banda_nome)
                            
                            with open(arquivo_local, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                            
                            size_mb = os.path.getsize(arquivo_local) / (1024*1024)
                            print(f"      ✅ {banda} baixado! ({size_mb:.1f} MB)")
                            banda_success += 1
                        else:
                            print(f"      ❌ {banda}: Não é arquivo de imagem válido")
                    else:
                        print(f"      ❌ {banda}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"      ❌ {banda}: {str(e)[:50]}...")
                    continue
            
            # Baixar thumbnail como referência
            try:
                print(f"   📸 Baixando thumbnail de referência...")
                response = requests.get(thumbnail_url, stream=True)
                response.raise_for_status()
                
                thumb_path = os.path.join(pasta_imagem, 'thumbnail.png')
                with open(thumb_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                thumb_size = os.path.getsize(thumb_path) / 1024
                print(f"      ✅ Thumbnail baixado ({thumb_size:.1f} KB)")
                
            except Exception as e:
                print(f"      ❌ Erro no thumbnail: {e}")
            
            if banda_success > 0:
                download_count += 1
                print(f"   🎉 Sucesso! {banda_success} bandas baixadas")
            else:
                print(f"   ⚠️  Apenas thumbnail disponível")
                
        except Exception as e:
            print(f"   ❌ Erro geral: {e}")
            continue
    
    print(f"\n🎉 RESULTADO FINAL:")
    print(f"📊 Imagens processadas: {len(produtos['features'])}")
    print(f"✅ Downloads bem-sucedidos: {download_count}")
    print(f"📁 Local: ./{download_folder}/")
    
    # Listar arquivos baixados
    try:
        total_files = 0
        total_size = 0
        
        for root, dirs, files in os.walk(download_folder):
            for file in files:
                if file.endswith(('.tif', '.png')):
                    full_path = os.path.join(root, file)
                    size = os.path.getsize(full_path)
                    total_files += 1
                    total_size += size
        
        print(f"📋 Total de arquivos: {total_files}")
        print(f"💾 Tamanho total: {total_size/(1024*1024):.1f} MB")
        
        if total_files > 0:
            print(f"\n💡 Os arquivos foram salvos em subpastas por imagem.")
            print(f"   Cada pasta contém as bandas disponíveis + thumbnail")
        
    except Exception as e:
        print(f"❌ Erro ao listar arquivos: {e}")

if __name__ == "__main__":
    baixar_imagens_alta_resolucao()