-- Função para criar a tabela users
CREATE OR REPLACE FUNCTION create_users_table()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    -- Cria a tabela users se ela não existir
    CREATE TABLE IF NOT EXISTS public.users (
        id UUID PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Adiciona comentário na tabela
    COMMENT ON TABLE public.users IS 'Tabela para armazenar informações dos usuários';
END;
$$;
