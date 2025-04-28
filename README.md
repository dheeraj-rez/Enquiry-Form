# Enquiry Form API on AWS

This project demonstrates a simple HTTP API for an enquiry form using Python, AWS Lambda, and API Gateway with the Serverless Framework.

## Deployment

Deploy the API with:

```bash
serverless deploy
```

After deployment, note the API endpoint from the output.

## API Endpoints

### Submit Enquiry

**Endpoint:** `/submit`  
**Method:** `POST`  
**Description:** Handles form submissions.

## Local Development

Run the API locally:

```bash
serverless offline
```

The API will be available at `http://localhost:3000`.

## Environment Variables

Ensure the following environment variables are set:

- `NOTION_TOKEN`
- `TOUR_DATABASE_ID`
- `CONTACT_DATABASE_ID`
- `EMAIL_USER`
- `EMAIL_PASS`

## Dependencies

Install dependencies with:

```bash
serverless plugin install -n serverless-python-requirements
```

Add required packages to `requirements.txt`.

For more details, refer to the [Serverless Framework documentation](https://www.serverless.com/framework/docs/).
