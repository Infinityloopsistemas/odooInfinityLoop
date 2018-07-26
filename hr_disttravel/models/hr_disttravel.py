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
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from openerp import models, fields, api ,osv
from openerp import tools
from openerp.tools.translate import _
from dateutil import rrule, parser
import datetime
import googlemaps
import math


def distance(lat1, long1, lat2, long2):
    orig_coord = lat1,long1
    dest_coord =  lat2,long2
    distancia = 0
    gmaps = googlemaps.Client(key='xxxxxxxxxxxx')
    try:
        result = gmaps.distance_matrix(orig_coord, dest_coord, mode='driving', units='metric')
        distancia = result['rows'][0]['elements'][0]['distance']['value']/1000
    except KeyError:
        distancia = Hdistance(lat1, long1, lat2, long2)

    return distancia


def Hdistance(lat1, long1, lat2, long2):
    # Note: The formula used in this function is not exact, as it assumes
    # the Earth is a perfect sphere.

    # Mean radius of Earth in Kms
    radius_earth = 6371

    # Convert latitude and longitude to
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0
    phi1 = lat1 * degrees_to_radians
    phi2 = lat2 * degrees_to_radians
    lambda1 = long1 * degrees_to_radians
    lambda2 = long2 * degrees_to_radians
    dphi = phi2 - phi1
    dlambda = lambda2 - lambda1

    a = haversine(dphi) + math.cos(phi1) * math.cos(phi2) * haversine(dlambda)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius_earth * c
    return d

def haversine(angle):
  h = math.sin(angle / 2) ** 2
  return h


class HrDistTravelConfig(models.Model):
    _name = 'hr.dist.travel.config'


    initial_depot_lat = fields.Float(digits=(3,8), string="Latitud Origen",default=28.1107879)
    initial_depot_lon = fields.Float(digits=(3, 8),string="Longitud Origen",default=-15.420175)
    apikey            = fields.Char(string="API Key Google Maps", default='AIzaSyDyFx_OUiOmI6XYNnfbFAxyQkA_UMi0-9o')
    costfuel          = fields.Float(digits=(4,5), string="Coste Fuel",default=0.12)


