drop DATABASE IF EXISTS photoshare;
create database photoshare;
USE photoshare;

CREATE TABLE Users(
 user_id INTEGER AUTO_INCREMENT,
 first_name VARCHAR(100),
 last_name VARCHAR(100),
 email VARCHAR(100),
 birth_date DATE,
 hometown VARCHAR(100),
 gender VARCHAR(100),
 password VARCHAR(100) NOT NULL,
 PRIMARY KEY (user_id)
 );

 CREATE TABLE Friends(
 user_id1 INTEGER,
 user_id2 INTEGER,
 PRIMARY KEY (user_id1, user_id2),
 CONSTRAINT friend_user1_fk
     FOREIGN KEY (user_id1)
     REFERENCES Users(user_id) ON DELETE CASCADE,
 CONSTRAINT friend_user2_fk
     FOREIGN KEY (user_id2)
     REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Albums(
 albums_id INTEGER AUTO_INCREMENT,
 name VARCHAR(100),
 date DATE,
 user_id INTEGER NOT NULL,
 PRIMARY KEY (albums_id),
 CONSTRAINT albums_user_fk
	FOREIGN KEY (user_id)
	REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Tags(
 tag_id INTEGER AUTO_INCREMENT,
 name VARCHAR(100),
 PRIMARY KEY (tag_id)
);

CREATE TABLE Photos(
 photo_id INTEGER AUTO_INCREMENT,
 caption VARCHAR(100),
 data LONGBLOB,
 albums_id INTEGER NOT NULL,
 user_id INTEGER NOT NULL,
 PRIMARY KEY (photo_id),
 CONSTRAINT photos_album_fk
    FOREIGN KEY (albums_id) REFERENCES Albums (albums_id) ON DELETE CASCADE,
 CONSTRAINT photos_user_fk
    FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
);

CREATE TABLE Tagged(
 photo_id INTEGER,
 tag_id INTEGER,
 PRIMARY KEY (photo_id, tag_id),
 CONSTRAINT tagged_photo_fk
     FOREIGN KEY(photo_id)
     REFERENCES Photos (photo_id) ON DELETE CASCADE,
 CONSTRAINT tagged_tag_fk 
    FOREIGN KEY(tag_id)
    REFERENCES Tags (tag_id) ON DELETE CASCADE
);

CREATE TABLE Comments(
 comment_id INTEGER AUTO_INCREMENT,
 user_id INTEGER NOT NULL,
 photo_id INTEGER NOT NULL,
 text VARCHAR (100),
 date DATE,
 PRIMARY KEY (comment_id),
 CONSTRAINT comments_user_fk
    FOREIGN KEY (user_id)
    REFERENCES Users (user_id) ON DELETE CASCADE,
 CONSTRAINT comments_photo_fk
     FOREIGN KEY (photo_id)
     REFERENCES Photos (photo_id) ON DELETE CASCADE
);

CREATE TABLE Likes(
 photo_id INTEGER,
 user_id INTEGER,
 PRIMARY KEY (photo_id,user_id),
 CONSTRAINT likes_photo_fk
    FOREIGN KEY (photo_id)
    REFERENCES Photos (photo_id) ON DELETE CASCADE,
CONSTRAINT likes_user_fk
     FOREIGN KEY (user_id)
     REFERENCES Users (user_id) ON DELETE CASCADE
);

