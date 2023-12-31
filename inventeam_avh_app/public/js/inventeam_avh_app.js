frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			 frm.add_custom_button(__('Whatsapp'), function() {
				// Custom button action here
				frappe.call({
					method: 'inventeam_avh_app.inventeam_interakt_whatsapp.doctype.whatsapp_messages.api.send_message',
					args: {
						"doc_type": "Sales Invoice",
						"doc_name": frm.doc.name
					},
					callback: function(response) {
						if (response.message) {
							frappe.msgprint('Whatsapp Message Triggered', 'Success', 'green');
						} else {
							frappe.msgprint('Failed to trigger Whatsapp message', 'Error', 'red');
						}
					}
				});
			});
		}
    }
});