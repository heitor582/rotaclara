PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS gerente (
 id INTEGER PRIMARY KEY, nome TEXT NOT NULL, telefone TEXT NOT NULL, email TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS motorista (
 id INTEGER PRIMARY KEY, gerente_id INTEGER REFERENCES gerente(id), nome TEXT NOT NULL,
 telefone TEXT NOT NULL, documento TEXT NOT NULL UNIQUE, veiculo TEXT NOT NULL,
 km_por_litro REAL NOT NULL CHECK(km_por_litro > 0)
);
CREATE TABLE IF NOT EXISTS usuario (
 id INTEGER PRIMARY KEY, login TEXT NOT NULL UNIQUE, senha_hash TEXT NOT NULL,
 perfil TEXT NOT NULL CHECK(perfil IN ('administrador','gerente','motorista')),
 motorista_id INTEGER UNIQUE REFERENCES motorista(id), gerente_id INTEGER UNIQUE REFERENCES gerente(id),
 CHECK((perfil='motorista' AND motorista_id IS NOT NULL AND gerente_id IS NULL) OR
 (perfil='gerente' AND gerente_id IS NOT NULL AND motorista_id IS NULL) OR
 (perfil='administrador' AND motorista_id IS NULL AND gerente_id IS NULL))
);
CREATE TABLE IF NOT EXISTS parametro (
 id INTEGER PRIMARY KEY CHECK(id=1), valor_combustivel REAL NOT NULL CHECK(valor_combustivel>=0),
 km_por_litro REAL NOT NULL CHECK(km_por_litro>0), custo_por_km REAL NOT NULL CHECK(custo_por_km>=0),
 jornada_padrao_horas REAL NOT NULL DEFAULT 8 CHECK(jornada_padrao_horas>0 AND jornada_padrao_horas<=24),
 excluir_partida INTEGER NOT NULL DEFAULT 1 CHECK(excluir_partida=1),
 regra_calculo TEXT NOT NULL DEFAULT 'saida_menos_chegada' CHECK(regra_calculo='saida_menos_chegada')
);
CREATE TABLE IF NOT EXISTS roteiro (
 id INTEGER PRIMARY KEY, data TEXT NOT NULL, motorista_id INTEGER NOT NULL REFERENCES motorista(id),
 distancia_total REAL NOT NULL CHECK(distancia_total>=0), tempo_total_parado REAL NOT NULL DEFAULT 0,
 custo_estimado REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'planejado' CHECK(status IN ('planejado','em_andamento','concluido')),
 valor_combustivel REAL NOT NULL, km_por_litro REAL NOT NULL CHECK(km_por_litro>0),
 custo_por_km REAL NOT NULL, jornada_padrao_horas REAL NOT NULL,
 UNIQUE(motorista_id,data)
);
CREATE TABLE IF NOT EXISTS ponto (
 id INTEGER PRIMARY KEY, roteiro_id INTEGER NOT NULL REFERENCES roteiro(id), endereco TEXT NOT NULL,
 latitude REAL NOT NULL CHECK(latitude BETWEEN -90 AND 90), longitude REAL NOT NULL CHECK(longitude BETWEEN -180 AND 180),
 data_hora_chegada TEXT, data_hora_saida TEXT, tempo_parado_minutos REAL NOT NULL DEFAULT 0 CHECK(tempo_parado_minutos>=0),
 ordem_sequencial INTEGER NOT NULL CHECK(ordem_sequencial>0), UNIQUE(roteiro_id,ordem_sequencial),
 CHECK(data_hora_saida IS NULL OR (data_hora_chegada IS NOT NULL AND data_hora_saida>=data_hora_chegada))
);
CREATE TABLE IF NOT EXISTS auditoria (
 id INTEGER PRIMARY KEY, usuario_id INTEGER NOT NULL REFERENCES usuario(id), instante TEXT NOT NULL,
 ponto_id INTEGER REFERENCES ponto(id), acao TEXT NOT NULL, antes TEXT NOT NULL, depois TEXT NOT NULL, motivo TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS auditoria_sem_update BEFORE UPDATE ON auditoria BEGIN SELECT RAISE(ABORT,'Auditoria imutavel'); END;
CREATE TRIGGER IF NOT EXISTS auditoria_sem_delete BEFORE DELETE ON auditoria BEGIN SELECT RAISE(ABORT,'Auditoria imutavel'); END;
CREATE TABLE IF NOT EXISTS sessao (token_hash TEXT PRIMARY KEY, usuario_id INTEGER NOT NULL REFERENCES usuario(id), expira REAL NOT NULL);
CREATE INDEX IF NOT EXISTS idx_roteiro_data ON roteiro(data,motorista_id);
CREATE INDEX IF NOT EXISTS idx_motorista_gerente ON motorista(gerente_id);
CREATE INDEX IF NOT EXISTS idx_ponto_roteiro ON ponto(roteiro_id,ordem_sequencial);
CREATE INDEX IF NOT EXISTS idx_auditoria_instante ON auditoria(instante);
