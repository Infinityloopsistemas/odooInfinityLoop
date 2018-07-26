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


class projectTemplateWork(models.Model):
    _name ='project.template.work'
    _description ="Plantilla de trabajos de tarea asociadas al proyecto"

    name                =  fields.Char("Accion a realizar")
    product_id          =  fields.Many2one('product.product',string="Servicio", domain =[('product_tmpl_id.type','=','service'),('product_tmpl_id.sale_ok','=',True)] ,help="Servicios a realizar")
    recurring_rule_type = fields.Selection([
        ('daily', 'Dia(s)'),
        ('weekly', 'Semana(s)'),
        ('monthly', 'Mes(s)'),
        ('yearly', 'Ano(s)'),
    ], string="Recurrencia")


class projectWorks(models.Model):
    _name ='project.work.service'
    _description="Trabajos de servicios del proyecto"

    name              = fields.Char("Servicio",help="Definicion del servicio a realizar")
    templatework_id   = fields.Many2one('project.template.work',string='Accion a Realizar')
    project_id        = fields.Many2one('project.project')
    date_begin        = fields.Date("F.Aplicacion",help="Fecha a partir que entra en vigencia en las tareas",required=True)
    date_end          = fields.Date("F.Deshabilitar",help="Fecha apartir  se elimina de tareas")

    @api.onchange('date_end')
    def onchange_date(self):
        if self.date_end ==False:
            self.date_begin=None


    @api.model
    @api.returns('self',lambda rec: rec.id)
    def create(self,values):
        faplica    = values.get('date_begin',None)
        project_id = values.get('project_id',None)
        #Tareas del proyecto
        if faplica:
            obj_taskwork = self.env['project.task.work']
            tasks_ids    = self.env['project.task'].search([('typetask','!=','O'),('date_deadline','>=',faplica),('project_id','=',project_id)])
            for task in tasks_ids:
                obj_taskwork.create({'name': values.get('name') , 'date': task.date_start, 'task_id': task.id, 'user_id' : task.user_id.id ,'hours' : 0.5 })

        return super(projectWorks,self).create(values)

    @api.multi
    def write(self,values):
        faplica    = values.get('date_begin', None)
        fdisab     = values.get('date_end',None)
        project_id = self.project_id
        print project_id, fdisab,faplica
        nombre     = values.get('name',self.name)
        if fdisab:
            tasks_ids = self.env['project.task'].search([('typetask', '!=', 'O'), ('date_deadline', '>=', fdisab),('project_id','=',project_id.id)])
            for task in tasks_ids:
                for work in task.work_ids.search([('name','=', nombre),('task_id','=',task.id)]):
                    work.unlink()
        if faplica and nombre:
            #Elimina todas las referencias de los works a partir de la fecha de aplicacion
            #Evitamos duplicidad de works
            tasks_ids = self.env['project.task'].search(
                [('typetask', '!=', 'O'), ('date_deadline', '>=', faplica), ('project_id', '=', project_id.id)])
            for task in tasks_ids:
                for work in task.work_ids.search([('name', '=', nombre), ('task_id', '=', task.id)]):
                    work.unlink()
            #Crea las nuevas referencias a partir de la fecha de aplicacion
            tasks_ids    = self.env['project.task'].search([('typetask', '!=', 'O'), ('date_deadline', '>=', faplica),('project_id','=',project_id.id)])
            for task in tasks_ids:
                print "Crea desde actualizacion"
                task.work_ids.create({'name': nombre ,'date': task.date_start, 'task_id': task.id, 'user_id' : task.user_id.id ,'hours' : 0.5 })

        return super(projectWorks,self).write(values)

    @api.multi
    def unlink(self, values):
        pass


class project_project(models.Model):
    _inherit = 'project.project'

    workservice_ids = fields.One2many('project.work.service','project_id')


class projectTask(models.Model):
    _inherit = 'project.task'

    locomotion = fields.Selection([("P", "Propia"), ("E", "Empresa")], default="E")
    typetask   = fields.Selection([('R', "Audi.Remota"), ("P", "Audi.Presencial"),("O","Otras Tareas")], default="O")


class project_work(models.Model):
    _inherit     = "project.task.work"
    _description = "Project Task Work Recurrent"

    state = fields.Boolean(string="Realizada", default=False)

    @api.constrains('state')
    def constraints_state(self):
        if self.state:
            self.task_id.date_end = fields.Date.today()
        else:
            self.task_id.date_end = None

    @api.onchange('state')
    def onchange_state(self):
        if self.state:
            self.task_id.date_end = fields.Date.today()
        else:
            self.task_id.date_end = None

    @api.constrains('date')
    def constraints_date(self):
        self.task_id.date_start = self.date

    @api.onchange('date')
    def onchange_date(self):
        self.task_id.date_start = self.date

    @api.multi
    def unlink(self):
        hat_obj = self.env['hr.analytic.timesheet']
        hat_ids = []
        print "Entra para elimnar lineas de ht.analytic.timesheet"
        for task in self:
            if task.hr_analytic_timesheet_id:
                hat_ids.append(task.hr_analytic_timesheet_id.id)
        if hat_ids:
            hat_obj.sudo().unlink(hat_ids)
            print "Elimina"
        return super(project_work,self).unlink()





