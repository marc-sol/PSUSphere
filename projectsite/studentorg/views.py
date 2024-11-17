from django.shortcuts import render

from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from studentorg.models import Organization
from studentorg.forms import OrganizationForm
from studentorg.models import OrgMember
from studentorg.forms import OrgMemberForm
from studentorg.models import Student
from studentorg.forms import StudentForm
from studentorg.models import College
from studentorg.forms import CollegeForm
from studentorg.models import Program
from studentorg.forms import ProgramForm
from typing import Any
from django.db.models.query import QuerySet
from django.db.models import Q
from django.urls import reverse_lazy
from django.db import connection 
from django.http import JsonResponse 
from django.db.models.functions import ExtractMonth
from django.db.models import Count 
from datetime import datetime
from django.utils.decorators import method_decorator 
from django.contrib.auth.decorators import login_required

@method_decorator(login_required, name='dispatch')
class HomePageView(ListView): 
    model = Organization 
    context_object_name = 'home' 
    template_name = "home.html"

class ChartView(ListView): 
    template_name = 'chart.html'
    
    def get_context_data(self, **kwargs): 
        context = super().get_context_data(**kwargs) 
        return context
    
    def get_queryset(self, *args, **kwargs): 
        pass

def PieCountbySeverity(request): 
    query = ''' 
    SELECT severity_level, COUNT(*) as count 
    FROM fire_incident GROUP BY severity_level 
    ''' 
    data = {} 
    with connection.cursor() as cursor: 
        cursor.execute(query) 
        rows = cursor.fetchall()
    if rows: # Construct the dictionary with severity level as keys and count as values 
        data = {severity: count for severity, count in rows} 
    else: 
        data = {}
    return JsonResponse(data)

def MultilineIncidentTop3Country(request):
    
    query = '''
        SELECT 
        fl.country,
        strftime('%m', fi.date_time) AS month, 
        COUNT(fi.id) AS incident_count 
    FROM 
        fire_incident fi 
    JOIN 
        fire_locations fl ON fi.location_id = fl.id 
    WHERE 
        fl.country IN ( 
            SELECT 
                fl_top.country 
            FROM 
                fire_incident fi_top 
            JOIN 
                fire_locations fl_top ON fi_top.location_id = fl_top.id 
            WHERE 
                strftime('%Y', fi_top.date_time) = strftime('%Y', 'now') 
            GROUP BY 
                fl_top.country 
            ORDER BY 
                COUNT(fi_top.id) DESC 
            LIMIT 3 
        ) 
        AND strftime('%Y', fi.date_time) = strftime('%Y', 'now') 
    GROUP BY 
        fl.country, month 
    ORDER BY 
        fl.country, month; 
    '''

    with connection.cursor() as cursor: 
        cursor.execute(query) 
        rows = cursor.fetchall()
        
    # Initialize a dictionary to store the result 
    result = {}

    # Initialize a set of months from January to December 
    months = set(str(i).zfill(2) for i in range(1, 13))

    # Loop through the query results 
    for row in rows: 
        country = row[0] 
        month = row[1] 
        total_incidents = row[2]

        # If the country is not in the result dictionary, initialize it with all months set to zero 
        if country not in result: 
            result[country] = {month: 0 for month in months}

        # Update the incident count for the corresponding month 
        result[country][month] = total_incidents

        # Ensure there are always 3 countries in the result 
        while len(result) < 3: 
            # Placeholder name for missing countries 
            missing_country = f"Country {len(result) + 1}" 
            result[missing_country] = {month: 0 for month in months}
        
        for country in result: 
            result[country] = dict(sorted(result[country].items()))
        return JsonResponse(result)
    
def multipleBarbySeverity(request): 
    query = '''
    SELECT 
        fi.severity_level, 
        strftime('%m', fi.date_time) AS month, 
        COUNT(fi.id) AS incident_count 
    FROM 
        fire_incident fi
    GROUP BY fi.severity_level, month 
    '''

    with connection.cursor() as cursor: 
        cursor.execute(query) 
        rows = cursor.fetchall()
    
    result = {} 
    months = set(str(i).zfill(2) for i in range(1, 13))
    
    for row in rows: 
        level = str(row[0]) # Ensure the severity level is a string 
        month = row[1] 
        total_incidents = row[2]

        if level not in result: 
            result[level] = {month: 0 for month in months}

        result[level][month] = total_incidents

        # Sort months within each severity level 
        for level in result: 
            result[level] = dict(sorted(result[level].items()))
        return JsonResponse(result)


class OrganizationList(ListView): 
    model = Organization 
    context_object_name = 'organization' 
    template_name = 'org_list.html' 
    paginate_by = 5

    def get_queryset(self, *args, **kwargs): 
        qs = super(OrganizationList, self).get_queryset(*args, **kwargs) 
        if self.request.GET.get("q") != None:
            query = self.request.GET.get('q') 
            qs = qs.filter(Q(name__icontains=query) | 
                           Q(description__icontains=query)) 
            return qs

