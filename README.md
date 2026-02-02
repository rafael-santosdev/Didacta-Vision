# Didacta-Vision

Link do Projeto no Figma: https://www.figma.com/design/x5HZ5erW9YcUf0RG3AK78u/Didacta-Vision?node-id=0-1&p=f&t=c4CgvDEdQZ8LHJxc-0

## Envio de e-mail (código de verificação)

O sistema envia o código de verificação por e-mail no cadastro e na recuperação de senha. Em redes que bloqueiam SMTP (por exemplo, rede do IFRN), o envio pode falhar; nesses casos, o usuário pode usar o **código temporário** exibido na tela de verificação (acesso provisório por 1 hora).

### Configuração recomendada

- **SMTP (Gmail, etc.):** Defina `EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD` no `.env`. O envio usa timeout de 10 segundos (`EMAIL_TIMEOUT`) para não travar em redes que bloqueiam a porta.
- **Rede IFRN / institucional:** Para maior chance de entrega do e-mail na rede do IFRN, use **Mailgun** (envio por HTTPS, porta 443):
  - Crie uma conta em [Mailgun](https://www.mailgun.com/) e configure um domínio.
  - No `.env`:
    - `EMAIL_MAILGUN_API_KEY=sua-chave-api`
    - `EMAIL_MAILGUN_DOMAIN=seu-dominio.com`
  - Com isso, o sistema tenta Mailgun primeiro; se não estiver configurado, usa SMTP.

Variáveis no `.env` (e-mail):

| Variável | Descrição |
|----------|-----------|
| `EMAIL_HOST_USER` | E-mail do remetente (ex.: Gmail). **Obrigatório** para envio por SMTP. |
| `EMAIL_HOST_PASSWORD` | Senha ou **Senha de app** (Gmail com 2FA). **Obrigatório** para SMTP. |
| `EMAIL_TIMEOUT` | Timeout em segundos para SMTP (padrão: 10). |
| `EMAIL_MAILGUN_API_KEY` | Chave da API Mailgun (opcional). |
| `EMAIL_MAILGUN_DOMAIN` | Domínio verificado no Mailgun (opcional). |
| `EMAIL_MAILGUN_ONLY` | Se `True`, usa apenas Mailgun (não tenta SMTP). |

### E-mail não chega (nem na rede de casa)

1. **Confirme o `.env`**  
   O envio só acontece se `EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD` estiverem definidos (ou Mailgun configurado). Sem isso, o sistema não envia e você deve usar o **código temporário** na tela de verificação.

2. **Gmail**  
   - Se a conta tem **verificação em duas etapas**: use uma **Senha de app** em vez da senha normal.  
     [Conta Google](https://myaccount.google.com/) → Segurança → Senhas de app → gerar uma para "Mail". Use essa senha em `EMAIL_HOST_PASSWORD`.  
   - Servidor: `smtp.gmail.com`, porta `587`, TLS ativado.

3. **Pasta de spam**  
   O primeiro e-mail costuma ir para spam ou “Promoções”. Peça para o usuário conferir spam e lixo eletrônico.

4. **Modo DEBUG**  
   Com `DEBUG=True`, se o envio falhar a mensagem de aviso mostra o detalhe do erro (ex.: autenticação). Use isso para ajustar o `.env`.

5. **Mailgun (alternativa ao Gmail)**  
   Se Gmail continuar bloqueando ou o e-mail não chegar, use Mailgun (conta gratuita, envio por HTTPS). Configure `EMAIL_MAILGUN_API_KEY` e `EMAIL_MAILGUN_DOMAIN` no `.env`.