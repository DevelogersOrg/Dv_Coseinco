odoo.define('solse_vat_pos_pe.pos_screens', function(require) {
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

models.load_fields("res.partner", ["state_id", "city_id", "l10n_pe_district", "doc_type", "doc_number", 
    "commercial_name", "legal_name", "is_validate", "state", "condition", "l10n_latam_identification_type_id"]);

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

models.PosModel = models.PosModel.extend({
    initialize: function (session, attributes) {
        var res = PosModelSuper.prototype.initialize.apply(this, arguments);
        this.doc_types = [];
        return res;
    }
});


});