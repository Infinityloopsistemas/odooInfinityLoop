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
import urllib


__author__ = 'julian'
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from openerp import models, fields, api ,osv
from openerp import tools
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from dateutil import rrule, parser
import datetime
import googlemaps
import math




class HrIncentiveTemplate(models.Model):
    """Asignamos por empleado plan de incentivo asi como las reglas para el plan"""
    _name = 'hr.incentive.template'
    _description='Configuracion plantillas de incentivos'
    _sql_constraints = [
        ('hr_incentive_template_uniq',
         'UNIQUE (employee_id, active)',
         'Solo puede existir una plantilla ACTVA por empleado a la vez!')]

    name           = fields.Char(string="Plantilla")
    employee_id    = fields.Many2one("hr.employee")
    active         = fields.Boolean("Activo")
    hrincetemp_ids = fields.One2many('hr.incentive.template.rules','hrincetemp_id')



class HrIncentivesRules(models.Model):
    _name = 'hr.incentive.template.rules'
    _description='Reglas de configuracion de incentivos'

    name          = fields.Char(string="Descripcion")
    hrincetemp_id = fields.Many2one('hr.incentive.template')
    typetask      = fields.Selection([('R', "Remota"), ('P', "Presencial")], default="R")
    rule          = fields.Char(string="Regla", default="lambda x: 1 if x <=50 else 0")
    incentive     = fields.Float( digits=(10,3), string="Incentivo", help="Valor del incentivo, dependiedo del tipo")
    typdist       = fields.Selection([('A', "Absoluto"), ('P', "%")], default="A", help="Tipo de reparto del incentivo")



class HrIncentiveHistory(models.Model):
    _name = 'hr.incentive.history'
    _description = 'Historico de incentivos'

    @api.one
    def _calc_total_tasks(self):
        numtareas=0
        for taskincen in self.taskincentive_ids:
            numtareas += 1

        self.total_tasks= numtareas

    @api.one
    def _calc_coste_incentive(self):
        total_incentivo = 0
        for taskincen in self.taskincentive_ids:
            total_incentivo += taskincen.commission
        self.total_incentive = total_incentivo



    name               = fields.Char(string="Descripcion")
    hrtraincentive_id  = fields.Many2one("hr.incentive.template")
    employee_id        = fields.Many2one("hr.employee" )
    period_id          = fields.Many2one("account.period")
    date_calculate     = fields.Char(string="Date Calculate")
    total_tasks        = fields.Float( digits=(10,3), compute="_calc_total_tasks")
    total_incentive    = fields.Float( digits=(10,3), compute="_calc_coste_incentive")
    taskincentive_ids  = fields.One2many('hr.task.incentive.line','taskincentive_id')
    state              = fields.Selection([('open', 'Sin Calcular'), ('calculate', 'Calculado')],
                                  string='Status', readonly=True, required=True,default="open",
                                  track_visibility='always', copy=False)

    @api.constrains("employee_id")
    def constrains_employee(self):
        for row in self:
            hr_tra_confg = self.env["hr.incentive.template"].search([('employee_id','=',row.employee_id.id)], limit=1)
            if not hr_tra_confg.id:
                raise ValidationError("Cree una plantilla de incentivos para este empleado")
            self.hrtraincentive_id = hr_tra_confg.id


    @api.one
    def action_draft(self):
        self.state = "open"
        for datail in self.taskincentive_ids:
            datail.unlink()


    @api.one
    def action_calculate_incentive(self):

        obj_project_task    = self.env["project.task"]
        obj_employee        = self.env["hr.employee"]
        obj_taskinceline    = self.env["hr.task.incentive.line"]
        self.date_calculate = fields.Date.today()
        self.state          = "calculate"
        employee_ids        = [self.employee_id]


        for employee_id in employee_ids:
            # Intervalo de dias 1 al 25
            start_date = fields.Date.from_string(self.period_id.date_start)
            stop_date  = fields.Date.from_string(self.period_id.date_stop)
            adates= list(rrule.rrule(rrule.DAILY,
                         dtstart=parser.parse(fields.Date.to_string(start_date)),
                         until=parser.parse(fields.Date.to_string(stop_date) )))


            for row_date in adates:
                coordenadas = []
                partners = []
                search_date=  fields.Date.to_string(row_date)

                #Filtrado de tares Remotas o Presenciales y ademas que tenga fecha de finalizacion
                project_tasks_ids = obj_project_task.search([ ('typetask','!=',"O"),('date_end','!=',False),('user_id', '=', employee_id.user_id.id),('date_deadline','>=',search_date), \
                                                             ('date_deadline','<=',search_date),('project_id','!=',False)])

                for row_task in project_tasks_ids:

                     task_exist = obj_taskinceline.search([('task_id','=',row_task.id)])
                     if not task_exist:
                         idpartner  = row_task.project_id.partner_id.id
                         obanalytic = row_task.project_id.analytic_account_id
                         if obanalytic:
                            price     =  obanalytic.amount_max
                            if price !=0:
                                self.taskincentive_ids.create({'taskincentive_id': self.id, 'name': row_task.project_id.name, 'date': row_task.date_end,'task_id': row_task.id, 'price_contract': price })


class HrIncentiveLine(models.Model):
    _name = 'hr.task.incentive.line'
    _description = 'Incentivos por tareas'


    @api.one
    def _calc_incentive(self):
        obj_template_ids = self.taskincentive_id.hrtraincentive_id.hrincetemp_ids
        print obj_template_ids
        for objrule in obj_template_ids:

            if objrule.rule:
                if self.task_id.typetask == objrule.typetask:
                    distribucion = objrule.typdist
                    lamfunc =eval(objrule.rule)
                    asignada = lamfunc(float(self.price_contract))
                    if asignada ==1 :
                        if distribucion=="A":
                            self.commission = objrule.incentive
                        if distribucion =="P":
                            self.commission = objrule.incentive*self.price_contract/100



    taskincentive_id   = fields.Many2one('hr.incentive.history')
    name               = fields.Char(string="Tarea")
    date               = fields.Date(string="Fecha")
    task_id            = fields.Many2one('project.task')
    price_contract     = fields.Float(digits=(10,3), string="Price Contrato")
    commission         = fields.Float(digits=(10,3), string="Incentive",compute='_calc_incentive')
