class HrDistanceHistory(models.Model):
    _name = 'hr.dist.travel'
    _description = 'History Kms route for day'
    ETIQUETA = "VEHICULO"

    @api.depends('disttravel_ids')
    @api.one
    def _calc_total_distance(self):
        totdist = 0.0
        for rowlinetask in self.disttravel_ids:
            totdist = totdist + rowlinetask.distance_total
            print "Distancia total %s " % totdist
        self.total_distance = totdist

    @api.depends('disttravel_ids')
    @api.one
    def _calc_coste_distance(self):
        obj_config = self.env['hr.dist.travel.config']
        cost             = obj_config.search([])[0]
        if cost:
            self.total_coste = self.total_distance * cost.costfuel
        else:
            self.total_coste=0

    name           = fields.Char(string="Descripcion")
    employee_id    = fields.Many2one("hr.employee" ,domain = [('category_ids.name', 'in', [ETIQUETA])])
    period_id      = fields.Many2one("account.period")
    date_calculate = fields.Char(string="Date Calculate")
    total_distance = fields.Float( digits=(10,3), compute="_calc_total_distance")
    total_coste    = fields.Float( digits=(10,3), compute="_calc_coste_distance")
    disttravel_ids = fields.One2many('hr.dist.travel.line','hrdisttravel_id')
    state          = fields.Selection([('open', 'Sin Calcular'), ('calculate', 'Calculado')],
                                  string='Status', readonly=True, required=True,default="open",
                                  track_visibility='always', copy=False)






    class CreateDistanceCallback(object):
        """Create callback to calculate distances between points."""

        def __init__(self, locations):

            """Create the distance matrix."""
            size = len(locations)
            self.matrix = {}

            for from_node in xrange(size):
                self.matrix[from_node] = {}
                for to_node in xrange(size):
                    if from_node == to_node:
                        self.matrix[from_node][to_node] = 0
                    else:
                        x1 = locations[from_node][0]
                        y1 = locations[from_node][1]
                        x2 = locations[to_node][0]
                        y2 = locations[to_node][1]
                        self.matrix[from_node][to_node] = distance(x1, y1, x2, y2)

        def Distance(self, from_node, to_node):
            return self.matrix[from_node][to_node]

    @api.one
    def action_draft(self):
        self.state = "open"
        for datail in self.disttravel_ids:
            datail.unlink()


    @api.one
    def action_calculate_distance(self):


        hr_tra_confg        = self.env["hr.dist.travel.config"]
        obj_project_task    = self.env["project.task"]
        obj_employee        = self.env["hr.employee"]
        self.date_calculate = fields.Date.today()
        self.state          = "calculate"
        employee_ids        = [self.employee_id]
        obj_depots          = hr_tra_confg.search([])[0]
        DEPOTS = [obj_depots.initial_depot_lat,obj_depots.initial_depot_lon]

        for employee_id in employee_ids:
            # Intervalo de dias 1 al 25
            start_date = fields.Date.from_string(self.period_id.date_start) + datetime.timedelta(days=-5)
            stop_date  = fields.Date.from_string(self.period_id.date_stop) + datetime.timedelta(days=-5)
            adates= list(rrule.rrule(rrule.DAILY,
                         dtstart=parser.parse(fields.Date.to_string(start_date)),
                         until=parser.parse(fields.Date.to_string(stop_date) )))


            for row_date in adates:
                coordenadas = []
                partners = []
                search_date=  fields.Date.to_string(row_date)
                project_tasks_ids = obj_project_task.search([('locomotion','=','P'),('user_id', '=', employee_id.user_id.id),('date_deadline','>=',search_date),('date_deadline','<=',search_date),('project_id','!=',False)])
                coordenadas.append(DEPOTS)
                partners.append("GIVA SL")

                for row_task in project_tasks_ids:

                    idpartner= [row_task.project_id.partner_id.id]
                    if not row_task.project_id.partner_id.partner_latitude:

                        row_task.partner_id.geo_localize()

                    if row_task.project_id.partner_id.partner_latitude:
                        coordenadas.append([row_task.project_id.partner_id.partner_latitude,row_task.project_id.partner_id.partner_longitude])
                        partners.append(row_task.project_id.partner_id.name)


                #Procedemos a crear Matriz de distancias
                tsp_size = len(partners)

                # Optimizamos la ruta (TSps)
                # Create routing model
                if tsp_size > 1:

                    # TSP of size tsp_size
                    # Second argument = 1 to build a single tour (it's a TSP).
                    # Nodes are indexed from 0 to tsp_size - 1. By default the start of
                    # the route is node 0.
                    routing = pywrapcp.RoutingModel(tsp_size, 1)
                    search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()

                    # Setting first solution heuristic: the
                    # method for finding a first solution to the problem.
                    search_parameters.first_solution_strategy = (
                        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

                    # Create the distance callback, which takes two arguments (the from and to node indices)
                    # and returns the distance between these nodes.

                    dist_between_nodes = self.CreateDistanceCallback(coordenadas)
                    dist_callback = dist_between_nodes.Distance
                    routing.SetArcCostEvaluatorOfAllVehicles(dist_callback)
                    # Solve, returns a solution if any.
                    assignment = routing.SolveWithParameters(search_parameters)
                    if assignment:
                        # Solution cost.
                        print "Total distance: " + str(assignment.ObjectiveValue()) + " Kms\n"
                        # Inspect solution.
                        # Only one route here; otherwise iterate from 0 to routing.vehicles() - 1
                        route_number = 0
                        index = routing.Start(route_number)  # Index of the variable for the starting node.
                        route = ''
                        while not routing.IsEnd(index):
                            # Convert variable indices to node indices in the displayed route.
                            route += partners[routing.IndexToNode(index)] + ' -> '
                            index = assignment.Value(routing.NextVar(index))
                        route += partners[routing.IndexToNode(index)]
                        self.disttravel_ids.create({'hrdisttravel_id': self.id ,'name': route,'date':search_date,'distance_total':assignment.ObjectiveValue() })
                    else:
                        print 'Sin solucion'
                else:
                    print 'Specify an instance greater than 0.'





class HrDistanceTravelLine(models.Model):
    _name = 'hr.dist.travel.line'
    _description = 'Line travel history kms route for day'

    @api.one
    def _calccosttravel(self):
        obj_config = self.env['hr.dist.travel.config']
        cost = obj_config.search([])[0]
        self.costtravel = self.distance_total* cost.costfuel

    hrdisttravel_id    = fields.Many2one('hr.dist.travel')
    name               = fields.Char(string="Ruta")
    date               = fields.Date(string="Fecha")
    distance_total     = fields.Float(digits=(10, 3))
    costtravel         = fields.Float(digits=(10,3), string="Coste", compute='_calccosttravel')

















