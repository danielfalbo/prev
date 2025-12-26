CREATE TABLE authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    html TEXT
);

CREATE TABLE weblog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    listed INTEGER DEFAULT 1 NOT NULL,
    html TEXT
);

CREATE TABLE resource_authors (
    resource_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    PRIMARY KEY (resource_id, author_id),
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
);

CREATE INDEX idx_resource_authors_author ON resource_authors(author_id);
