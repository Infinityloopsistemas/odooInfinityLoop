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

from openerp import models, fields, _,api
import json
import urllib2




class siva_partner(models.Model):
    _inherit = 'res.partner'

    dbname_siva        = fields.Char("Base Datos SIVA")
    dominio_siva       = fields.Char("Dominio SIVA")
    activo_siva        = fields.Boolean("Activo en SIVA")
    partner_siva_ids   = fields.One2many('siva.company','partner_id')
    fechaultima        = fields.Date("F.Ultima Actualizacion")



    @api.multi
    def action_button_getcompanysiva(self):
        db              =  self.dbname_siva
        user            = 'admin'
        password        = 'fractal'
        url_certificate = "https://%s.%s/web/session/authenticate" % (self.dbname_siva,self.dominio_siva)
        url_work        = "https://%s.%s/web/dataset/call_kw" % (self.dbname_siva, self.dominio_siva)

        if self.dbname_siva and self.dominio_siva:
            request = urllib2.Request(
                 url_certificate,
                json.dumps({
                    'jsonrpc': '2.0',
                    'params': {
                        'db': db,
                        'login': user,
                        'password': password,
                    },
                }),
                {'Content-type': 'application/json'})

            result = urllib2.urlopen(request).read()
            result = json.loads(result)
            session_id = result['result']['session_id']

            request = urllib2.Request(
                url_work,
                json.dumps({
                    'jsonrpc': '2.0',
                    'params': {
                        'model': 'res.company',
                        'method': 'search_read',
                        'args': [[],['name'],
            ],
            'kwargs': {'context': {'lang': 'es_ES'}},
            },
            }),
            {
                'X-Openerp-Session-Id': session_id,
                'Content-type': 'application/json',
            })
            result = urllib2.urlopen(request).read()
            result = json.loads(result)

            objsiva = self.env['siva.company']
            for module in result['result']:
                actuobjsiva= objsiva.search([('partner_id','=',self.id),('siva_company_id','=', module['id'])])
                if actuobjsiva:
                    registro = {'name': module['name'],'fechaultima':fields.Date.today()}
                    actuobjsiva.write(registro)
                else:
                    registro = {'name':  module['name'], 'siva_company_id' : module['id'] , 'partner_id': self.id, 'fechaultima':fields.Date.today()}
                    objsiva.create(registro)
            vals={}
            vals['fechaultima']= fields.Date.today()
            self.write(vals)
