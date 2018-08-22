import torch
import torch.nn as nn

from torch.nn.modules.batchnorm import _BatchNorm
from torch.nn  import functional as F

class _CINorm(_BatchNorm):
    def __init__(self, num_features, num_con=8, eps=1e-5, momentum=0.1, affine=False):
        super(_CINorm, self).__init__(
            num_features, eps, momentum, affine)
        self.ConBias = nn.Sequential(
            nn.Linear(num_con, num_features),
            nn.Tanh()
        )
    def forward(self, input, ConInfor):
        b, c = input.size(0), input.size(1)

        # Repeat stored stats and affine transform params
        running_mean = self.running_mean.repeat(b)
        running_var = self.running_var.repeat(b)

        if self.affine:
            bias = self.bias.repeat(b).view(b,c,1,1)
            weight = self.weight.repeat(b).view(b,c,1,1)

        tarBias = self.ConBias(ConInfor).view(b,c,1,1)
        input_reshaped = input.contiguous().view(1, b * c, *input.size()[2:])
        out = F.batch_norm(
            input_reshaped, running_mean, running_var, None, None,
            True, self.momentum, self.eps)

        # Reshape back
        self.running_mean.copy_(running_mean.view(b, c).mean(0, keepdim=False))
        self.running_var.copy_(running_var.view(b, c).mean(0, keepdim=False))

        return (out.view(b, c, *input.size()[2:])+tarBias)*weight + bias

    def eval(self):
        return self
class CINorm2d(_CINorm):

    def _check_input_dim(self, input):
        if input.dim() != 4:
            raise ValueError('expected 4D input (got {}D input)'
                             .format(input.dim()))
        super(CINorm2d, self)._check_input_dim(input)