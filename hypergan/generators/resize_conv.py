import tensorflow as tf
import numpy as np
from hypergan.util.hc_tf import *

def generator(config, net):
    depth=0
    w=int(net.get_shape()[1])
    target_w=int(config['x_dims'][0])
    while(w<target_w):
      w*=2
      depth +=1

    target_size = int(net.get_shape()[1])*(2**depth)*int(net.get_shape()[2])*(2**depth)*config['channels']
    nets=[]
    activation = config['generator.activation']
    batch_size = config['batch_size']
    depth_reduction = np.float32(config['generator.resize_conv.depth_reduction'])
    batch_norm = config['generator.regularizers.layer']

    s = [int(x) for x in net.get_shape()]
    net = block_conv(net, tf.nn.tanh, batch_size, 'identity', 'g_layers_init', output_channels=int(net.get_shape()[3]), filter=3, dropout=get_tensor('dropout'))
    z_proj = net

    for i in range(depth):
        s = [int(x) for x in net.get_shape()]
        layers = int(net.get_shape()[3])//depth_reduction
        if(i == depth-1):
            layers=config['channels']
        resized_wh=[s[1]*2, s[2]*2]
        if config['generator.layer.noise']:
            noise = [s[0],resized_wh[0],resized_wh[1],2**(depth-i)]
        else:
            noise = None
        net = tf.image.resize_images(net, [resized_wh[0], resized_wh[1]], 1)
        fltr = 3
        if fltr > net.get_shape()[1]:
            fltr=int(net.get_shape()[1])
        if fltr > net.get_shape()[2]:
            fltr=int(net.get_shape()[2])
        #if(i == 0):
        #    net = block_conv(net, tf.nn.tanh, batch_size, 'identity', 'g_layers_'+str(i), output_channels=layers, filter=fltr, batch_norm=None, noise_shape=noise, dropout=get_tensor('dropout'))
        #else:
        net = block_conv(net, activation, batch_size, 'identity', 'g_layers_'+str(i), output_channels=layers, filter=fltr, batch_norm=batch_norm, noise_shape=noise)
        if(net.get_shape()[3] != 3):
            #split_z_proj = tf.slice(z_proj, [0,0,0,0], [-1,-1,-1,1024//(2**(i+1))])
            #resized_z_proj = tf.image.resize_images(split_z_proj, [resized_wh[0], resized_wh[1]], 1)
            #print("RESIZED ", resized_z_proj.get_shape(), net.get_shape())
            #net = tf.concat(3, [net, resized_z_proj])
            
            reshaped_z_proj = tf.reshape(z_proj, [config['batch_size'], resized_wh[0], resized_wh[1], -1])
            print("RESHAPED", reshaped_z_proj.get_shape(), net.get_shape())
            net = tf.concat(3, [net, reshaped_z_proj])

        if(i == depth-1):
            first3 = net
        else:
            first3 = tf.slice(net, [0,0,0,0], [-1,-1,-1,3])
        #if(i<depth -1):
        first3 = batch_norm(config['batch_size'], name='g_bn_first3_'+str(i))(first3)
        first3 = config['generator.final_activation'](first3)
        nets.append(first3)
        size = int(net.get_shape()[1])*int(net.get_shape()[2])*int(net.get_shape()[3])
        print("[generator] layer",net, size, target_size,"  with noise ",noise)

    return nets


