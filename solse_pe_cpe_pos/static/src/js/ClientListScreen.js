odoo.define('solse_pe_cpe_pos.ClientListScreen', function(require) {
    'use strict';

    const ClientListScreen = require('point_of_sale.ClientListScreen');
    const Registries = require('point_of_sale.Registries');
    const session = require('web.session');
    const core = require('web.core');
    const { useListener } = require('web.custom_hooks');
    const _t = core._t;
    const QWeb = core.qweb;

    const ClientListScreenCPE = ClientListScreen =>
        class extends ClientListScreen {
        	constructor() {
            	super(...arguments);
            	this.departamento = null;
			    this.provincia = null;
			    this.distrito = null;
            }
            
		    editClient(){
		        super.editClient();    
		    }
        };

    Registries.Component.extend(ClientListScreen, ClientListScreenCPE);

    return ClientListScreen;
});
