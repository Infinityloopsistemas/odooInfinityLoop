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
from dateutil.relativedelta import relativedelta
import datetime
from openerp import api


class ProjectRecurrentWizardTask(models.TransientModel):
    _name = 'project.recurrent.wizard.task'
    _description = "Wizard para la creacion de tareas recurrentes de proyectos"

    name                = fields.Char(string="Denominar Tareas")
    project_ids         = fields.Many2many("project.project",string="Proyectos")
    date_start          = fields.Date(string="F.Inicio")
    date_end            = fields.Date(string="F.Fin")
    recurring_rule_type = fields.Selection([
        ('daily', 'Dia(s)'),
        ('weekly', 'Semana(s)'),
        ('monthly', 'Mes(s)'),
        ('yearly', 'Ano(s)'),
    ], string = "Recurrencia" )
    recurring_interval  = fields.Integer(string='Repetir Cada', help="Repetir todos (Dias/Semanas/Meses/Anos)")
    description         = fields.Text(string="Descripcion")
    categ_ids           = fields.Many2many('project.category', string='Etiquetas')
    manager_id          = fields.Many2one(  'res.users',string='Responsable')
    #stage_id            = fields.Many2one('project.task.type', string='Etapa'  )
    typetask            = fields.Selection([('R', "Remota"), ("P", "Presencial")], string="Tipo Tarea")
    templatework_ids    = fields.One2many('project.recurrent.wizard.work', 'project_work_id',"Works")


    @api.multi
    def action_button_generar(self):
        task_obj      = self.env['project.task']
        task_work_obj = self.env['project.task.work']


        for project in self.project_ids:
            fecha_ini = fields.Date.from_string(self.date_start)
            fecha_fin = fields.Date.from_string(self.date_end)
            next_date = fecha_ini
            interval = self.recurring_interval
            ic=0
            stage = {'name': "%s %s" % (self.name, str(next_date.year))}
            idstage = self.env['project.task.type'].sudo().create(stage)
            while next_date <= fecha_fin:
                if ic>10:
                    ic=0
                else:
                    ic+=1
                if self.recurring_rule_type == 'daily':
                    new_date = next_date + relativedelta(days=+interval)
                elif self.recurring_rule_type == 'weekly':
                    new_date = next_date + relativedelta(weeks=+interval)
                elif self.recurring_rule_type == 'monthly':
                    new_date = next_date + relativedelta(months=+interval)
                else:
                    new_date = next_date + relativedelta(years=+interval)

                if next_date.month+1 > 12:
                    mes= 1
                    ano= next_date.year+1
                else:
                    mes =next_date.month+1
                    ano =next_date.year

                lastdaydate= datetime.date(ano, mes, 1) - datetime.timedelta(days=1)
                initdate    = datetime.date(next_date.year,next_date.month,1)

                nombre    =  str(self.name) + " (%s) MES %s - %s" % (project.name,str(next_date.month).zfill(2) ,str(next_date.year))
                task      = {"date_start": fields.Date.to_string(initdate), "date_end": fields.Date.to_string(new_date), 'project_id' : project.id, 'kanban_state':'normal' , \
                        'categ_ids' : [(6,0, [cat.id for cat in self.categ_ids]) ], 'user_id' : self.manager_id.id, "stage_id" :  idstage.id, 'typetask' : self.typetask , \
                        'date_deadline': fields.Date.to_string(lastdaydate), 'name' : nombre ,'color':ic}


                idtask = task_obj.sudo().create(task)

                for works in self.templatework_ids:
                     work = { 'name' : str(works.name) , 'task_id':idtask.id, 'date': fields.Date.to_string(initdate), 'user_id': self.manager_id.id , 'hours': works.hours_est}
                     task_work_obj.sudo().create(work)

                #Creamos los works de servicios contratados
                for workser in idtask.project_id.workservice_ids:
                    task_work_obj.sudo().create(
                        {'name': workser.name, 'date': idtask.date_start, 'task_id': idtask.id,
                         'user_id': idtask.user_id.id, 'hours': 0.5})



                next_date = new_date


class ProjectRecurrentWizardWork(models.TransientModel):
    _name = 'project.recurrent.wizard.work'

    project_work_id = fields.Many2one('project.recurrent.wizard.task',"Tasks")
    name            =  fields.Char(string="Trabajos")
    hours_est       =  fields.Float(string="Horas Estimadas", default=0.0)

