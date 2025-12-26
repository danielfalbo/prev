CREATE TABLE authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookmarks (
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

CREATE TABLE bookmark_authors (
    bookmark_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    PRIMARY KEY (bookmark_id, author_id),
    FOREIGN KEY (bookmark_id) REFERENCES bookmarks(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
);

CREATE INDEX idx_bookmarks_authors_author ON bookmark_authors(author_id);
