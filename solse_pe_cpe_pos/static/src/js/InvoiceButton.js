odoo.define('solse_pe_cpe_pos.InvoiceButton', function(require) {
	'use strict';

	const InvoiceButton = require('point_of_sale.InvoiceButton');
	const Registries = require('point_of_sale.Registries');
	const session = require('web.session');
	const core = require('web.core');
	const _t = core._t;
	const QWeb = core.qweb;

	const { useListener } = require('web.custom_hooks');
    const { useContext } = owl.hooks;
    const { isRpcError } = require('point_of_sale.utils');
    const PosComponent = require('point_of_sale.PosComponent');
    const OrderManagementScreen = require('point_of_sale.OrderManagementScreen');
    const OrderFetcher = require('point_of_sale.OrderFetcher');
    const contexts = require('point_of_sale.PosContext');

	const InvoiceButtonCPE = InvoiceButton =>
		class extends InvoiceButton {
			async _invoiceOrder() {
				const order = this.selectedOrder;
				if (!order) return;

				const orderId = order.backendId;

				// Part 0.1. If already invoiced, print the invoice.
				if (this.isAlreadyInvoiced) {
					await this._downloadInvoice(orderId);
					return;
				}

				// Part 0.2. Check if order belongs to an active session.
				// If not, do not allow invoicing.
				if (order.isFromClosedSession) {
					this.showPopup('ErrorPopup', {
						title: this.env._t('Session is closed'),
						body: this.env._t('Cannot invoice order from closed session.'),
					});
					return;
				}

				// Part 1: Handle missing client.
				// Write to pos.order the selected client.
				if (!order.get_client()) {
					const { confirmed: confirmedPopup } = await this.showPopup('ConfirmPopup', {
						title: 'Need customer to invoice',
						body: 'Do you want to open the customer list to select customer?',
					});
					if (!confirmedPopup) return;

					const { confirmed: confirmedTempScreen, payload: newClient } = await this.showTempScreen(
						'ClientListScreen'
					);
					if (!confirmedTempScreen) return;

					await this.rpc({
						model: 'pos.order',
						method: 'write',
						args: [[orderId], { partner_id: newClient.id }],
						kwargs: { context: this.env.session.user_context },
					});
				}

				// Part 2: Invoice the order.
				await this.rpc(
					{
						model: 'pos.order',
						method: 'action_pos_order_invoice',
						args: [orderId],
						kwargs: { context: this.env.session.user_context },
					},
					{
						timeout: 30000,
						shadow: true,
					}
				);

				// Part 3: Download invoice.
				await this._downloadInvoice(orderId);

				// Invalidate the cache then fetch the updated order.
				OrderFetcher.invalidateCache([orderId]);
				await OrderFetcher.fetch();
				this.selectedOrder = OrderFetcher.get(this.selectedOrder.backendId);
			}
		};

	Registries.Component.extend(InvoiceButton, InvoiceButtonCPE);
	return InvoiceButton;
});