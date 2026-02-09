# 🚀 Deploy do Burocrata de Bolso

## 🌐 Configurações de Domínio

### Domínios Configurados
- **Site Principal:** `www.burocratadebolso.com.br`
- **App Streamlit:** `burocratadefinitivo.streamlit.app`

## ☁️ Deploy no Streamlit Cloud

### 1. Preparar o Ambiente
```bash
# Verificar arquivos de configuração
ls -la .streamlit/

# Verificar dependências
pip install -r requirements.txt
```

### 2. Deploy Automático
```bash
# Fazer push para o repositório
git add .
git commit -m "Deploy: Configurações de domínio atualizadas"
git push origin main

# O Streamlit Cloud fará deploy automático
```

### 3. Configurações no Streamlit Cloud
1. Acesse: [share.streamlit.io](https://share.streamlit.io)
2. Selecione o app: `burocratadefinitivo`
3. Configure as variáveis de ambiente:
   ```
   DOMAIN=www.burocratadebolso.com.br
   STREAMLIT_URL=https://burocratadefinitivo.streamlit.app
   ```

## 🔧 Configurações de Domínio Personalizado

### 1. Configurar DNS
No seu provedor de domínio, adicione os registros:

```
Tipo: CNAME
Nome: www
Valor: proxy.streamlit.app
TTL: 3600

Tipo: CNAME  
Nome: @
Valor: proxy.streamlit.app
TTL: 3600
```

### 2. Configurar no Streamlit
1. Vá para: [share.streamlit.io](https://share.streamlit.io)
2. Clique em "Advanced settings"
3. Adicione domínio personalizado:
   - Custom URL: `www.burocratadebolso.com.br`
   - Redirect URL: `https://burocratadefinitivo.streamlit.app`

## 📱 Acesso ao Sistema

### Links de Acesso
- **🌐 Site Principal:** [www.burocratadebolso.com.br](https://www.burocratadebolso.com.br)
- **☁️ App Streamlit:** [burocratadefinitivo.streamlit.app](https://burocratadefinitivo.streamlit.app)

### Conta de Desenvolvimento
- **📧 E-mail:** `pedrohenriquemarques720@gmail.com`
- **🔑 Senha:** `Liz1808#`
- **💎 Créditos:** Ilimitados

## 🔒 Configurações de Segurança

### HTTPS
- ✅ Certificado SSL automático pelo Streamlit
- ✅ Redirecionamento HTTP → HTTPS
- ✅ Headers de segurança configurados

### Variáveis de Ambiente
```bash
# Configurações sensíveis (não commitar)
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
```

## 📊 Monitoramento e Logs

### Acessar Logs
```bash
# Via Streamlit CLI
streamlit logs burocratadefinitivo

# Via interface web
# 1. Acesse share.streamlit.io
# 2. Clique no app
# 3. Vá para "Logs"
```

### Métricas de Performance
- **Uptime:** Monitoramento 24/7
- **Response Time:** < 2 segundos
- **Error Rate:** < 1%
- **Concurrent Users:** Até 100

## 🔄 Atualizações e Manutenção

### Deploy Automático
```bash
# Script de deploy rápido
#!/bin/bash
echo "🚀 Iniciando deploy do Burocrata de Bolso..."

# Commit mudanças
git add .
git commit -m "Auto-deploy: $(date)"
git push origin main

echo "✅ Deploy concluído!"
echo "🌐 Acesse: https://burocratadefinitivo.streamlit.app"
```

### Backup Automático
```bash
# Backup do banco de dados
cp usuarios_burocrata.db backups/usuarios_burocrata_$(date +%Y%m%d_%H%M%S).db

# Backup para nuvem (opcional)
# aws s3 cp usuarios_burocrata.db s3://seu-bucket/backups/
```

## 🚨 Solução de Problemas

### Erros Comuns

#### 1. App não carrega
```bash
# Verificar logs
streamlit logs burocratadefinitivo

# Verificar dependências
pip install -r requirements.txt --upgrade
```

#### 2. Erro de importação
```bash
# Verificar estrutura de arquivos
ls -la
tree .

# Verificar imports
python -c "from config import DOMAIN_CONFIG; print('OK')"
```

#### 3. Problemas de domínio
```bash
# Verificar DNS
nslookup www.burocratadebolso.com.br
dig www.burocratadebolso.com.br

# Verificar configuração Streamlit
# Acessar share.streamlit.io > Advanced settings
```

### Contato de Suporte Técnico
- **📧 E-mail:** contatoburocrata@outlook.com
- **📷 Instagram:** @burocratadebolso
- **⏰ Tempo Resposta:** Até 24h

## 📈 Performance e Otimização

### Configurações de Produção
```toml
# .streamlit/config.toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#10263D"
backgroundColor = "#10263D"
textColor = "#FFFFFF"
```

### Cache e Otimização
- **Cache de configurações:** Reduz acesso a disco
- **Compressão de PDFs:** Otimiza uso de memória
- **Pool de conexões:** Melhora performance do banco

## 🎯 Checklist de Deploy

### Antes do Deploy
- [ ] Testar localmente (`streamlit run app.py`)
- [ ] Verificar dependências (`pip install -r requirements.txt`)
- [ ] Backup do banco de dados
- [ ] Atualizar versão no README.md
- [ ] Commitar mudanças

### Após o Deploy
- [ ] Verificar se app carrega
- [ ] Testar login/cadastro
- [ ] Testar upload de PDF
- [ ] Verificar links do domínio
- [ ] Monitorar logs por 24h

## 📱 Acesso Móvel

### PWA (Progressive Web App)
- ✅ Design responsivo
- ✅ Instalação na tela inicial
- ✅ Funciona offline parcialmente
- ✅ Notificações push (futuro)

### Compatibilidade
- **iOS:** Safari 12+
- **Android:** Chrome 80+
- **Desktop:** Chrome, Firefox, Safari, Edge

---

## 🎉 Deploy Concluído!

Seu Burocrata de Bolso está agora no ar com:

- 🌐 **Domínio profissional:** www.burocratadebolso.com.br
- ☁️ **App Streamlit:** burocratadefinitivo.streamlit.app  
- 🔒 **Segurança:** HTTPS e proteções ativas
- 📊 **Monitoramento:** Logs e métricas disponíveis
- 📱 **Mobile-first:** Design responsivo

**Acesso imediato:**
- [🌐 Site Principal](https://www.burocratadebolso.com.br)
- [☁️ App Streamlit](https://burocratadefinitivo.streamlit.app)

---

**Suporte técnico:** contatoburocrata@outlook.com  
**Desenvolvido por:** Pedro Henrique © 2026
