import os
import glob
import torch
import argparse
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from model import *
from dataloader import *
import pandas

def arg_parser():
    parser = argparse.ArgumentParser(description='Data Pruning Parser')
    parser.add_argument('--model', type=str, default='./model/proxy_ordinal.ckpt', help='model path')
    parser.add_argument('--thr1', '--threshold1', default=0, type=int, help='rural score threshold')
    parser.add_argument('--thr2', '--threshold2', default=10, type=int, help='city score threshold')
    parser.add_argument('--path', type=str, default='./data/zl15_32645/', help='./data/zl*_timeline/') 
    parser.add_argument('--csv_name', type=str, help='example.csv') 
    return parser.parse_args()

def main(args):
    net = models.resnet18(pretrained = True)
    feature_size = net.fc.in_features
    net.fc = nn.Sequential()
    model = BinMultitask(net, feature_size, args.thr1, args.thr2, ordinal=True)
    
    if torch.cuda.device_count() > 1:
        model = nn.DataParallel(model)    

    model.load_state_dict(torch.load(args.model)['state_dict'], strict=True)    
    model.cuda()
    with torch.no_grad():
        return_model_score(args, model, args.path)


def return_model_score(args, model, path):
    model.eval()
    transform = transforms.Compose([
                                  transforms.Resize(256),
                                  transforms.CenterCrop(224),
                                  transforms.ToTensor(),
                                  transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    
    dir_path = path
    adm1_list = glob.glob(path+'*/')

    y_x_dict = {'y_x':[],'adm1':[],'adm2':[],'score':[]}

    for adm1_path in adm1_list:
        print(adm1_path)
        adm2_list = glob.glob(adm1_path+'*/')
        for adm2_path in adm2_list[:]:
            print(adm2_path)
            png_list = glob.glob(adm2_path+'*.png')
            for png_path in png_list:
                image = Image.open(png_path)
                print(png_path)
                image = transform(image).unsqueeze(0).cuda()
                _, score, _ = model(image)
                del image
                adm1 = adm1_path.split('/')[-2]
                adm2 = adm2_path.split('/')[-2]
                png = png_path.split('/')[-1][:-len('.png')]
                y_x_dict['y_x'].append(png)
                y_x_dict['adm1'].append(adm1)
                y_x_dict['adm2'].append(adm2)
                y_x_dict['score'].append(score.item())        

    df = pd.DataFrame.from_dict(y_x_dict)
    df.to_csv('./local_score/'+args.csv_name, index=False)
    total = 0

if __name__ == '__main__':
    args = arg_parser()
    main(args)