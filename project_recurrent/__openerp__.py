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
{
    'name': "Recurrent Task Project",

    'summary': """
       Generador de tareas recurrentes con atributos """,

    'description': """
        Generador de tareas recurrentes segun los criterios de parametrización
    """,

    'author': "Infinityloop Sistemas S.L",
    'website': "http://www.infinityloop.es",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Utilities',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','project'],

    # always loaded
    'data': [
         'security/ir.model.access.csv',
         'views/project.xml',
         'wizard/project_create_task_view.xml',

    ],
    # only loaded in demonstration mode

    'installable': True,
    'auto_install': False,
}