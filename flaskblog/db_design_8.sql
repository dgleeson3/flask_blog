CREATE TABLE "user" (
  "id" serial PRIMARY KEY,
  "email" varchar UNIQUE,
  "username" varchar,
  "password" varchar,
  "image_file" varchar
);

CREATE TABLE "post" (
  "id" serial PRIMARY KEY,
  "title" varchar UNIQUE,
  "date_posted" timestamp,
  "content" varchar,
  "user_id" integer
);

CREATE TABLE "site" (
  "id" serial PRIMARY KEY,
  "user_id" integer,
  "site_name" varchar,
  "site_contact_details" varchar
);

CREATE TABLE "device" (
  "id" serial PRIMARY KEY,
  "device_type_name" integer,
  "device_sim_number" varchar,
  "access_point_name" varchar,
  "site_id" integer
);

CREATE TABLE "phone_number" (
  "id" serial PRIMARY KEY,
  "device_id" integer,
  "phone_number" varchar,
  "user_name" varchar
);

CREATE TABLE "keypad_code" (
  "id" serial PRIMARY KEY,
  "device_id" integer,
  "name" varchar,
  "country_id" integer
);

CREATE TABLE "open_number_white_list" (
  "id" serial PRIMARY KEY,
  "device_id" integer,
  "country_code" varchar,
  "name" varchar
);

CREATE TABLE "out_of_hours" (
  "id" serial PRIMARY KEY,
  "device_id" integer,
  "country_code" varchar,
  "name" varchar
);

ALTER TABLE "site" ADD FOREIGN KEY ("user_id") REFERENCES "user" ("id");

ALTER TABLE "post" ADD FOREIGN KEY ("user_id") REFERENCES "user" ("id");

ALTER TABLE "device" ADD FOREIGN KEY ("site_id") REFERENCES "site" ("id");

ALTER TABLE "phone_number" ADD FOREIGN KEY ("device_id") REFERENCES "device" ("id");

ALTER TABLE "keypad_code" ADD FOREIGN KEY ("device_id") REFERENCES "device" ("id");

ALTER TABLE "open_number_white_list" ADD FOREIGN KEY ("device_id") REFERENCES "device" ("id");

ALTER TABLE "out_of_hours" ADD FOREIGN KEY ("device_id") REFERENCES "device" ("id");
