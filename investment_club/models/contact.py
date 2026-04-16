from odoo import api, fields, models

class Contact(models.Model):
    _inherit = "res.partner"


    code = fields.Char(string="Code")



