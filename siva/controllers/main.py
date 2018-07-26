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

from openerp import http
from openerp.http import request
import googlemaps
import math


class EnviarLocales(http.Controller):


    def haversine(angle):
        h = math.sin(angle / 2) ** 2
        return h


    def Hdistance(self,lat1, long1, lat2, long2):
        # Note: The formula used in this function is not exact, as it assumes
        # the Earth is a perfect sphere.

        # Mean radius of Earth in Kms
        radius_earth = 6371

        # Convert latitude and longitude to
        # spherical coordinates in radians.
        degrees_to_radians = math.pi / 180.0
        phi1 = lat1 * degrees_to_radians
        phi2 = lat2 * degrees_to_radians
        lambda1 = long1 * degrees_to_radians
        lambda2 = long2 * degrees_to_radians
        dphi = phi2 - phi1
        dlambda = lambda2 - lambda1

        a = self.haversine(dphi) + math.cos(phi1) * math.cos(phi2) * self.haversine(dlambda)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = radius_earth * c
        return d

    def haversine(self,angle):
        h = math.sin(angle / 2) ** 2
        return h


    def distance(self,lat1, long1, lat2, long2):
        orig_coord = lat1, long1
        dest_coord = lat2, long2
        distancia = 0
        gmaps = googlemaps.Client(key='xxxxxxxxx')
        try:
            result = gmaps.distance_matrix(orig_coord, dest_coord, mode='driving', units='metric')
            distancia = result['rows'][0]['elements'][0]['distance']['value'] / 1000
        except KeyError:
            distancia = self.Hdistance(lat1, long1, lat2, long2)

        return distancia


    @http.route('/web/siva/login', type='http', auth="public",methods=['POST'])
    def get_login(self,login,password,latitud,longitud):
        uid = request.session.authenticate('givasl', login, password)
        print "Entra en web controller"
        print uid
        if uid is not False:
            uid=19 # a modo test
            #Buscamos relacion de locales permitidos utilizando la geolocalizacion como filtro
            objproject    = request.env['project.project']
            #Localizamos el id del empleado
            objrhemployee = request.env['hr.employee'].sudo().search([('user_id','=',uid)])
            print "Id Empleado %s " % objrhemployee
            if objrhemployee:
             #Localizammos el ids de los diferentes proyectos asociados al empleado
             objprojects_ids = objproject.sudo().search([('employee_id','=',objrhemployee.id),('partner_id.parent_id.activo_siva','!=',False)])
             #objprojects_ids = objproject.sudo().search([('employee_id', '=', objrhemployee.id)])
             #Procedemos agrupar por partner_id los filtrar por activo_siva = True
             apartner_id_all =[]
             apartner_id =[]
             print "Proyectos %s " % objprojects_ids
             for objpartner in objprojects_ids:
                 part_lat=objpartner.partner_id.partner_latitude
                 part_lon=objpartner.partner_id.partner_longitude
                 if part_lat and part_lon:
                    distan = self.distance(latitud,longitud,part_lat,part_lon)
                    print "Distancia %s " % distan
                    if distan < 1:
                        apartner_id.append(objpartner.id)
                        break
                    else:
                        apartner_id_all.append(objpartner.id)

             if len(apartner_id)!=0:
                 print  apartner_id
                 #return apartner_id
             else:
                 print apartner_id_all
                 #return apartner_id_all


        return  "Wrong login/password"


