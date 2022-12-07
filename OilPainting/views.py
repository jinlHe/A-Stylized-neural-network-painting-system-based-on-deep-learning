import argparse

import torch

import torch.optim as optim
from django.shortcuts import render

from painter import *

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def main(request):
    if request.COOKIES.get('login') is not None:
        return render(request, 'stylized-neural-painting-oil.htm')
    else:
        return render(request, 'login.html')

