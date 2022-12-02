import argparse
import os.path
import imageio
from OilPainting import settings
import torch.optim as optim
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from paint.models import mypicture
from painter import *
from .models import info

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def main(request):
    return render(request, 'stylized-neural-painting-oil.htm')


def getArgs(request):
    # 先清空output 因为多个图片都存在output下了 生成gif会混乱
    output_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # C:\Users\Donquixote\Desktop\OilPainting
    output_path = os.path.join(output_path, "static/output")
    if len(os.listdir(output_path)) != 0:
        # shutil.rmtree(output_path)  # 递归删除文件夹，即：删除非空文件夹
        del_files(output_path)
    photo = request.FILES.get("image")
    if photo is not None:
        canvas_color = request.POST.get("canvas_color")
        max_strokes = request.POST.get("max_strokes")
        output_type = request.POST.get("output_type")
        renderer = request.POST.get("renderer")
        print(canvas_color)
        print(max_strokes)
        print(output_type)
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
        print(photo.name)
        new_img.save()
        photo_path = os.path.join(settings.MEDIA_ROOT, 'photos', photo.name)
        args = setArgs(photo_path=photo_path, canvas_color=canvas_color, max_strokes=max_strokes, renderer=renderer,
                       renderer_checkpoint_dir=renderer_checkpoint_dir)
        pt = ProgressivePainter(args=args)
        list = info.objects.filter(id=1)
        if len(list) == 0:
            info.objects.create(current=0, total=0, msg="begin...")
        optimize_x(pt)
        myinfo = info.objects.get(id=1)
        myinfo.msg = "over..."
        myinfo.save()
        # 运行完后生成很多png 需要将png合成gif然后返回gif地址
        png_dir = output_path
        png_list = os.listdir(png_dir)
        png_name = get_png_name(png_list)
        gif_name = png_list[0].split('_')[0]
        gif_name = gif_name + '.gif'
        png2gif(source=args.output_dir, gifname=gif_name, time=0.05)
        gif_path = '/static/output/' + gif_name
        png_path = '/static/output/' + png_name
        myinfo = info.objects.get(id=1)
        myinfo.msg = ""
        myinfo.save()
        if output_type == 'gif':
            content = {
                'gif_path': gif_path
            }
        else:
            content = {
                'gif_path': png_path
            }
        response = JsonResponse(content, safe=False)
        response.set_cookie('content_img', png_list[0].split('_')[0])
        return response
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


def png2gif(source, gifname, time):
    os.chdir(source)  # os.chdir()：改变当前工作目录到指定的路径
    file_list = os.listdir()  # os.listdir()：文件夹中的文件/文件夹的名字列表
    frames = []  # 读入缓冲区
    for png in file_list:
        frames.append(imageio.v2.imread(png))
    imageio.mimsave(gifname, frames, 'GIF', duration=time)


def get_png_name(png_list):
    moban = png_list[0].split('_')[0]
    length = len(png_list) - 2
    png_name = moban + '_rendered_stroke_0' + str(length) + '.png'
    return png_name


