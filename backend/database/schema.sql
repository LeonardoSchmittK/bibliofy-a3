-- Bibliofy - criação das tabelas (PostgreSQL)
-- Baseado no ER (docs/UML/Banco de dados/diagrama_er.puml) e na issue #16.
-- Regras: sem hard delete (usar livro.arquivado) e FKs com ON DELETE RESTRICT.

BEGIN;

-- Ids amigáveis (RF18): codigo gerado por sequence com prefixo, usado em filtros e consultas.
CREATE SEQUENCE seq_pessoa_codigo;
CREATE SEQUENCE seq_livro_codigo;
CREATE SEQUENCE seq_emprestimo_codigo;

-- papel: LEITOR ou BIBLIOTECARIO (RNF07).
-- ativo é o status cadastral (RF05); o bloqueio por atraso fica na tabela bloqueio.
CREATE TABLE pessoa (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo      VARCHAR(20)  NOT NULL DEFAULT ('cus_' || lpad(nextval('seq_pessoa_codigo')::text, 8, '0')),
    matricula   VARCHAR(30)  NOT NULL,
    nome        VARCHAR(150) NOT NULL,
    email       VARCHAR(100) NOT NULL,
    telefone    VARCHAR(20),
    senha_hash  VARCHAR(255) NOT NULL,
    papel       VARCHAR(20)  NOT NULL DEFAULT 'LEITOR',
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_pessoa_codigo UNIQUE (codigo),
    CONSTRAINT uq_pessoa_matricula UNIQUE (matricula),
    CONSTRAINT ck_pessoa_papel CHECK (papel IN ('LEITOR', 'BIBLIOTECARIO'))
);

-- E-mail único sem diferenciar maiúsculas/minúsculas.
CREATE UNIQUE INDEX uq_pessoa_email ON pessoa (lower(email));

CREATE TABLE livro (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo           VARCHAR(20)  NOT NULL DEFAULT ('liv_' || lpad(nextval('seq_livro_codigo')::text, 8, '0')),
    isbn             VARCHAR(20)  NOT NULL,
    nome             VARCHAR(200) NOT NULL,
    autor            VARCHAR(150) NOT NULL,
    editora          VARCHAR(150) NOT NULL,
    genero           VARCHAR(80)  NOT NULL,
    data_lancamento  DATE         NOT NULL,
    quantidade_total INTEGER      NOT NULL,
    arquivado        BOOLEAN      NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_livro_codigo UNIQUE (codigo),
    CONSTRAINT uq_livro_isbn UNIQUE (isbn),
    CONSTRAINT ck_livro_quantidade CHECK (quantidade_total >= 0)
);

-- status_atual: ATRASADO é atualizado por um cron job diário no backend (RF12).
-- PERDIDO: exemplar não devolvido. Não conta como empréstimo ativo do leitor.
-- Arquivar um livro não altera empréstimos em andamento: eles seguem o fluxo
-- normal (renovação, devolução, atraso) e só novos empréstimos são bloqueados.
CREATE TABLE emprestimo (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo           VARCHAR(20) NOT NULL DEFAULT ('emp_' || lpad(nextval('seq_emprestimo_codigo')::text, 8, '0')),
    pessoa_id        BIGINT  NOT NULL,
    livro_id         BIGINT  NOT NULL,
    data_emprestimo  DATE    NOT NULL,
    data_prevista    DATE    NOT NULL,
    data_devolucao   DATE,
    renovado         BOOLEAN NOT NULL DEFAULT FALSE,
    status_atual     VARCHAR(25) NOT NULL DEFAULT 'EMPRESTADO',
    CONSTRAINT uq_emprestimo_codigo UNIQUE (codigo),
    CONSTRAINT ck_emprestimo_status CHECK (status_atual IN
        ('EMPRESTADO', 'ATRASADO', 'DEVOLVIDO', 'DEVOLVIDO_COM_ATRASO', 'PERDIDO')),
    CONSTRAINT ck_emprestimo_status_devolucao CHECK (
        (status_atual IN ('EMPRESTADO', 'ATRASADO', 'PERDIDO') AND data_devolucao IS NULL)
        OR (status_atual IN ('DEVOLVIDO', 'DEVOLVIDO_COM_ATRASO') AND data_devolucao IS NOT NULL)
    ),
    CONSTRAINT fk_emprestimo_pessoa FOREIGN KEY (pessoa_id)
        REFERENCES pessoa (id) ON DELETE RESTRICT,
    CONSTRAINT fk_emprestimo_livro FOREIGN KEY (livro_id)
        REFERENCES livro (id) ON DELETE RESTRICT,
    CONSTRAINT ck_emprestimo_prevista CHECK (data_prevista >= data_emprestimo),
    CONSTRAINT ck_emprestimo_devolucao CHECK (data_devolucao IS NULL OR data_devolucao >= data_emprestimo),
    -- Alvo da FK composta de bloqueio (garante bloqueio da mesma pessoa do empréstimo).
    CONSTRAINT uq_emprestimo_id_pessoa UNIQUE (id, pessoa_id)
);

