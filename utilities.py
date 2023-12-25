from torch_geometric.datasets import CoraFull, Reddit
from ogb.nodeproppred import PygNodePropPredDataset
import torch

from backbones.gcn import GCN
from backbones.gat import GAT
from methods.joint import Joint
from methods.bare import Bare
from methods.ergnn import ERGNN
from methods.ssm import SSM
from methods.cgm import CGM
from methods.ewc import EWC
from methods.mas import MAS
from methods.gem import GEM
from methods.twp import TWP
from methods.lwf import LWF


def get_memory_bank_name(args):
    if args.cgl_method == "ergnn":
        result_name = f"_MFPlus"
    elif args.cgl_method == "ssm":
        result_name = f"_random"
    elif "cgm" in args.cgl_method:
        cgm_args = eval(args.cgm_args)
        result_name = f"_flr_{cgm_args['feat_lr']}_{cgm_args['n_encoders']}_{cgm_args['update_epoch']}_dim_{cgm_args['hid_dim']}"
        if cgm_args['activation'] == False:
            result_name += "_nonact"
    else:
        result_name = f""

    if args.pseudo_label:
        result_name += "_pl"
    return f"{args.dataset_name}_{args.budget}_{args.cgl_method}" + result_name

def print_performance_matrix(performace_matrix, m_update):
    for k in range(performace_matrix.shape[0]):
        accs = []
        for k_ in range(k + 1):
            acc = performace_matrix[k, k_]
            accs.append(acc)
            if m_update == "all":
                print(f"T{k_} {acc:.2f}",end="|")
            elif m_update == "onlyCurrent":
                if k == k_:
                    print(f"T{k_} {acc:.2f}",end="|")
        print(f"AP: {sum(accs) / len(accs):.2f}")

def get_dataset(args):
    if args.dataset_name == "corafull":
        dataset = CoraFull(args.data_dir)
    elif args.dataset_name == "arxiv":
        dataset = PygNodePropPredDataset(name="ogbn-arxiv", root=args.data_dir)
        data = dataset[0]
        data.y.squeeze_()
    elif args.dataset_name == "reddit":
        dataset = Reddit(args.data_dir)
    elif args.dataset_name == "products":
        dataset = PygNodePropPredDataset(name="ogbn-products", root=args.data_dir)
        dataset.data.y.squeeze_()
    elif args.dataset_name == "papers100m":
        dataset = PygNodePropPredDataset(name="ogbn-papers100M", root=args.data_dir)
        dataset.data.y.squeeze_()
    return dataset
    
def get_backbone_model(dataset, data_stream, args):
    if args.cgl_method == "twp":
        model = GAT(dataset.num_features, 32, data_stream.n_tasks * args.cls_per_task, 2).to(args.device)
    else:
        model = GCN(dataset.num_features, args.hidden, data_stream.n_tasks * args.cls_per_task, args.layers_num).to(args.device)
    return model

def get_cgl_model(model, data_stream, args):
    if args.cgl_method == "joint":
        cgl_model = Joint(model, args.lr, data_stream.tasks, None, args.m_update, args.pseudo_label, args.device)
    elif args.cgl_method == "bare":
        cgl_model = Bare(model, data_stream.tasks, args.device)
    elif args.cgl_method == "ergnn":
        cgl_model = ERGNN(model, args.lr, data_stream.tasks, args.budget, args.m_update, args.pseudo_label, args.device)
    elif args.cgl_method == "ssm":
        cgl_model = SSM(model, args.lr, data_stream.tasks, args.budget, args.m_update, args.pseudo_label, args.device)
    elif args.cgl_method == "cgm":
        cgl_model = CGM(model, args.lr, data_stream.tasks, args.budget, args.m_update, args.pseudo_label, args.device, eval(args.cgm_args))
    elif args.cgl_method == "ewc":
        cgl_model = EWC(model, data_stream.tasks, args.device, eval(args.ewc_args))
    elif args.cgl_method == "mas":
        cgl_model = MAS(model, data_stream.tasks, args.device, eval(args.mas_args))
    elif args.cgl_method == "gem":
        cgl_model = GEM(model, data_stream.tasks, args.device, eval(args.gem_args))
    elif args.cgl_method == "twp":
        cgl_model = TWP(model, data_stream.tasks, args.device, eval(args.twp_args))
    elif args.cgl_method == "lwf":
        cgl_model = LWF(model, data_stream.tasks, args.device, eval(args.lwf_args))
    return cgl_model