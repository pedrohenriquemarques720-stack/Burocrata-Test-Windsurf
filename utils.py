import re
import unicodedata
import pdfplumber
import streamlit as st

def limpar_texto(texto):
    """Limpa texto removendo caracteres especiais e normalizando"""
    if not texto:
        return ""
    
    # Converter para string se não for
    texto = str(texto)
    
    # Remover caracteres de controle e substituir por espaço
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', texto)
    
    # Normalizar caracteres Unicode
    try:
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    except:
        pass
    
    # Substituir múltiplos espaços por um único espaço
    texto = re.sub(r'\s+', ' ', texto)
    
    return texto.strip()

def extrair_texto_pdf(arquivo):
    """Extração ULTRA robusta de texto de PDF"""
    try:
        texto_total = ""
        
        # Primeiro, ler o arquivo como bytes para verificação
        conteudo = arquivo.read()
        arquivo.seek(0)  # Voltar ao início para o pdfplumber
        
        # Tentar detectar encoding
        try:
            # Tentar como UTF-8
            preview = conteudo[:1000].decode('utf-8', errors='ignore')
        except:
            try:
                # Tentar como latin-1
                preview = conteudo[:1000].decode('latin-1', errors='ignore')
            except:
                preview = ""
        
        with pdfplumber.open(arquivo) as pdf:
            for i, pagina in enumerate(pdf.pages):
                try:
                    # Método 1: Extração padrão
                    texto = pagina.extract_text()
                    if texto and len(texto.strip()) > 20:
                        texto_total += texto + "\n\n"
                    else:
                        # Método 2: Extração com tolerância alta
                        texto = pagina.extract_text(
                            x_tolerance=5,
                            y_tolerance=5,
                            keep_blank_chars=False,
                            use_text_flow=True
                        )
                        if texto and len(texto.strip()) > 20:
                            texto_total += texto + "\n\n"
                        else:
                            # Método 3: Extrair por linhas
                            chars = pagina.chars
                            if chars:
                                linhas = {}
                                for char in chars:
                                    y = char['top']
                                    if y not in linhas:
                                        linhas[y] = []
                                    linhas[y].append(char)
                                
                                for y in sorted(linhas.keys()):
                                    linha_chars = sorted(linhas[y], key=lambda c: c['x0'])
                                    linha_texto = ''.join(c['text'] for c in linha_chars)
                                    if linha_texto.strip():
                                        texto_total += linha_texto + "\n"
                
                except Exception as e:
                    continue
        
        # Se ainda não tem texto suficiente, tentar métodos extremos
        if len(texto_total.strip()) < 100:
            try:
                # Usar OCR como último recurso (simulado)
                st.warning("⚠️ PDF difícil de ler. Usando métodos avançados...")
                
                # Extrair tabelas
                with pdfplumber.open(arquivo) as pdf:
                    for pagina in pdf.pages:
                        tabelas = pagina.extract_tables()
                        if tabelas:
                            for tabela in tabelas:
                                for linha in tabela:
                                    if linha:
                                        linha_texto = " | ".join(str(c).strip() for c in linha if c)
                                        if linha_texto:
                                            texto_total += linha_texto + "\n"
            except:
                pass
        
        texto_limpo = limpar_texto(texto_total)
        
        if not texto_limpo or len(texto_limpo) < 50:
            st.error("❌ Não foi possível extrair texto suficiente do PDF")
            return None
            
        return texto_limpo
        
    except Exception as e:
        st.error(f"❌ Erro crítico ao processar PDF: {str(e)}")
        return None