-- No máximo um empréstimo ativo por pessoa (RF17).
CREATE UNIQUE INDEX uq_emprestimo_ativo_por_pessoa
    ON emprestimo (pessoa_id)
    WHERE status_atual IN ('EMPRESTADO', 'ATRASADO');

CREATE INDEX ix_emprestimo_livro ON emprestimo (livro_id);

-- Livro arquivado não aceita novos empréstimos (RF04/RF19).
CREATE FUNCTION fn_bloqueia_emprestimo_livro_arquivado() RETURNS trigger AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM livro WHERE id = NEW.livro_id AND arquivado) THEN
        RAISE EXCEPTION 'Livro % está arquivado e não aceita novos empréstimos', NEW.livro_id
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_emprestimo_livro_arquivado
    BEFORE INSERT ON emprestimo
    FOR EACH ROW EXECUTE FUNCTION fn_bloqueia_emprestimo_livro_arquivado();

-- Usado pelo job diário que marca os atrasados.
CREATE INDEX ix_emprestimo_prevista_ativo
    ON emprestimo (data_prevista)
    WHERE status_atual = 'EMPRESTADO';

CREATE TABLE bloqueio (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pessoa_id      BIGINT       NOT NULL,
    emprestimo_id  BIGINT       NOT NULL,
    inicio         DATE         NOT NULL,
    fim_exclusivo  DATE         NOT NULL,
    motivo         VARCHAR(200) NOT NULL,
    CONSTRAINT uq_bloqueio_emprestimo UNIQUE (emprestimo_id),
    CONSTRAINT fk_bloqueio_pessoa FOREIGN KEY (pessoa_id)
        REFERENCES pessoa (id) ON DELETE RESTRICT,
    CONSTRAINT fk_bloqueio_emprestimo FOREIGN KEY (emprestimo_id, pessoa_id)
        REFERENCES emprestimo (id, pessoa_id) ON DELETE RESTRICT,
    CONSTRAINT ck_bloqueio_periodo CHECK (fim_exclusivo > inicio)
);

CREATE INDEX ix_bloqueio_pessoa ON bloqueio (pessoa_id);

-- Registro das operações críticas (RNF09). Só recebe INSERT, gravado na mesma
-- transação da operação auditada. Nunca guardar senha_hash em dados.
CREATE TABLE auditoria (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    responsavel_id  BIGINT      NOT NULL,
    acao            VARCHAR(30) NOT NULL,
    entidade        VARCHAR(30) NOT NULL,
    entidade_id     BIGINT      NOT NULL,
    dados           JSONB,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_auditoria_pessoa FOREIGN KEY (responsavel_id)
        REFERENCES pessoa (id) ON DELETE RESTRICT,
    CONSTRAINT ck_auditoria_acao CHECK (acao IN
        ('CADASTRO', 'ALTERACAO', 'ARQUIVAMENTO', 'EMPRESTIMO', 'RENOVACAO', 'DEVOLUCAO', 'PERDA', 'BLOQUEIO')),
    CONSTRAINT ck_auditoria_entidade CHECK (entidade IN
        ('PESSOA', 'LIVRO', 'EMPRESTIMO', 'BLOQUEIO'))
);

CREATE INDEX ix_auditoria_entidade ON auditoria (entidade, entidade_id);
CREATE INDEX ix_auditoria_responsavel ON auditoria (responsavel_id);

-- Disponibilidade = quantidade_total - exemplares emprestados ou perdidos (atributo derivado).
CREATE VIEW vw_livro_disponibilidade AS
SELECT l.id,
       l.codigo,
       l.isbn,
       l.nome,
       l.autor,
       l.editora,
       l.genero,
       l.arquivado,
       l.quantidade_total,
       l.quantidade_total - COUNT(e.id) AS quantidade_disponivel
FROM livro l
LEFT JOIN emprestimo e
       ON e.livro_id = l.id
      AND e.status_atual IN ('EMPRESTADO', 'ATRASADO', 'PERDIDO')
GROUP BY l.id;

COMMIT;