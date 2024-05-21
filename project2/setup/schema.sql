CREATE TABLE IF NOT EXISTS articles (
  title VARCHAR PRIMARY KEY,
  body TEXT NOT NULL,
  search_vector TSVECTOR
);

CREATE INDEX articles_search_idx ON articles USING GIN (search_vector);
