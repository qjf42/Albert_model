# coding: utf-8

import torch
import pandas as pd


class PytorchUtils:
    @staticmethod
    def load_model(model_path: str, device: str = 'cpu') -> torch.nn.Module:
        try:
            model = torch.load(model_path, map_location=torch.device(device))
            assert isinstance(model, torch.nn.Module), 'model is not a torch.nn.Module'
            model.eval()
        except Exception as e:
            raise Exception(f'Failed to load model, {e}')
        return model

    @staticmethod
    def memory_usage(model: torch.nn.Module) -> int:
        # param size
        size = sum(p.numel() * p.element_size() for p in model.parameters())
        # TODO
        # forward
        # output
        # return f'{(size / 2**20):.2f}MB'
        return size

    @staticmethod
    def profile(model: torch.nn.Module) -> pd.DataFrame:
        # https://pytorch.org/tutorials/recipes/recipes/profiler.html
        pass
