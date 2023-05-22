odoo.define('solse_pe_cpe_web.website_sale', function(require){
	'use strict';

	var publicWidget = require('web.public.widget');
	var website_sale = require('website_sale.website_sale');
	var rpc = require('web.rpc');

	publicWidget.registry.WebsiteSale.include({
		events: _.extend({}, publicWidget.registry.WebsiteSale.prototype.events, {
			'change select[name="state_id"]': '_onChangeDepartamento',
			'change select[name="city_id"]': '_onChangeProvincia',
			'change select[name="l10n_pe_district"]': '_onChangeDistrito',
			'change input[name="doc_number"]': '_onChangeDoc_number',
		}),
		init: function () {
			this._super.apply(this, arguments);
			this._changeCountry = _.debounce(this._changeCountry.bind(this), 400);
			this._changeDepartamento = _.debounce(this._changeDepartamento.bind(this), 500);
			this._changeProvincia = _.debounce(this._changeProvincia.bind(this), 600);
		},
		_changeCountry: function () {
			console.log("cambio de pais ")
			let pais = $("#country_id").val();
			console.log(pais)
			if (!$("#country_id").val()) {
				return;
			}
			let div = $("#country_id")[0];
			if(div.options[div.selectedIndex].text == 'Perú'){
				$('.div_provincia').show();
				$('.div_distrito').show();
				this._changeDepartamento();
				this._onChangeProvincia();
			} else {
				$('.div_provincia').hide();
				$('.div_distrito').hide();
			}
			console.log("cambio de paisssssssssssssssssssssssss")
			this._rpc({
				route: "/shop/country_infos/" + $("#country_id").val(),
				params: {
					mode: 'shipping',
				},
			}).then(function (data) {
				console.log(data)
				// placeholder phone_code
				//$("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

				// populate states and display
				var selectStates = $("select[name='state_id']");
				// dont reload state at first loading (done in qweb)
				if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
					if (data.states.length) {
						selectStates.html('');
						_.each(data.states, function (x) {
							var opt = $('<option>').text(x[1])
								.attr('value', x[0])
								.attr('data-code', x[2]);
							selectStates.append(opt);
						});
						selectStates.parent('div').show();
					} else {
						selectStates.val('').parent('div').hide();
					}
					selectStates.data('init', 0);
				} else {
					selectStates.data('init', 0);
				}

				// manage fields order / visibility
				if (data.fields) {
					if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)){
						$(".div_zip").before($(".div_city"));
					} else {
						$(".div_zip").after($(".div_city"));
					}
					var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
					_.each(all_fields, function (field) {
						$(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields)>=0);
					});
				}
			});
		},
		_changeDepartamento: function () {
			let combo = document.getElementById("country_id");
			let pais = combo.options[combo.selectedIndex].text;
			var auto_sel_provincia = false;
			let state_id = $("#state_id").val();
			if (!$("#state_id").val() && pais != 'Perú') {
				return;
			} else if((!state_id || state_id == null) && pais == 'Perú') {
				console.log("+++++++++++++++++++++esteeeeeeeeeeeee")
				console.log($("#state_id").val())
				$("#state_id").val('1160');
				auto_sel_provincia = '1501';
				console.log("finalllllllllllll")
				console.log($("#state_id").val())
				state_id = $("#state_id").val();
			}
			if(state_id == null) {
				console.log("igual 1")
			}
			if(state_id == "null") {
				console.log("igual 2")
			}
			console.log(":::::::::::::::::::::::::::::::::222")
			console.log($("#state_id").val())
			console.log(pais)
			this._rpc({
				route: "/solse/departamento_infos/" + $("#state_id").val(),
				params: {
					mode: 'shipping',
				},
			}).then(function (data) {
				var selectStates = $("select[name='city_id']");
				if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
					if (data.provincias.length) {
						selectStates.html('');
						_.each(data.provincias, function (x) {
							var opt = $('<option>').text(x[1])
								.attr('value', x[0])
								.attr('data-code', x[2]);
							if (auto_sel_provincia == x[2]) {
								opt.attr('selected', 'true')
							}
							selectStates.append(opt);
						});
						selectStates.parent('div').show();
					} else {
						selectStates.val('').parent('div').hide();
					}
					selectStates.data('init', 0);
				} else {
					selectStates.data('init', 0);
				}
			});
		},
		_onChangeDepartamento: function (ev) {
			if (!this.$('.checkout_autoformat').length) {
				return;
			}
			this._changeDepartamento();
			this._onChangeProvincia();
		},
		_changeProvincia: function () {
			var self = this;
			if (!$("#city_id").val()) {
				return;
			}
			let div = $("#city_id")[0];
			$("#city").val(div.options[div.selectedIndex].text);
			this._rpc({
				route: "/solse/provincia_infos/" + $("#city_id").val(),
				params: {
					mode: 'shipping',
				},
			}).then(function (data) {
				var selectStates = $("select[name='l10n_pe_district']");
				if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
					if (data.distritos.length) {
						selectStates.html('');
						_.each(data.distritos, function (x) {
							var opt = $('<option>').text(x[1])
								.attr('value', x[0])
								.attr('data-code', x[2]);
							selectStates.append(opt);
						});
						selectStates.parent('div').show();
						self._onChangeDistrito()
					} else {
						selectStates.val('').parent('div').hide();
					}
					selectStates.data('init', 0);
				} else {
					selectStates.data('init', 0);
				}
			});
		},
		_onChangeProvincia: function (ev) {
			if (!this.$('.checkout_autoformat').length) {
				return;
			}
			this._changeProvincia();
		},
		_onChangeDoc_number: function(ev) {
			let nro_doc = $("input[name='doc_number']").val()
			$("#vat").val(nro_doc);
			this._consultarDatos(nro_doc);
		},
		_onChangeDistrito: function(ev){
			let div = $("#l10n_pe_district")[0];
			let option = div.options[div.selectedIndex]
			$("#zip").val($(option).data('code'));
		},
		_consultarDatos: function(nro_doc) {
			var self = this;
			if (!$("#l10n_latam_identification_type_id").val() || !$("input[name='doc_number']").val()) {
				return;
			}
			let div = $("#l10n_latam_identification_type_id")[0];
			var tipo_doc = '';
			for (let i = 0; i < div.options.length; i ++){
				if(div.options[i].selected){
					tipo_doc = div.options[i].text;
				}
			}
			if(tipo_doc != 'DNI' && tipo_doc !='RUC'){
				return;
			}
			tipo_doc = tipo_doc == "DNI" ? "dni" : tipo_doc == "RUC" ? "ruc" : "";
			if(tipo_doc == "") {
				return;
			}
			this._rpc({
				route: '/solse/buscar/'+nro_doc+'/'+tipo_doc,
				params: {},
			}).then(function (datos) {
				if(tipo_doc=='dni') {
					$("input[name='name']").val(datos['data']['data']['names']);
				} else {
					$("input[name='name']").val(datos['data']['data']['razonSocial']);
				}
			});
		}
	})
});