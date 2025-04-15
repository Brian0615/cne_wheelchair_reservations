# CNE Wheelchair Reservations

## Docker

### Building the Images

```bash
docker compose build
```

> #### Building Individual Images
> ```bash
> docker build -t brianlammm/cne_api -f api.Dockerfile .
> docker build -t brianlammm/cne_ui -f ui.Dockerfile .
> ```

### Pushing the Images to Docker Hub

```bash
docker compose push
```

> #### Pushing Individual Images
> ```bash
> docker push brianlammm/cne_api
> docker push brianlammm/cne_ui
> ```

### Running the Containers

**Using Docker Compose**
```bash
docker compose up
```

**Running an Individual Container**

```bash
docker run --env-file api.env brianlammm/cne_api
```

### Required Environment Variables

#### API

| Variable                | Description                                          |
|:------------------------|:-----------------------------------------------------|
| `AWS_ACCESS_KEY_ID`     | The access key ID for the AWS account (optional)     |
| `AWS_DEFAULT_REGION`    | The default region for the AWS account (optional)    |
| `AWS_SECRET_ACCESS_KEY` | The secret access key for the AWS account (optional) |
| `CNE_YEAR`              | The year of the CNE (used for DynamoDB and S3 paths) |
| `S3_BUCKET`             | The name of the S3 bucket to connect to              |

**Authentication Methods for S3**

* **AWS IAM Access Key**: provided by `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION`
* **AWS IAM Role**: provided by the IAM role attached to the local / EC2 instance

#### UI

| Variable           | Description                                                     |
|:-------------------|:----------------------------------------------------------------|
| `API_HOST`         | The host of the API                                             |
| `API_PORT`         | The port of the API                                             |
| `AUTH_METHOD`      | The authentication method to use (either `local` or `cognito`)  |
| `AUTH_CONFIG_PATH` | The path to the authentication configuration file for Streamlit |
| `CNE_YEAR`         | The year of the CNE                                             |
| `PDF_PASSWORD`     | The password for locking PDF permissions                        |

**Authentication Methods for UI**
* **Local**: uses Streamlit Authenticator with credentials stored in a local file provided by `AUTH_CONFIG_PATH`
* **Cognito**: uses AWS Cognito for authentication (and `AUTH_CONFIG_PATH` is not used)
