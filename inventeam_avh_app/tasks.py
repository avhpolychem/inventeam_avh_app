import frappe
import json
from frappe.integrations.utils import make_post_request
from datetime import datetime

def cron():
    query = """SELECT customer,contact_email,posting_date,NAME AS invoice_no,outstanding_amount,due_date,DATEDIFF(CURDATE(),due_date) AS Overdue_Days 
            FROM `tabSales Invoice`
            WHERE outstanding_amount > 0 AND DATEDIFF(CURDATE(),due_date) > 0 AND customer='Adduco Polypack'
            Order BY customer,contact_email,due_date"""
            
    sql_data = frappe.db.sql(query, as_dict=True)
    
    distinct_email_id = set()
    
    message_body_head = """<table style="font-family:Calibri;width:627px;border-collapse:collapse;color:rgb(96,96,96);border:thin solid rgb(229,228,226);background-color:rgb(144,144,144);font-size:0.75em">
                            <thead>
                                <tr>
                                    <td colspan="8" align="center" style="color:rgb(239,239,239);font-size:1.5em;vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)"><b>Inventeam Solutions Pvt. Ltd. - Credit Department</b></td>
                                </tr>
                                <tr>
                                    <td colspan="8" bgcolor="White" valign="middle" style="vertical-align:middle;background-color:white;padding:0.6em">Dear Sir/ Madam,<br><br>Greetings of the Day!<br><br>We would like to bring it to your immediate attention following invoices getting due in next 10 days and / or invoices already overdue as on today.<br><br>You are requested to make necessary arrangements to pay these invoices as per the due dates mentioned in the table below.<br><br></td>
                                </tr>
                                <tr>
                                 <th bgcolor="#909090" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Bill No</th>
                                 <th bgcolor="#909090" align="center" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Bill Date</th>
                                 <th bgcolor="#909090" align="center" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Due Date</th>
                                 <th bgcolor="#909090" align="center" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Amount (Rs.)</th>
                                 <th bgcolor="#909090" align="center" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Overdue Days</th>
                              </tr>
                            </thead>"""
    
    message_body_footer = """<tr bgcolor="#efefef" style="background-color:rgb(250,250,250)">
                                 <td colspan="8" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)"><br><br><b>For making the payment thru RTGS/ NEFT to AVH Polychem Pvt. Ltd., our bank details are mentioned below.</b></td>
                              </tr>
                              <tr bgcolor="#fafafa" style="background-color:rgb(239,239,239)">
                                 <td colspan="3" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)"><b>Bank Name:</b></td>
                                 <td colspan="5" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">HDFC Bank Ltd</td>
                              </tr>
                              <tr bgcolor="#efefef" style="background-color:rgb(250,250,250)">
                                 <td colspan="3" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)"><b>Beneficiary Name:</b></td>
                                 <td colspan="5" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">AVH Polychem Private Limited</td>
                              </tr>
                              <tr bgcolor="#fafafa" style="border-bottom:1px solid rgb(64,64,64);background-color:rgb(239,239,239)">
                                 <td colspan="3" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)"><b>Account No:</b></td>
                                 <td colspan="5" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">01822560002048</td>
                              </tr>
                              <tr bgcolor="#efefef" style="border-bottom:1px solid rgb(64,64,64);background-color:rgb(250,250,250)">
                                 <td colspan="3" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)"><b>IFSC Code:</b></td>
                                 <td colspan="5" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">HDFC0000182.</td>
                              </tr>
                              <tr bgcolor="#fafafa" style="border-bottom:1px solid rgb(64,64,64);background-color:rgb(239,239,239)">
                                 <td colspan="8" bgcolor="White" valign="middle" style="vertical-align:middle;border:thin solid rgb(229,228,226);background-color:white;padding:0.6em">If you have any queries please contact concerned person in AVH Polychem Private Limited<br><br>Regards,<br>Credit Department<br><a href="mailto:RKushte@vinmar.com" target="_blank">RKushte@vinmar.com</a>&nbsp;- 022-35462127<br><a href="mailto:Siddhesh.Pingale@axiaplastics.com" target="_blank">Siddhesh.Pingale@axiaplastics.<wbr>com</a>&nbsp;- 022-35462311<br><a href="mailto:Anil.Gaud@axiaplastics.com" target="_blank">Anil.Gaud@axiaplastics.com</a>&nbsp;- 022-35462320<br><br></td>
                              </tr>
                            </tbody>
                           <tfoot style="color:rgb(48,48,48)">
                              <tr>
                                 <td colspan="8" align="center" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)"><b>This is an auto generated e-mail, please ignore this mail if already paid.</b></td>
                              </tr>
                           </tfoot>
                        </table>"""
    
    message_body_row = """<tbody>"""
    recipients = ""
    
    for row in sql_data:
        email_id = row.contact_email
        if email_id not in distinct_email_id:
            distinct_email_id.add(email_id)
            
            if message_body_row == "<tbody>":
                message_body = message_body_head + message_body_row + message_body_footer
                frappe.enqueue(
                    method=frappe.sendmail,
                    queue='short',
                    job_name='Outstanding Notification',
                    recipients= recipients,
                    subject= "Overdue Payment Pending",
                    message= message_body
                )
                
            message_body_row = """<tbody>"""    
            recipients = email_id
            
        
        message_body_row = message_body_row + f"""<tr bgcolor="#efefef" style="background-color:rgb(250,250,250)">
                                                   <td style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{row.invoice_no}</td>
                                                   <td align="center" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{row.posting_date}</td>
                                                   <td align="center" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{row.due_date}</td>
                                                   <td align="right" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{frappe.utils.fmt_money(row.outstanding_amount,currency='INR')}</td>
                                                   <td align="center" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{row.Overdue_Days}</td>
                                                   </tr>"""
            
        
    if message_body_row == "<tbody>":
        message_body = message_body_head + message_body_row + message_body_footer
        print(message_body)
        frappe.enqueue(
            method=frappe.sendmail,
            queue='short',
            job_name='Outstanding Notification',
            recipients= recipients,
            subject= "Overdue Payment Pending",
            message= message_body
        )

