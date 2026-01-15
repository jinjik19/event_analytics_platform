env "postgres" {
  url = getenv("POSTGRES_URL")
  dev = "docker://postgres/17-bookworm/dev?search_path=public"

  schema {
    src = "db/schema/postgres"
  }

  migration {
    dir = "file://db/migrations/postgres"
  }
}
