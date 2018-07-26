# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 InfinityLoop Sistemas S.L (<http://www.infinityloop.es>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, _

from openerp import api


class siva_project(models.Model):
    _inherit = 'project.project'

    employee_id      = fields.Many2one("hr.employee", string="Empleado", domain=[('category_ids.name', 'in', ['AUDITOR'])], help="Solo empleados con categoria de AUDITOR")
    user_siva        = fields.Char("Usuario SIVA")
    pass_siva        = fields.Char("Clave SIVA")
    company_siva_id  = fields.Many2one("siva.company",string="Local SIVA" )
    elementos_ids    = fields.One2many('siva.project.elements','project_id')




    @api.onchange('user_siva')
    def onchange_partner(self):
        res = {}
        idsrow = []
        if not res.get('domain', {}):
            if len(idsrow) != 0:
                res['domain'] = {'company_siva_id': [('partner_id', 'in', self.partner_id.parent_id.id)]}

        return res



class siva_project_elements(models.Model):
     _name ='siva.project.elements'
     _description = "Elementos que conforman la instalacion"

     name              = fields.Char("Ubicacion")
     project_id        = fields.Many2one('project.project')
     date_install      = fields.Date("F.Instala")
     date_baja         = fields.Date("F.Baja")
     product_id        = fields.Many2one('product.product',"Elemento")
     serial            = fields.Char("Serial")
     cantidad          = fields.Integer("Cantidad")




