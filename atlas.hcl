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

env "clickhouse" {
  url = getenv("CLICKHOUSE_URL")
  dev = "docker://clickhouse/clickhouse-server:25.11/dev"

  schema {
    src = "db/schema/clickhouse"
  }

  migration {
    dir = "file://db/migrations/clickhouse"
  }

  format {
    migrate {
      diff = "{{ sql . \"  \" }}"
    }
  }
}
