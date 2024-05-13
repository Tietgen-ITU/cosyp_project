CREATE TABLE IF NOT EXISTS articles (
  title VARCHAR(255) PRIMARY KEY,
  body TEXT NOT NULL,
  search_vector TSVECTOR
);

CREATE INDEX articles_search_vector_idx ON articles USING GIN (search_vector);
