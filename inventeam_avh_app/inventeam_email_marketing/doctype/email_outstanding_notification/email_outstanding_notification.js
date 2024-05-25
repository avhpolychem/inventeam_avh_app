// Copyright (c) 2024, Inventeam Solutions Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Email Outstanding Notification', {
	refresh: function(frm) {
		frm.set_query("contact", function(doc, cdt, cdn){
            let d = locals[cdt][cdn];
            return {
                "filters": [
                    ["Dynamic Link", "link_doctype", "=", 'Customer' ],
					["Dynamic Link", "link_name", "=", d.customer ],
                ]
            };
        });
	},
	/*contact: function(frm) {
		frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Contact Email',
                fieldname: 'email_id',
				filters: {
					'custom_is_outstanding_notification_email': 1,
					'contact': frm.doc.contact
				}
            },
            callback: function(response) {
				frm.set_value('email', response.message.email);
            }
        });
	}*/
});
