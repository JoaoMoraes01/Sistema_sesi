# Publicar uma demonstração no Render com MySQL

Esta configuração mantém o backend FastAPI, o frontend estático e o MySQL. Foi pensada para uma demonstração escolar com dados fictícios, não para operação real com dados de alunos.

## Antes de começar

1. Use uma conta no [Aiven](https://aiven.io/free-mysql-database) para criar o serviço MySQL gratuito e uma conta no [Render](https://render.com/) para importar o repositório.
2. No Aiven, anote usuário, senha, host e porta apresentados na tela de conexão. Use o nome do banco fornecido pelo serviço (muitas vezes `defaultdb`). Baixe o certificado CA PEM e guarde-o em local seguro.
3. Não carregue `app.seed_teste` nem dados reais na instância pública. Os registros ficam acessíveis a qualquer pessoa que obtenha as credenciais do sistema; a URL não é um controle de acesso.

## Publicar

1. Faça commit e push destas alterações para uma branch do repositório GitHub.
2. No Render, crie um serviço **Blueprint** apontando para o repositório e a branch. O arquivo `render.yaml` configura o comando de build, a porta dinâmica e o plano gratuito.
3. No formulário do Render, preencha as variáveis marcadas como secretas/não sincronizadas:
   - `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT` e `MYSQL_DB`: valores do painel Aiven.
   - `MYSQL_SSL_CA`: conteúdo do certificado CA PEM baixado do provedor.
   - `ADMIN_DEFAULT_PASSWORD`: defina uma senha forte e exclusiva para o primeiro login de administrador, antes do primeiro deploy.
4. Confirme que `MYSQL_SSL=true` e `OPEN_BROWSER=false`. O `JWT_SECRET_KEY` é gerado pelo Render no Blueprint; não o altere entre reinicializações.
5. Aguarde o build e abra a URL `.onrender.com`. Entre como `admin` com a senha inicial definida acima e troque-a após o primeiro acesso.
6. Faça um teste de login, criação/edição/exclusão de um registro totalmente fictício e verifique o histórico. Não faça testes com CPF ou outros dados de pessoas reais.

## Limitações e cuidado com os dados

- No Render gratuito, a aplicação pode dormir após 15 minutos sem acesso; o primeiro acesso seguinte pode demorar aproximadamente um minuto. O filesystem do serviço é efêmero, por isso o banco remoto é obrigatório.
- O plano MySQL gratuito da Aiven tem limites de recursos, pode desligar após inatividade e não é recomendado para tráfego ou uso operacional elevado. Confira limites e termos atuais nos painéis dos fornecedores.
- Faça cópias de segurança do banco e confirme que consegue restaurá-las. Não trate uma conta gratuita de demonstração como armazenamento permanente.
- O repositório README lista pendências de segurança ainda não resolvidas. Portanto, não use o sistema para gerir matrículas reais ou dados pessoais/sensíveis sem revisão de segurança e autorização institucional.