class OrganizationCreateView(CreateView): 
    model = Organization 
    form_class = OrganizationForm 
    template_name = 'org_add.html' 
    success_url = reverse_lazy('organization-list')

class OrganizationUpdateView(UpdateView): 
    model = Organization 
    form_class = OrganizationForm 
    template_name = 'org_edit.html' 
    success_url = reverse_lazy('organization-list')

class OrganizationDeleteView(DeleteView): 
    model = Organization 
    template_name = 'org_del.html' 
    success_url = reverse_lazy('organization-list')

class OrgMemberList(ListView): 
    model = OrgMember 
    context_object_name = 'orgmember' 
    template_name = 'org_member_list.html' 
    paginate_by = 5

    def get_queryset(self, *args, **kwargs): 
        qs = super(OrgMemberList, self).get_queryset(*args, **kwargs) 
        if self.request.GET.get("q") != None:
            query = self.request.GET.get('q') 
            qs = qs.filter(Q(name__icontains=query) | 
                           Q(description__icontains=query)) 
            return qs

class OrgMemberCreateView(CreateView): 
    model = OrgMember 
    form_class = OrgMemberForm 
    template_name = 'org_member_add.html' 
    success_url = reverse_lazy('orgmember-list')

class OrgMemberUpdateView(UpdateView): 
    model = OrgMember 
    form_class = OrgMemberForm 
    template_name = 'org_member_edit.html' 
    success_url = reverse_lazy('orgmember-list')

class OrgMemberDeleteView(DeleteView): 
    model = OrgMember 
    template_name = 'org_member_del.html' 
    success_url = reverse_lazy('orgmember-list')

class StudentList(ListView): 
    model = Student
    context_object_name = 'student' 
    template_name = 'student_list.html' 
    paginate_by = 5

    def get_queryset(self, *args, **kwargs): 
        qs = super(StudentList, self).get_queryset(*args, **kwargs) 
        if self.request.GET.get("q") != None:
            query = self.request.GET.get('q') 
            qs = qs.filter(Q(name__icontains=query) | 
                           Q(description__icontains=query)) 
            return qs

class StudentCreateView(CreateView): 
    model = Student 
    form_class = StudentForm
    template_name = 'student_add.html' 
    success_url = reverse_lazy('student-list')

class StudentUpdateView(UpdateView): 
    model = Student 
    form_class = StudentForm 
    template_name = 'student_edit.html' 
    success_url = reverse_lazy('student-list')

class StudentDeleteView(DeleteView): 
    model = Student 
    template_name = 'student_del.html' 
    success_url = reverse_lazy('student-list')

class CollegeList(ListView): 
    model = College
    context_object_name = 'college' 
    template_name = 'college_list.html' 
    paginate_by = 5

    def get_queryset(self, *args, **kwargs): 
        qs = super(CollegeList, self).get_queryset(*args, **kwargs) 
        if self.request.GET.get("q") != None:
            query = self.request.GET.get('q') 
            qs = qs.filter(Q(name__icontains=query) | 
                           Q(description__icontains=query)) 
            return qs

class CollegeCreateView(CreateView): 
    model = College 
    form_class = CollegeForm
    template_name = 'college_add.html' 
    success_url = reverse_lazy('college-list')

class CollegeUpdateView(UpdateView): 
    model = College 
    form_class = CollegeForm 
    template_name = 'college_edit.html' 
    success_url = reverse_lazy('college-list')

class CollegeDeleteView(DeleteView): 
    model = College 
    template_name = 'college_del.html' 
    success_url = reverse_lazy('college-list')

class ProgramList(ListView): 
    model = College
    context_object_name = 'college' 
    template_name = 'college_list.html' 
    paginate_by = 5

    def get_queryset(self, *args, **kwargs): 
        qs = super(ProgramList, self).get_queryset(*args, **kwargs) 
        if self.request.GET.get("q") != None:
            query = self.request.GET.get('q') 
            qs = qs.filter(Q(name__icontains=query) | 
                           Q(description__icontains=query)) 
            return qs

class ProgramCreateView(CreateView): 
    model = Program 
    form_class = ProgramForm
    template_name = 'program_add.html' 
    success_url = reverse_lazy('program-list')

class ProgramUpdateView(UpdateView): 
    model = Program 
    form_class = ProgramForm
    template_name = 'program_edit.html' 
    success_url = reverse_lazy('program-list')

class ProgramDeleteView(DeleteView): 
    model = Program 
    template_name = 'program_del.html' 
    success_url = reverse_lazy('program-list')