from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView


class Register(APIView):

    def post(self, request):

        return HttpResponse(200)
