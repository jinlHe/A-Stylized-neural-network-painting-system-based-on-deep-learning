import argparse

import imageio
from django.http import JsonResponse
from django.shortcuts import render
from torch import optim

from OilPainting import settings
from paint.models import mypicture
from painter import *

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def main(request):
    if request.COOKIES.get('content_img') is None:
        # return render(request, 'stylized-tansfer.htm')
        return render(request, 'no_content_img.html')
    else:
        return render(request, 'stylized-tansfer.htm')


def getArgs(request):
    photo = request.FILES.get("image")
    if photo is not None:
        output_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))  # C:\Users\Donquixote\Desktop\OilPainting
        output_path = os.path.join(output_path, "static/output")
        content_img = request.COOKIES.get('content_img')
        npz_name = content_img + '_strokes.npz'
        vector_file = os.path.join(output_path, npz_name)
        style_img_path = os.path.join(settings.MEDIA_ROOT, 'photos', photo.name)
        content_img_name = content_img + '_input.png'
        content_img_path = os.path.join(output_path, content_img_name)
        canvas_color = request.POST.get("canvas_color")
        max_strokes = request.POST.get("max_strokes")
        transfer_mode = request.POST.get("transfer_mode")
        renderer = request.POST.get("renderer")
        print(canvas_color)
        print(max_strokes)
        print(transfer_mode)
        print(renderer)
        if renderer == 'watercolor':
            renderer_checkpoint_dir = './checkpoints_G_watercolor'
        elif renderer == 'markerpen':
            renderer_checkpoint_dir = './checkpoints_G_markerpen'
        elif renderer == 'oilpaintbrush':
            renderer_checkpoint_dir = './checkpoints_G_oilpaintbrush'
        else:
            renderer_checkpoint_dir = './checkpoints_G_rectangle'
        new_img = mypicture(
            photo=photo,  # 拿到图片
            name=photo.name  # 拿到图片的名字
        )
        new_img.save()
        args = setArgs(renderer=renderer, vector_file=vector_file, style_img_path=style_img_path, content_img_path=content_img_path, transfer_mode=transfer_mode, canvas_color=canvas_color, renderer_checkpoint_dir=renderer_checkpoint_dir)
        pt = NeuralStyleTransfer(args=args)
        list = info.objects.filter(id=1)
        if len(list) == 0:
            info.objects.create(current=0, total=0, msg="begin...")
        optimize_x(pt, args)
        myinfo = info.objects.get(id=1)
        myinfo.msg = "over..."
        myinfo.save()

        png_name = content_img + '_style_transfer_' + photo.name + '.png'
        png_path = '/static/outout/' + png_name

        myinfo = info.objects.get(id=1)
        myinfo.msg = "over..."
        myinfo.save()
        content = {
                'gif_path': png_path
            }
        # return render(request, 'stylized-neural-painting-oil.htm', content)
        return JsonResponse(content, safe=False)
    else:
        content = {
            'error_msg': '请上传图片!'
        }
        return render(request, 'stylized-neural-painting-oil.htm', content)


def del_files(path_file):
    ls = os.listdir(path_file)
    for i in ls:
        f_path = os.path.join(path_file, i)
        # 判断是否是一个目录,若是,则递归删除
        if os.path.isdir(f_path):
            del_files(f_path)
        else:
            os.remove(f_path)


def getMsg(request):
    myinfo = info.objects.get(id=1)
    json = {'msg': myinfo.msg}
    return JsonResponse(json, safe=False)


