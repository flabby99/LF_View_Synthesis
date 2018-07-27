"""Handles functions such as loading from checkpoints"""
import os
import math

import torch

def check_cuda(config):
    """Checks cuda settings from config - Returns true if cuda available"""
    cuda = config['NETWORK']['cuda'] == 'True'
    cuda_device = config['NETWORK']['gpu_id']
    if cuda:
        print("=> using gpu id: '{}'".format(cuda_device))
        os.environ["CUDA_VISIBLE_DEVICES"] = cuda_device
        if not torch.cuda.is_available():
            raise Exception("No GPU found or Wrong gpu id")
        print("=> cudnn version is", torch.backends.cudnn.version())
    return cuda

def save_checkpoint(model, epoch, optimizer, best_loss, save_dir, name):
    """Saves model params and epoch number at save_dir/name"""
    if (model is None) or (epoch is None):
        print("No model or epoch given for saving")
        return -1
        
    model_out_path = os.path.join(save_dir, name)
    state = {"epoch": epoch, 
             "model": model,
             "state_dict": model.state_dict(),
             "best_loss": best_loss,
             "optimizer": optimizer.state_dict()}

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    torch.save(state, model_out_path)

    print("Checkpoint saved to {}".format(model_out_path))

def load_from_checkpoint(model, optimizer, args, config):
    resume_location = os.path.join(
        config['PATH']['checkpoint_dir'],
        args.checkpoint)
    best_loss = math.inf
    if os.path.isfile(resume_location):
        print("=> loading checkpoint '{}'".format(resume_location))
        checkpoint = torch.load(resume_location)
        args.start_epoch = checkpoint["epoch"] + 1
        model.load_state_dict(checkpoint["model"].state_dict())
        best_loss = checkpoint["best_loss"]
        optimizer.load_state_dict(checkpoint["optimizer"])
        print("=> loaded checkpoint '{}' (epoch {})".format(
                resume_location, checkpoint['epoch']))
    else:
        print("=> no checkpoint found at '{}'".format(resume_location))
    return best_loss

def load_weights(model, args, config):
    """Load the state dict into the passed in model"""

    weights_location = os.path.join(
        config['PATH']['model_dir'],
        args.pretrained)
    if os.path.isfile(weights_location):
        print("=> loading model '{}'".format(weights_location))
        weights = torch.load(weights_location)
        model.load_state_dict(weights['model'].state_dict())
    else:
        print("=> no model found at '{}'".format(weights_location))

def load_model_and_weights(args, config):
    """Load the model defined in config and args and the weights"""
    # Load the architecture
    model = torch.load(os.path.join(
                config['PATH']['model_dir'], args.pretrained))['model']
    # Load the weights
    load_weights(model, args, config)
    return model

def print_mem_usage():
    """Prints torch gpu memeory usage"""
    print("Using {:5} / {:5} tensor memory {:.1f}% of max".format(
        torch.cuda.memory_allocated(),
        torch.cuda.max_memory_allocated(),
        (torch.cuda.memory_allocated() / 
         torch.cuda.max_memory_allocated()) * 100
    ))
    print("Using {} / {} cached memory {:.1f}% of max".format(
        torch.cuda.memory_cached(),
        torch.cuda.max_memory_cached(),
        (torch.cuda.memory_cached() / 
         torch.cuda.max_memory_cached()) * 100
    ))

def merge_weights(avg_model, new_model, interpolation_factor = 0.5):
    """Merges the weights of model1 and model2"""
    beta = interpolation_factor    
    params1 = avg_model.named_parameters()
    params2 = new_model.named_parameters()

    dict_params2 = dict(params2)

    for name1, param1 in params1:
        if name1 in dict_params2:
            if "weight" not in name1:
                continue
            else:
                dict_params2[name1].data.copy_(
                    (1-beta)*param1.data + (beta)*dict_params2[name1].data)

    model_dict = avg_model.state_dict()
    model_dict.update(dict_params2)
    avg_model.load_state_dict(model_dict)