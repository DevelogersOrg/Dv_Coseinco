odoo.define('solse_pe_cpe_pos.PaymentScreen', function(require) {
	'use strict';

	const PaymentScreen = require('point_of_sale.PaymentScreen');
	const Registries = require('point_of_sale.Registries');
	const session = require('web.session');
	const core = require('web.core');
	const rpc = require('web.rpc');
	const _t = core._t;
	const QWeb = core.qweb;

	const PaymentScreenCPE = PaymentScreen =>
		class extends PaymentScreen {
			async validate_journal_invoice() {
				var self = this;
				var order = this.env.pos.get_order();
				var doc_type = order.get_doc_type();
				var doc_number = order.get_doc_number();
				var client = order.get_client();
				let val_diario = order.check_pe_journal(doc_type, doc_number);
				if(!val_diario[0]){
					self.showPopup('ErrorTracebackPopup',{
						  'title': _t('Error en el diario'),
						  'body':  val_diario[1],
					});
					return true;
				}
				var res = false;
				var is_validate = this.env.pos.validate_pe_doc(doc_type, doc_number);
				var cpe_type = order.get_cpe_type();
				var err_lines = false;
				order.orderlines.each(_.bind( function(item) {
					if ((item.get_quantity() <= 0 || item.get_unit_price() <= 0) && !err_lines) {
						return true;    
					}
					
				}, this));
				if (err_lines){
					self.showPopup('ErrorTracebackPopup',{
								  'title': _t('Error en lineas de Pedido'),
								  'body':  _t('La cantidad o el precio unitario del producto debe ser mayor que 0 '
									),
							});
					res = true;
				}
				if(!client){
					self.showPopup('ErrorTracebackPopup',{
								  'title': _t('Error en cliente'),
								  'body':  _t('El cliente es necesario'
									),
							});
					res = true;
				}
				if (self.env.pos.company.sunat_amount< order.get_total_with_tax() && !doc_type && !doc_number){
					const { confirmed } = await self.showPopup('ConfirmPopup',{
								'title': _t('An anonymous order cannot be invoiced'),
								'body': _t('Debe seleccionar un cliente con RUC ó DNI válido antes de poder facturar su pedido.'),
					});
					/*if (confirmed) {
						self.showScreen('ClientListScreen');
					}*/
					res = true;
				}

				if ( ['1', '6'].indexOf(doc_type)!=-1 && !is_validate){
					const { confirmed } = await self.showPopup('ConfirmPopup',{
								title: _t('Please select the Customer'),
								body: _t('Debe seleccionar un cliente con RUC ó DNI válido antes de poder facturar su pedido.'),
					});
					/*if (confirmed) {
						self.showScreen('ClientListScreen');
					}*/
					res = true;
				}
				/*if ( ['01', '03'].indexOf(cpe_type)==-1){
				   self.showPopup('ErrorTracebackPopup','No se puede emitir ese tipo de bono. Configura bien tu diario');
					res = true;
				}*/
				if (cpe_type=='01' && doc_type!='6') {
					const { confirmed } = await self.showPopup('ConfirmPopup',{
								'title': _t('Please select the Customer'),
								'body': _t('Debe seleccionar un cliente con RUC antes de poder facturar su pedido.'),
					});
					/*if (confirmed) {
						self.showScreen('ClientListScreen');
					}*/
					res = true;
				}
				if (cpe_type=='03' && doc_type=='6') {
					const { confirmed } = await self.showPopup('ConfirmPopup',{
								'title': _t('Please select the Customer'),
								'body': _t('Debe seleccionar un cliente con DNI antes de poder facturar su pedido.'),
					});
					/*if (confirmed) {
						self.showScreen('ClientListScreen');
					}*/
					res = true;
				}
				order.pe_invoice_date = moment(new Date().getTime()).format('YYYY-MM-DD HH:mm:ss');
				return res;
				
			}
			async _onNewOrder(newOrder){
				super._onNewOrder(newOrder);
				var self = this;
				var sale_journals = this.render_sale_journals();
				//$('.payment-buttons').html('');
				$('.js_invoice').css({'display': 'none'});
				sale_journals.appendTo($('.payment-buttons'));
				$('.js_sale_journal').click(function () {
					self.click_sale_journals($(this).data('id'));
				});
			}
			render_sale_journals() {
				var self = this;
				var sale_journals = $(QWeb.render('SaleInvoiceJournal', { widget: this.env }));
				return sale_journals;
			}
			click_sale_journals(doc_type_sale_id) {
				var order = this.env.pos.get_order();
				$('.js_invoice').click();
				if (order.get_doc_type_sale() != doc_type_sale_id) {
					order.set_doc_type_sale(doc_type_sale_id);
					$('.js_sale_journal').removeClass('highlight');
					$('div[data-id="' + doc_type_sale_id + '"]').addClass('highlight');
				} else {
					order.set_doc_type_sale(false);
					$('.js_sale_journal').removeClass('highlight');
				}
			}
			async _isOrderValid(isForceValidate) {
				var res = super._isOrderValid(isForceValidate);
				if (!res) {
					return res;
				}
				var order = this.env.pos.get_order();
				var doc_type = order.get_cpe_type();
				if(doc_type) {
					if (await this.validate_journal_invoice()) {
						return false;
					}
				}
				return res;
			}
			async validateOrder(isForceValidate) {
				if(this.env.pos.config.cash_rounding) {
					if(!this.env.pos.get_order().check_paymentlines_rounding()) {
						this.showPopup('ErrorPopup', {
							title: this.env._t('Rounding error in payment lines'),
							body: this.env._t("The amount of your payment lines must be rounded to validate the transaction."),
						});
						return;
					}
				}
				if (await this._isOrderValid(isForceValidate)) {
					// remove pending payments before finalizing the validation
					for (let line of this.paymentLines) {
						if (!line.is_done()) this.currentOrder.remove_paymentline(line);
					}
					await this._finalizeValidation();
				}
			}
			
			validarSerieOffline() {
				let serie = "";
				//serie = "F002-545454";
				return serie;
			}

			async _finalizeValidation() {

				if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
					this.env.pos.proxy.printer.open_cashbox();
				}

				this.currentOrder.initialize_validation_date();
				this.currentOrder.finalized = true;
				var order = this.env.pos.get_order();
				var doc_type = order.get_cpe_type();
				let syncedOrderBackendIds = [];
				var self = this;
				var ejecutar = true;
				try {
					if (this.currentOrder.is_to_invoice() || doc_type) {
						syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
							this.currentOrder
						);
						rpc.query({
							model: 'pos.order',
							method: 'generar_enviar_xml_cpe',
							args: [{"pos_order_id": syncedOrderBackendIds}],
						}).then(function (data) {
							if(data.length > 0) {
								order.set_number(data[0]['serie']);
							} else {
								console.log('no obtuvo respuestaaaaaaaa')
							}
							ejecutar = false;
							self.showScreen(self.nextScreen);
						});
					} else {
						syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
						self.showScreen(self.nextScreen);
						
					}
				} catch (error) {
					if (error.code == 700)
						this.error = true;
					if (error instanceof Error) {
						throw error;
					} else {
						await this._handlePushOrderError(error);
						let correlativo = this.validarSerieOffline()
						if(correlativo) {
							this.currentOrder.number = correlativo;
							this.env.pos.push_single_order(this.currentOrder);
						} else {
							this.showPopup('OfflineErrorPopup', {
								title: this.env._t('Connection Error'),
								body: "No se pudo obtener la serie, esta sera generada automáticamente una vez el pedido se sincronice. Vuelva a imprimir la factura una vez el pedido este sincronizado.",
							});
						}
						this.showScreen(this.nextScreen);
					}
				}
				if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
					const result = await this._postPushOrderResolve(
						this.currentOrder,
						syncedOrderBackendIds
					);
					if (!result) {
						await this.showPopup('ErrorPopup', {
							title: 'Error: no internet connection.',
							body: error,
						});

						let correlativo = this.validarSerieOffline()
						if(correlativo) {
							this.currentOrder.number = correlativo;
							this.env.pos.push_single_order(this.currentOrder);
						} else {
							this.showPopup('OfflineErrorPopup', {
								title: this.env._t('Connection Error'),
								body: "No se pudo obtener la serie, esta sera generada automáticamente una vez el pedido se sincronice. Vuelva a imprimir la factura una vez el pedido este sincronizado.",
							});
						}
					}
				}
				/*if (ejecutar == true) {
					this.showScreen(this.nextScreen);
				}*/
				

				// If we succeeded in syncing the current order, and
				// there are still other orders that are left unsynced,
				// we ask the user if he is willing to wait and sync them.
				if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
					const { confirmed } = await this.showPopup('ConfirmPopup', {
						title: this.env._t('Remaining unsynced orders'),
						body: this.env._t(
							'There are unsynced orders. Do you want to sync these orders?'
						),
					});
					if (confirmed) {
						// NOTE: Not yet sure if this should be awaited or not.
						// If awaited, some operations like changing screen
						// might not work.
						this.env.pos.push_orders();
					}
				}
			}
		};

	Registries.Component.extend(PaymentScreen, PaymentScreenCPE);

	return PaymentScreen;
});
