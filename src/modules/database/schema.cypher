CREATE CONSTRAINT player_id IF NOT EXISTS ON (p:Player) ASSERT p.id IS UNIQUE;
CREATE CONSTRAINT game_id IF NOT EXISTS ON (g:Game) ASSERT g.id IS UNIQUE;
CREATE CONSTRAINT blunder_id IF NOT EXISTS ON (b:Blunder) ASSERT b.id IS UNIQUE;
CREATE CONSTRAINT opening_eco IF NOT EXISTS ON (o:Opening) ASSERT o.eco_code IS UNIQUE;
CREATE CONSTRAINT position_fen IF NOT EXISTS ON (p:Position) ASSERT p.fen IS UNIQUE;

CREATE INDEX player_rating IF NOT EXISTS FOR (p:Player) ON (p.rating);
CREATE INDEX game_date IF NOT EXISTS FOR (g:Game) ON (g.date);
CREATE INDEX blunder_severity IF NOT EXISTS FOR (b:Blunder) ON (b.severity);
