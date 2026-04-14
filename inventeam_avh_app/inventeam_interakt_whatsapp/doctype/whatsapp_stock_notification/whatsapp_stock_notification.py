import frappe
import json
import os
import subprocess
from frappe.integrations.utils import make_post_request
from datetime import datetime
from frappe.model.document import Document
from frappe.utils import get_site_path

def save_whatsapp_api_data(api_key, api_url, template_name, whatsapp_number, contact_name, text_message):
    current_datetime = datetime.now()
    
    frappe.get_doc({
        "doctype": "Whatsapp Messages API Data",
        "api_key": api_key,
        "api_url": api_url,
        "template_name": template_name,
        "whatsapp_number": whatsapp_number,
        "contact_name": contact_name,
        "text_message": text_message,
        "api_trigger": 0,
        "api_data_date": current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    }).save(ignore_permissions=True)

    
@frappe.whitelist()
def send_whatsapp_message(api_key, api_url, template_name, whatsapp_number, contact_name, text_message):
    # Use 4 spaces for indentation
    current_datetime = datetime.now()
    headers = {
            "authorization": f"Basic {api_key}",
            "content-type": "application/json"
        }
    photo_url = "https://avhpolychem.frappe.cloud/files/AVHPL_Logo.jpg"
    body_values = [contact_name + " ji", text_message]

    if template_name == "stock_notification":
        data_dict = convert_to_structure(text_message)
        photo_url = generate_price_list_image(data_dict)
        template_name = "stock_notification_de"
        body_values.pop(1)

    data = {
            "countryCode": "+91",
            "phoneNumber": whatsapp_number,
            "callbackData": "some text here",
            "type": "Template",
            "template": {
                "name": template_name,
                "languageCode": "en",
                "bodyValues": body_values,
                "fileName": "AVH_Logo.jpg",
                "headerValues": [
                    photo_url
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



def get_available_items(group=None, sub_group=None):
    min_qty = frappe.db.get_single_value('Custom Stock Setting', 'min_qty')
    cond = ""
    if min_qty:
        cond = " and (bn.actual_qty - bn.reserved_qty) > " + str(min_qty)
    if group:
        cond = cond + " and it.group='" + group + "'"
    if sub_group:
        cond = cond + " and it.sub_group='" + sub_group + "'"
        
    available_item = frappe.db.sql("""
    select bn.item_code,it.item_name,bn.warehouse,bn.actual_qty,bn.reserved_qty, (bn.actual_qty - bn.reserved_qty) as rem_qty,it.group,it.sub_group from `tabBin` bn inner join `tabItem` it on it.name = bn.item_code where bn.actual_qty > 0  AND bn.warehouse NOT LIKE ('%In Transit%') {cond}
    """.format(cond=cond),as_dict=1)
    return available_item

def get_invoiced_contact_whatsapp(item):
    data = []
    subgrp = frappe.db.get_value("Item",item,"sub_group")
    if subgrp:
        similar_item = frappe.db.sql("""
        select name from `tabItem` where sub_group = %s
        """,(subgrp),as_dict=1)
        s_l = [i['name'] for i in similar_item]
        if similar_item:
            data = frappe.db.sql("""
                select
                sii.item_code,
                sii.item_name,
                si.customer,
                c.customer_name,                
                cc.first_name as contact_name,
                cp.phone
                from
                `tabSales Invoice Item` sii
                left join `tabSales Invoice` si on si.name = sii.parent
                left join `tabCustomer` c on c.name = si.customer
                left join `tabDynamic Link` cdl on cdl.link_name = c.name
                left join `tabContact` cc on cdl.parent = cc.name
                join `tabContact Phone` cp on cp.parent = cc.name 
                where
                si.docstatus = 1
                and
                cdl.link_doctype = 'Customer'
                and
                cp.is_whatsapp_no_ak = 1
                and
                sii.item_code in %(l)s group by cp.phone,sii.item_code
                order by si.name
                """, ({"l":tuple(s_l)}),as_dict = True)
            return data
    return data

def get_subgroup_contact_whatsapp(item):
    data = []
    subgrp = frappe.db.get_value("Item",item,"sub_group") 
    if subgrp:
        data = frappe.db.sql("""
            select
            cp.phone,
            cc.first_name as contact_name
            from
            `tabContact Phone` cp
            left join `tabDynamic Link` cdl on cp.parent = cdl.parent
            left join `tabContact` cc on cp.parent = cc.name
            left join `tabContact Sub Group` ccsg on ccsg.parent = cc.name
            where
            ccsg.sub_group = %s
            and
            cp.is_whatsapp_no_ak = 1
            """,(subgrp),as_dict = True)
    return data


class WhatsappStockNotification(Document):
    def after_insert(self):
        # Use 4 spaces for indentation
        wa_setting = frappe.get_doc("Whatsapp Setting", "Whatsapp Setting")
        api_key = wa_setting.api_key
        api_url = wa_setting.api_url
        
        f_group = None
        f_sub_group = None
        if self.group:
            f_group = self.group
        if self.sub_group:
            f_sub_group = self.sub_group
        available_items = get_available_items(f_group, f_sub_group);
        
        contact_response = []
        for item in available_items:
            invoiced_contact_list = get_invoiced_contact_whatsapp(item.item_code)
            for contact in invoiced_contact_list:
                contact_response.append({
                    "item_code": item.item_code,
                    "item_name":item.item_name,
                    "warehouse": item.warehouse,
                    "actual_qty": item.actual_qty,
                    "reserved_qty": item.reserved_qty,
                    "rem_qty": item.rem_qty,
                    "group": item.group,
                    "sub_group": item.sub_group,
                    "contact_name":contact.contact_name,
                    "whatsapp_number":contact.phone
                })
            
            subgroup_contact_list = get_subgroup_contact_whatsapp(item.item_code)
            for contact in subgroup_contact_list:    
                contact_response.append({
                    "item_code":item.item_code,
                    "item_name":item.item_name,
                    "warehouse":item.warehouse,
                    "actual_qty":item.actual_qty,
                    "reserved_qty":item.reserved_qty,
                    "rem_qty": item.rem_qty,
                    "group":item.group,
                    "sub_group":item.sub_group,
                    "contact_name":contact.contact_name,
                    "whatsapp_number":contact.phone
                })
                
        text_message=""
        i = 0
        template_name = self.template_name
        
        sorted_contact_response = sorted(contact_response, key=lambda x: (x["contact_name"], x["whatsapp_number"], x["warehouse"], x["sub_group"]))
        
        distinct_whatsapp_number = set()
        distinct_warehouse = set()
        distinct_subgroup = set()
        distinct_item = set()
        for index, row in enumerate(sorted_contact_response):
            whatsapp_number = row["whatsapp_number"]
            if whatsapp_number not in distinct_whatsapp_number:
                distinct_whatsapp_number.add(whatsapp_number)
                text_message=""
                distinct_warehouse = set()
                distinct_subgroup = set()
                distinct_item = set()

            contact_name = row["contact_name"]
            warehouse = row["warehouse"]
            sub_group = row["sub_group"]
            group = row["group"]
            item_code = row["item_code"]
            item_name = row["item_name"]
            actual_qty = row["actual_qty"]
            reserved_qty = row["reserved_qty"]
            rem_qty = row["rem_qty"]
            
            if warehouse not in distinct_warehouse:
                distinct_warehouse.add(warehouse)
                distinct_subgroup = set()
                distinct_item = set()
                text_message += f"\\n*_{warehouse}_*\\n"
                
            if sub_group not in distinct_subgroup:
                distinct_subgroup.add(sub_group)
                text_message += f"\\n*{sub_group}*\\n"

            if item_code not in distinct_item:
                distinct_item.add(item_code)
                text_message += f"{item_code}\\n"

            #text_message += f"{item_code}\\n"

            if index < len(sorted_contact_response) - 1:
                next_row = sorted_contact_response[index + 1]
                if next_row['whatsapp_number'] not in distinct_whatsapp_number:
                    i += 1
                    save_whatsapp_api_data(api_key,api_url, template_name, whatsapp_number, contact_name, text_message)
                    #enqueue_send_whatsapp_message(api_key,api_url, template_name, whatsapp_number, contact_name, text_message)
            else:
                i += 1
                save_whatsapp_api_data(api_key,api_url, template_name, whatsapp_number, contact_name, text_message)
                #enqueue_send_whatsapp_message(api_key,api_url, template_name, whatsapp_number, contact_name, text_message)
                
        self.message_count = i
        self.save()


# Generate Image Link To Send Image into Stock Notification
def generate_price_list_image(data):
    try:
        # 1️⃣ Render HTML
        html = frappe.render_template(
            "inventeam_avh_app/inventeam_interakt_whatsapp/doctype/whatsapp_stock_notification/stock_notification.html",
            {"data": data},
        )

        # 2️⃣ Create Folder Path
        folder_path = os.path.join(
            get_site_path(), "public", "files", "customer_price_list"
        )

        # ✅ Create folder if not exists
        os.makedirs(folder_path, exist_ok=True)

        # 3️⃣ Output filename
        filename = f"price_list_image_{frappe.generate_hash(length=8)}.png"
        output_path = os.path.join(folder_path, filename)

        # 4️⃣ wkhtmltoimage command
        command = [
            "wkhtmltoimage",
            "--quality", "80",
            "--width", "1600",
            "--zoom", "2",
            "--disable-smart-width",
            "--enable-local-file-access",
            "-",
            output_path
        ]

        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, stderr = process.communicate(input=html.encode("utf-8"))

        # Optional: check if failed
        if process.returncode != 0:
            frappe.throw(f"Image generation failed: {stderr.decode()}")

        return frappe.utils.get_url(f"/files/customer_price_list/{filename}")

    except Exception as e:
        frappe.log_error("Generate Stock Notification Image", f"Error generating image: {str(e)} \n\n\n Data: {str(data)}")


# Convery Raw Text to Proper Dict Format
def convert_to_structure(text):
    try:
        # ==========================================
        # 🔥 STEP 1: HANDLE BOTH TEXT FORMATS
        # ==========================================
        if "\\n" in text:
            text = text.encode().decode("unicode_escape")

        # Normalize line breaks
        text = text.replace("\r", "")

        result = {}
        current_warehouse = None
        current_group = None

        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # ==============================
            # 🏭 Warehouse *_Warehouse_*
            # ==============================
            if line.startswith("*_") and line.endswith("_*"):
                current_warehouse = line[2:-2].strip()

                if current_warehouse not in result:
                    result[current_warehouse] = {}

                current_group = None
                continue

            # ==============================
            # 📦 Group *Group*
            # ==============================
            elif line.startswith("*") and line.endswith("*") and not line.startswith("*_"):
                if not current_warehouse:
                    continue

                current_group = line.strip("*").strip()

                if current_group not in result[current_warehouse]:
                    result[current_warehouse][current_group] = []

                continue

            # ==============================
            # 📄 Items
            # ==============================
            else:
                if current_warehouse and current_group:
                    if line not in result[current_warehouse][current_group]:
                        result[current_warehouse][current_group].append(line)

        # ==========================================
        # 🔄 FINAL OUTPUT FORMAT
        # ==========================================
        final_data = []

        for warehouse in sorted(result.keys()):
            subgroups = []

            for group in sorted(result[warehouse].keys()):
                subgroups.append({
                    "name": group,
                    "items": sorted(result[warehouse][group])
                })

            final_data.append({
                "warehouse": warehouse,
                "item_subgroups": subgroups
            })

        return final_data

    except Exception as e:
        frappe.log_error(
            "Text Parse Error",
            f"{str(e)}\n\nTEXT:\n{text}"
        )
        return []

# Delete All Stock Notification Images
def delete_all_stock_images():
    folder_path = os.path.join(get_site_path(), "public", "files", "customer_price_list")
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)