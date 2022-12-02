import argparse

import imageio
from django.http import JsonResponse
from django.shortcuts import render
from torch import optim

from OilPainting import settings
from paint.models import mypicture
from painter import *




def login(request):
    return render(request, 'login.html')

