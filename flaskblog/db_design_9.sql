CREATE TABLE "user_accounts" (
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
  "key_code" varchar
);

CREATE TABLE "call_out_phone_numbers" (
  "id" serial PRIMARY KEY,
  "device_id" integer,
  "phone_number" varchar,
  "user_name" varchar
);

CREATE TABLE "out_of_hours" (
  "id" serial PRIMARY KEY,
  "device_id" integer,
  "out_of_hours_enabled" bool,
  "start_time" varchar,
  "end_time" varchar,
  "days" varchar,
  "alternative_phone_no" varchar
);

CREATE TABLE "config_misc" (
  "id" serial PRIMARY KEY,
  "device_id" integer,
  "security_code_enabled" bool,
  "security_code" varchar,
  "gate_lock_on" bool,
  "pulse_time" varchar
);

ALTER TABLE "site" ADD FOREIGN KEY ("user_id") REFERENCES "user_accounts" ("id");

ALTER TABLE "post" ADD FOREIGN KEY ("user_id") REFERENCES "user_accounts" ("id");

ALTER TABLE "device" ADD FOREIGN KEY ("site_id") REFERENCES "site" ("id");

ALTER TABLE "phone_number" ADD FOREIGN KEY ("device_id") REFERENCES "device" ("id");

ALTER TABLE "keypad_code" ADD FOREIGN KEY ("device_id") REFERENCES "device" ("id");

ALTER TABLE "call_out_phone_numbers" ADD FOREIGN KEY ("device_id") REFERENCES "device" ("id");

ALTER TABLE "out_of_hours" ADD FOREIGN KEY ("device_id") REFERENCES "device" ("id");

ALTER TABLE "config_misc" ADD FOREIGN KEY ("device_id") REFERENCES "device" ("id");
