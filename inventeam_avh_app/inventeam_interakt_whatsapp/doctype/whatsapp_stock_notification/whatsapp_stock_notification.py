import frappe
import json
from frappe.integrations.utils import make_post_request
from datetime import datetime
from frappe.model.document import Document

def enqueue_send_whatsapp_message(api_key, api_url, template_name, mobile_no, contact_name):
    frappe.enqueue(
        'inventeam_avh_app.inventeam_interakt_whatsapp.doctype.whatsapp_stock_notification.whatsapp_stock_notification.send_whatsapp_message',
        queue='short',
        job_name='Stock WhatsApp Notification',
        api_key= api_key,
        api_url= api_url,
        template_name= template_name,
        mobile_no= mobile_no,
        contact_name= contact_name,
    )
    
@frappe.whitelist()
def send_whatsapp_message(api_key, api_url, template_name, mobile_no, contact_name):
    # Use 4 spaces for indentation
    current_datetime = datetime.now()
    headers = {
            "authorization": f"Basic {api_key}",
            "content-type": "application/json"
        }
        
    data = {
            "countryCode": "+91",
            "phoneNumber": mobile_no,
            "callbackData": "some text here",
            "type": "Template",
            "template": {
                "name": template_name,
                "languageCode": "en",
                "bodyValues": [
                    contact_name,
                ]
            }
        }
        
    response = make_post_request(
        f"{api_url}",
        headers=headers,
        data=json.dumps(data)
    )

    # Create a WhatsApp Message document
    frappe.get_doc({
        "doctype": "Whatsapp Messages",
        "label": "Notification",
        "message": str(data['template']),
        "to": data['phoneNumber'],
        "message_id": response['id'],
        "sent_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    }).save(ignore_permissions=True)
    
class WhatsappStockNotification(Document):
    def after_insert(self):
        # Use 4 spaces for indentation
        wa_setting = frappe.get_doc("Whatsapp Setting", "Whatsapp Setting")
        api_key = wa_setting.api_key
        api_url = wa_setting.api_url
    
        sql = self.data_query  # Assuming self.query is a valid SQL query
        if self.mobile_no:
            sql = f"{sql} and mobile_no like '{self.mobile_no}%'"
            
        results = frappe.db.sql(sql, as_dict=True)
        template_name = self.template_name
        i = 0
        for result in results:
            i += 1
            enqueue_send_whatsapp_message(api_key,api_url, template_name, result["mobile_no"], result["ContactName"])
        
        self.message_count = i
        self.save()