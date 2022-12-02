from django.shortcuts import render
from painter import *

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def main(request):
    return render(request, 'stylized-tansfer.htm')