def send_whatsapp_stock_notification():
    query = """SELECT * FROM `tabWhatsapp Messages API Data`
                WHERE api_trigger = 0
                LIMIT 1"""
            
    sql_data = frappe.db.sql(query, as_dict=True)

    for row in sql_data:
        send_whatsapp_message(row.api_key,row.api_url,row.template_name,row.whatsapp_number,row.contact_name,row.text_message)
        #frappe.enqueue(
        #    'inventeam_avh_app.inventeam_interakt_whatsapp.doctype.whatsapp_stock_notification.whatsapp_stock_notification.send_whatsapp_message',
        #    queue='short',
        #    job_name='Stock WhatsApp Notification',
        #    api_key= row.api_key,
        #    api_url= row.api_url,
        #    template_name= row.template_name,
        #    whatsapp_number= row.whatsapp_number,
        #    contact_name= row.contact_name,
        #    text_message= row.text_message
        #)
        
        doc = frappe.get_doc("Whatsapp Messages API Data", row.name)
        doc.api_trigger = 1
        doc.save()

def weekly():
    pass


def send_whatsapp_message(api_key, api_url, template_name, whatsapp_number, contact_name, text_message):
    # Use 4 spaces for indentation
    current_datetime = datetime.now()
    headers = {
            "authorization": f"Basic {api_key}",
            "content-type": "application/json"
        }
        
    data = {
            "countryCode": "+91",
            "phoneNumber": whatsapp_number,
            "callbackData": "some text here",
            "type": "Template",
            "template": {
                "name": template_name,
                "languageCode": "en",
                "bodyValues": [
                    contact_name + " ji",
                    text_message,
                ],
                "fileName": "AVH_Logo.jpg",
                "headerValues": [
                    "https://avh.inventeam.in/files/AVHPL_Logo.jpg"
                ],
            }
        }
    
    response = make_post_request(
        f"{api_url}",
        headers=headers,
        data=json.dumps(data)
    )

    frappe.get_doc({
        "doctype": "Whatsapp Messages",
        "label": "Stock Notification",
        "request_data": data,
        "response_data": response,
        "to": data['phoneNumber'],
        "message_id": response['id'],
        "sent_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    }).save(ignore_permissions=True)