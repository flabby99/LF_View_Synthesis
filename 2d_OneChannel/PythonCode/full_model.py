"""Contains the full model, including
Model
Optimizer
LR scheduler
Criterion
"""
import torch.nn as nn
import torch.optim as optim

from res_model import BigRipool
from torch.optim.lr_scheduler import CosineAnnealingLR
# from torch.optim.lr_scheduler import CyclicLR

def setup_model(args):
    """Returns a tuple of the model, criterion, optimizer and lr_scheduler"""
    print("Building model")
    model = BigRipool(
        layers=args.layers, 
        activation_fn=nn.ELU,
        thin=False,
        inchannels=193)
    criterion = nn.MSELoss(size_average=True)
    optimizer = optim.SGD(
        model.parameters(),
        lr=args.lr,
        momentum=args.momentum,
        weight_decay=args.weight_decay,
        nesterov=True)
    # See https://arxiv.org/abs/1608.03983
    lr_scheduler = CosineAnnealingLR(
        optimizer,
        T_max = (args.nEpochs // 10) + 1)
    """lr_scheduler = CyclicLR(
        optimizer)"""

    return (model, criterion, optimizer, lr_scheduler)