def optimize_x(pt):
    pt._load_checkpoint()
    pt.net_G.eval()
    myinfo = info.objects.get(id=1)
    myinfo.current = 0
    myinfo.total = 0
    myinfo.msg = 'begin drawing...'
    myinfo.save()
    print('begin drawing...')

    PARAMS = np.zeros([1, 0, pt.rderr.d], np.float32)

    if pt.rderr.canvas_color == 'white':
        CANVAS_tmp = torch.ones([1, 3, 128, 128]).to(device)
    else:
        CANVAS_tmp = torch.zeros([1, 3, 128, 128]).to(device)

    for pt.m_grid in range(1, pt.max_divide + 1):

        pt.img_batch = utils.img2patches(pt.img_, pt.m_grid).to(device)
        pt.G_final_pred_canvas = CANVAS_tmp

        pt.initialize_params()
        pt.x_ctt.requires_grad = True
        pt.x_color.requires_grad = True
        pt.x_alpha.requires_grad = True
        utils.set_requires_grad(pt.net_G, False)

        pt.optimizer_x = optim.RMSprop([pt.x_ctt, pt.x_color, pt.x_alpha], lr=pt.lr, centered=True)

        pt.step_id = 0
        for pt.anchor_id in range(0, pt.m_strokes_per_block):
            pt.stroke_sampler(pt.anchor_id)
            iters_per_stroke = 40
            for i in range(iters_per_stroke):
                pt.G_pred_canvas = CANVAS_tmp

                # update x
                pt.optimizer_x.zero_grad()

                pt.x_ctt.data = torch.clamp(pt.x_ctt.data, 0.1, 1 - 0.1)
                pt.x_color.data = torch.clamp(pt.x_color.data, 0, 1)
                pt.x_alpha.data = torch.clamp(pt.x_alpha.data, 0, 1)

                pt._forward_pass()
                pt._drawing_step_states()
                pt._backward_x()

                pt.x_ctt.data = torch.clamp(pt.x_ctt.data, 0.1, 1 - 0.1)
                pt.x_color.data = torch.clamp(pt.x_color.data, 0, 1)
                pt.x_alpha.data = torch.clamp(pt.x_alpha.data, 0, 1)

                pt.optimizer_x.step()
                pt.step_id += 1

        v = pt._normalize_strokes(pt.x)
        PARAMS = np.concatenate([PARAMS, np.reshape(v, [1, -1, pt.rderr.d])], axis=1)
        CANVAS_tmp = pt._render(PARAMS)[-1]
        CANVAS_tmp = utils.img2patches(CANVAS_tmp, pt.m_grid + 1, to_tensor=True).to(device)

    pt._save_stroke_params(PARAMS)
    pt.final_rendered_images = pt._render(PARAMS)
    pt._save_rendered_images()


def setArgs(photo_path, canvas_color, max_strokes, renderer, renderer_checkpoint_dir):
    parser = argparse.ArgumentParser(description='STYLIZED NEURAL PAINTING')
    parser.add_argument('--img_path', type=str, default=photo_path, metavar='str',
                        help='path to test image (default: ./test_images/sunflowers.jpg)')
    parser.add_argument('--renderer', type=str, default=renderer, metavar='str',
                        help='renderer: [watercolor, markerpen, oilpaintbrush, rectangle (default oilpaintbrush)')
    parser.add_argument('--canvas_color', type=str, default=canvas_color, metavar='str',
                        help='canvas_color: [black, white] (default black)')
    parser.add_argument('--canvas_size', type=int, default=512, metavar='str',
                        help='size of the canvas for stroke rendering')
    parser.add_argument('--max_m_strokes', type=int, default=max_strokes, metavar='str',
                        help='max number of strokes (default 500)')
    parser.add_argument('--max_divide', type=int, default=5, metavar='N',
                        help='divide an image up-to max_divide x max_divide patches (default 5)')
    parser.add_argument('--beta_L1', type=float, default=1.0,
                        help='weight for L1 loss (default: 1.0)')
    parser.add_argument('--with_ot_loss', action='store_true', default=False,
                        help='imporve the convergence by using optimal transportation loss')
    parser.add_argument('--beta_ot', type=float, default=0.1,
                        help='weight for optimal transportation loss (default: 0.1)')
    parser.add_argument('--net_G', type=str, default='zou-fusion-net', metavar='str',
                        help='net_G: plain-dcgan, plain-unet, huang-net, or zou-fusion-net (default: zou-fusion-net)')
    parser.add_argument('--renderer_checkpoint_dir', type=str, default=renderer_checkpoint_dir, metavar='str',
                        help='dir to load neu-renderer (default: ./checkpoints_G_oilpaintbrush)')
    parser.add_argument('--lr', type=float, default=0.005,
                        help='learning rate for stroke searching (default: 0.005)')
    parser.add_argument('--output_dir', type=str, default=r'./static/output', metavar='str',
                        help='dir to save painting results (default: ./output)')
    args = parser.parse_args(args=[])
    return args
