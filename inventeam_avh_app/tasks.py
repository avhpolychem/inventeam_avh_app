import frappe

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
    
def weekly():
    pass