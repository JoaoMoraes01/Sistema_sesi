-- =====================================================================
-- Cria um usuário dedicado para o sistema, em vez de usar o "root".
--
-- POR QUE: hoje o sistema conecta no MySQL como root, que pode TUDO
-- (apagar outros bancos, criar usuários, desligar o servidor...). Se a
-- senha do .env vazar ou alguém explorar uma falha no sistema, o estrago
-- fica limitado ao banco "sesi_gestao" se usarmos um usuário dedicado.
--
-- COMO USAR:
--   1. Abra o terminal como administrador
--   2. mysql -u root -p   (digite a senha atual do root)
--   3. Cole os comandos abaixo, TROCANDO a senha antes:
--      (ou rode de uma vez:  mysql -u root -p < seguranca_mysql.sql)
--   4. Atualize o arquivo .env: MYSQL_USER=sesi_app e a senha nova
--   5. Reinicie o sistema e confirme que o login e os cadastros funcionam
--
-- IMPORTANTE: troque 'TROQUE_ESTA_SENHA' por uma senha forte de verdade
-- (12+ caracteres, misturando letras, números e símbolos).
-- =====================================================================

CREATE USER IF NOT EXISTS 'sesi_app'@'localhost'
    IDENTIFIED BY 'sesiapp123456';

-- Permissões mínimas necessárias: ler, inserir, editar e apagar registros
-- APENAS no banco do sistema. Sem DROP, sem CREATE USER, sem acesso a
-- outros bancos.
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER
    ON sesi_gestao.*
    TO 'sesi_app'@'localhost';

FLUSH PRIVILEGES;

-- Conferir se ficou certo (deve listar apenas privilégios em sesi_gestao.*):
-- SHOW GRANTS FOR 'sesi_app'@'localhost';
