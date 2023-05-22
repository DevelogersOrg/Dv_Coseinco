odoo.define('solse_pe_cpe_pos.pos_screens', function(require) {
  "use strict";

var models = require('point_of_sale.models');
var PosDB = require('point_of_sale.DB');
var core    = require('web.core');
var rpc = require('web.rpc');
var concurrency = require('web.concurrency');
var QWeb = core.qweb;
var PosModelSuper = models.PosModel;
var PosDBSuper = PosDB;
var OrderSuper = models.Order;
var Mutex = concurrency.Mutex;

var _t      = core._t;

models.load_fields("res.currency", ["singular_name", "plural_name", "fraction_name", "show_fraction"]);
models.load_fields("res.partner", ["state_id", "city_id", "l10n_pe_district", "doc_type", "doc_number", 
	"commercial_name", "legal_name", "is_validate", "state", "condition", "l10n_latam_identification_type_id"]);
models.load_fields("res.company", ["street", "sunat_amount"]);
models.load_fields('pos.config', ['documento_venta_ids']);
models.load_fields('account.tax', ['mostrar_base']);

models.load_models([{
	model: 'l10n_latam.identification.type',
	fields: ["name", "id", "l10n_pe_vat_code"],
	//domain: function(self){return [['country_id.code', '=', 'PE']]},
	loaded: function(self, identifications){
		self.doc_code_by_id = {}
		_.each(identifications, function(doc) {
			self.doc_code_by_id[doc.id] = doc.l10n_pe_vat_code
		})
		self.doc_types = identifications
	},

}])

PosDB = PosDB.extend({
	init: function (options) {
		this.doc_type_sale_by_id = {};
		return PosDBSuper.prototype.init.apply(this, arguments);
	},
	add_doc_type_sale: function (doc_types) {
		if (!doc_types instanceof Array) {
			doc_types = [doc_types];
		}
		for (var i = 0, len = doc_types.length; i < len; i++) {
			this.doc_type_sale_by_id[doc_types[i].id] = doc_types[i];
		}
	},
	get_doc_type_sale_id: function (journal_id) {
		return this.doc_type_sale_by_id[journal_id];
	},
});

models.load_models(
	[{
		model: 'l10n_latam.document.type',
		fields: [],
		domain: function (self) { return [['id', 'in', self.config.documento_venta_ids]]; },
		loaded: function (self, documentos_venta) {
			self.l10n_latam_document_type_ids = documentos_venta;
			self.db.add_doc_type_sale(documentos_venta);
		},
	}]
);

models.PosModel = models.PosModel.extend({
	initialize: function (session, attributes) {
		var res = PosModelSuper.prototype.initialize.apply(this, arguments);
		this.db = new PosDB();
		this.mutex = new Mutex();                 // a local database used to search trough products and categories & store pending orders
		
		this.doc_types = []
		this.partner_states = [
					{'code': 'ACTIVO', 'name':'ACTIVO'},
					{'code': 'BAJA DE OFICIO', 'name':'BAJA DE OFICIO'},
					{'code': 'BAJA PROVISIONAL', 'name':'BAJA PROVISIONAL'},
					{'code': 'SUSPENSION TEMPORAL', 'name':'SUSPENSION TEMPORAL'},
					{'code': 'INHABILITADO-VENT.UN', 'name':'INHABILITADO-VENT.UN'},
					{'code': 'BAJA MULT.INSCR. Y O', 'name':'BAJA MULT.INSCR. Y O'},
					{'code': 'PENDIENTE DE INI. DE', 'name':'PENDIENTE DE INI. DE'},
					{'code': 'OTROS OBLIGADOS', 'name':'OTROS OBLIGADOS'},
					{'code': 'NUM. INTERNO IDENTIF', 'name':'NUM. INTERNO IDENTIF'},
					{'code': 'ANUL.PROVI.-ACTO ILI', 'name':'ANUL.PROVI.-ACTO ILI'},
					{'code': 'ANULACION - ACTO ILI', 'name':'ANULACION - ACTO ILI'},
					{'code': 'BAJA PROV. POR OFICI', 'name':'BAJA PROV. POR OFICI'},
					{'code': 'ANULACION - ERROR SU', 'name':'ANULACION - ERROR SU'},
					];
		this.partner_conditions = [
					{'code': 'HABIDO', 'name':'HABIDO'},
					{'code': 'NO HALLADO', 'name':'NO HALLADO'},
					{'code': 'NO HABIDO', 'name':'NO HABIDO'},
					{'code': 'PENDIENTE', 'name':'PENDIENTE'},
					{'code': 'NO HALLADO SE MUDO D', 'name':'NO HALLADO SE MUDO D'},
					{'code': 'NO HALLADO NO EXISTE', 'name':'NO HALLADO NO EXISTE'},
					{'code': 'NO HALLADO FALLECIO', 'name':'NO HALLADO FALLECIO'},
					{'code': 'NO HALLADO OTROS MOT', 'name':'NO HALLADO OTROS MOT'},
					{'code': 'NO APLICABLE', 'name':'NO APLICABLE'},
					{'code': 'NO HALLADO NRO.PUERT', 'name':'NO HALLADO NRO.PUERT'},
					{'code': 'NO HALLADO CERRADO', 'name':'NO HALLADO CERRADO'},
					{'code': 'POR VERIFICAR', 'name':'POR VERIFICAR'},
					{'code': 'NO HALLADO DESTINATA', 'name':'NO HALLADO DESTINATA'},
					{'code': 'NO HALLADO RECHAZADO', 'name':'NO HALLADO RECHAZADO'},
					{'code': '-', 'name':'NO HABIDO'},
					];
		return res;
	},
	validate_pe_doc: function (doc_type, doc_number) {
		if (!doc_type || !doc_number){
			return false;
		}
		if (doc_number.length==8 && doc_type=='1') {
			return true;
		}
		else if (doc_number.length==11 && doc_type=='6')
		{
			var vat= doc_number;
			var factor = '5432765432';
			var sum = 0;
			var dig_check = false;
			if (vat.length != 11){
				return false;
			}
			try{
				parseInt(vat)
			}
			catch(err){
				return false; 
			}
			
			for (var i = 0; i < factor.length; i++) {
				sum += parseInt(factor[i]) * parseInt(vat[i]);
			 } 

			var subtraction = 11 - (sum % 11);
			if (subtraction == 10){
				dig_check = 0;
			}
			else if (subtraction == 11){
				dig_check = 1;
			}
			else{
				dig_check = subtraction;
			}
			
			if (parseInt(vat[10]) != dig_check){
				return false;
			}
			return true;
		}
		else if (doc_number.length>=3 &&  ['0', '4', '7', 'A'].indexOf(doc_type)!=-1) {
			return true;
		}
		else if (doc_type.length>=2) {
			return true;
		}
		else {
			return false;
		}
	},
	push_and_invoice_order: function (order) {
		var self = this;
		var invoiced = new Promise(function (resolveInvoiced, rejectInvoiced) {
			if(!order.get_client()){
				rejectInvoiced({code:400, message:'Missing Customer', data:{}});
			}
			else {
				var order_id = self.db.add_order(order.export_as_JSON());

				self.flush_mutex.exec(function () {
					var done =  new Promise(function (resolveDone, rejectDone) {
						// envía el pedido al servidor
						// tenemos un tiempo de espera de 30 segundos en este empuje.
						// FIXME: si el servidor tarda más de 30 segundos en aceptar el pedido,
						// el cliente creerá que no se envió correctamente y es muy malo
						// las cosas sucederán ya que se enviará un duplicado la próxima vez
						// por lo que debemos asegurarnos de que el servidor detecte e ignore los pedidos duplicados

						var transfer = self._flush_orders([self.db.get_order(order_id)], {timeout:30000, to_invoice:true});

						transfer.catch(function (error) {
							rejectInvoiced(error);
							rejectDone();
						});

						// on success, get the order id generated by the server
						transfer.then(function(order_server_id){
							// generate the pdf and download it
							if (order_server_id.length) {
								/*self.do_action('point_of_sale.pos_invoice_report',{additional_context:{
									active_ids:order_server_id,
								}}).then(function () {
									resolveInvoiced(order_server_id);
									resolveDone();
								}).guardedCatch(function (error) {
									rejectInvoiced({code:401, message:'Backend Invoice', data:{order: order}});
									rejectDone();
								});*/

								// evitamos descargar el pdf de factura ya que hemos personalizado el ticket del pos
								resolveInvoiced(order_server_id);
							} else if (order_server_id.length) {
								resolveInvoiced(order_server_id);
								resolveDone();
							} else {
								// The order has been pushed separately in batch when
								// the connection came back.
								// The user has to go to the backend to print the invoice
								rejectInvoiced({code:401, message:'Backend Invoice', data:{order: order}});
								rejectDone();
							}
						});
						return done;
					});
				});
			}
		});

		return invoiced;
	},
});

models.Order = models.Order.extend({
	initialize: function (attributes, options) {
		var res = OrderSuper.prototype.initialize.apply(this, arguments);
		this.number = false;
		this.tipo_doc_venta_id = false;
		this.invoice_sequence_number = 0;
		this.sequence_set = false;
		this.date_invoice = false;
		this.pe_invoice_date = false;
		return res;
	},
	check_pe_journal: function () {
		var client = this.get_client();
		var doc_type=client ? client.doc_type : false;
		var tipo_doc_venta_id = this.get_doc_type_sale();

		/*if (!journal_id && this.pos.config.pe_auto_journal_select){
			if (doc_type == '6'){
				if (this.pos.config.pe_invoice_journal_id) {
					this.set_doc_type_sale(this.pos.config.pe_invoice_journal_id[0]);                    
				}
			}
			else {
				if (this.pos.config.pe_voucher_journal_id) {
					this.set_doc_type_sale(this.pos.config.pe_voucher_journal_id[0]);                       
				}
			}
		}*/

		var journal_type = this.get_cpe_type();
		if(!journal_type){
			return [false, 'Seleccione un diario valido'];
		}
		if(journal_type == '01' && doc_type != '6') {
			return [false, 'El tipo de documento del cliente no es valido para facturas'];
		} else if(journal_type == '03' && doc_type == '6') {
			return [false, 'El tipo de documento del cliente no es valido para boletas'];
		}
		return  [true, 'OK'];
	},
	get_cpe_type: function () {
		var tipo_doc_venta_id=this.get_doc_type_sale();
		if (!tipo_doc_venta_id){
			return false;
		}
		var doc_type_sale = this.pos.db.get_doc_type_sale_id(tipo_doc_venta_id);
		return doc_type_sale ? doc_type_sale.code : false;
	},
	es_cpe: function() {
		let tipo_doc_venta = this.get_cpe_type()
		if(tipo_doc_venta) {
			return true;
		}
		return false;
	},
	es_un_cpe: function() {
		var tipo_doc_venta = this.get_doc_type_sale();
		if (!tipo_doc_venta){
			return false;
		}
		var doc_type_sale = this.pos.db.get_doc_type_sale_id(tipo_doc_venta);
		return doc_type_sale ? doc_type_sale.is_cpe : false;
	},
	get_cpe_qr: function(){
		var res=[]
		res.push(this.pos.company.vat || '');
		res.push(this.get_cpe_type() || ' ');
		res.push(this.get_number() || ' ');
		res.push(this.get_total_tax() || 0.0);
		res.push(this.get_total_with_tax() || 0.0);
		res.push(moment(new Date().getTime()).format('YYYY-MM-DD'));
		res.push(this.get_doc_type() || '-');
		res.push(this.get_doc_number() || '-');
		var qr_string=res.join('|');
		return qr_string;
	},
	set_doc_type_sale: function (tipo_doc_venta_id) {
		this.assert_editable();
		this.tipo_doc_venta_id = tipo_doc_venta_id;
	},
	get_doc_type_sale: function () {
		return this.tipo_doc_venta_id;
	},
	/*assert_editable: function() {
		if (this.finalized) {
			throw new Error('Finalized Order cannot be modified');
		}
	},*/
	export_as_JSON: function () {
		var res = OrderSuper.prototype.export_as_JSON.apply(this, arguments);
		res['l10n_latam_document_type_id'] = this.tipo_doc_venta_id;
		res['number'] = this.number;
		res['date_invoice'] = moment(new Date().getTime()).format('YYYY/MM/DD');
		res['pe_invoice_date']= this.pe_invoice_date;
		return res;
	},
	export_for_printing: function(){
		var res = OrderSuper.prototype.export_for_printing.apply(this, arguments);
		var self = this;
		var qr_string = self.get_cpe_qr();
		var qrcodesingle = new QRCode(false, {width : 128, height : 128, correctLevel : QRCode.CorrectLevel.Q});
		qrcodesingle.makeCode(qr_string);
		let qrdibujo = qrcodesingle.getDrawing();
		res['sunat_qr_code'] = qrdibujo._canvas_base64;
		return res;
	},
	set_number: function (number) {
		//this.assert_editable();
		this.number = number;
	},
	get_number: function () {
		return this.number;
	},
	get_doc_type: function() {
		var client = this.get_client();
		var doc_type=client ? client.doc_type : "";
		return doc_type;
	},
	get_doc_number: function() {
		var client = this.get_client();
		var doc_number=client ? client.doc_number : "";
		return doc_number;
	},
	get_amount_text: function() {
		return numeroALetras(this.get_total_with_tax(), {
										  plural: this.pos.currency.plural_name,
										  singular: this.pos.currency.singular_name,
										  centPlural: this.pos.currency.show_fraction ? this.pos.currency.sfraction_name: "",
										  centSingular: this.pos.currency.show_fraction ? this.pos.currency.sfraction_name: ""
										})
	},
	get_tax_details: function(){
		var details = {};
		var fulldetails = [];

		var bases = {}

		this.orderlines.each(function(line){
			var ldetails = line.get_tax_details();
			for(var id in ldetails){
				if(ldetails.hasOwnProperty(id)){
					details[id] = (details[id] || 0) + ldetails[id];
					bases[id] = line.price;
				}
			}
		});

		for(var id in details){
			if(details.hasOwnProperty(id)){
				let impuesto = this.pos.taxes_by_id[id]
				let monto = details[id];
				if(impuesto.mostrar_base) {
					monto = bases[id]
				}
				fulldetails.push({amount: monto, tax: impuesto, name: impuesto.name});
			}
		}

		return fulldetails;
	},
});


});