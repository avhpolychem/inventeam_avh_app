# Copyright (c) 2024, Inventeam Solutions Pvt Ltd and contributors
# For license information, please see license.txt

# import frappe
import frappe
import json
from frappe.integrations.utils import make_post_request
from datetime import timedelta, date
from frappe.model.document import Document

class EmailOutstandingNotification(Document):
	def after_insert(self):

		customer = self.customer
		contact = self.contact
		duedate_next10days = date.today() + timedelta(days=10)

		distinct_email_id = set()
		
		message_body_head = f"""<table style="font-family:Calibri;width:627px;border-collapse:collapse;color:rgb(96,96,96);border:thin solid rgb(229,228,226);background-color:rgb(144,144,144);font-size:0.75em">
                            <thead>
                                <tr>
                                    <td colspan="8" align="center" style="color:rgb(239,239,239);font-size:1.5em;vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)"><b>AVH Polychem Private Limited</b></td>
                                </tr>
                                <tr>
                                    <td colspan="8" bgcolor="White" valign="middle" style="vertical-align:middle;background-color:white;padding:0.6em">Dear Sir/ Madam,<br><br>Greetings of the Day!<br><br>We would like to bring it to your immediate attention following invoices getting due in next 10 days and / or invoices already overdue as on today.<br><br>You are requested to make necessary arrangements to pay these invoices as per the due dates mentioned in the table below.<br><br></td>
                                </tr>
								<tr>
                                    <td colspan="8" align="center" style="color:rgb(239,239,239);font-size:1.5em;vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)"><b>@customer@</b></td>
                                </tr>
                                <tr>
                                 <th bgcolor="#909090" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Bill No</th>
                                 <th bgcolor="#909090" align="center" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Bill Date</th>
								 <th bgcolor="#909090" align="center" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Pmt.Term</th>
                                 <th bgcolor="#909090" align="center" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Due Date</th>
                                 <th bgcolor="#909090" align="center" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Amount (Rs.)</th>
								 <th bgcolor="#909090" align="center" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Already Due</th>
								 <th bgcolor="#909090" align="center" style="color:rgb(239,239,239);padding:0.5em;border:thin solid rgb(229,228,226)">Due Upto<br/>{duedate_next10days.strftime("%d-%m-%Y")}</th>
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
									<td colspan="5" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">57500000549220</td>
								</tr>
								<tr bgcolor="#efefef" style="border-bottom:1px solid rgb(64,64,64);background-color:rgb(250,250,250)">
									<td colspan="3" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)"><b>IFSC Code:</b></td>
									<td colspan="5" valign="middle" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">HDFC0004685</td>
								</tr>
								<tr bgcolor="#fafafa" style="border-bottom:1px solid rgb(64,64,64);background-color:rgb(239,239,239)">
									<td colspan="8" bgcolor="White" valign="middle" style="vertical-align:middle;border:thin solid rgb(229,228,226);background-color:white;padding:0.6em">If you have any queries please contact concerned person in AVH Polychem Private Limited<br><br>Kind Regards,<br>Sonal Mehta<br>AVH Polychem Pvt Ltd<br>Mobile : +91 8154014626 | Web: <a href="www.avh.co.in">www.avh.co.in</a> | Email: <a href="mailto:sonal@avh.co.in" target="_blank">sonal@avh.co.in</a></td>
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

		query = f"""SELECT customer,contact_person,`tabContact Email`.email_id,posting_date,`tabSales Invoice`.NAME AS invoice_no,
					net_total,outstanding_amount,due_date,DATEDIFF(CURDATE(),due_date) AS Overdue_Days,`tabSales Invoice`.payment_terms_template
					FROM `tabSales Invoice`
					Join `tabContact Email` on `tabContact Email`.parent = `tabSales Invoice`.contact_person 
					AND `tabContact Email`.custom_is_outstanding_notification_email = 1
					WHERE outstanding_amount > 0 AND DATEDIFF(CURDATE(),due_date) > 0 """
					
		
		if customer:
			query = query + """ And `tabSales Invoice`.customer={customer} """

		if contact:
			query = query + """ And `tabSales Invoice`.contact_person={contact} """

		query = query + """Order BY customer,contact_email,due_date"""

		sql_data = frappe.db.sql(query, as_dict=True)
		i = 0
		cuatomername=''
		for row in sql_data:
			already_due_amount = 0
			outstanding_amount = 0
			email_id = row.email_id
			if email_id not in distinct_email_id:
				distinct_email_id.add(email_id)
				i += 1
				if message_body_row != "<tbody>":
					message_body_row = message_body_row + """</tbody>"""
					message_body = message_body_head + message_body_row + message_body_footer
					message_body = message_body.replace('@customer@',cuatomername)
					frappe.enqueue(
						method=frappe.sendmail,
						queue='short',
						job_name='Outstanding Notification',
						recipients= recipients,
						subject= "Overdue Payment Pending",
						message= message_body
					)
				recipients = email_id
				cuatomername = row.customer
				message_body_row = """<tbody>"""    
				
				
			if row.Overdue_Days < 0:
				already_due_amount = row.outstanding_amount
			else:
				outstanding_amount = row.outstanding_amount

			message_body_row = message_body_row + f"""<tr bgcolor="#efefef" style="background-color:rgb(250,250,250)">
													<td style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{row.invoice_no}</td>
													<td align="center" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{row.posting_date.strftime("%d-%m-%Y")}</td>
													<td align="center" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{row.payment_terms_template}</td>
													<td align="center" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{row.due_date.strftime("%d-%m-%Y")}</td>
													<td align="right" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{frappe.utils.fmt_money(row.net_total,currency='INR')}</td>
													<td align="right" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{frappe.utils.fmt_money(outstanding_amount,currency='INR')}</td>
													<td align="right" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{frappe.utils.fmt_money(already_due_amount,currency='INR')}</td>
													<td align="center" style="vertical-align:middle;padding:0.5em;border:thin solid rgb(229,228,226)">{row.Overdue_Days}</td>
													</tr>"""
				
			
		if message_body_row != "<tbody>":
			message_body_row = message_body_row + """</tbody>"""
			message_body = message_body_head + message_body_row + message_body_footer
			message_body = message_body.replace('@customer@',cuatomername)
			#print(message_body)
			frappe.enqueue(
				method=frappe.sendmail,
				queue='short',
				job_name='Outstanding Notification',
				recipients= recipients,
				subject= "Overdue Payment Pending",
				message= message_body
			)

		self.message_count = i
		self.save()