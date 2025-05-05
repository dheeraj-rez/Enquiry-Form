import json
import logging
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Email configuration
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv('EMAIL_USER') 
SENDER_PASSWORD = os.getenv('EMAIL_PASS') 

# Notion configuration
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
TOUR_DATABASE_ID = os.environ.get("TOUR_DATABASE_ID")
CONTACT_DATABASE_ID = os.environ.get("CONTACT_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)

# Function to validate date format
def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def create_notion_page(database_id, properties):
    """
    Create a new page in the specified Notion database with the given properties.
    """
    try:
        response = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        return response
    except Exception as e:
        logger.error(f"Error creating Notion page: {e}")
        return None

# Function to send email
def send_email(receiver_email, subject, body_text):
    """
    Send an email using SMTP.
    """
    try:
        # Create an email message
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        # In future, we can add HTML content as well
        msg.set_content(body_text)
        # Create a secure SSL context
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            return True
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return False

# Lambda function handler
def handler_function(event, context):
    """
    Lambda function to handle incoming requests and add data to Notion.
    It validates the input data, adds it to the Notion database, and sends a confirmation email.
    """
    try:
        body = json.loads(event.get("body") or "{}")
        query_param = event.get("queryStringParameters") or {}
        type_param = query_param.get("type", "")

        # Validate query parameters
        if not type_param:
            return {"statusCode": 400, "body": json.dumps({"message":"Query param 'type' is required"})}
        if type_param not in ["contact-enquiry", "tour-enquiry"]:
            return {"statusCode": 400, "body": json.dumps({"message":"Invalid type. Must be 'enquiry' or 'contact'"})}

        # Check if the body is empty
        if not body:
            return {"statusCode": 400, "body": json.dumps({"message":"Body is required"})}

        if type_param == "tour-enquiry":
            # Extract data from the body
            email = body.get("email")
            name = body.get("full_name")
            contact = body.get("contact_number")
            preference = body.get("preference")
            start_date = body.get("start_date")
            end_date = body.get("end_date")
            num_of_people = body.get("num_of_people", {})
            adult = num_of_people.get("adult", 0)
            child = num_of_people.get("child", 0)
            num_of_rooms = body.get("num_of_rooms", {})
            double_bedroom = num_of_rooms.get("double_bedroom", 0)
            twin_bedroom = num_of_rooms.get("twin_bedroom", 0)
            tour_slug = body.get("tour_slug", "")

            # Validate required fields
            if not email :
                return {"statusCode": 400, "body": json.dumps({"message":"Email is required"})}
            
            if not name or not contact or not preference or not start_date or not end_date or not num_of_people or not num_of_rooms or not adult or not child or not double_bedroom or not twin_bedroom or not tour_slug:
                return {"statusCode": 400, "body": json.dumps({"message":"All fields are required"})}

            # Validate date format
            if not is_valid_date(start_date) or not is_valid_date(end_date):
                return {"statusCode": 400, "body": json.dumps({"message":"Invalid date format. Use YYYY-MM-DD."})}

            # Add the data to Notion
            database_id = TOUR_DATABASE_ID
            properties={
                    "Name": {"title": [{"text": {"content": name}}]},
                    "Email": {"email": email},
                    "Contact": {"phone_number": str(contact)},
                    "Preference": {"rich_text": [{"text": {"content": preference}}]},
                    "Start Date": {"date": {"start": start_date}},
                    "End Date": {"date": {"start": end_date}},
                    "Adults": {"number": adult},
                    "Children": {"number": child},
                    "Room With Double Bed": {"number": double_bedroom},
                    "Room With Twin Bed": {"number": twin_bedroom},
                    "Tour Slug": {"rich_text": [{"text": {"content": tour_slug}}]},
                }
            # email body and subject
            subject = "Tour Enquiry Form Submission"
            body_text = f"Thank you for your enquiry, {name}. We will get back to you soon."

        elif type_param == "contact-enquiry":
            logger.info("Contact enquiry")   
            # Extract data from the body
            email = body.get("email")
            first_name = body.get("first_name")
            last_name = body.get("last_name")
            country_code = body.get("country_code")
            phone_number = body.get("phone_number")
            referral_source = body.get("referral_source")
            signup_newsletter = body.get("signup_newsletter")
            raw_destinations = body.get("destinations", [])
            destinations = ", ".join(raw_destinations) if isinstance(raw_destinations, list) else raw_destinations
            travel_date = body.get("travel_date")
            duration = body.get("duration")
            num_of_peoples = body.get("num_of_peoples")
            spend_per_person = body.get("spend_per_person")
            requests = body.get("requests")
            # Validate required fields
            if not email:
                return {"statusCode": 400, "body": json.dumps({"message":"Email is required"})}
            
            if not first_name or not last_name or not country_code or not phone_number or not referral_source or not raw_destinations or not travel_date or not duration or not num_of_peoples or not spend_per_person or not requests:
                return {"statusCode": 400, "body": json.dumps({"message":"All fields are required"})}
            
            database_id = CONTACT_DATABASE_ID
            properties = {
                "Name": {"title": [{"text": {"content": f"{first_name} {last_name}"}}]},
                "Email": {"email": email},
                "Telephone": {"phone_number": str(country_code) + str(phone_number)},
                "How did you hear about us?": {"rich_text": [{"text": {"content": referral_source}}]},
                "Newsletter Signup": {"checkbox": signup_newsletter},
                "Where would you like to go?": {"rich_text": [{"text": {"content": destinations}}]},
                "When would you like to go?": {"rich_text": [{"text": {"content": travel_date}}]},
                "How long for?": {"rich_text": [{"text": {"content": duration}}]},
                "How many people are travelling?": {"number": num_of_peoples},
                "How much would you like to spend per person?": {"rich_text": [{"text": {"content": spend_per_person}}]},
                "Any other comments or requests?": {"rich_text": [{"text": {"content": requests}}]}
            }
            # email body and subject
            subject = "Contact Enquiry Form Submission"
            body_text = f"Thank you for your enquiry, {first_name}. We will get back to you soon."

        # Create a new page in Notion
        response = create_notion_page(database_id, properties)
        # Check if the page was created successfully
        if not response:
            logger.error("Failed to create Notion page")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Failed to add data to Notion"})
            }
        # Log the response from Notion
        logger.info(f"Notion response: {response.get('id')}")

        # Send email
        email_sent = send_email(email, subject, body_text)

        # Check if email was sent successfully
        if response and email_sent:
            logger.info(f"Email sent to {email}")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Enquiry submitted successfully"})
            }
        else:
            logger.error(f"Failed to send email to {email}")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Failed to send email"})
            }
    
    except json.JSONDecodeError as e:
        # Handle JSON decode error
        logger.error(f"Invalid JSON format: {e}")
        return {"statusCode": 400, "body": json.dumps({"message": "Invalid JSON format"})}
    
    except notion.APIResponseError as e:
        # Handle Notion API errors
        logger.error(f"Notion API error: {e}")
        return {"statusCode": 500, "body": json.dumps({"message": "Failed to add data to Notion"})}
    
    except smtplib.SMTPException as e:
        # Handle SMTP exceptions
        logger.error(f"SMTP error: {e}")
        return {"statusCode": 500, "body": json.dumps({"message": "Email sending failed"})}
    
    except Exception as e:
        # Catch-all for any other exceptions
        logger.error(f"Unexpected error: {e}")
        return {"statusCode": 500, "body": json.dumps({"message": "Internal server error"})}
    