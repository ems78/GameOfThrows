CREATE CONSTRAINT player_id IF NOT EXISTS ON (p:Player) ASSERT p.id IS UNIQUE;
CREATE CONSTRAINT game_id IF NOT EXISTS ON (g:Game) ASSERT g.id IS UNIQUE;
CREATE CONSTRAINT opening_eco IF NOT EXISTS ON (o:Opening) ASSERT o.eco_code IS UNIQUE;

CREATE INDEX player_rating IF NOT EXISTS FOR (p:Player) ON (p.rating);
CREATE INDEX game_created_at IF NOT EXISTS FOR (g:Game) ON (g.created_at);
CREATE INDEX game_last_move_at IF NOT EXISTS FOR (g:Game) ON (g.last_move_at);
CREATE INDEX game_winner IF NOT EXISTS FOR (g:Game) ON (g.winner);
CREATE INDEX game_victory_status IF NOT EXISTS FOR (g:Game) ON (g.victory_status);
CREATE INDEX game_increment_code IF NOT EXISTS FOR (g:Game) ON (g.increment_code);
CREATE INDEX opening_ply IF NOT EXISTS FOR (o:Opening) ON (o.ply);
