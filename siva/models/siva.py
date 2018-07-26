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


class SivaCompany(models.Model):
    _name        = 'siva.company'
    _description = 'Relacion de Company en Siva con respartners en Odoo Giva'

    name            = fields.Char("Nombre empresa en SIVA")
    siva_company_id = fields.Integer()
    partner_id      = fields.Many2one('res.partner', string="Partner en GIVA")
    fechaultima     = fields.Date("F.Ultima Actualizacion")

