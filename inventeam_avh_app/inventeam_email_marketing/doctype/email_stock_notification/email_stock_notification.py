# Copyright (c) 2023, Inventeam Solutions Pvt Ltd and contributors
# For license information, please see license.txt

# import frappe
import frappe
import json
from frappe.integrations.utils import make_post_request
from datetime import datetime
from frappe.model.document import Document

def enqueue_send_email(recipients, contact_name, subject, message):
    message_body = f"""Dear {contact_name} ji, 
                    <p>We are pleased to offer the following grades.</p>
                    <br>{message} <br> 
                    <p>If you require any other grade not mentioned above, we shall be able to offer you the same subject to availability.</p>
                    <p>Kindly contact respective sales person for product inquiry.</p>
                    Regards<br> 
                    <b>AVH Polychem Private Limited</b><br>
                    Phone: +91 2246002838 | Web: <a href="www.avh.co.in">avh.co.in</a> | Email: <a href="mailto:sales@avh.co.in" target="_blank">sales@avh.co.in</a>"""
    
    frappe.enqueue(
        method=frappe.sendmail,
        queue='short',
        job_name='Stock Email Notification',
        recipients= recipients,
        subject= subject,
        message= message_body
    )
    #frappe.enqueue(method=frappe.sendmail, queue='short', timeout=300, async=True, email_args)


def get_available_items(sub_group=None):
    min_qty = frappe.db.get_single_value('Custom Stock Setting', 'min_qty')
    cond = ""
    if min_qty:
        cond = " and (bn.actual_qty - bn.reserved_qty) > " + str(min_qty)

    if sub_group:
        cond = cond + " and it.sub_group='" + sub_group + "'"
        
    available_item = frappe.db.sql("""
    select bn.item_code,it.item_name,bn.warehouse,bn.actual_qty,bn.reserved_qty, (bn.actual_qty - bn.reserved_qty) as rem_qty,it.group,it.sub_group from `tabBin` bn inner join `tabItem` it on it.name = bn.item_code where bn.actual_qty > 0  AND bn.warehouse NOT LIKE ('%In Transit%') {cond}
    """.format(cond=cond),as_dict=1)
    return available_item

def get_invoiced_contact_email(item):
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
                ce.email_id
                from
                `tabSales Invoice Item` sii
                left join `tabSales Invoice` si on si.name = sii.parent
                left join `tabCustomer` c on c.name = si.customer
                left join `tabDynamic Link` cdl on cdl.link_name = c.name
                left join `tabContact` cc on cdl.parent = cc.name
                join `tabContact Email` ce on ce.parent = cc.name 
                where
                si.docstatus = 1
                and
                cdl.link_doctype = 'Customer'
                and
                ce.custom_is_offer_email = 1
                and
                sii.item_code in %(l)s group by ce.email_id,sii.item_code
                order by si.name
                """, ({"l":tuple(s_l)}),as_dict = True)
            return data
    return data

def get_subgroup_contact_email(item):
    data = []
    subgrp = frappe.db.get_value("Item",item,"sub_group") 
    if subgrp:
        data = frappe.db.sql("""
            select
            ce.email_id,
            cc.first_name as contact_name
            from
            `tabContact Email` ce
            left join `tabDynamic Link` cdl on ce.parent = cdl.parent
            left join `tabContact` cc on ce.parent = cc.name
            left join `tabContact Sub Group` ccsg on ccsg.parent = cc.name
            where
            ccsg.sub_group = %s
            and
            ce.custom_is_offer_email = 1
            """,(subgrp),as_dict = True)
    return data
    
class EmailStockNotification(Document):
    def after_insert(self):
        f_sub_group = None
        
        if self.sub_group:
            f_sub_group = self.sub_group
        available_items = get_available_items(f_sub_group)
        
        contact_response = []
        for item in available_items:
            invoiced_contact_list = get_invoiced_contact_email(item.item_code)
            for contact in invoiced_contact_list:
                contact_response.append({
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "warehouse": item.warehouse,
                    "actual_qty": item.actual_qty,
                    "reserved_qty": item.reserved_qty,
                    "rem_qty": item.rem_qty,
                    "group": item.group,
                    "sub_group": item.sub_group,
                    "contact_name": contact.contact_name,
                    "email_id": contact.email_id
                })
            
            subgroup_contact_list = get_subgroup_contact_email(item.item_code)
            for contact in subgroup_contact_list:    
                contact_response.append({
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "warehouse": item.warehouse,
                    "actual_qty": item.actual_qty,
                    "reserved_qty": item.reserved_qty,
                    "rem_qty": item.rem_qty,
                    "group": item.group,
                    "sub_group": item.sub_group,
                    "contact_name": contact.contact_name,
                    "email_id": contact.email_id
                })
                
        text_message = ""
        i = 0
        
        sorted_contact_response = sorted(contact_response, key=lambda x: (x["contact_name"], x["email_id"], x["warehouse"], x["sub_group"]))
        
        distinct_email_id = set()
        distinct_warehouse = set()
        distinct_subgroup = set()
        distinct_item = set()
        for index, row in enumerate(sorted_contact_response):
            email_id = row["email_id"]
            if email_id not in distinct_email_id:
                distinct_email_id.add(email_id)
                i += 1
                text_message = ""
                distinct_warehouse = set()
                distinct_subgroup = set()
                distinct_item = set()
            else:
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
                    if len(text_message) > 0:
                        text_message += '</td>'
                        text_message += '</tr>'
                        text_message += '</tbody>'
                        text_message += "</table>"
                        text_message += "<br>"
                    
                    text_message += '<table border="1" cellpadding="1" cellspacing="1" style="color: rgb(34, 34, 34); font-family: Arial, Helvetica, sans-serif; font-size: small; background-color: rgb(255, 255, 255); width: 500px;">'
                    text_message += '<thead>'
                    text_message += '<tr>'
                    text_message += f'<th colspan="2" style="background-color: rgb(204, 204, 204);">{warehouse}</th>'
                    text_message += '</tr>'
                    text_message += '<tr>'
                    text_message += '<th style="width: 50%;">Category</th>'
                    text_message += '<th style="width: 50%;">Products</th>'
                    text_message += '</tr>'
                    text_message += '</thead>'
                    text_message += '<tbody>'

                if sub_group not in distinct_subgroup:
                    if len(distinct_subgroup) == 0:
                        text_message += '</td>'
                        text_message += '</tr>'

                    distinct_subgroup.add(sub_group)
                    distinct_item.add(item_code)
                    
                    text_message += '<tr>'
                    text_message += f'<td style="margin: 0px;vertical-align: top;"><strong>{sub_group}</strong></td>'
                    text_message += f'<td style="margin: 0px;vertical-align: top;">{item_code}'
                elif item_code not in distinct_item:
                    distinct_item.add(item_code)
                    text_message += f'<br/>{item_code}'


                if index < len(sorted_contact_response) - 1:
                    next_row = sorted_contact_response[index + 1]
                    if next_row['email_id'] not in distinct_email_id:
                        text_message += '</td>'
                        text_message += '</tr>'
                        text_message += '</tbody>'
                        text_message += "</table>"
                        enqueue_send_email(email_id, contact_name, 'AVH Polychem Polymers offer', text_message)
                else:
                    text_message += '</tbody>'
                    text_message += "</table>"
                    enqueue_send_email(email_id, contact_name, 'AVH Polychem Polymers offer', text_message)
                
        self.message_count = i
        self.save()
