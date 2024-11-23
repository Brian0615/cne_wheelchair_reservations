# CNE Wheelchair Reservations

## Docker

### Building the Containers

```bash
docker build -t brianlammm/cne_api -f api.Dockerfile .
docker build -t brianlammm/cne_ui -f ui.Dockerfile .
```

### Pushing the Containers to Docker Hub

```bash
docker push brianlammm/cne_api
docker push brianlammm/cne_ui
```

### Running the Containers

```bash
docker compose up
```

### Required Environment Variables

#### API

| Variable            | Description                                  |
|:--------------------|:---------------------------------------------|
| `POSTGRES_DATABASE` | The name of the database to connect to       |
| `POSTGRES_HOST`     | The host of the database                     |
| `POSTGRES_PORT`     | The port of the database                     |
| `POSTGRES_USERNAME` | The user to connect to the database with     |
| `POSTGRES_PASSWORD` | The password to connect to the database with |
| `POSTGRES_SCHEMA`   | The schema to use in the database            |

#### UI

| Variable   | Description         |
|:-----------|:--------------------|
| `API_HOST` | The host of the API |
| `API_PORT` | The port of the API |
| `CNE_YEAR` | The year of the CNE |