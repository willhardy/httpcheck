-- It would be theoretically possible to normalise this, but I don't see any
-- need in this context. Most important are the unique constraints to
-- prevent duplicates when the same data are imported twice.
-- If it were important to save space, we could separate url, exception,
-- regex and identifier. SELECT queries would also be slightly faster, but the
-- INSERT logic would be more complicated.
CREATE TABLE IF NOT EXISTS attempts (
    id serial NOT NULL PRIMARY KEY,
    url varchar(200) NOT NULL,
    timestamp timestamp with time zone NOT NULL,
    response_time double precision CHECK (response_time > 0),
    is_online boolean NOT NULL,
    status_code smallint CHECK (status_code >= 0),
    hostname varchar(255) NOT NULL,
    identifier varchar(200) NOT NULL,
    exception varchar(200) NOT NULL,
    retries integer NOT NULL CHECK (retries >= 0),
    regex text NULL,
    regex_found boolean NULL,
    UNIQUE (url, identifier, timestamp)
);

-- Most queries are probably going to want to filter by URL and sort by timestamp
CREATE INDEX IF NOT EXISTS timestamp_idx ON attempts (url, timestamp);
