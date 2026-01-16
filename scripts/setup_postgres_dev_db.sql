DO
$do$
BEGIN
   IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE  rolname = 'learnscripture_dev') THEN
      RAISE NOTICE 'Role "learnscripture_dev" already exists. Skipping.';
   ELSE
      CREATE USER learnscripture_dev WITH PASSWORD 'learnscripture_dev';
   END IF;
END
$do$;

GRANT ALL ON DATABASE learnscripture_dev TO learnscripture_dev;
GRANT ALL ON DATABASE learnscripture_wordsuggestions_dev TO learnscripture_dev;
ALTER USER learnscripture_dev CREATEDB;
ALTER DATABASE learnscripture_dev OWNER to learnscripture_dev;
ALTER DATABASE learnscripture_wordsuggestions_dev OWNER to learnscripture_dev;
