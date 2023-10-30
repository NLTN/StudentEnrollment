PRAGMA foreign_key = ON;
BEGIN TRANSACTION;

DROP TABLE IF EXISTS user;
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    hashed_password TEXT NOT NULL
);

DROP TABLE IF EXISTS roles;
CREATE TABLE roles (
    id INTEGER PRIMARY KEY,
    role_name TEXT NOT NULL
);

DROP TABLE IF EXISTS user_role;
CREATE TABLE user_role (
    user_id INTEGER,
    role_id INTEGER,
    PRIMARY KEY (user_id, role_id)
    FOREIGN KEY (user_id) REFERENCES user(id)
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

COMMIT;