CREATE TABLE IF NOT EXISTS notes (
    id         SERIAL PRIMARY KEY,
    title      TEXT        NOT NULL,
    content    TEXT        NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO notes (title, content)
SELECT title, content
FROM (
    VALUES
        (
            'Welcome to DataNotes',
            'This is a note taking app for the Datacenters subject. Everything you write is stored in a PostgreSQL database (SGBD) through the Flask API.'
        ),
        (
            'Tier levels',
            E'Tier I: single path, no redundancy.\nTier II: redundant components.\nTier III: concurrently maintainable.\nTier IV: fault tolerant, 99.995% availability.'
        ),
        (
            'PUE',
            'Power Usage Effectiveness = total facility power / IT equipment power. A PUE of 1.0 is the theoretical ideal; modern hyperscale sites reach ~1.1.'
        ),
        (
            'Cooling',
            'Common approaches: raised-floor CRAC units, in-row cooling, rear-door heat exchangers and direct-to-chip liquid cooling for high density racks.'
        )
) AS seed(title, content)
WHERE NOT EXISTS (SELECT 1 FROM notes);
