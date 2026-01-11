env "postgres" {
  url = getenv("POSTGRES_URL")
  dev = getenv("POSTGRES_URL")

  schema {
    src = "db/schema/postgres"
  }

  migration {
    dir = "file://db/migrations/postgres"
  }
}
