import os
import pdfplumber

# Lista de contratos para analisar
contratos = [
    'CONTRATO DE EMPREGO 1.pdf',
    'CONTRATO DE EMPREGO 2.pdf', 
    'CONTRATO DE EMPREGO 3.pdf',
    'CONTRATO DE LOCAÇÃO 2.pdf',
    'CONTRATO DE LOCAÇÃO 3.pdf',
    'CONTRATOS DE LOCAÇÃO COM ARMADILHAS.pdf',
    'Contrato de Locação Residencial.pdf'
]

caminho_base = r'C:\Users\pedro\OneDrive\Área de Trabalho\Teste do burocrata'

print('VERIFICACAO DOS PDFs')
print('=' * 50)

for contrato in contratos:
    caminho_completo = os.path.join(caminho_base, contrato)
    print(f'\n[ARQUIVO] {contrato}')
    print('-' * 30)
    
    try:
        with pdfplumber.open(caminho_completo) as pdf:
            print(f'Paginas: {len(pdf.pages)}')
            
            # Verificar primeira pagina
            if len(pdf.pages) > 0:
                page = pdf.pages[0]
                text = page.extract_text()
                if text:
                    print(f'Texto encontrado: {len(text)} caracteres')
                    print(f'Primeiras 200 chars: {text[:200]}')
                else:
                    print('SEM TEXTO - Possivelmente imagem')
                    
                # Verificar se tem imagens
                images = page.images
                if images:
                    print(f'Imagens na pagina: {len(images)}')
                    
            # Verificar se esta criptografado
            if hasattr(pdf, 'is_encrypted') and pdf.is_encrypted:
                print('PDF CRIPTOGRAFADO!')
                
    except Exception as e:
        print(f'ERRO: {e}')
    
    print()
