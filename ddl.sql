DROP DATABASE IF EXISTS socialnetwork;
CREATE DATABASE socialnetwork;
USE socialnetwork;

CREATE TABLE user(
   uid VARCHAR(50),
   first_name VARCHAR(50),
   last_name VARCHAR(50),
   email VARCHAR(50),
   dob DATE,
   hometown VARCHAR(50),
   gender VARCHAR(10),
   pw VARCHAR(50),
   PRIMARY KEY (uid)
);

CREATE TABLE friend(
   uid1 VARCHAR(50),
   uid2 VARCHAR(50),
   PRIMARY KEY (uid1,uid2),
   CONSTRAINT friend_fk FOREIGN KEY (uid1) REFERENCES user(uid),
   CONSTRAINT friend_fk2 FOREIGN KEY (uid2) REFERENCES user(uid)
);

CREATE TABLE album(
   id VARCHAR(50),
   name VARCHAR(50),
   owner_uid VARCHAR(50),
   date_created DATE,
   PRIMARY KEY (id),
   CONSTRAINT album_fk FOREIGN KEY (owner_uid) REFERENCES user(uid)
);

CREATE TABLE photo(
   pid VARCHAR(50),
   caption CHAR,
   filepath CHAR,
   PRIMARY KEY (pid)
);

CREATE TABLE comment(
   id VARCHAR(50),
   text CHAR,
   date_created DATE,
   pid VARCHAR(50),
   PRIMARY KEY (id),
   CONSTRAINT comment_fk FOREIGN KEY (pid) REFERENCES photo(pid)
);

CREATE TABLE tag(
   tid VARCHAR(50),
   name VARCHAR(50),
   PRIMARY KEY (tid)
);

CREATE TABLE tagged(
   tid VARCHAR(50),
   pid VARCHAR(50),
   PRIMARY KEY (tid,pid),
   CONSTRAINT tagged_fk FOREIGN KEY (tid) REFERENCES tag(tid),
   CONSTRAINT tagged_fk2 FOREIGN KEY (pid) REFERENCES photo(pid)
);

CREATE TABLE likes(
   uid VARCHAR(50),
   pid VARCHAR(50),
   PRIMARY KEY (uid,pid),
   CONSTRAINT likes_fk FOREIGN KEY (uid) REFERENCES user(uid),
   CONSTRAINT likes_fk2 FOREIGN KEY (pid) REFERENCES photo(pid)
);


   