def optimize_x(pt, args):
    pt._load_checkpoint()
    pt.net_G.eval()

    if args.transfer_mode == 0:  # transfer color only
        pt.x_ctt.requires_grad = False
        pt.x_color.requires_grad = True
        pt.x_alpha.requires_grad = False
    else:  # transfer both color and texture
        pt.x_ctt.requires_grad = True
        pt.x_color.requires_grad = True
        pt.x_alpha.requires_grad = True

    pt.optimizer_x_sty = optim.RMSprop([pt.x_ctt, pt.x_color, pt.x_alpha], lr=pt.lr)

    iters_per_stroke = 100
    for i in range(iters_per_stroke):
        pt.optimizer_x_sty.zero_grad()

        pt.x_ctt.data = torch.clamp(pt.x_ctt.data, 0.1, 1 - 0.1)
        pt.x_color.data = torch.clamp(pt.x_color.data, 0, 1)
        pt.x_alpha.data = torch.clamp(pt.x_alpha.data, 0, 1)

        if args.canvas_color == 'white':
            pt.G_pred_canvas = torch.ones([pt.m_grid * pt.m_grid, 3, 128, 128]).to(device)
        else:
            pt.G_pred_canvas = torch.zeros(pt.m_grid * pt.m_grid, 3, 128, 128).to(device)

        pt._forward_pass()
        pt._style_transfer_step_states()
        pt._backward_x_sty()
        pt.optimizer_x_sty.step()

        pt.x_ctt.data = torch.clamp(pt.x_ctt.data, 0.1, 1 - 0.1)
        pt.x_color.data = torch.clamp(pt.x_color.data, 0, 1)
        pt.x_alpha.data = torch.clamp(pt.x_alpha.data, 0, 1)

        pt.step_id += 1
    myinfo = info.objects.get(id=1)
    myinfo.msg = 'saving style transfer result...'
    myinfo.save()
    print('saving style transfer result...')
    v_n = pt._normalize_strokes(pt.x)
    pt.final_rendered_images = pt._render_on_grids(v_n)

    file_dir = os.path.join(
        args.output_dir, args.content_img_path.split('\\')[-1][:-4])
    plt.imsave(file_dir + '_style_img_' +
               args.style_img_path.split('\\')[-1][:-4] + '.png', pt.style_img_)
    plt.imsave(file_dir + '_style_transfer_' +
               args.style_img_path.split('\\')[-1][:-4] + '.png', pt.final_rendered_images[-1])


def setArgs(renderer, vector_file, style_img_path, content_img_path, transfer_mode, canvas_color, renderer_checkpoint_dir):
    parser = argparse.ArgumentParser(description='STYLIZED NEURAL PAINTING')
    parser.add_argument('--renderer', type=str, default=renderer, metavar='str',
                        help='renderer: [watercolor, markerpen, oilpaintbrush, rectangle (default oilpaintbrush)')
    parser.add_argument('--vector_file', type=str, default=vector_file, metavar='str',
                        help='path to pre-generated stroke vector file (default: ...)')
    parser.add_argument('--style_img_path', type=str, default=style_img_path, metavar='str',
                        help='path to style image (default: ...)')
    parser.add_argument('--content_img_path', type=str, default=content_img_path, metavar='str',
                        help='path to content image (default: ...)')
    parser.add_argument('--transfer_mode', type=int, default=transfer_mode, metavar='N',
                        help='style transfer mode, 0: transfer color only, 1: transfer both color and texture, '
                             'defalt: 1')
    parser.add_argument('--canvas_color', type=str, default=canvas_color, metavar='str',
                        help='canvas_color: [black, white] (default black)')
    parser.add_argument('--canvas_size', type=int, default=512, metavar='str',
                        help='size of the canvas for stroke rendering')
    parser.add_argument('--beta_L1', type=float, default=1.0,
                        help='weight for L1 loss (default: 1.0)')
    parser.add_argument('--beta_sty', type=float, default=0.5,
                        help='weight for vgg style loss (default: 0.5)')
    parser.add_argument('--net_G', type=str, default='zou-fusion-net', metavar='str',
                        help='net_G: plain-dcgan, plain-unet, huang-net, or zou-fusion-net (default: zou-fusion-net)')
    parser.add_argument('--renderer_checkpoint_dir', type=str, default=renderer_checkpoint_dir, metavar='str',
                        help='dir to load neu-renderer (default: ./checkpoints_G_oilpaintbrush)')
    parser.add_argument('--lr', type=float, default=0.005,
                        help='learning rate for stroke searching (default: 0.005)')
    parser.add_argument('--output_dir', type=str, default=r'./static/output', metavar='str',
                        help='dir to save style transfer results (default: ./output)')
    args = parser.parse_args()
    return args
